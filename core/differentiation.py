from __future__ import annotations

import pandas as pd

from utils.helpers import clamp


def apply_undiscovered_detector(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    differentiated = frame.copy()
    differentiated["demand_momentum"] = (
        0.60 * differentiated["demand_score"] + 0.40 * differentiated["virality_score"]
    ).clip(0, 100)
    differentiated["competition_advantage"] = differentiated["competition_score"].clip(0, 100)
    differentiated["saturation_advantage"] = differentiated["saturation_score"].clip(0, 100)
    differentiated["discovery_gap_score"] = (
        0.40 * differentiated["demand_momentum"]
        + 0.25 * differentiated["competition_advantage"]
        + 0.20 * differentiated["novelty"]
        + 0.15 * differentiated["saturation_advantage"]
    ).clip(0, 100)
    differentiated["undiscovered_opportunity"] = differentiated.apply(
        lambda row: bool(
            row["discovery_gap_score"] >= 70
            and row["opportunity_score"] >= 65
            and row["confidence_score"] >= 60
        ),
        axis=1,
    )
    differentiated["discovery_gap_summary"] = differentiated.apply(
        lambda row: _summary(row["discovery_gap_score"], row["undiscovered_opportunity"]),
        axis=1,
    )
    differentiated["discovery_gap_score"] = differentiated["discovery_gap_score"].map(lambda value: round(clamp(value, 0, 100), 2))
    return differentiated


def _summary(score: float, is_qualified: bool) -> str:
    if is_qualified:
        return f"Undiscovered opportunity score {score:.1f}: rising demand without obvious crowding."
    if score >= 65:
        return f"Discovery gap {score:.1f}: interesting, but still too exposed or uncertain."
    return f"Discovery gap {score:.1f}: demand exists, yet differentiation is limited."
