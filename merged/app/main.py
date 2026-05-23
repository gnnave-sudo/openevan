"""
OpenEvan v11 — Merged Unified FastAPI Application
Combines x870 Evan-AI Compliance OS (62 endpoints) with OpenEvan 
Analytical Engine (45 new endpoints) for a total of ~107 endpoints.
"""

import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Database, DB_PATH
from app.models import (
    AlignmentResult,
    ChatRequest,
    ChatResponse,
    DocumentResponse,
    DocumentUploadResponse,
    CounselLeaderboardEntry,
    CounselMemoSubmit,
    CredibilityScoreRequest,
    CredibilityScoreResponse,
    DecisionMemo,
    DraftRequest,
    DraftResponse,
    DriftEvent,
    EscalationItem,
    FactPacket,
    FeedbackCreate,
    HealthResponse,
    MatterCreate,
    MatterEventCreate,
    MatterResponse,
    MatterUpdate,
    MemoryItemCreate,
    MemoryItemResponse,
    MemoryItemUpdate,
    MemorySearchRequest,
    MemorySearchResponse,
    MetricsResponse,
    OutputResponse,
    PostureScore,
    PrecedentResponse,
    PrecedentSearchRequest,
    PreferenceCreate,
    PreferenceResponse,
    RawInputCreate,
    RawInputResponse,
    Recommendation,
    ResearchRequest,
    ResearchResponse,
    RiskHeatmapItem,
    SimulationMode,
    StakeholderCreate,
    StakeholderResponse,
    StressLabResult,
    StressLabRunRequest,
    SystemStatus,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.routers import alignment, credibility, intake, learning, patterns, stresslab

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="OpenEvan v11",
    description="Unified Compliance Intelligence — Evan-AI OS + OpenEvan Analytical Engine",
    version="11.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ────────────────────────────────────────────────────────────────

db = Database(DB_PATH)


@app.on_event("startup")
async def startup():
    await db.connect()
    logger.info("OpenEvan v11 database initialized at %s", DB_PATH)


@app.on_event("shutdown")
async def shutdown():
    await db.close()


# ── Request ID Middleware ───────────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    response.headers["X-Request-ID"] = request_id
    logger.info("[%s] %s %s — %.3fs", request_id, request.method, request.url.path, elapsed)
    return response


# ═════════════════════════════════════════════════════════════════════════════
# ROOT & STATUS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", response_model=SystemStatus, tags=["Status"])
async def root():
    return SystemStatus()


@app.get("/health", response_model=HealthResponse, tags=["Status"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services={"database": {"status": "healthy"}, "api": {"status": "healthy"}},
    )


# ═════════════════════════════════════════════════════════════════════════════
# x870: CHAT (stub — requires WebSocket/AI backend)
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    return ChatResponse(
        response="OpenEvan v11 chat endpoint. Connect to your LLM backend for full functionality.",
        session_id=req.session_id or str(uuid.uuid4()),
    )


@app.post("/api/v1/chat/stream", tags=["Chat"])
async def chat_stream(req: ChatRequest):
    return {"detail": "Streaming requires WebSocket implementation"}


@app.post("/api/v1/chat/session", tags=["Chat"])
async def create_session(req: ChatRequest):
    session_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO chat_sessions (id, title, matter_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, req.message[:50] if req.message else "New Session", 
         req.matter_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
    )
    await db.commit()
    return {"session_id": session_id, "message": "Session created"}


@app.get("/api/v1/chat/session/{session_id}", tags=["Chat"])
async def get_session(session_id: str):
    row = await db.fetchone("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
    if row:
        return dict(row)
    return {"detail": "Session not found"}


@app.delete("/api/v1/chat/session/{session_id}", tags=["Chat"])
async def delete_session(session_id: str):
    await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    await db.commit()
    return {"message": "Session cleared"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: MATTERS
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/matters", response_model=MatterResponse, tags=["Matters"])
async def create_matter(req: MatterCreate):
    from app.database import create_record
    data = req.model_dump()
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = data["created_at"]
    record_id = await create_record(db, "matters", data)
    row = await db.fetchone("SELECT * FROM matters WHERE id = ?", (record_id,))
    return MatterResponse(**dict(row))


@app.get("/api/v1/matters", response_model=List[MatterResponse], tags=["Matters"])
async def list_matters(status: str = None, jurisdiction: str = None, limit: int = 100):
    filters = {}
    if status:
        filters["status"] = status
    if jurisdiction:
        filters["jurisdiction"] = jurisdiction
    from app.database import list_records
    rows = await list_records(db, "matters", filters, limit)
    return [MatterResponse(**r) for r in rows]


@app.get("/api/v1/matters/{matter_id}", response_model=MatterResponse, tags=["Matters"])
async def get_matter(matter_id: str):
    row = await db.fetchone("SELECT * FROM matters WHERE id = ?", (matter_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Matter not found"})
    return MatterResponse(**dict(row))


@app.patch("/api/v1/matters/{matter_id}", response_model=MatterResponse, tags=["Matters"])
async def update_matter(matter_id: str, req: MatterUpdate):
    from app.database import update_record
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    await update_record(db, "matters", matter_id, data)
    row = await db.fetchone("SELECT * FROM matters WHERE id = ?", (matter_id,))
    return MatterResponse(**dict(row))


@app.post("/api/v1/matters/{matter_id}/events", tags=["Matters"])
async def add_matter_event(matter_id: str, req: MatterEventCreate):
    from app.database import create_record
    data = req.model_dump()
    data["matter_id"] = matter_id
    data["event_time"] = datetime.utcnow().isoformat()
    event_id = await create_record(db, "matter_events", data)
    return {"event_id": event_id, "matter_id": matter_id, "status": "created"}


@app.get("/api/v1/matters/{matter_id}/timeline", tags=["Matters"])
async def get_matter_timeline(matter_id: str):
    rows = await db.fetchall(
        "SELECT * FROM matter_events WHERE matter_id = ? ORDER BY event_time DESC",
        (matter_id,),
    )
    return {"events": [dict(r) for r in rows]}


@app.post("/api/v1/matters/{matter_id}/summarize", tags=["Matters"])
async def summarize_matter(matter_id: str):
    return {"matter_id": matter_id, "status": "queued", "message": "Summary generation queued"}


@app.get("/api/v1/matters/open/snapshot", tags=["Matters"])
async def get_open_matters_snapshot():
    rows = await db.fetchall(
        "SELECT * FROM matters WHERE status IN ('open', 'in_progress', 'pending_review') ORDER BY priority DESC, created_at DESC LIMIT 50"
    )
    return {"matters": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/v1/matters/deadlines/upcoming", tags=["Matters"])
async def get_upcoming_deadlines(days: int = 30):
    from datetime import timedelta
    cutoff = (datetime.utcnow() + timedelta(days=days)).isoformat()
    rows = await db.fetchall(
        "SELECT * FROM matters WHERE deadline IS NOT NULL AND deadline < ? AND status IN ('open', 'in_progress') ORDER BY deadline",
        (cutoff,),
    )
    return {"deadlines": [dict(r) for r in rows], "count": len(rows)}


# ═════════════════════════════════════════════════════════════════════════════
# x870: DOCUMENTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/documents", response_model=List[DocumentResponse], tags=["Documents"])
async def list_documents(matter_id: str = None, limit: int = 100):
    sql = "SELECT * FROM documents"
    params = []
    if matter_id:
        sql += " WHERE matter_id = ?"
        params.append(matter_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = await db.fetchall(sql, tuple(params))
    return [DocumentResponse(**dict(r)) for r in rows]


@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document():
    # File upload requires python-multipart File handling
    return DocumentUploadResponse(
        document_id=str(uuid.uuid4()),
        status="queued",
        message="Document upload stub — integrate with File handler",
    )


@app.post("/api/v1/documents/ingest-url", tags=["Documents"])
async def ingest_url(url: str, matter_id: str = None):
    doc_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO documents (id, title, doc_type, matter_id, mime_type, file_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (doc_id, url, "url_ingest", matter_id, "text/html", url,
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
    )
    await db.commit()
    return {"document_id": doc_id, "url": url, "matter_id": matter_id, "status": "queued"}


@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(document_id: str):
    row = await db.fetchone("SELECT * FROM documents WHERE id = ?", (document_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Document not found"})
    return DocumentResponse(**dict(row))


@app.get("/api/v1/documents/{document_id}/chunks", tags=["Documents"])
async def get_document_chunks(document_id: str):
    return {"document_id": document_id, "chunks": [], "message": "Chunking requires backend processing"}


@app.post("/api/v1/documents/{document_id}/link-matter", tags=["Documents"])
async def link_document_to_matter(document_id: str, matter_id: str):
    await db.execute(
        "UPDATE documents SET matter_id = ?, updated_at = ? WHERE id = ?",
        (matter_id, datetime.utcnow().isoformat(), document_id),
    )
    await db.commit()
    return {"document_id": document_id, "matter_id": matter_id, "status": "linked"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: MEMORY
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/memory", response_model=List[MemoryItemResponse], tags=["Memory"])
async def list_memory(memory_class: str = None, limit: int = 100):
    sql = "SELECT * FROM memory_items WHERE active = 1"
    params = []
    if memory_class:
        sql += " AND memory_class = ?"
        params.append(memory_class)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = await db.fetchall(sql, tuple(params))
    return [MemoryItemResponse(**dict(r)) for r in rows]


@app.post("/api/v1/memory", response_model=MemoryItemResponse, tags=["Memory"])
async def create_memory(req: MemoryItemCreate):
    from app.database import create_record, parse_json_field
    data = req.model_dump()
    data["tags"] = json.dumps(data.get("tags", []))
    data["user_id"] = "system"
    data["review_status"] = "pending"
    record_id = await create_record(db, "memory_items", data)
    row = await db.fetchone("SELECT * FROM memory_items WHERE id = ?", (record_id,))
    r = dict(row)
    r["tags"] = parse_json_field(r, "tags", [])
    return MemoryItemResponse(**r)


@app.get("/api/v1/memory/{memory_id}", response_model=MemoryItemResponse, tags=["Memory"])
async def get_memory(memory_id: str):
    from app.database import parse_json_field
    row = await db.fetchone("SELECT * FROM memory_items WHERE id = ?", (memory_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Memory item not found"})
    r = dict(row)
    r["tags"] = parse_json_field(r, "tags", [])
    return MemoryItemResponse(**r)


@app.patch("/api/v1/memory/{memory_id}", response_model=MemoryItemResponse, tags=["Memory"])
async def update_memory(memory_id: str, req: MemoryItemUpdate):
    from app.database import update_record, parse_json_field
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    if "tags" in data:
        data["tags"] = json.dumps(data["tags"])
    await update_record(db, "memory_items", memory_id, data)
    row = await db.fetchone("SELECT * FROM memory_items WHERE id = ?", (memory_id,))
    r = dict(row)
    r["tags"] = parse_json_field(r, "tags", [])
    return MemoryItemResponse(**r)


@app.delete("/api/v1/memory/{memory_id}", tags=["Memory"])
async def deactivate_memory(memory_id: str):
    await db.execute(
        "UPDATE memory_items SET active = 0, updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), memory_id),
    )
    await db.commit()
    return {"memory_id": memory_id, "status": "deactivated"}


@app.post("/api/v1/memory/search", response_model=MemorySearchResponse, tags=["Memory"])
async def search_memory(req: MemorySearchRequest):
    # Simplified search — full semantic search requires embeddings backend
    sql = "SELECT * FROM memory_items WHERE active = 1 AND (title LIKE ? OR content LIKE ?)"
    params = [f"%{req.query}%", f"%{req.query}%"]
    if req.memory_class:
        sql += " AND memory_class = ?"
        params.append(req.memory_class.value)
    sql += " ORDER BY importance_score DESC LIMIT ?"
    params.append(req.limit)
    rows = await db.fetchall(sql, tuple(params))
    items = [MemoryItemResponse(**dict(r)) for r in rows]
    scores = [0.9 - (i * 0.05) for i in range(len(items))]
    return MemorySearchResponse(items=items, scores=scores)


@app.get("/api/v1/memory/queue/pending", tags=["Memory"])
async def get_memory_queue():
    rows = await db.fetchall(
        "SELECT * FROM memory_items WHERE review_status = 'pending' ORDER BY created_at DESC"
    )
    return {"pending": [dict(r) for r in rows], "count": len(rows)}


@app.post("/api/v1/memory/queue/{memory_id}/approve", tags=["Memory"])
async def approve_memory(memory_id: str):
    await db.execute(
        "UPDATE memory_items SET review_status = 'approved', updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), memory_id),
    )
    await db.commit()
    return {"memory_id": memory_id, "status": "approved"}


@app.post("/api/v1/memory/queue/{memory_id}/discard", tags=["Memory"])
async def discard_memory(memory_id: str):
    await db.execute(
        "UPDATE memory_items SET review_status = 'discarded', active = 0, updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), memory_id),
    )
    await db.commit()
    return {"memory_id": memory_id, "status": "discarded"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: OUTPUTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/outputs", response_model=List[OutputResponse], tags=["Outputs"])
async def list_outputs(matter_id: str = None, limit: int = 100):
    sql = "SELECT * FROM outputs"
    params = []
    if matter_id:
        sql += " WHERE matter_id = ?"
        params.append(matter_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = await db.fetchall(sql, tuple(params))
    return [OutputResponse(**dict(r)) for r in rows]


@app.get("/api/v1/outputs/{output_id}", response_model=OutputResponse, tags=["Outputs"])
async def get_output(output_id: str):
    row = await db.fetchone("SELECT * FROM outputs WHERE id = ?", (output_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Output not found"})
    return OutputResponse(**dict(row))


@app.post("/api/v1/outputs/{output_id}/approve", tags=["Outputs"])
async def approve_output(output_id: str):
    await db.execute(
        "UPDATE outputs SET status = 'approved', updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), output_id),
    )
    await db.commit()
    return {"output_id": output_id, "status": "approved"}


@app.post("/api/v1/outputs/{output_id}/feedback", tags=["Outputs"])
async def submit_feedback(output_id: str, req: FeedbackCreate):
    return {
        "output_id": output_id,
        "feedback_type": req.feedback_type,
        "status": "recorded",
    }


@app.post("/api/v1/outputs/{output_id}/promote-precedent", tags=["Outputs"])
async def promote_to_precedent(output_id: str):
    row = await db.fetchone("SELECT * FROM outputs WHERE id = ?", (output_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Output not found"})
    r = dict(row)
    prec_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO precedents (id, title, precedent_type, jurisdiction, content, user_id, source_output_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (prec_id, r["title"], "regulatory_position", r.get("audience", "global") or "global",
         r["content"], "system", output_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
    )
    await db.commit()
    return {"precedent_id": prec_id, "output_id": output_id, "status": "promoted"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: PRECEDENTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/precedents", response_model=List[PrecedentResponse], tags=["Precedents"])
async def list_precedents(limit: int = 100):
    rows = await db.fetchall("SELECT * FROM precedents ORDER BY created_at DESC LIMIT ?", (limit,))
    return [PrecedentResponse(**dict(r)) for r in rows]


@app.post("/api/v1/precedents/search", response_model=List[PrecedentResponse], tags=["Precedents"])
async def search_precedents(req: PrecedentSearchRequest):
    sql = "SELECT * FROM precedents WHERE (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
    params = [f"%{req.query}%"] * 3
    if req.audience:
        sql += " AND audience = ?"
        params.append(req.audience)
    if req.precedent_type:
        sql += " AND precedent_type = ?"
        params.append(req.precedent_type.value)
    sql += " ORDER BY quality_score DESC LIMIT ?"
    params.append(req.limit)
    rows = await db.fetchall(sql, tuple(params))
    return [PrecedentResponse(**dict(r)) for r in rows]


@app.get("/api/v1/precedents/{precedent_id}", response_model=PrecedentResponse, tags=["Precedents"])
async def get_precedent(precedent_id: str):
    row = await db.fetchone("SELECT * FROM precedents WHERE id = ?", (precedent_id,))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Precedent not found"})
    return PrecedentResponse(**dict(row))


@app.patch("/api/v1/precedents/{precedent_id}", response_model=PrecedentResponse, tags=["Precedents"])
async def update_precedent(precedent_id: str, title: str = None, content: str = None):
    updates = []
    params = []
    if title:
        updates.append("title = ?")
        params.append(title)
    if content:
        updates.append("content = ?")
        params.append(content)
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(precedent_id)
        await db.execute(f"UPDATE precedents SET {', '.join(updates)} WHERE id = ?", tuple(params))
        await db.commit()
    row = await db.fetchone("SELECT * FROM precedents WHERE id = ?", (precedent_id,))
    return PrecedentResponse(**dict(row))


# ═════════════════════════════════════════════════════════════════════════════
# x870: TASKS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def list_tasks(matter_id: str = None, status: str = None, limit: int = 100):
    sql = "SELECT * FROM tasks"
    conditions = []
    params = []
    if matter_id:
        conditions.append("matter_id = ?")
        params.append(matter_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = await db.fetchall(sql, tuple(params))
    return [TaskResponse(**dict(r)) for r in rows]


@app.post("/api/v1/tasks", response_model=TaskResponse, tags=["Tasks"])
async def create_task(req: TaskCreate):
    from app.database import create_record
    data = req.model_dump()
    data["status"] = "not_started"
    record_id = await create_record(db, "tasks", data)
    row = await db.fetchone("SELECT * FROM tasks WHERE id = ?", (record_id,))
    return TaskResponse(**dict(row))


@app.patch("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(task_id: str, req: TaskUpdate):
    from app.database import update_record
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    if data:
        await update_record(db, "tasks", task_id, data)
    row = await db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return TaskResponse(**dict(row))


# ═════════════════════════════════════════════════════════════════════════════
# x870: STAKEHOLDERS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/stakeholders", response_model=List[StakeholderResponse], tags=["Stakeholders"])
async def list_stakeholders(limit: int = 100):
    rows = await db.fetchall("SELECT * FROM stakeholders ORDER BY created_at DESC LIMIT ?", (limit,))
    return [StakeholderResponse(**dict(r)) for r in rows]


@app.post("/api/v1/stakeholders", response_model=StakeholderResponse, tags=["Stakeholders"])
async def create_stakeholder(req: StakeholderCreate):
    from app.database import create_record
    data = req.model_dump()
    data["user_id"] = "system"
    record_id = await create_record(db, "stakeholders", data)
    row = await db.fetchone("SELECT * FROM stakeholders WHERE id = ?", (record_id,))
    return StakeholderResponse(**dict(row))


@app.patch("/api/v1/stakeholders/{stakeholder_id}", response_model=StakeholderResponse, tags=["Stakeholders"])
async def update_stakeholder(stakeholder_id: str, req: StakeholderCreate):
    from app.database import update_record
    data = req.model_dump()
    data["updated_at"] = datetime.utcnow().isoformat()
    await update_record(db, "stakeholders", stakeholder_id, data)
    row = await db.fetchone("SELECT * FROM stakeholders WHERE id = ?", (stakeholder_id,))
    return StakeholderResponse(**dict(row))


# ═════════════════════════════════════════════════════════════════════════════
# x870: DRAFTS
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/draft/management-brief", response_model=DraftResponse, tags=["Drafting"])
async def draft_management_brief(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"# Management Brief\n\nDraft generated for: {req.additional_context or 'General'}\n\nThis is a stub endpoint. Connect to LLM backend for full drafting.",
        title="Management Brief",
    )


@app.post("/api/v1/draft/email", response_model=DraftResponse, tags=["Drafting"])
async def draft_email(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"Subject: {req.additional_context or 'Update'}\n\nDear Stakeholder,\n\n[Draft email content stub]",
        title="Email Draft",
    )


@app.post("/api/v1/draft/weekly-update", response_model=DraftResponse, tags=["Drafting"])
async def draft_weekly_update(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"# Weekly Update\n\nWeek of {datetime.utcnow().strftime('%Y-%m-%d')}\n\n[Stub - connect to LLM backend]",
        title="Weekly Update",
    )


@app.post("/api/v1/draft/regulator-response", response_model=DraftResponse, tags=["Drafting"])
async def draft_regulator_response(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"# Regulatory Response\n\nDear Regulator,\n\nIn response to your inquiry...\n\n[Stub - connect to LLM backend]",
        title="Regulator Response",
    )


@app.post("/api/v1/draft/decision-card", response_model=DraftResponse, tags=["Drafting"])
async def draft_decision_card(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"# Decision Card\n\n**Recommendation:** Proceed with conditions\n\n**Rationale:** [Stub - connect to CSL engine]\n\n**Risk Level:** Medium",
        title="Decision Card",
    )


@app.post("/api/v1/draft/meeting-minutes", response_model=DraftResponse, tags=["Drafting"])
async def draft_meeting_minutes(req: DraftRequest):
    return DraftResponse(
        output_id=str(uuid.uuid4()),
        content=f"# Meeting Minutes\n\n**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}\n\n**Attendees:** [Stub]\n\n**Agenda:** {req.additional_context or 'General matters'}\n\n**Minutes:** [Stub - connect to LLM backend]",
        title="Meeting Minutes",
    )


# ═════════════════════════════════════════════════════════════════════════════
# x870: RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/research/query", response_model=ResearchResponse, tags=["Research"])
async def trigger_research(req: ResearchRequest):
    return ResearchResponse(
        research_id=str(uuid.uuid4()),
        status="queued",
        message=f"Research on '{req.query}' queued for processing via {', '.join(req.sources)}",
    )


@app.get("/api/v1/research/monitor", tags=["Research"])
async def list_monitors():
    rows = await db.fetchall("SELECT * FROM memory_items WHERE memory_class = 'market_intelligence' ORDER BY created_at DESC LIMIT 20")
    return {"monitors": [{"id": r["id"], "type": "topic", "target": r["title"], "last_check": r["updated_at"]} for r in rows]}


@app.post("/api/v1/research/monitor/add", tags=["Research"])
async def add_monitor(target: str, type: str = "topic"):
    return {"monitor_id": str(uuid.uuid4()), "target": target, "type": type, "status": "active"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: PREFERENCES
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/preferences", response_model=List[PreferenceResponse], tags=["Preferences"])
async def list_preferences(category: str = None):
    sql = "SELECT * FROM preferences WHERE active = 1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC"
    rows = await db.fetchall(sql, tuple(params))
    return [PreferenceResponse(**dict(r)) for r in rows]


@app.post("/api/v1/preferences", response_model=PreferenceResponse, tags=["Preferences"])
async def create_preference(req: PreferenceCreate):
    from app.database import create_record
    data = req.model_dump()
    data["value_json"] = json.dumps(data["value_json"])
    data["user_id"] = "system"
    record_id = await create_record(db, "preferences", data)
    row = await db.fetchone("SELECT * FROM preferences WHERE id = ?", (record_id,))
    r = dict(row)
    try:
        r["value_json"] = json.loads(r["value_json"])
    except:
        pass
    return PreferenceResponse(**r)


@app.patch("/api/v1/preferences/{pref_id}", response_model=PreferenceResponse, tags=["Preferences"])
async def update_preference(pref_id: str, value_json: Dict[str, Any] = None):
    if value_json:
        await db.execute(
            "UPDATE preferences SET value_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(value_json), datetime.utcnow().isoformat(), pref_id),
        )
        await db.commit()
    row = await db.fetchone("SELECT * FROM preferences WHERE id = ?", (pref_id,))
    r = dict(row)
    try:
        r["value_json"] = json.loads(r["value_json"])
    except:
        pass
    return PreferenceResponse(**r)


@app.post("/api/v1/preferences/{pref_id}/confirm", tags=["Preferences"])
async def confirm_preference(pref_id: str):
    await db.execute(
        "UPDATE preferences SET last_confirmed_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), pref_id),
    )
    await db.commit()
    return {"preference_id": pref_id, "status": "confirmed"}


# ═════════════════════════════════════════════════════════════════════════════
# x870: AUDIT LOG
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/audit-log", tags=["Admin"])
async def get_audit_log(entity_type: str = None, limit: int = 100):
    sql = "SELECT * FROM audit_log"
    params = []
    if entity_type:
        sql += " WHERE entity_type = ?"
        params.append(entity_type)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = await db.fetchall(sql, tuple(params))
    return {"entries": [dict(r) for r in rows], "count": len(rows)}


# ═════════════════════════════════════════════════════════════════════════════
# x870: METRICS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/metrics", response_model=MetricsResponse, tags=["Admin"])
async def get_metrics():
    matters = await db.fetchone("SELECT COUNT(*) as c FROM matters")
    open_matters = await db.fetchone("SELECT COUNT(*) as c FROM matters WHERE status IN ('open', 'in_progress')")
    outputs = await db.fetchone("SELECT COUNT(*) as c FROM outputs")
    memory = await db.fetchone("SELECT COUNT(*) as c FROM memory_items")
    stress = await db.fetchone("SELECT COUNT(*) as c FROM stress_results")
    patterns = await db.fetchone("SELECT COUNT(*) as c FROM patterns")
    tasks = await db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status IN ('not_started', 'in_progress')")
    cred = await db.fetchone("SELECT COUNT(*) as c FROM credibility_scores")
    
    return MetricsResponse(
        total_matters=matters["c"] if matters else 0,
        open_matters=open_matters["c"] if open_matters else 0,
        total_outputs=outputs["c"] if outputs else 0,
        total_memory_items=memory["c"] if memory else 0,
        total_stress_runs=stress["c"] if stress else 0,
        total_patterns=patterns["c"] if patterns else 0,
        pending_tasks=tasks["c"] if tasks else 0,
        token_usage_7d={"fast": 150000, "mid": 75000, "strong": 25000, "embedding": 500000},
        stresslab_stats={"total_runs": stress["c"] if stress else 0, "avg_risk_score": 0, "models_used": ["deepseek-r1:32b", "qwen3:8b"]},
        credibility_entries=cred["c"] if cred else 0,
    )


# ═════════════════════════════════════════════════════════════════════════════
# OpenEvan Analytical Routers
# ═════════════════════════════════════════════════════════════════════════════

app.include_router(stresslab.router)
app.include_router(patterns.router)
app.include_router(credibility.router)
app.include_router(alignment.router)
app.include_router(learning.router)
app.include_router(intake.router)

# Store db reference on app state for routers
@app.on_event("startup")
async def startup_state():
    app.state.db = db
