from __future__ import annotations

from statistics import mean

import pandas as pd

from core.models import ContextProfile, ResearchRequest
from utils.config import BASE_WEIGHTS, MAX_IMPACTS
from utils.helpers import clamp, safe_divide


PLATFORM_MODIFIERS = {
    "TikTok": {"demand": 0.00, "competition": -0.04, "profit": 0.02, "virality": 0.11, "saturation": -0.01},
    "TikTok Shop": {"demand": 0.00, "competition": -0.04, "profit": 0.02, "virality": 0.11, "saturation": -0.01},
    "Amazon": {"demand": 0.02, "competition": 0.05, "profit": -0.01, "virality": -0.04, "saturation": 0.04},
    "Shopify": {"demand": 0.00, "competition": -0.02, "profit": 0.03, "virality": 0.03, "saturation": -0.01},
}

BUDGET_MODIFIERS = {
    "low": {"demand": -0.02, "competition": 0.03, "profit": 0.05, "virality": 0.00, "saturation": 0.02},
    "mid": {"demand": 0.00, "competition": 0.00, "profit": 0.00, "virality": 0.00, "saturation": 0.00},
    "high": {"demand": 0.03, "competition": 0.00, "profit": -0.03, "virality": 0.00, "saturation": 0.00},
}

MARKET_MODIFIERS = {
    "US": {"demand": 0.01, "competition": 0.03, "profit": 0.00, "virality": 0.00, "saturation": 0.03},
    "EU": {"demand": 0.01, "competition": 0.03, "profit": 0.00, "virality": 0.00, "saturation": 0.03},
    "Global": {"demand": 0.02, "competition": -0.02, "profit": 0.00, "virality": 0.01, "saturation": -0.01},
}

PRODUCT_TYPE_MODIFIERS = {
    "consumer": {"demand": 0.00, "competition": 0.00, "profit": 0.00, "virality": 0.03, "saturation": 0.00},
    "b2b": {"demand": 0.00, "competition": 0.03, "profit": 0.03, "virality": -0.05, "saturation": 0.00},
    "utility": {"demand": 0.01, "competition": 0.02, "profit": 0.03, "virality": -0.03, "saturation": 0.00},
}


def score_products(frame: pd.DataFrame, request: ResearchRequest, context: ContextProfile) -> pd.DataFrame:
    if frame.empty:
        return frame

    scored = frame.copy()
    scored_rows: list[dict[str, object]] = []
    for row in scored.to_dict(orient="records"):
        weights = _dynamic_weights(row, context)
        factor_scores = {
            "demand": float(row["demand_score"]),
            "competition": float(row["competition_score"]),
            "profit": float(row["profit_score"]),
            "virality": float(row["virality_score"]),
            "saturation": float(row["saturation_score"]),
        }
        adjustments: dict[str, float] = {}
        explanations: list[str] = []
        total_adjustment = 0.0
        for factor, score in factor_scores.items():
            centered = (score - 50.0) / 50.0
            adjustment = centered * MAX_IMPACTS[factor] * safe_divide(weights[factor], BASE_WEIGHTS[factor], 1.0)
            adjustments[factor] = adjustment
            total_adjustment += adjustment
            explanations.append(_adjustment_reason(factor, row, adjustment))

        opportunity_score = clamp(50.0 + total_adjustment, 0.0, 100.0)
        source_reliability = float(row["source_reliability"]) * 100.0
        signal_consistency = clamp(
            0.60 * float(row["source_agreement"]) + 0.40 * (100.0 - abs(float(row["demand_proxy"]) - float(row["engagement_proxy"]))),
            0.0,
            100.0,
        )
        confidence_score = clamp(
            0.40 * source_reliability
            + 0.25 * signal_consistency
            + 0.20 * float(row["data_completeness"])
            + 0.15 * float(row["market_fit_certainty"]),
            0.0,
            100.0,
        )
        confidence_factor = 0.55 if confidence_score < 55 else 0.65 if confidence_score < 70 else 0.78
        row["target_ad_cost"] = float(row["break_even_ad_cost"]) * confidence_factor
        row["estimated_profit_per_unit"] = float(row["pre_ad_contribution_margin"]) - float(row["target_ad_cost"])
        row["profit_score"] = clamp(
            0.45 * float(row["margin_score"])
            + 0.30 * clamp(float(row["break_even_ad_cost"]) * 6.5, 0, 100)
            + 0.25 * clamp(float(row["estimated_profit_per_unit"]) * 4.0, 0, 100),
            0.0,
            100.0,
        )
        risk_level = _risk_level(row, confidence_score, context)

        row["effective_weights"] = weights
        row["weight_summary"] = ", ".join(f"{factor} {weights[factor]:.2f}" for factor in weights)
        row["factor_adjustments"] = adjustments
        row["score_explanations"] = explanations
        row["opportunity_score"] = round(opportunity_score, 2)
        row["confidence_score"] = round(confidence_score, 2)
        row["signal_consistency"] = round(signal_consistency, 2)
        row["risk_level"] = risk_level
        row["uncertainty_flag"] = bool(row["uncertainty_flag"] or confidence_score < 60 or signal_consistency < 55)
        scored_rows.append(row)
    return pd.DataFrame(scored_rows)


def summarize_effective_weights(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return dict(BASE_WEIGHTS)
    values = {factor: [] for factor in BASE_WEIGHTS}
    for weights in frame["effective_weights"].tolist():
        for factor in BASE_WEIGHTS:
            values[factor].append(weights[factor])
    return {factor: round(mean(entries), 4) for factor, entries in values.items()}


def _dynamic_weights(row: dict[str, object], context: ContextProfile) -> dict[str, float]:
    weights = dict(BASE_WEIGHTS)
    modifiers = [
        PLATFORM_MODIFIERS.get(context.platform, {}),
        BUDGET_MODIFIERS.get(context.budget_segment, {}),
        MARKET_MODIFIERS.get(context.market, {}),
        PRODUCT_TYPE_MODIFIERS.get(str(row.get("product_type", "consumer")), {}),
        _data_quality_modifier(row),
    ]
    for modifier in modifiers:
        for factor, delta in modifier.items():
            weights[factor] = weights.get(factor, 0.0) + delta

    for factor in weights:
        weights[factor] = max(0.05, weights[factor])
    total = sum(weights.values())
    return {factor: round(value / total, 4) for factor, value in weights.items()}


def _data_quality_modifier(row: dict[str, object]) -> dict[str, float]:
    demand_reliability = float(row.get("demand_reliability", 60))
    source_agreement = float(row.get("source_agreement", 60))
    modifier = {"demand": 0.0, "competition": 0.0, "profit": 0.0, "virality": 0.0, "saturation": 0.0}
    if demand_reliability < 50:
        modifier["demand"] -= 0.06
        modifier["profit"] += 0.03
        modifier["virality"] += 0.02
        modifier["saturation"] += 0.01
    if source_agreement >= 75:
        modifier["demand"] += 0.03
    return modifier


def _adjustment_reason(factor: str, row: dict[str, object], adjustment: float) -> str:
    impact = int(round(adjustment))
    prefix = "+" if impact >= 0 else ""
    if factor == "demand":
        return f"{prefix}{impact} demand from repeated interest across {len(row['source_mix'])} source(s)"
    if factor == "competition":
        descriptor = "manageable" if impact >= 0 else "crowded"
        return f"{prefix}{impact} competition due to {descriptor} seller density"
    if factor == "profit":
        return f"{prefix}{impact} profit from {row['estimated_margin_pct']:.1f}% projected margin"
    if factor == "virality":
        return f"{prefix}{impact} virality from demonstrable use and social-hook potential"
    return f"{prefix}{impact} saturation from category crowding levels"


def _risk_level(row: dict[str, object], confidence_score: float, context: ContextProfile) -> str:
    if (
        confidence_score < 55
        or float(row["raw_competition"]) > 75
        or float(row["raw_saturation"]) > 75
        or float(row["operational_complexity"]) > 55
    ):
        return "High"
    if (
        confidence_score >= 70
        and float(row["estimated_margin_pct"]) >= context.margin_floor * 100 + 5
        and float(row["raw_competition"]) <= 60
        and float(row["raw_saturation"]) <= 60
    ):
        return "Low"
    return "Medium"
