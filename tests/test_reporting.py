from agents.orchestrator import ProductResearchOrchestrator
from core.models import ResearchRequest
from storage.db import ResearchRepository


def test_reporting_creates_json_export(tmp_path) -> None:
    repository = ResearchRepository(tmp_path / "history.db")
    orchestrator = ProductResearchOrchestrator(repository=repository)
    run = orchestrator.run(
        ResearchRequest(
            niche="pet grooming",
            market="US",
            budget_min=15,
            budget_max=80,
            platform="Shopify",
            top_n=3,
        ),
        generate_pdf=False,
    )
    assert run.exports["json"]
