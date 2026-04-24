from __future__ import annotations

from core.models import CandidateProduct, ContextProfile, ResearchRequest
from core.processing import prepare_candidates
from utils.helpers import niche_match_score


def test_niche_match_score_handles_comma_separated_niches() -> None:
    niche = "phone cases, laptop stands, USB hubs"

    assert niche_match_score(niche, ["Collapsible Laptop Stand", "Office", "desk,laptop,remote work"]) >= 50
    assert niche_match_score(niche, ["Kitchen Sink Splash Guard", "Kitchen", "kitchen,cleaning,sink"]) == 0


def test_niche_match_score_ignores_generic_home_tokens() -> None:
    niche = "home gym equipment, resistance bands, foam rollers"

    assert niche_match_score(niche, ["Cordless Handheld Vacuum", "Home", "cleaning,home,vacuum,portable"]) == 0
    assert niche_match_score(niche, ["Yoga Stretch Strap", "Fitness", "fitness,recovery,stretch,yoga"]) == 0


def test_prepare_candidates_prefers_relevant_matches_when_any_exist() -> None:
    request = ResearchRequest(
        niche="phone cases, laptop stands, USB hubs",
        market="US",
        budget_min=10,
        budget_max=60,
        platform="Shopify",
    )
    context = ContextProfile(
        platform="Shopify",
        market="US",
        budget_segment="low",
        budget_strictness="tight",
        market_competitiveness="high",
        product_archetype="consumer",
        margin_floor=0.35,
        query_terms=[request.niche],
    )
    candidates = [
        CandidateProduct(
            name="Collapsible Laptop Stand",
            category="Office",
            price=33.99,
            engagement_proxy=72,
            demand_proxy=74,
            competition_proxy=42,
            virality_proxy=50,
            saturation_proxy=38,
            source="offline_catalog",
            source_kind="offline_fallback",
            supplier_cost=8.70,
            novelty=60,
            product_type="consumer",
            operational_complexity=20,
            audience_hint="Remote professionals improving ergonomics",
            trend_region="US",
            keywords=["desk", "laptop", "remote work", "ergonomic"],
            platform_fit_shopify=84,
            platform_fit_amazon=73,
            platform_fit_tiktok=52,
            platform_fit_other=61,
            source_confidence=0.60,
            search_term=request.niche,
        ),
        CandidateProduct(
            name="Kitchen Sink Splash Guard",
            category="Kitchen",
            price=18.49,
            engagement_proxy=75,
            demand_proxy=74,
            competition_proxy=33,
            virality_proxy=60,
            saturation_proxy=32,
            source="offline_catalog",
            source_kind="offline_fallback",
            supplier_cost=3.50,
            novelty=64,
            product_type="consumer",
            operational_complexity=15,
            audience_hint="Renters and busy home cooks",
            trend_region="US",
            keywords=["kitchen", "cleaning", "sink", "organization"],
            platform_fit_shopify=82,
            platform_fit_amazon=55,
            platform_fit_tiktok=69,
            platform_fit_other=56,
            source_confidence=0.60,
            search_term=request.niche,
        ),
    ]

    prepared = prepare_candidates(candidates, request, context)

    assert prepared["name"].tolist() == ["Collapsible Laptop Stand"]
