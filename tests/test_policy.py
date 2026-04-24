from agents.policy import (
    build_context_profile,
    should_drill_down,
    should_expand_scope,
    should_raise_margin_floor,
    should_relax_niche,
)
from core.models import ResearchRequest


def test_build_context_profile_assigns_expected_margin_floor() -> None:
    request = ResearchRequest(niche="pet grooming", market="US", budget_min=20, budget_max=45, platform="Shopify")
    context = build_context_profile(request)
    assert context.budget_segment == "low"
    assert context.margin_floor == 0.35
    assert "budget_sensitive" in context.strategy_flags


def test_policy_thresholds_behave_as_expected() -> None:
    assert should_expand_scope(10) is True
    assert should_relax_niche(11) is True
    assert should_raise_margin_floor(0.6) is True
    assert should_drill_down([80, 77, 79, 60, 82, 78]) is True
