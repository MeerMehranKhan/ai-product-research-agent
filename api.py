from __future__ import annotations

from bootstrap import configure_paths

configure_paths()

from core.models import ResearchRequest
from agents.orchestrator import ProductResearchOrchestrator
from storage.db import ResearchRepository

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - optional dependency in local verification
    FastAPI = None
    HTTPException = Exception


def create_app() -> "FastAPI":
    if FastAPI is None:  # pragma: no cover - exercised when dependency missing
        raise ImportError("FastAPI is not installed. Install requirements.txt to use api.py.")

    repository = ResearchRepository()
    orchestrator = ProductResearchOrchestrator(repository=repository)
    app = FastAPI(title="AI Product Research Agent", version="1.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs")
    def list_runs() -> list[dict[str, object]]:
        return repository.list_runs()

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, object]:
        payload = repository.get_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return payload

    @app.post("/analyze")
    def analyze(payload: dict[str, object]) -> dict[str, object]:
        request = ResearchRequest(
            niche=str(payload.get("niche", "")),
            market=str(payload.get("market", "US")),
            budget_min=float(payload.get("budget_min", 20.0)),
            budget_max=float(payload.get("budget_max", 120.0)),
            platform=str(payload.get("platform", "Shopify")),
            top_n=int(payload.get("top_n", 5)),
        )
        run = orchestrator.run(request, generate_pdf=False)
        return run.to_dict()

    return app


app = create_app() if FastAPI is not None else None
