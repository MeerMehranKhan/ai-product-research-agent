from __future__ import annotations

from statistics import mean

from core.models import ContextProfile, ResearchRequest
from utils.config import ADJACENT_TERMS, GENERIC_DISCOVERY_TERMS, MARKET_COMPETITIVENESS
from utils.helpers import normalize_text


def build_context_profile(request: ResearchRequest) -> ContextProfile:
    budget_segment = "low" if request.budget_max <= 60 else "mid" if request.budget_max <= 150 else "high"
    budget_strictness = "tight" if request.budget_max <= 50 else "balanced" if request.budget_max <= 150 else "flexible"
    normalized_niche = normalize_text(request.niche)
    product_archetype = "b2b" if any(token in normalized_niche for token in ["salon", "office", "warehouse", "commercial"]) else "consumer"
    margin_floor = margin_floor_for(budget_segment, request.platform, product_archetype)
    query_terms = initial_query_terms(request.niche)
    strategy_flags: list[str] = []
    if budget_segment == "low":
        strategy_flags.append("budget_sensitive")
    if request.platform in {"TikTok", "TikTok Shop"}:
        strategy_flags.append("social_commerce")
    return ContextProfile(
        platform=request.platform,
        market=request.market,
        budget_segment=budget_segment,
        budget_strictness=budget_strictness,
        market_competitiveness=MARKET_COMPETITIVENESS.get(request.market, "medium"),
        product_archetype=product_archetype,
        margin_floor=margin_floor,
        query_terms=query_terms,
        strategy_flags=strategy_flags,
        budget_tolerance=0.0,
    )


def margin_floor_for(budget_segment: str, platform: str, product_archetype: str) -> float:
    if product_archetype == "b2b":
        return 0.20
    if platform == "Amazon":
        return 0.25
    if budget_segment == "low":
        return 0.35
    return 0.30


def initial_query_terms(niche: str) -> list[str]:
    if niche.strip():
        normalized = normalize_text(niche)
        terms = [niche.strip()]
        for token, extras in ADJACENT_TERMS.items():
            if token in normalized:
                terms.extend(extras[:2])
        return list(dict.fromkeys(terms))
    return GENERIC_DISCOVERY_TERMS.copy()


def expand_query_terms(current_terms: list[str], niche: str, categories: list[str]) -> list[str]:
    expanded = list(current_terms)
    normalized_niche = normalize_text(niche)
    for token, extras in ADJACENT_TERMS.items():
        if token in normalized_niche or any(token in normalize_text(category) for category in categories):
            expanded.extend(extras)
    expanded.extend(GENERIC_DISCOVERY_TERMS[:2])
    return list(dict.fromkeys(expanded))


def adjacent_niche_suggestion(niche: str, top_categories: list[str]) -> str:
    normalized_niche = normalize_text(niche)
    for token, extras in ADJACENT_TERMS.items():
        if token in normalized_niche:
            return extras[0]
    if top_categories:
        category = normalize_text(top_categories[0])
        for token, extras in ADJACENT_TERMS.items():
            if token in category:
                return extras[0]
    return "problem solver home upgrade"


def should_expand_scope(candidate_count: int) -> bool:
    return candidate_count < 20


def should_relax_niche(candidate_count: int) -> bool:
    return candidate_count < 12


def should_drill_down(competition_values: list[float]) -> bool:
    if not competition_values:
        return False
    high_comp = [value for value in competition_values if value > 75]
    return len(high_comp) / len(competition_values) > 0.60


def should_raise_margin_floor(fail_ratio: float) -> bool:
    return fail_ratio > 0.50


def should_shift_weights_for_weak_demand(demand_reliability_values: list[float]) -> bool:
    if not demand_reliability_values:
        return False
    return mean(demand_reliability_values) < 50


def classify_outcome(best_score: float, top_count: int) -> str:
    if top_count == 0 or best_score < 55:
        return "avoid"
    if best_score < 65:
        return "caution"
    return "go"
