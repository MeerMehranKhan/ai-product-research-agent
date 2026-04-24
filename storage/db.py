from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.models import AnalysisRun, TraceEvent
from utils.config import DB_PATH
from utils.helpers import json_dumps, make_json_safe


class ResearchRepository:
    def __init__(self, db_path: str | Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    outcome TEXT,
                    request_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    insights_json TEXT,
                    effective_weights_json TEXT,
                    exports_json TEXT
                );

                CREATE TABLE IF NOT EXISTS trace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    decision TEXT,
                    metadata_json TEXT,
                    FOREIGN KEY(run_id) REFERENCES analysis_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS product_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    product_slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES analysis_runs(run_id)
                );
                """
            )

    def create_run(self, run: AnalysisRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO analysis_runs (
                    run_id, created_at, status, outcome, request_json, context_json, insights_json, effective_weights_json, exports_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.created_at,
                    "running",
                    run.outcome,
                    json_dumps(run.request.to_dict()),
                    json_dumps(run.context.to_dict()),
                    json_dumps(run.run_insights),
                    json_dumps(run.effective_weights),
                    json_dumps(run.exports),
                ),
            )

    def save_trace_event(self, run_id: str, event: TraceEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO trace_events (run_id, timestamp, step, status, message, decision, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    event.timestamp,
                    event.step,
                    event.status,
                    event.message,
                    event.decision,
                    json_dumps(event.metadata),
                ),
            )

    def finalize_run(self, run: AnalysisRun) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM product_results WHERE run_id = ?", (run.run_id,))
            for product in run.top_products:
                connection.execute(
                    """
                    INSERT INTO product_results (run_id, product_slug, name, category, kind, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        product["product_slug"],
                        product["name"],
                        product["category"],
                        "top",
                        json_dumps(product),
                    ),
                )
            for product in run.avoided_products:
                connection.execute(
                    """
                    INSERT INTO product_results (run_id, product_slug, name, category, kind, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        product["product_slug"],
                        product["name"],
                        product["category"],
                        "avoided",
                        json_dumps(product),
                    ),
                )
            connection.execute(
                """
                UPDATE analysis_runs
                SET status = ?, outcome = ?, context_json = ?, insights_json = ?, effective_weights_json = ?, exports_json = ?
                WHERE run_id = ?
                """,
                (
                    "complete",
                    run.outcome,
                    json_dumps(run.context.to_dict()),
                    json_dumps(run.run_insights),
                    json_dumps(run.effective_weights),
                    json_dumps(run.exports),
                    run.run_id,
                ),
            )

    def mark_failed(self, run_id: str, message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE analysis_runs SET status = ?, outcome = ?, insights_json = ? WHERE run_id = ?",
                ("failed", "avoid", json_dumps({"error": message}), run_id),
            )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT run_id, created_at, status, outcome, request_json, insights_json
                FROM analysis_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        results = []
        for row in rows:
            request_payload = json.loads(row["request_json"])
            insights = json.loads(row["insights_json"] or "{}")
            results.append(
                {
                    "run_id": row["run_id"],
                    "created_at": row["created_at"],
                    "status": row["status"],
                    "outcome": row["outcome"],
                    "request": request_payload,
                    "best_opportunity": insights.get("best_opportunity"),
                }
            )
        return results

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            run_row = connection.execute("SELECT * FROM analysis_runs WHERE run_id = ?", (run_id,)).fetchone()
            if run_row is None:
                return None
            trace_rows = connection.execute(
                "SELECT * FROM trace_events WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()
            product_rows = connection.execute(
                "SELECT * FROM product_results WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()

        payload = {
            "run_id": run_row["run_id"],
            "created_at": run_row["created_at"],
            "status": run_row["status"],
            "outcome": run_row["outcome"],
            "request": json.loads(run_row["request_json"]),
            "context": json.loads(run_row["context_json"]),
            "run_insights": json.loads(run_row["insights_json"] or "{}"),
            "effective_weights": json.loads(run_row["effective_weights_json"] or "{}"),
            "exports": json.loads(run_row["exports_json"] or "{}"),
            "trace": [
                {
                    "timestamp": row["timestamp"],
                    "step": row["step"],
                    "status": row["status"],
                    "message": row["message"],
                    "decision": row["decision"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                }
                for row in trace_rows
            ],
            "top_products": [],
            "avoided_products": [],
        }
        for row in product_rows:
            product = json.loads(row["payload_json"])
            if row["kind"] == "top":
                payload["top_products"].append(product)
            else:
                payload["avoided_products"].append(product)
        return make_json_safe(payload)
