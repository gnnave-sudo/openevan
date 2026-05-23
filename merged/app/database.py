"""
OpenEvan v11 — Merged Unified Database
Combines x870 tables (matters, documents, memory, tasks, stakeholders, outputs, precedents)
with OpenEvan tables (raw_inputs, fact_packets, stress_results, patterns, alignment, 
credibility, posture_scores, drift_events).
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite

DB_PATH = os.environ.get("EVAN_DB_PATH", "openevan_v11.db")

# ── Unified Schema ─────────────────────────────────────────────────────────

CREATE_TABLES_SQL = """
-- x870: Matters
CREATE TABLE IF NOT EXISTS matters (
    id TEXT PRIMARY KEY,
    matter_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    entity TEXT NOT NULL,
    regulator TEXT,
    product TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'open',
    summary TEXT,
    working_position TEXT,
    current_risk TEXT,
    owner TEXT,
    deadline TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matter_events (
    id TEXT PRIMARY KEY,
    matter_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    details_json TEXT DEFAULT '{}',
    source_type TEXT,
    source_ref TEXT,
    importance_score REAL DEFAULT 0.5,
    event_time TEXT NOT NULL,
    created_by TEXT,
    FOREIGN KEY (matter_id) REFERENCES matters(id)
);

-- x870: Documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    matter_id TEXT,
    source_system TEXT,
    mime_type TEXT NOT NULL,
    sensitivity_level TEXT DEFAULT 'internal',
    file_path TEXT,
    version INTEGER DEFAULT 1,
    checksum TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (matter_id) REFERENCES matters(id)
);

-- x870: Memory
CREATE TABLE IF NOT EXISTS memory_items (
    id TEXT PRIMARY KEY,
    memory_class TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    importance_score REAL DEFAULT 0.5,
    confidence_score REAL DEFAULT 0.8,
    valid_from TEXT,
    valid_to TEXT,
    source_type TEXT,
    source_ref TEXT,
    user_id TEXT,
    active INTEGER DEFAULT 1,
    review_status TEXT DEFAULT 'approved',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- x870: Outputs
CREATE TABLE IF NOT EXISTS outputs (
    id TEXT PRIMARY KEY,
    output_type TEXT NOT NULL,
    matter_id TEXT,
    audience TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    status TEXT DEFAULT 'draft',
    quality_rating REAL,
    model_used TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (matter_id) REFERENCES matters(id)
);

-- x870: Precedents
CREATE TABLE IF NOT EXISTS precedents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    precedent_type TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    audience TEXT,
    topic_tags TEXT DEFAULT '[]',
    summary TEXT,
    content TEXT NOT NULL,
    user_id TEXT,
    quality_score REAL DEFAULT 0.0,
    source_output_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- x870: Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    matter_id TEXT,
    owner TEXT,
    priority TEXT DEFAULT 'medium',
    due_date TEXT,
    status TEXT DEFAULT 'not_started',
    blocker TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (matter_id) REFERENCES matters(id)
);

-- x870: Stakeholders
CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT,
    relationship_type TEXT NOT NULL,
    tone_profile TEXT,
    decision_preference_summary TEXT,
    notes TEXT,
    user_id TEXT,
    credibility_score_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- x870: Preferences
CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL DEFAULT 0.8,
    source_type TEXT,
    source_ref TEXT,
    user_id TEXT,
    active INTEGER DEFAULT 1,
    last_confirmed_at TEXT,
    created_at TEXT NOT NULL
);

-- x870: Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    user_id TEXT,
    details_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

-- x870: Chat Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    matter_id TEXT,
    context_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- OpenEvan L1: Raw Inputs
CREATE TABLE IF NOT EXISTS raw_inputs (
    id TEXT PRIMARY KEY,
    input_type TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

-- OpenEvan L1: Fact Packets
CREATE TABLE IF NOT EXISTS fact_packets (
    id TEXT PRIMARY KEY,
    raw_input_id TEXT NOT NULL,
    matter_id TEXT,
    jurisdiction TEXT NOT NULL,
    regulator TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    product_class TEXT NOT NULL,
    target_user_type TEXT NOT NULL,
    licensing_category TEXT NOT NULL,
    revenue_model TEXT NOT NULL,
    custody_model TEXT NOT NULL,
    cross_border_elements TEXT DEFAULT '[]',
    obligations TEXT DEFAULT '{}',
    control_representations TEXT DEFAULT '{}',
    risk_signals TEXT DEFAULT '[]',
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (raw_input_id) REFERENCES raw_inputs(id)
);

-- OpenEvan L2: Stress Results
CREATE TABLE IF NOT EXISTS stress_results (
    id TEXT PRIMARY KEY,
    matter_id TEXT,
    fact_packet_id TEXT,
    mode TEXT NOT NULL DEFAULT 'standard',
    scenarios TEXT DEFAULT '[]',
    overall_risk_score REAL NOT NULL DEFAULT 0.0,
    risk_dimensions TEXT DEFAULT '[]',
    final_recommendation TEXT NOT NULL DEFAULT 'HOLD',
    decisive_obligations TEXT DEFAULT '[]',
    key_control_gaps TEXT DEFAULT '[]',
    evidence_checklist TEXT DEFAULT '[]',
    regulator_objections TEXT DEFAULT '[]',
    generated_at TEXT NOT NULL,
    model_used TEXT,
    FOREIGN KEY (matter_id) REFERENCES matters(id),
    FOREIGN KEY (fact_packet_id) REFERENCES fact_packets(id)
);

-- OpenEvan L3: Patterns
CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    stress_result_id TEXT,
    matter_id TEXT,
    recurring_obligations TEXT DEFAULT '[]',
    risk_drivers TEXT DEFAULT '[]',
    compliance_weaknesses TEXT DEFAULT '[]',
    early_warning_signals TEXT DEFAULT '[]',
    risk_index TEXT DEFAULT '{}',
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (stress_result_id) REFERENCES stress_results(id)
);

-- OpenEvan L4: Alignment Results
CREATE TABLE IF NOT EXISTS alignment_results (
    id TEXT PRIMARY KEY,
    matter_id TEXT,
    counsel_name TEXT NOT NULL,
    overall_alignment REAL NOT NULL DEFAULT 0.0,
    dimensions TEXT DEFAULT '[]',
    key_gaps TEXT DEFAULT '[]',
    recommendations TEXT DEFAULT '[]',
    analyzed_at TEXT NOT NULL,
    FOREIGN KEY (matter_id) REFERENCES matters(id)
);

-- OpenEvan L5: Escalations
CREATE TABLE IF NOT EXISTS escalations (
    id TEXT PRIMARY KEY,
    priority TEXT NOT NULL DEFAULT 'P1',
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    related_matter_id TEXT,
    related_output_id TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL,
    FOREIGN KEY (related_matter_id) REFERENCES matters(id)
);

-- OpenEvan L6: Posture Scores
CREATE TABLE IF NOT EXISTS posture_scores (
    id TEXT PRIMARY KEY,
    overall_score REAL NOT NULL DEFAULT 0.0,
    dimension_scores TEXT DEFAULT '{}',
    trend TEXT DEFAULT 'stable',
    assessed_at TEXT NOT NULL
);

-- OpenEvan L6: Drift Events
CREATE TABLE IF NOT EXISTS drift_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    impact_score REAL NOT NULL DEFAULT 0.0,
    previous_posture REAL DEFAULT 0.0,
    new_posture REAL DEFAULT 0.0,
    detected_at TEXT NOT NULL
);

-- OpenEvan CS: Credibility Scores
CREATE TABLE IF NOT EXISTS credibility_scores (
    id TEXT PRIMARY KEY,
    counsel_name TEXT NOT NULL,
    dimensions TEXT DEFAULT '{}',
    overall_score REAL NOT NULL DEFAULT 0.0,
    tier TEXT DEFAULT 'Monitor',
    track_record TEXT DEFAULT '{}',
    matter_id TEXT,
    scored_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_matters_status ON matters(status);
CREATE INDEX IF NOT EXISTS idx_matters_jurisdiction ON matters(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_stress_matter ON stress_results(matter_id);
CREATE INDEX IF NOT EXISTS idx_patterns_matter ON patterns(matter_id);
CREATE INDEX IF NOT EXISTS idx_memory_class ON memory_items(memory_class);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);
CREATE INDEX IF NOT EXISTS idx_credibility_name ON credibility_scores(counsel_name);
"""


# ── Database Manager ───────────────────────────────────────────────────────

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(CREATE_TABLES_SQL)
        await self._db.commit()
        return self

    async def close(self):
        if self._db:
            await self._db.close()

    async def execute(self, sql: str, parameters: tuple = ()):
        return await self._db.execute(sql, parameters)

    async def execute_many(self, sql: str, parameters: list):
        return await self._db.executemany(sql, parameters)

    async def fetchone(self, sql: str, parameters: tuple = ()):
        async with self._db.execute(sql, parameters) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, parameters: tuple = ()):
        async with self._db.execute(sql, parameters) as cursor:
            return await cursor.fetchall()

    async def commit(self):
        await self._db.commit()


# ── Generic CRUD Operations ────────────────────────────────────────────────

async def create_record(db: Database, table: str, data: Dict[str, Any]) -> str:
    record_id = str(uuid.uuid4())
    data["id"] = record_id
    now = datetime.utcnow().isoformat()
    if "created_at" not in data:
        data["created_at"] = now
    if "updated_at" not in data:
        data["updated_at"] = now
    
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = tuple(
        json.dumps(v) if isinstance(v, (list, dict)) else v 
        for v in data.values()
    )
    
    await db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    await db.commit()
    return record_id


async def get_record(db: Database, table: str, record_id: str) -> Optional[Dict[str, Any]]:
    row = await db.fetchone(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
    if row:
        return dict(row)
    return None


async def list_records(db: Database, table: str, filters: Dict[str, Any] = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
    sql = f"SELECT * FROM {table}"
    params = []
    if filters:
        conditions = []
        for k, v in filters.items():
            conditions.append(f"{k} = ?")
            params.append(v)
        sql += " WHERE " + " AND ".join(conditions)
    sql += f" ORDER BY created_at DESC LIMIT {limit}"
    
    rows = await db.fetchall(sql, tuple(params))
    return [dict(r) for r in rows]


async def update_record(db: Database, table: str, record_id: str, 
                        data: Dict[str, Any]) -> bool:
    if not data:
        return False
    
    data["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join([f"{k} = ?" for k in data.keys()])
    values = tuple(
        json.dumps(v) if isinstance(v, (list, dict)) else v 
        for v in data.values()
    )
    
    cursor = await db.execute(f"UPDATE {table} SET {sets} WHERE id = ?", 
                              values + (record_id,))
    await db.commit()
    return cursor.rowcount > 0


def parse_json_field(row: Dict[str, Any], field: str, default: Any = None):
    val = row.get(field)
    if val is None:
        return default if default is not None else []
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else []
    return val
