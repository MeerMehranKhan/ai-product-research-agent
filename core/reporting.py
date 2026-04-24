from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.models import AnalysisRun
from utils.config import EXPORT_DIR
from utils.helpers import format_currency, json_dumps, make_json_safe
from utils.llm import available_provider


def build_run_insights(
    top_products: list[dict[str, object]],
    avoided_products: list[dict[str, object]],
    adjacent_niche: str,
) -> dict[str, object]:
    if not top_products:
        return {
            "best_opportunity": None,
            "safest_opportunity": None,
            "most_overlooked_opportunity": None,
            "biggest_red_flag": "No products met the current confidence and economics thresholds.",
            "adjacent_niche_suggestion": adjacent_niche,
            "insight_mode": "rule_based",
            "llm_provider": available_provider(),
        }

    best = max(top_products, key=lambda item: item["opportunity_score"])
    safest = max(top_products, key=lambda item: (item["confidence_score"], -item["raw_competition"]))
    overlooked = max(top_products, key=lambda item: item["discovery_gap_score"])
    red_flag = avoided_products[0]["reason"] if avoided_products else "Crowding risk should be watched during launch."
    return {
        "best_opportunity": {"name": best["name"], "score": best["opportunity_score"]},
        "safest_opportunity": {"name": safest["name"], "confidence": safest["confidence_score"]},
        "most_overlooked_opportunity": {
            "name": overlooked["name"],
            "discovery_gap_score": overlooked["discovery_gap_score"],
        },
        "biggest_red_flag": red_flag,
        "adjacent_niche_suggestion": adjacent_niche,
        "insight_mode": "rule_based",
        "llm_provider": available_provider(),
    }


def write_json_report(run: AnalysisRun) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{run.run_id}.json"
    path.write_text(json_dumps(run.to_dict()), encoding="utf-8")
    return str(path)


def write_pdf_report(run: AnalysisRun) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{run.run_id}.pdf"
    document = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("AI Product Research Agent", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Run ID: {run.run_id}", styles["Normal"]))
    story.append(Paragraph(f"Outcome: {run.outcome.title()}", styles["Normal"]))
    story.append(Spacer(1, 12))

    table_rows = [["Product", "Opportunity", "Confidence", "Margin", "Suggested Price"]]
    for product in run.top_products[:5]:
        table_rows.append(
            [
                product["name"],
                f"{product['opportunity_score']:.1f}",
                f"{product['confidence_score']:.1f}",
                f"{product['estimated_margin_pct']:.1f}%",
                format_currency(product["suggested_selling_price"]),
            ]
        )
    table = Table(table_rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4b5563")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Run Insights", styles["Heading2"]))
    story.append(Paragraph(json.dumps(make_json_safe(run.run_insights), indent=2), styles["Code"]))
    document.build(story)
    return str(path)
