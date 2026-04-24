from agents.orchestrator import ProductResearchOrchestrator
from core.models import ResearchRequest
from storage.db import ResearchRepository


def test_orchestrator_runs_offline_and_records_expand_scope(tmp_path) -> None:
    repository = ResearchRepository(tmp_path / "history.db")
    orchestrator = ProductResearchOrchestrator(repository=repository)
    request = ResearchRequest(
        niche="aquascaping",
        market="US",
        budget_min=15,
        budget_max=60,
        platform="TikTok",
        top_n=4,
    )
    run = orchestrator.run(request, generate_pdf=False)
    decisions = [event.decision for event in run.trace if event.decision]
    assert "expand_scope" in decisions
    assert repository.get_run(run.run_id) is not None


def test_orchestrator_returns_avoided_products_for_crowded_market(tmp_path) -> None:
    repository = ResearchRepository(tmp_path / "history.db")
    orchestrator = ProductResearchOrchestrator(repository=repository)
    request = ResearchRequest(
        niche="projector gadget",
        market="Global",
        budget_min=20,
        budget_max=120,
        platform="Amazon",
        top_n=3,
    )
    run = orchestrator.run(request, generate_pdf=False)
    assert run.top_products
    assert run.outcome in {"go", "caution", "avoid"}


def test_orchestrator_does_not_surface_irrelevant_products_for_accessory_niches(tmp_path) -> None:
    repository = ResearchRepository(tmp_path / "history.db")
    orchestrator = ProductResearchOrchestrator(repository=repository)
    request = ResearchRequest(
        niche="phone cases, laptop stands, USB hubs",
        market="US",
        budget_min=10,
        budget_max=60,
        platform="Shopify",
        top_n=5,
    )

    run = orchestrator.run(request, generate_pdf=False)
    top_names = [product["name"] for product in run.top_products]

    assert "Kitchen Sink Splash Guard" not in top_names
    assert "Collapsible Laptop Stand" in top_names


def test_orchestrator_does_not_surface_generic_home_products_for_gym_queries(tmp_path) -> None:
    repository = ResearchRepository(tmp_path / "history.db")
    orchestrator = ProductResearchOrchestrator(repository=repository)
    request = ResearchRequest(
        niche="home gym equipment, resistance bands, foam rollers",
        market="US",
        budget_min=10,
        budget_max=70,
        platform="Shopify",
        top_n=5,
    )

    run = orchestrator.run(request, generate_pdf=False)
    top_names = [product["name"] for product in run.top_products]

    assert "Cordless Handheld Vacuum" not in top_names
