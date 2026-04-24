from __future__ import annotations

from core.models import ContextProfile, ResearchRequest
from utils.helpers import format_currency


def build_reasoning_layers(row: dict[str, object], request: ResearchRequest, context: ContextProfile) -> dict[str, str]:
    source_mix = ", ".join(row["source_mix"])
    surface = (
        f"Demand looks {'strong' if row['demand_score'] >= 70 else 'moderate'} with an opportunity score of "
        f"{row['opportunity_score']:.1f}. Competition is {'manageable' if row['competition_score'] >= 55 else 'heavy'}, "
        f"and projected pre-ad margin is {row['estimated_margin_pct']:.1f}%."
    )
    deep = (
        f"Interest is supported by {len(row['source_mix'])} source(s) ({source_mix}) and a demand reliability score of "
        f"{row['demand_reliability']:.1f}. Likely buyers are {row['audience_hint'] or 'general online shoppers'}, "
        f"and the strongest signal is coming from {row['trend_region']} where the product maps well to {context.platform}."
    )
    strategic = (
        f"Position {row['name']} as a {row['pricing_strategy_suggestion'].lower()} offer. Lead with the clearest pain-point "
        f"demo, keep pricing around {format_currency(row['suggested_selling_price'])}, and protect against "
        f"{'uncertainty in demand signals' if row['uncertainty_flag'] else 'category crowding'} during launch."
    )
    return {
        "surface_reasoning": surface,
        "deep_reasoning": deep,
        "strategic_reasoning": strategic,
    }
