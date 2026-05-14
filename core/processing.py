from __future__ import annotations

from statistics import mean

import pandas as pd

from core.models import CandidateProduct, ContextProfile, ResearchRequest
from utils.config import PLATFORM_FIT_COLUMNS, SOURCE_KIND_CONFIDENCE
from utils.helpers import best_query_match_score, keyword_list, normalize_text, safe_divide, slugify


def prepare_candidates(
    candidates: list[CandidateProduct],
    request: ResearchRequest,
    context: ContextProfile,
) -> pd.DataFrame:
    if not candidates:
        return pd.DataFrame()

    frame = pd.DataFrame([candidate.to_dict() for candidate in candidates])
    frame["name"] = frame["name"].fillna("").astype(str)
    frame["category"] = frame["category"].fillna("General").astype(str)
    frame["normalized_name"] = frame["name"].map(normalize_text)
    frame["normalized_category"] = frame["category"].map(normalize_text)
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce").fillna(0.0)
    numeric_columns = [
        "engagement_proxy",
        "demand_proxy",
        "competition_proxy",
        "virality_proxy",
        "saturation_proxy",
        "supplier_cost",
        "novelty",
        "operational_complexity",
        "platform_fit_shopify",
        "platform_fit_amazon",
        "platform_fit_tiktok",
        "platform_fit_other",
        "source_confidence",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    frame["keywords"] = frame["keywords"].fillna("").astype(str)
    frame["source_kind"] = frame["source_kind"].fillna("offline_fallback")
    frame["source_reliability_raw"] = frame["source_kind"].map(SOURCE_KIND_CONFIDENCE).fillna(frame["source_confidence"]).astype(float)

    lower_bound = request.budget_min * (1 - context.budget_tolerance) if request.budget_min else 0.0
    upper_bound = request.budget_max * (1 + context.budget_tolerance) if request.budget_max else float("inf")
    budget_mask = frame["price"].between(lower_bound, upper_bound)
    if budget_mask.any():
        frame = frame[budget_mask].copy()
    if frame.empty:
        return frame

    effective_queries = [request.niche, *context.query_terms]
    frame["search_match"] = frame.apply(
        lambda row: best_query_match_score(effective_queries, [row["name"], row["category"], row["keywords"]]) if request.niche else 60.0,
        axis=1,
    )
    if request.niche:
        relevant_mask = frame["search_match"] >= 12.0
        frame = frame[relevant_mask].copy()
    if frame.empty:
        return frame
    frame["market_match"] = frame["trend_region"].fillna("Global").apply(
        lambda value: 100.0 if str(value).lower() in {request.market.lower(), "global"} else 55.0
    )
    frame["price_band"] = (frame["price"] / 5.0).round()
    platform_column = PLATFORM_FIT_COLUMNS.get(context.platform, "platform_fit_other")
    frame["platform_fit_score"] = frame[platform_column].fillna(frame["platform_fit_other"]).astype(float)
    frame["dedupe_key"] = frame["normalized_name"] + "|" + frame["normalized_category"]

    grouped_rows = []
    for _, group in frame.groupby("dedupe_key", as_index=False):
        keywords = sorted({keyword.strip() for entry in group["keywords"].tolist() for keyword in keyword_list(entry)})
        source_mix = sorted(set(group["source"].tolist()))
        source_kind_mix = sorted(set(group["source_kind"].tolist()))
        price_std = float(group["price"].std(ddof=0) or 0.0)
        avg_price = float(group["price"].mean())
        agreement = max(0.0, 100.0 - safe_divide(price_std, max(avg_price, 1.0), 0.0) * 220.0)
        source_agreement = min(100.0, agreement + min(len(source_mix), 3) * 8.0)
        source_reliability = min(1.0, mean(group["source_reliability_raw"].tolist()) + 0.03 * max(len(source_mix) - 1, 0))
        supplier_series = group["supplier_cost"].replace(0, pd.NA).dropna()
        supplier_cost = float(supplier_series.mean()) if not supplier_series.empty else 0.0
        grouped_rows.append(
            {
                "product_slug": slugify(group.iloc[0]["name"]),
                "name": group.iloc[0]["name"],
                "category": group.iloc[0]["category"],
                "price": avg_price,
                "engagement_proxy": float(group["engagement_proxy"].mean()),
                "demand_proxy": float(group["demand_proxy"].mean()),
                "competition_proxy": float(group["competition_proxy"].mean()),
                "virality_proxy": float(group["virality_proxy"].mean()),
                "saturation_proxy": float(group["saturation_proxy"].mean()),
                "supplier_cost": supplier_cost,
                "novelty": float(group["novelty"].mean()),
                "product_type": group["product_type"].mode().iloc[0] if not group["product_type"].mode().empty else "consumer",
                "operational_complexity": float(group["operational_complexity"].mean()),
                "audience_hint": group["audience_hint"].mode().iloc[0] if not group["audience_hint"].mode().empty else "",
                "trend_region": group["trend_region"].mode().iloc[0] if not group["trend_region"].mode().empty else "Global",
                "keywords": keywords,
                "platform_fit_shopify": float(group["platform_fit_shopify"].mean()),
                "platform_fit_amazon": float(group["platform_fit_amazon"].mean()),
                "platform_fit_tiktok": float(group["platform_fit_tiktok"].mean()),
                "platform_fit_other": float(group["platform_fit_other"].mean()),
                "platform_fit_score": float(group["platform_fit_score"].mean()),
                "search_match": float(group["search_match"].max()),
                "market_match": float(group["market_match"].mean()),
                "source_mix": source_mix,
                "source_kind_mix": source_kind_mix,
                "source_count": len(source_mix),
                "source_reliability": source_reliability,
                "source_agreement": source_agreement,
                "data_completeness": _data_completeness(group.iloc[0].to_dict()),
                "search_terms_seen": sorted({term for entry in group["search_term"].fillna("").tolist() for term in keyword_list(entry)}),
            }
        )
    return pd.DataFrame(grouped_rows)


def _data_completeness(row: dict[str, object]) -> float:
    required = [
        "name",
        "category",
        "price",
        "engagement_proxy",
        "demand_proxy",
        "competition_proxy",
        "virality_proxy",
        "saturation_proxy",
    ]
    present = 0
    for column in required:
        value = row.get(column)
        if value not in (None, "", 0):
            present += 1
    return 100.0 * safe_divide(present, len(required), 0.0)
