from core.models import ContextProfile
from core.scoring import score_products
import pandas as pd


def test_dynamic_scoring_shifts_weight_toward_virality_for_tiktok() -> None:
    frame = pd.DataFrame(
        [
            {
                "product_slug": "portable-blender",
                "name": "Portable Blender Bottle",
                "category": "Kitchen",
                "price": 29.99,
                "engagement_proxy": 80,
                "demand_proxy": 75,
                "competition_proxy": 40,
                "virality_proxy": 82,
                "saturation_proxy": 35,
                "supplier_cost": 8.2,
                "novelty": 70,
                "product_type": "consumer",
                "operational_complexity": 24,
                "audience_hint": "Gym-goers",
                "trend_region": "Global",
                "keywords": ["portable", "fitness"],
                "platform_fit_score": 88,
                "source_mix": ["offline_catalog"],
                "source_kind_mix": ["offline_fallback"],
                "source_count": 1,
                "source_reliability": 0.62,
                "source_agreement": 66,
                "data_completeness": 100,
                "search_terms_seen": ["portable blender"],
                "market_match": 100,
                "search_match": 72,
                "estimated_margin_pct": 41,
                "margin_score": 60,
                "break_even_ad_cost": 12,
                "pre_ad_contribution_margin": 14,
                "profit_score": 66,
                "demand_score": 78,
                "competition_score": 63,
                "virality_score": 84,
                "saturation_score": 68,
                "market_fit_certainty": 79,
                "uncertainty_flag": False,
                "raw_competition": 37,
                "raw_saturation": 32,
            }
        ]
    )
    context = ContextProfile(
        platform="TikTok",
        market="US",
        budget_segment="low",
        budget_strictness="tight",
        market_competitiveness="high",
        product_archetype="consumer",
        margin_floor=0.35,
        query_terms=["portable blender"],
    )
    scored = score_products(frame, ResearchRequest(), context)
    weights = scored.iloc[0]["effective_weights"]
    assert weights["virality"] > weights["competition"]
    assert scored.iloc[0]["opportunity_score"] > 50


from core.models import ResearchRequest  # noqa: E402
