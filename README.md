# AI Product Research Agent

An adaptive, offline-safe product discovery system for e-commerce sellers. It discovers candidate products, engineers monetization signals, dynamically scores opportunities, and turns the best products into concrete launch plans with confidence and risk context.

## What It Does

- Understands the user's niche, market, budget, and platform.
- Runs a decision-making agent, not just a fixed pipeline.
- Expands scope when the candidate pool is weak.
- Drills into long-tail opportunities when early leaders are too crowded.
- Tightens economics when margins are not good enough.
- Scores products with platform-, market-, budget-, and data-quality-aware weights.
- Surfaces overlooked products with the Undiscovered Product Detector.
- Produces money metrics, reasoning layers, and action plans for each recommendation.
- Stores run history in SQLite and supports JSON/PDF reporting.

## Architecture

### Core Flow

1. Input understanding
2. Data discovery
3. Cleaning and structuring
4. Feature engineering
5. Dynamic scoring
6. Ranking and differentiation
7. Action and reasoning generation
8. Final report and persistence

### Main Modules

- [app.py](/D:/ai-product-research-agent/app.py): Streamlit entrypoint and interactive workspace.
- [agents/orchestrator.py](/D:/ai-product-research-agent/agents/orchestrator.py): Non-linear agent controller with branching decisions.
- [agents/policy.py](/D:/ai-product-research-agent/agents/policy.py): Thresholds, branch logic, and outcome gating.
- [core/discovery/adapters.py](/D:/ai-product-research-agent/core/discovery/adapters.py): Live, snapshot, and offline discovery adapters.
- [core/features.py](/D:/ai-product-research-agent/core/features.py): Monetization, signal, and fit engineering.
- [core/scoring.py](/D:/ai-product-research-agent/core/scoring.py): Dynamic weights, opportunity scoring, confidence, and risk.
- [core/action_engine.py](/D:/ai-product-research-agent/core/action_engine.py): Deterministic validation, sourcing, listing, and launch plans.
- [storage/db.py](/D:/ai-product-research-agent/storage/db.py): SQLite history and persistence.

## Project Structure

```text
ai-product-research-agent/
├── app.py
├── api.py
├── requirements.txt
├── README.md
├── .env.example
├── agents/
├── core/
├── data/
├── storage/
├── tests/
├── ui/
└── utils/
```

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Optional API keys

Copy `.env.example` to `.env` and add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` if you want to extend the insight layer later. The app works without keys.

## Running The App

### Streamlit UI

```powershell
streamlit run app.py
```

### Optional FastAPI

```powershell
uvicorn api:app --reload
```

## How Offline Safety Works

- Live adapters are attempted first.
- If they fail or return too few candidates, the agent switches to local HTML snapshots.
- If the pool is still weak, the agent falls back to a bundled offline product catalog.
- Every result retains source labels so confidence and uncertainty stay visible.

## Storage

The app stores:

- analysis runs
- execution trace events
- top products
- avoided products
- exports

SQLite lives at [storage/analysis_history.db](/D:/ai-product-research-agent/storage/analysis_history.db).

## Testing

```powershell
pytest
```

## Notes

- The differentiator in v1 is the Undiscovered Product Detector.
- FastAPI is intentionally optional so Streamlit stays the primary product surface.
- The scoring engine never hardcodes final scores; it computes them from factor scores, max impacts, and dynamic weights.
