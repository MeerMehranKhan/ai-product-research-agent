from __future__ import annotations

import pandas as pd

from core.models import ContextProfile, ResearchRequest
from utils.config import (
    BEGINNER_FRIENDLY_COMPLEXITY_MAX,
    BEGINNER_FRIENDLY_MARGIN_MIN,
    CATEGORY_COMPLEXITY,
    CATEGORY_COST_RATIO,
    MARKET_SHIPPING_BASE,
    PLATFORM_FEE_RULES,
)
from utils.helpers import best_query_match_score, clamp, psych_price, safe_divide


def engineer_features(frame: pd.DataFrame, request: ResearchRequest, context: ContextProfile) -> pd.DataFrame:
    if frame.empty:
        return frame

    engineered = frame.copy()
    engineered["category_cost_ratio"] = engineered["category"].map(CATEGORY_COST_RATIO).fillna(0.30)
    engineered["category_complexity"] = engineered["category"].map(CATEGORY_COMPLEXITY).fillna(engineered["operational_complexity"])
    engineered["estimated_supplier_cost"] = engineered.apply(
        lambda row: row["supplier_cost"] if row["supplier_cost"] > 0 else row["price"] * row["category_cost_ratio"],
        axis=1,
    )
    shipping_base = MARKET_SHIPPING_BASE.get(request.market, MARKET_SHIPPING_BASE["Other"])
    engineered["shipping_buffer"] = shipping_base + engineered["operational_complexity"] * 0.03
    engineered["packaging_reserve"] = 0.75 + engineered["category_complexity"] * 0.015
    engineered["estimated_landed_cost"] = (
        engineered["estimated_supplier_cost"] + engineered["shipping_buffer"] + engineered["packaging_reserve"]
    )

    fee_rule = PLATFORM_FEE_RULES.get(context.platform, PLATFORM_FEE_RULES["Other"])
    engineered["required_price_for_margin_floor"] = (
        engineered["estimated_landed_cost"] + fee_rule["fixed"]
    ) / max(0.10, (1 - fee_rule["pct"] - context.margin_floor))
    engineered["premium_positioning"] = (
        (engineered["demand_proxy"] >= 72) & (engineered["competition_proxy"] <= 55) & (engineered["virality_proxy"] <= 60)
    )
    engineered["suggested_selling_price"] = engineered.apply(
        lambda row: psych_price(
            max(row["price"] * 1.04, row["required_price_for_margin_floor"]),
            premium=bool(row["premium_positioning"]),
        ),
        axis=1,
    )
    engineered["platform_fee_estimate"] = engineered["suggested_selling_price"] * fee_rule["pct"] + fee_rule["fixed"]
    engineered["pre_ad_contribution_margin"] = (
        engineered["suggested_selling_price"] - engineered["estimated_landed_cost"] - engineered["platform_fee_estimate"]
    )
    engineered["break_even_ad_cost"] = engineered["pre_ad_contribution_margin"].clip(lower=0.0)

    # Use only the original niche (not all expanded query terms) for a tight
    # relevance signal.  Expanded terms are for discovery breadth, not fit scoring.
    niche_queries = [request.niche] if request.niche else []
    engineered["niche_fit"] = engineered.apply(
        lambda row: best_query_match_score(
            niche_queries,
            [row["name"], row["category"], " ".join(row["keywords"])],
        )
        if request.niche
        else 60.0,
        axis=1,
    )
    engineered["impulse_price_score"] = engineered["suggested_selling_price"].apply(
        lambda price: 88.0 if 15 <= price <= 40 else 64.0 if price < 60 else 48.0
    )
    engineered["demand_score"] = (
        0.38 * engineered["demand_proxy"]
        + 0.24 * engineered["engagement_proxy"]
        + 0.18 * engineered["platform_fit_score"]
        + 0.10 * engineered["market_match"]
        + 0.10 * engineered["source_agreement"]
    ).clip(0, 100)
    engineered["raw_competition"] = (
        0.70 * engineered["competition_proxy"] + 0.30 * engineered["saturation_proxy"]
    ).clip(0, 100)
    engineered["competition_score"] = (100 - engineered["raw_competition"]).clip(0, 100)
    engineered["virality_score"] = (
        0.50 * engineered["virality_proxy"]
        + 0.20 * engineered["novelty"]
        + 0.15 * engineered["impulse_price_score"]
        + 0.15 * engineered["niche_fit"]
    ).clip(0, 100)
    engineered["raw_saturation"] = (
        0.65 * engineered["saturation_proxy"] + 0.35 * engineered["competition_proxy"]
    ).clip(0, 100)
    engineered["saturation_score"] = (100 - engineered["raw_saturation"]).clip(0, 100)
    engineered["demand_reliability"] = (
        0.55 * engineered["source_agreement"] + 45.0 * engineered["source_reliability"]
    ).clip(0, 100)
    engineered["market_fit_certainty"] = (
        0.45 * engineered["platform_fit_score"]
        + 0.35 * engineered["market_match"]
        + 0.20 * engineered["niche_fit"]
    ).clip(0, 100)
    engineered["margin_pct_raw"] = 100 * engineered["pre_ad_contribution_margin"].div(engineered["suggested_selling_price"].replace(0, pd.NA))
    engineered["estimated_margin_pct"] = engineered["margin_pct_raw"].fillna(0.0).clip(lower=0.0)
    engineered["margin_score"] = (engineered["estimated_margin_pct"] * 1.45).clip(0, 100)
    engineered["ad_headroom_score"] = (engineered["break_even_ad_cost"] * 6.5).clip(0, 100)
    engineered["unit_profit_score"] = (engineered["pre_ad_contribution_margin"] * 4.0).clip(0, 100)
    engineered["profit_score"] = (
        0.45 * engineered["margin_score"]
        + 0.30 * engineered["ad_headroom_score"]
        + 0.25 * engineered["unit_profit_score"]
    ).clip(0, 100)

    target_ad_multiplier = {"tight": 0.55, "balanced": 0.65, "flexible": 0.75}.get(context.budget_strictness, 0.65)
    engineered["target_ad_cost"] = engineered["break_even_ad_cost"] * target_ad_multiplier
    engineered["estimated_profit_per_unit"] = engineered["pre_ad_contribution_margin"] - engineered["target_ad_cost"]
    engineered["pricing_strategy_suggestion"] = engineered.apply(_pricing_strategy, axis=1)
    engineered["economics_pass"] = (
        (engineered["estimated_margin_pct"] >= context.margin_floor * 100)
        & (engineered["break_even_ad_cost"] >= 8)
        & (engineered["pre_ad_contribution_margin"] >= 6)
    )
    engineered["beginner_friendly"] = (
        (engineered["operational_complexity"] <= BEGINNER_FRIENDLY_COMPLEXITY_MAX)
        & (engineered["estimated_margin_pct"] >= BEGINNER_FRIENDLY_MARGIN_MIN)
        & (engineered["raw_competition"] <= 60)
    )
    engineered["uncertainty_flag"] = (
        (engineered["source_agreement"] < 45) | (engineered["demand_reliability"] < 45)
    )
    return engineered


def _pricing_strategy(row: pd.Series) -> str:
    if row["suggested_selling_price"] <= 25 and row["virality_score"] >= 65:
        return "Impulse-buy rounding"
    if row["estimated_margin_pct"] >= 42 and row["category"] in {"Beauty", "Pet Care", "Kitchen"}:
        return "Bundle-first pricing"
    if row["premium_positioning"]:
        return "Premium problem-solver"
    return "Anchor-and-discount"
