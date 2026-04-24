from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ResearchRequest:
    niche: str = ""
    market: str = "US"
    budget_min: float = 20.0
    budget_max: float = 120.0
    platform: str = "Shopify"
    top_n: int = 5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContextProfile:
    platform: str
    market: str
    budget_segment: str
    budget_strictness: str
    market_competitiveness: str
    product_archetype: str
    margin_floor: float
    query_terms: list[str] = field(default_factory=list)
    strategy_flags: list[str] = field(default_factory=list)
    budget_tolerance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CandidateProduct:
    name: str
    category: str
    price: float
    engagement_proxy: float
    demand_proxy: float
    competition_proxy: float
    virality_proxy: float
    saturation_proxy: float
    source: str
    source_kind: str
    supplier_cost: float | None = None
    novelty: float = 50.0
    product_type: str = "consumer"
    operational_complexity: float = 40.0
    audience_hint: str = ""
    trend_region: str = "Global"
    keywords: list[str] = field(default_factory=list)
    platform_fit_shopify: float = 60.0
    platform_fit_amazon: float = 60.0
    platform_fit_tiktok: float = 60.0
    platform_fit_other: float = 55.0
    source_confidence: float = 0.6
    search_term: str = ""
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["keywords"] = ",".join(self.keywords)
        return payload


@dataclass(slots=True)
class TraceEvent:
    step: str
    status: str
    message: str
    timestamp: str
    decision: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisRun:
    run_id: str
    request: ResearchRequest
    context: ContextProfile
    trace: list[TraceEvent]
    top_products: list[dict[str, Any]]
    avoided_products: list[dict[str, Any]]
    run_insights: dict[str, Any]
    effective_weights: dict[str, float]
    outcome: str
    exports: dict[str, str | None] = field(default_factory=dict)
    created_at: str = field(default_factory=str)

    @classmethod
    def empty(cls, request: ResearchRequest, context: ContextProfile) -> "AnalysisRun":
        return cls(
            run_id=uuid4().hex,
            request=request,
            context=context,
            trace=[],
            top_products=[],
            avoided_products=[],
            run_insights={},
            effective_weights={},
            outcome="pending",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "request": self.request.to_dict(),
            "context": self.context.to_dict(),
            "trace": [event.to_dict() for event in self.trace],
            "top_products": self.top_products,
            "avoided_products": self.avoided_products,
            "run_insights": self.run_insights,
            "effective_weights": self.effective_weights,
            "outcome": self.outcome,
            "exports": self.exports,
            "created_at": self.created_at,
        }
