from __future__ import annotations

from dataclasses import replace

import pandas as pd

from agents.policy import (
    adjacent_niche_suggestion,
    build_context_profile,
    classify_outcome,
    expand_query_terms,
    should_drill_down,
    should_expand_scope,
    should_raise_margin_floor,
    should_relax_niche,
    should_shift_weights_for_weak_demand,
)
from core.action_engine import build_action_block
from core.differentiation import apply_undiscovered_detector
from core.discovery.adapters import build_default_adapters
from core.features import engineer_features
from core.models import AnalysisRun, ResearchRequest, TraceEvent
from core.processing import prepare_candidates
from core.reasoning import build_reasoning_layers
from core.reporting import build_run_insights, write_json_report, write_pdf_report
from core.scoring import score_products, summarize_effective_weights
from storage.db import ResearchRepository
from utils.helpers import make_json_safe, utc_now_iso


class ProductResearchOrchestrator:
    def __init__(self, repository: ResearchRepository | None = None) -> None:
        self.repository = repository or ResearchRepository()
        self.adapters = build_default_adapters()

    def run(
        self,
        request: ResearchRequest,
        on_event: callable | None = None,
        generate_pdf: bool = False,
    ) -> AnalysisRun:
        context = build_context_profile(request)
        run = AnalysisRun.empty(request=request, context=context)
        run.created_at = utc_now_iso()
        self.repository.create_run(run)

        def emit(step: str, status: str, message: str, decision: str | None = None, **metadata: object) -> None:
            event = TraceEvent(
                step=step,
                status=status,
                message=message,
                timestamp=utc_now_iso(),
                decision=decision,
                metadata=make_json_safe(metadata),
            )
            run.trace.append(event)
            self.repository.save_trace_event(run.run_id, event)
            if on_event is not None:
                on_event(event)

        try:
            emit(
                "input_understanding",
                "running",
                f"Built context profile for {request.platform} in {request.market} with a {context.budget_segment} budget posture.",
                budget_segment=context.budget_segment,
                margin_floor=context.margin_floor,
            )

            candidates = []
            emit("data_discovery", "running", "Attempting primary live discovery adapters first.")
            live_candidates = []
            if request.platform == "Amazon":
                live_candidates.extend(self.adapters["amazon_live"].discover(request, context, context.query_terms))
            else:
                live_candidates.extend(self.adapters["aliexpress_live"].discover(request, context, context.query_terms))
            candidates.extend(live_candidates)

            processed = prepare_candidates(candidates, request, context)
            live_count = len(processed.index) if not processed.empty else 0
            emit("data_discovery", "info", f"Primary live discovery produced {live_count} cleaned candidates.", source="live")

            if should_expand_scope(live_count):
                expanded_terms = expand_query_terms(context.query_terms, request.niche, processed["category"].tolist() if not processed.empty else [])
                context = replace(context, query_terms=expanded_terms, budget_tolerance=0.15)
                run.context = context
                emit(
                    "data_discovery",
                    "decision",
                    "Candidate pool is thin, so the agent expanded search scope with adjacent terms and a wider budget band.",
                    decision="expand_scope",
                    threshold="candidate_count < 20",
                    effect={"query_terms": expanded_terms, "budget_tolerance": 0.15},
                )
                snapshot_key = "amazon_snapshot" if request.platform == "Amazon" else "aliexpress_snapshot"
                snapshot_candidates = self.adapters[snapshot_key].discover(request, context, context.query_terms)
                candidates.extend(snapshot_candidates)
                processed = prepare_candidates(candidates, request, context)
                emit("data_discovery", "info", f"Snapshot discovery increased the cleaned pool to {len(processed.index)}.", source="snapshot")

            if should_relax_niche(len(processed.index) if not processed.empty else 0):
                context.strategy_flags.append("relaxed_niche")
                run.context = context
                emit(
                    "data_discovery",
                    "decision",
                    "The pool is still too small, so the agent relaxed niche strictness while keeping the requested market and platform fixed.",
                    decision="relax_niche",
                    threshold="candidate_count < 12",
                    effect={"relaxed_niche": True},
                )
                offline_candidates = self.adapters["offline_catalog"].discover(
                    request,
                    context,
                    context.query_terms,
                    relax_niche=True,
                    top_k=40,
                )
                candidates.extend(offline_candidates)
                processed = prepare_candidates(candidates, request, context)
            elif should_expand_scope(len(processed.index) if not processed.empty else 0):
                offline_candidates = self.adapters["offline_catalog"].discover(
                    request,
                    context,
                    context.query_terms,
                    relax_niche=False,
                    top_k=30,
                )
                candidates.extend(offline_candidates)
                processed = prepare_candidates(candidates, request, context)

            if processed.empty:
                offline_candidates = self.adapters["offline_catalog"].discover(
                    request,
                    context,
                    context.query_terms,
                    relax_niche=True,
                    top_k=40,
                )
                candidates.extend(offline_candidates)
                processed = prepare_candidates(candidates, request, context)

            if processed.empty:
                emit(
                    "processing",
                    "warning",
                    "No products remained after applying budget and niche relevance checks.",
                )
                return self._finalize_no_match_run(run, request, generate_pdf, emit)

            emit(
                "processing",
                "running",
                f"Normalized, deduplicated, and structured {len(processed.index)} candidate products across {processed['category'].nunique() if not processed.empty else 0} categories.",
            )

            featured = engineer_features(processed, request, context)
            emit(
                "feature_extraction",
                "running",
                f"Engineered monetization and signal features for {len(featured.index)} candidates using a margin floor of {context.margin_floor:.0%}.",
            )

            if featured.empty:
                emit(
                    "feature_extraction",
                    "warning",
                    "No candidates had enough relevant signal to move into scoring.",
                )
                return self._finalize_no_match_run(run, request, generate_pdf, emit)

            if should_shift_weights_for_weak_demand(featured["demand_reliability"].tolist()):
                context.strategy_flags.append("weak_demand_reliability")
                run.context = context
                emit(
                    "feature_extraction",
                    "decision",
                    "Demand signals are noisy, so the agent will lean more on virality, niche fit, and economics during scoring.",
                    decision="shift_scoring_weights",
                    threshold="average demand reliability < 50",
                    effect={"strategy_flags": context.strategy_flags},
                )

            early_pool = featured.sort_values(["demand_score", "platform_fit_score"], ascending=False).head(10)
            if should_drill_down(early_pool["raw_competition"].tolist()):
                drill_terms = expand_query_terms(context.query_terms, adjacent_niche_suggestion(request.niche, early_pool["category"].tolist()), early_pool["category"].tolist())
                emit(
                    "feature_extraction",
                    "decision",
                    "Early leaders are too crowded, so the agent is drilling into long-tail subcategories and lower-competition variants.",
                    decision="niche_drill_down",
                    threshold=">60% of early top products have competition above 75",
                    effect={"query_terms": drill_terms},
                )
                drill_candidates = self.adapters["offline_catalog"].discover(
                    request,
                    context,
                    drill_terms,
                    relax_niche=False,
                    top_k=25,
                    prioritize_long_tail=True,
                )
                candidates.extend(drill_candidates)
                processed = prepare_candidates(candidates, request, context)
                featured = engineer_features(processed, request, context)

            margin_fail_ratio = 1.0 - float(featured["economics_pass"].mean()) if not featured.empty else 1.0
            filtered_out: list[dict[str, object]] = []
            if should_raise_margin_floor(margin_fail_ratio):
                new_floor = min(context.margin_floor + 0.05, 0.45)
                context = replace(context, margin_floor=new_floor)
                run.context = context
                emit(
                    "scoring",
                    "decision",
                    "Too many candidates fail minimum economics, so the agent raised the margin floor and removed weak-profit options.",
                    decision="tighten_margin_floor",
                    threshold=">50% of products fail economics",
                    effect={"margin_floor": new_floor},
                )
                failing = featured[featured["estimated_margin_pct"] < new_floor * 100]
                filtered_out.extend(self._serialize_avoided(failing, "Rejected after tighter margin floor."))
                featured = engineer_features(processed, request, context)
                featured = featured[featured["estimated_margin_pct"] >= new_floor * 100].reset_index(drop=True)

            if featured.empty:
                emit(
                    "scoring",
                    "warning",
                    "Candidates were removed by economics checks before ranking could finish.",
                )
                return self._finalize_no_match_run(run, request, generate_pdf, emit, filtered_out)

            scored = score_products(featured, request, context)
            emit("scoring", "running", f"Scored {len(scored.index)} products with dynamic weights tuned to this run.")
            scored = apply_undiscovered_detector(scored)
            emit("ranking", "running", "Applied the Undiscovered Product Detector and prepared recommendation ranking.")

            top_products = self._build_top_products(scored, request, context)
            avoided_products = filtered_out + self._build_avoided_products(scored, top_products)
            adjacent_niche = adjacent_niche_suggestion(request.niche, [product["category"] for product in top_products] if top_products else [])
            run.top_products = top_products
            run.avoided_products = avoided_products[:8]
            run.run_insights = build_run_insights(run.top_products, run.avoided_products, adjacent_niche)
            run.effective_weights = summarize_effective_weights(scored)
            run.outcome = classify_outcome(
                max((product["opportunity_score"] for product in run.top_products), default=0.0),
                len(run.top_products),
            )
            emit(
                "report_generation",
                "running",
                f"Built a {run.outcome} recommendation set with {len(run.top_products)} top opportunities and {len(run.avoided_products)} avoided products.",
            )

            run.exports["json"] = write_json_report(run)
            run.exports["pdf"] = write_pdf_report(run) if generate_pdf else None
            self.repository.finalize_run(run)
            emit("report_generation", "complete", "Analysis complete and persisted to SQLite history.", exports=run.exports)
            return run
        except Exception as exc:  # pragma: no cover - exercised through runtime
            emit("report_generation", "failed", f"Run failed: {exc}")
            self.repository.mark_failed(run.run_id, str(exc))
            raise

    def _finalize_no_match_run(
        self,
        run: AnalysisRun,
        request: ResearchRequest,
        generate_pdf: bool,
        emit: callable,
        avoided_products: list[dict[str, object]] | None = None,
    ) -> AnalysisRun:
        adjacent_niche = adjacent_niche_suggestion(request.niche, [])
        run.top_products = []
        run.avoided_products = (avoided_products or [])[:8]
        run.run_insights = build_run_insights(run.top_products, run.avoided_products, adjacent_niche)
        run.effective_weights = summarize_effective_weights(pd.DataFrame())
        run.outcome = classify_outcome(0.0, 0)
        emit(
            "report_generation",
            "running",
            "The agent did not find enough relevant products to recommend in this run.",
        )
        run.exports["json"] = write_json_report(run)
        run.exports["pdf"] = write_pdf_report(run) if generate_pdf else None
        self.repository.finalize_run(run)
        emit("report_generation", "complete", "Analysis complete and persisted to SQLite history.", exports=run.exports)
        return run

    def _build_top_products(
        self,
        scored: pd.DataFrame,
        request: ResearchRequest,
        context: object,
    ) -> list[dict[str, object]]:
        if scored.empty:
            return []
        ranked = scored.sort_values(
            ["opportunity_score", "confidence_score", "discovery_gap_score", "estimated_profit_per_unit"],
            ascending=False,
        )
        selected_rows = []
        category_counts: dict[str, int] = {}
        for row in ranked.to_dict(orient="records"):
            category = str(row["category"])
            if category_counts.get(category, 0) >= 1 and len(selected_rows) < request.top_n and ranked["category"].nunique() > 2:
                continue
            category_counts[category] = category_counts.get(category, 0) + 1
            selected_rows.append(row)
            if len(selected_rows) >= request.top_n:
                break
        if len(selected_rows) < request.top_n:
            selected_slugs = {row["product_slug"] for row in selected_rows}
            for row in ranked.to_dict(orient="records"):
                if row["product_slug"] in selected_slugs:
                    continue
                selected_rows.append(row)
                if len(selected_rows) >= request.top_n:
                    break

        products = []
        for row in selected_rows:
            action_block = build_action_block(row, request, context)
            reasoning = build_reasoning_layers(row, request, context)
            payload = {
                **row,
                **reasoning,
                "action_plan": action_block,
            }
            products.append(make_json_safe(payload))
        return products

    def _build_avoided_products(self, scored: pd.DataFrame, top_products: list[dict[str, object]]) -> list[dict[str, object]]:
        if scored.empty:
            return []
        selected_slugs = {product["product_slug"] for product in top_products}
        remaining = scored[~scored["product_slug"].isin(selected_slugs)].copy()
        remaining["avoid_reason"] = remaining.apply(self._avoid_reason, axis=1)
        avoided = remaining.sort_values(["risk_level", "raw_competition", "opportunity_score"], ascending=[False, False, True]).head(8)
        return self._serialize_avoided(avoided, None)

    def _serialize_avoided(self, frame: pd.DataFrame, fallback_reason: str | None) -> list[dict[str, object]]:
        products = []
        for row in frame.to_dict(orient="records"):
            reason = row.get("avoid_reason") or fallback_reason or "Rejected during ranking."
            products.append(
                make_json_safe(
                    {
                        "product_slug": row["product_slug"],
                        "name": row["name"],
                        "category": row["category"],
                        "reason": reason,
                        "opportunity_score": row.get("opportunity_score", 0.0),
                        "confidence_score": row.get("confidence_score", 0.0),
                        "risk_level": row.get("risk_level", "High"),
                        "estimated_margin_pct": row.get("estimated_margin_pct", 0.0),
                        "raw_competition": row.get("raw_competition", 0.0),
                    }
                )
            )
        return products

    @staticmethod
    def _avoid_reason(row: pd.Series) -> str:
        if not bool(row["economics_pass"]):
            return "Margins are too thin for a safe first test."
        if row["risk_level"] == "High":
            return "Confidence is too low or operational risk is too high."
        if row["raw_competition"] > 75:
            return "Competition is too crowded for a clean entry."
        if row["raw_saturation"] > 70:
            return "Category saturation is too elevated."
        return "Other options offer a better mix of confidence, margin, and room to grow."
