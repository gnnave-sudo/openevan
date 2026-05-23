"""
Evan Legal Quant Workflow Stack - SQLite Persistence Layer
Full async database with 14 tables across 7 layers + Part II.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite

# ── Configuration ─────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("EVAN_DB_PATH", "evan_quant.db")

# ── SQL Schema ────────────────────────────────────────────────────────────────

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS raw_inputs (
    id TEXT PRIMARY KEY,
    input_type TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS fact_packets (
    id TEXT PRIMARY KEY,
    raw_input_id TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    regulator TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    product_class TEXT NOT NULL,
    target_user_type TEXT NOT NULL,
    licensing_category TEXT NOT NULL,
    revenue_model TEXT NOT NULL,
    custody_model TEXT NOT NULL,
    cross_border_elements TEXT NOT NULL DEFAULT '[]',
    obligations TEXT NOT NULL DEFAULT '{}',
    control_representations TEXT NOT NULL DEFAULT '{}',
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (raw_input_id) REFERENCES raw_inputs(id)
);

CREATE TABLE IF NOT EXISTS stress_results (
    id TEXT PRIMARY KEY,
    fact_packet_id TEXT NOT NULL,
    scenarios TEXT NOT NULL DEFAULT '[]',
    final_risk_rating REAL NOT NULL DEFAULT 0.0,
    decisive_obligations TEXT NOT NULL DEFAULT '[]',
    key_control_gaps TEXT NOT NULL DEFAULT '[]',
    evidence_checklist TEXT NOT NULL DEFAULT '[]',
    regulator_objections TEXT NOT NULL DEFAULT '[]',
    final_recommendation TEXT NOT NULL DEFAULT 'HOLD',
    generated_at TEXT NOT NULL,
    FOREIGN KEY (fact_packet_id) REFERENCES fact_packets(id)
);

CREATE TABLE IF NOT EXISTS simulation_scenarios (
    id TEXT PRIMARY KEY,
    fact_packet_id TEXT NOT NULL,
    stress_result_id TEXT NOT NULL,
    scenario_number INTEGER NOT NULL,
    business_advocate TEXT NOT NULL DEFAULT '',
    compliance_reviewer TEXT NOT NULL DEFAULT '',
    regulator_proxy TEXT NOT NULL DEFAULT '',
    neutral_adjudicator TEXT NOT NULL DEFAULT '',
    risk_score_overall REAL NOT NULL DEFAULT 0.0,
    risk_score_dimensions TEXT NOT NULL DEFAULT '{}',
    recommendation TEXT NOT NULL DEFAULT 'HOLD',
    generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pattern_extracts (
    id TEXT PRIMARY KEY,
    stress_result_id TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    product_type TEXT NOT NULL,
    risk_drivers TEXT NOT NULL DEFAULT '[]',
    recurrent_obligations TEXT NOT NULL DEFAULT '[]',
    recurring_control_weaknesses TEXT NOT NULL DEFAULT '[]',
    regulatory_posture_signals TEXT NOT NULL DEFAULT '[]',
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (stress_result_id) REFERENCES stress_results(id)
);

CREATE TABLE IF NOT EXISTS risk_indices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_risk_index TEXT NOT NULL DEFAULT '{}',
    obligation_frequency TEXT NOT NULL DEFAULT '{}',
    control_failure_frequency TEXT NOT NULL DEFAULT '{}',
    counsel_alignment_index TEXT NOT NULL DEFAULT '{}',
    escalation_likelihood TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS counsel_memos (
    id TEXT PRIMARY KEY,
    counsel_name TEXT NOT NULL,
    memo_content TEXT NOT NULL,
    related_fact_packet_id TEXT,
    submitted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alignment_results (
    id TEXT PRIMARY KEY,
    memo_id TEXT NOT NULL,
    alignment_score REAL NOT NULL DEFAULT 0.0,
    dimension_scores TEXT NOT NULL DEFAULT '{}',
    missing_regulator_objections TEXT NOT NULL DEFAULT '[]',
    missing_evidence_hooks TEXT NOT NULL DEFAULT '[]',
    overconfidence_flags TEXT NOT NULL DEFAULT '[]',
    suggested_clarification_questions TEXT NOT NULL DEFAULT '[]',
    analyzed_at TEXT NOT NULL,
    FOREIGN KEY (memo_id) REFERENCES counsel_memos(id)
);

CREATE TABLE IF NOT EXISTS decision_memos (
    id TEXT PRIMARY KEY,
    stress_result_id TEXT NOT NULL,
    title TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    risk_assessment TEXT NOT NULL,
    recommendations TEXT NOT NULL DEFAULT '[]',
    next_steps TEXT NOT NULL DEFAULT '[]',
    generated_at TEXT NOT NULL,
    FOREIGN KEY (stress_result_id) REFERENCES stress_results(id)
);

CREATE TABLE IF NOT EXISTS escalation_items (
    id TEXT PRIMARY KEY,
    priority TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS control_investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_name TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    estimated_cost TEXT NOT NULL DEFAULT '',
    risk_reduction REAL NOT NULL DEFAULT 0.0,
    jurisdictions TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS drift_detections (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    previous_score REAL NOT NULL DEFAULT 0.0,
    current_score REAL NOT NULL DEFAULT 0.0,
    drift_detected INTEGER NOT NULL DEFAULT 0,
    drift_magnitude REAL NOT NULL DEFAULT 0.0,
    posture_change TEXT NOT NULL DEFAULT '',
    detected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS credibility_scores (
    id TEXT PRIMARY KEY,
    counsel_name TEXT NOT NULL,
    matter_id TEXT NOT NULL,
    dimension_scores TEXT NOT NULL DEFAULT '{}',
    weighted_score REAL NOT NULL DEFAULT 0.0,
    risk_tier TEXT NOT NULL DEFAULT 'WEAK',
    scored_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS counsel_track_records (
    counsel_name TEXT PRIMARY KEY,
    average_score REAL NOT NULL DEFAULT 0.0,
    scores_by_jurisdiction TEXT NOT NULL DEFAULT '{}',
    scores_over_time TEXT NOT NULL DEFAULT '[]',
    enforcement_correlation REAL NOT NULL DEFAULT 0.0,
    hindsight_accuracy REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT NOT NULL
);
"""


# ── JSON helpers ──────────────────────────────────────────────────────────────


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(text: str) -> Any:
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


# ── Database class ────────────────────────────────────────────────────────────


class Database:
    """Async SQLite persistence for the Evan Legal Quant Workflow Stack."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ── Init ─────────────────────────────────────────────────────────────────

    async def init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.executescript(CREATE_TABLES_SQL)
            await conn.commit()

    # ── Raw Inputs ───────────────────────────────────────────────────────────

    async def save_raw_input(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT OR REPLACE INTO raw_inputs
                (id, input_type, source, content, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["input_type"],
                    data["source"],
                    data["content"],
                    data["timestamp"].isoformat()
                    if isinstance(data["timestamp"], datetime)
                    else str(data["timestamp"]),
                    data.get("status", "pending"),
                ),
            )
            await conn.commit()

    async def get_raw_input(self, id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM raw_inputs WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def list_raw_inputs(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM raw_inputs ORDER BY timestamp DESC"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def update_raw_input_status(
        self, id: str, status: str
    ) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                "UPDATE raw_inputs SET status = ? WHERE id = ?",
                (status, id),
            )
            await conn.commit()

    # ── Fact Packets ─────────────────────────────────────────────────────────

    async def save_fact_packet(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("extracted_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO fact_packets
                (id, raw_input_id, jurisdiction, regulator, activity_type,
                 product_class, target_user_type, licensing_category,
                 revenue_model, custody_model, cross_border_elements,
                 obligations, control_representations, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["raw_input_id"],
                    data["jurisdiction"],
                    data["regulator"],
                    data["activity_type"],
                    data["product_class"],
                    data["target_user_type"],
                    data["licensing_category"],
                    data["revenue_model"],
                    data["custody_model"],
                    _dumps(data.get("cross_border_elements", [])),
                    _dumps(data.get("obligations", {})),
                    _dumps(data.get("control_representations", {})),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_fact_packet(self, id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM fact_packets WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["cross_border_elements"] = _loads(
                result["cross_border_elements"]
            )
            result["obligations"] = _loads(result["obligations"])
            result["control_representations"] = _loads(
                result["control_representations"]
            )
            return result

    async def get_fact_packet_by_raw(
        self, raw_id: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM fact_packets WHERE raw_input_id = ? LIMIT 1",
                (raw_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["cross_border_elements"] = _loads(
                result["cross_border_elements"]
            )
            result["obligations"] = _loads(result["obligations"])
            result["control_representations"] = _loads(
                result["control_representations"]
            )
            return result

    # ── Stress Results ───────────────────────────────────────────────────────

    async def save_stress_result(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("generated_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO stress_results
                (id, fact_packet_id, scenarios, final_risk_rating,
                 decisive_obligations, key_control_gaps, evidence_checklist,
                 regulator_objections, final_recommendation, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["fact_packet_id"],
                    _dumps(data.get("scenarios", [])),
                    data.get("final_risk_rating", 0.0),
                    _dumps(data.get("decisive_obligations", [])),
                    _dumps(data.get("key_control_gaps", [])),
                    _dumps(data.get("evidence_checklist", [])),
                    _dumps(data.get("regulator_objections", [])),
                    data.get("final_recommendation", "HOLD"),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_stress_result(self, id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM stress_results WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["scenarios"] = _loads(result["scenarios"])
            result["decisive_obligations"] = _loads(
                result["decisive_obligations"]
            )
            result["key_control_gaps"] = _loads(result["key_control_gaps"])
            result["evidence_checklist"] = _loads(
                result["evidence_checklist"]
            )
            result["regulator_objections"] = _loads(
                result["regulator_objections"]
            )
            return result

    async def list_stress_results(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM stress_results ORDER BY generated_at DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["scenarios"] = _loads(r["scenarios"])
                r["decisive_obligations"] = _loads(
                    r["decisive_obligations"]
                )
                r["key_control_gaps"] = _loads(r["key_control_gaps"])
                r["evidence_checklist"] = _loads(r["evidence_checklist"])
                r["regulator_objections"] = _loads(
                    r["regulator_objections"]
                )
                results.append(r)
            return results

    # ── Simulation Scenarios ─────────────────────────────────────────────────

    async def save_scenario(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("generated_at", datetime.utcnow())
            agent_positions = data.get("agent_positions", {})
            risk_score = data.get("risk_score", {})
            await conn.execute(
                """INSERT OR REPLACE INTO simulation_scenarios
                (id, fact_packet_id, stress_result_id, scenario_number,
                 business_advocate, compliance_reviewer, regulator_proxy,
                 neutral_adjudicator, risk_score_overall,
                 risk_score_dimensions, recommendation, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["fact_packet_id"],
                    data.get("stress_result_id", ""),
                    data["scenario_number"],
                    agent_positions.get("business_advocate", ""),
                    agent_positions.get("compliance_reviewer", ""),
                    agent_positions.get("regulator_proxy", ""),
                    agent_positions.get("neutral_adjudicator", ""),
                    risk_score.get("overall", 0.0)
                    if isinstance(risk_score, dict)
                    else 0.0,
                    _dumps(risk_score.get("dimensions", {}))
                    if isinstance(risk_score, dict)
                    else "{}",
                    data.get("recommendation", "HOLD"),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def list_scenarios(
        self, result_id: str
    ) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM simulation_scenarios WHERE stress_result_id = ? ORDER BY scenario_number",
                (result_id,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["agent_positions"] = {
                    "business_advocate": r.pop("business_advocate", ""),
                    "compliance_reviewer": r.pop("compliance_reviewer", ""),
                    "regulator_proxy": r.pop("regulator_proxy", ""),
                    "neutral_adjudicator": r.pop("neutral_adjudicator", ""),
                }
                r["risk_score"] = {
                    "overall": r.pop("risk_score_overall", 0.0),
                    "dimensions": _loads(
                        r.pop("risk_score_dimensions", "{}")
                    ),
                }
                results.append(r)
            return results

    # ── Pattern Extracts ─────────────────────────────────────────────────────

    async def save_pattern_extract(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("extracted_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO pattern_extracts
                (id, stress_result_id, jurisdiction, product_type,
                 risk_drivers, recurrent_obligations,
                 recurring_control_weaknesses, regulatory_posture_signals,
                 extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["stress_result_id"],
                    data["jurisdiction"],
                    data["product_type"],
                    _dumps(data.get("risk_drivers", [])),
                    _dumps(data.get("recurrent_obligations", [])),
                    _dumps(data.get("recurring_control_weaknesses", [])),
                    _dumps(data.get("regulatory_posture_signals", [])),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_pattern_extract(
        self, id: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM pattern_extracts WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["risk_drivers"] = _loads(result["risk_drivers"])
            result["recurrent_obligations"] = _loads(
                result["recurrent_obligations"]
            )
            result["recurring_control_weaknesses"] = _loads(
                result["recurring_control_weaknesses"]
            )
            result["regulatory_posture_signals"] = _loads(
                result["regulatory_posture_signals"]
            )
            return result

    async def list_pattern_extracts(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM pattern_extracts ORDER BY extracted_at DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["risk_drivers"] = _loads(r["risk_drivers"])
                r["recurrent_obligations"] = _loads(
                    r["recurrent_obligations"]
                )
                r["recurring_control_weaknesses"] = _loads(
                    r["recurring_control_weaknesses"]
                )
                r["regulatory_posture_signals"] = _loads(
                    r["regulatory_posture_signals"]
                )
                results.append(r)
            return results

    # ── Risk Indices ─────────────────────────────────────────────────────────

    async def update_risk_indices(
        self, indices: Dict[str, Any]
    ) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT OR REPLACE INTO risk_indices
                (id, jurisdiction_risk_index, obligation_frequency,
                 control_failure_frequency, counsel_alignment_index,
                 escalation_likelihood, updated_at)
                VALUES (
                    (SELECT id FROM risk_indices ORDER BY id DESC LIMIT 1),
                    ?, ?, ?, ?, ?, ?
                )""",
                (
                    _dumps(indices.get("jurisdiction_risk_index", {})),
                    _dumps(indices.get("obligation_frequency", {})),
                    _dumps(indices.get("control_failure_frequency", {})),
                    _dumps(indices.get("counsel_alignment_index", {})),
                    _dumps(indices.get("escalation_likelihood", {})),
                    datetime.utcnow().isoformat(),
                ),
            )
            await conn.commit()

    async def get_risk_indices(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM risk_indices ORDER BY id DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            if not row:
                return {
                    "jurisdiction_risk_index": {},
                    "obligation_frequency": {},
                    "control_failure_frequency": {},
                    "counsel_alignment_index": {},
                    "escalation_likelihood": {},
                }
            result = dict(row)
            result["jurisdiction_risk_index"] = _loads(
                result["jurisdiction_risk_index"]
            )
            result["obligation_frequency"] = _loads(
                result["obligation_frequency"]
            )
            result["control_failure_frequency"] = _loads(
                result["control_failure_frequency"]
            )
            result["counsel_alignment_index"] = _loads(
                result["counsel_alignment_index"]
            )
            result["escalation_likelihood"] = _loads(
                result["escalation_likelihood"]
            )
            return result

    # ── Counsel Memos ────────────────────────────────────────────────────────

    async def save_counsel_memo(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("submitted_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO counsel_memos
                (id, counsel_name, memo_content, related_fact_packet_id,
                 submitted_at)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["counsel_name"],
                    data["memo_content"],
                    data.get("related_fact_packet_id"),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_counsel_memo(self, id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM counsel_memos WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def list_counsel_memos(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM counsel_memos ORDER BY submitted_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # ── Alignment Results ────────────────────────────────────────────────────

    async def save_alignment_result(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("analyzed_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO alignment_results
                (id, memo_id, alignment_score, dimension_scores,
                 missing_regulator_objections, missing_evidence_hooks,
                 overconfidence_flags, suggested_clarification_questions,
                 analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["memo_id"],
                    data.get("alignment_score", 0.0),
                    _dumps(data.get("dimension_scores", {})),
                    _dumps(data.get("missing_regulator_objections", [])),
                    _dumps(data.get("missing_evidence_hooks", [])),
                    _dumps(data.get("overconfidence_flags", [])),
                    _dumps(
                        data.get("suggested_clarification_questions", [])
                    ),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_alignment_result(
        self, id: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM alignment_results WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["dimension_scores"] = _loads(result["dimension_scores"])
            result["missing_regulator_objections"] = _loads(
                result["missing_regulator_objections"]
            )
            result["missing_evidence_hooks"] = _loads(
                result["missing_evidence_hooks"]
            )
            result["overconfidence_flags"] = _loads(
                result["overconfidence_flags"]
            )
            result["suggested_clarification_questions"] = _loads(
                result["suggested_clarification_questions"]
            )
            return result

    async def get_alignment_by_memo(
        self, memo_id: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM alignment_results WHERE memo_id = ? LIMIT 1",
                (memo_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["dimension_scores"] = _loads(result["dimension_scores"])
            result["missing_regulator_objections"] = _loads(
                result["missing_regulator_objections"]
            )
            result["missing_evidence_hooks"] = _loads(
                result["missing_evidence_hooks"]
            )
            result["overconfidence_flags"] = _loads(
                result["overconfidence_flags"]
            )
            result["suggested_clarification_questions"] = _loads(
                result["suggested_clarification_questions"]
            )
            return result

    # ── Decision Memos ───────────────────────────────────────────────────────

    async def save_decision_memo(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("generated_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO decision_memos
                (id, stress_result_id, title, executive_summary,
                 risk_assessment, recommendations, next_steps,
                 generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["stress_result_id"],
                    data["title"],
                    data["executive_summary"],
                    data["risk_assessment"],
                    _dumps(data.get("recommendations", [])),
                    _dumps(data.get("next_steps", [])),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_decision_memo(self, id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM decision_memos WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["recommendations"] = _loads(result["recommendations"])
            result["next_steps"] = _loads(result["next_steps"])
            return result

    async def list_decision_memos(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM decision_memos ORDER BY generated_at DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["recommendations"] = _loads(r["recommendations"])
                r["next_steps"] = _loads(r["next_steps"])
                results.append(r)
            return results

    # ── Escalation Items ─────────────────────────────────────────────────────

    async def save_escalation_item(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            due = data.get("due_date")
            await conn.execute(
                """INSERT OR REPLACE INTO escalation_items
                (id, priority, title, description, jurisdiction,
                 due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["priority"],
                    data["title"],
                    data["description"],
                    data["jurisdiction"],
                    due.isoformat()
                    if isinstance(due, datetime)
                    else str(due) if due else None,
                    data.get("status", "open"),
                ),
            )
            await conn.commit()

    async def get_escalation_item(
        self, id: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM escalation_items WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def list_escalation_items(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM escalation_items ORDER BY priority ASC, id DESC"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # ── Control Investments ──────────────────────────────────────────────────

    async def save_control_investment(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT OR REPLACE INTO control_investments
                (id, control_name, priority, estimated_cost,
                 risk_reduction, jurisdictions)
                VALUES (
                    COALESCE((SELECT id FROM control_investments
                     WHERE control_name = ?), NULL),
                    ?, ?, ?, ?, ?)""",
                (
                    data["control_name"],
                    data["control_name"],
                    data.get("priority", 0),
                    data.get("estimated_cost", ""),
                    data.get("risk_reduction", 0.0),
                    _dumps(data.get("jurisdictions", [])),
                ),
            )
            await conn.commit()

    async def list_control_investments(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM control_investments ORDER BY priority ASC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["jurisdictions"] = _loads(r["jurisdictions"])
                results.append(r)
            return results

    # ── Drift Detections ─────────────────────────────────────────────────────

    async def save_drift_detection(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("detected_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO drift_detections
                (id, product_id, previous_score, current_score,
                 drift_detected, drift_magnitude, posture_change,
                 detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["product_id"],
                    data.get("previous_score", 0.0),
                    data.get("current_score", 0.0),
                    1 if data.get("drift_detected") else 0,
                    data.get("drift_magnitude", 0.0),
                    data.get("posture_change", ""),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def list_drift_detections(
        self, product_id: str
    ) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM drift_detections WHERE product_id = ? ORDER BY detected_at DESC",
                (product_id,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["drift_detected"] = bool(r["drift_detected"])
                results.append(r)
            return results

    # ── Credibility Scores ───────────────────────────────────────────────────

    async def save_credibility_score(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            ts = data.get("scored_at", datetime.utcnow())
            await conn.execute(
                """INSERT OR REPLACE INTO credibility_scores
                (id, counsel_name, matter_id, dimension_scores,
                 weighted_score, risk_tier, scored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["id"],
                    data["counsel_name"],
                    data["matter_id"],
                    _dumps(data.get("dimension_scores", {})),
                    data.get("weighted_score", 0.0),
                    data.get("risk_tier", "WEAK"),
                    ts.isoformat() if isinstance(ts, datetime) else str(ts),
                ),
            )
            await conn.commit()

    async def get_credibility_scores(
        self, counsel_name: str
    ) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM credibility_scores WHERE counsel_name = ? ORDER BY scored_at DESC",
                (counsel_name,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["dimension_scores"] = _loads(r["dimension_scores"])
                results.append(r)
            return results

    async def list_all_credibility_scores(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM credibility_scores ORDER BY scored_at DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["dimension_scores"] = _loads(r["dimension_scores"])
                results.append(r)
            return results

    # ── Counsel Track Records ────────────────────────────────────────────────

    async def update_counsel_track_record(
        self, track: Dict[str, Any]
    ) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT OR REPLACE INTO counsel_track_records
                (counsel_name, average_score, scores_by_jurisdiction,
                 scores_over_time, enforcement_correlation,
                 hindsight_accuracy, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    track["counsel_name"],
                    track["average_score"],
                    _dumps(track.get("scores_by_jurisdiction", {})),
                    _dumps(track.get("scores_over_time", [])),
                    track.get("enforcement_correlation", 0.0),
                    track.get("hindsight_accuracy", 0.0),
                    datetime.utcnow().isoformat(),
                ),
            )
            await conn.commit()

    async def get_counsel_track_record(
        self, name: str
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM counsel_track_records WHERE counsel_name = ?",
                (name,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["scores_by_jurisdiction"] = _loads(
                result["scores_by_jurisdiction"]
            )
            result["scores_over_time"] = _loads(result["scores_over_time"])
            return result

    async def list_counsel_leaderboard(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM counsel_track_records ORDER BY average_score DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["scores_by_jurisdiction"] = _loads(
                    r["scores_by_jurisdiction"]
                )
                r["scores_over_time"] = _loads(r["scores_over_time"])
                results.append(r)
            return results


# Global singleton
db = Database()
