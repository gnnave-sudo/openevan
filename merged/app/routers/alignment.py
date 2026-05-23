"""
OpenEvan L4: Counsel Alignment Router
Compares external counsel memos against internally derived positions.
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.models import AlignmentResult, CounselMemoSubmit

router = APIRouter(prefix="/api/v1/alignment", tags=["Alignment"])

DIMENSIONS = [
    ("legal_interpretation", 0.25),
    ("risk_assessment", 0.25),
    ("recommended_action", 0.20),
    ("timeline", 0.15),
    ("jurisdictional_scope", 0.15),
]


def _analyze_alignment(memo: str, context: str = None) -> dict:
    """Simulate alignment analysis between counsel memo and internal position."""
    # In production, this would compare against the matter's working_position
    h = hash(memo + (context or ""))
    
    dim_scores = {}
    for dim, weight in DIMENSIONS:
        base = 55 + (h % 30)
        if "conservative" in memo.lower():
            base -= 5
        if "aggressive" in memo.lower():
            base += 10
        dim_scores[dim] = round(min(95, max(20, base + (hash(dim) % 10 - 5))), 1)
    
    overall = round(sum(dim_scores[d] * w for d, w in DIMENSIONS), 1)
    
    gaps = []
    if dim_scores["legal_interpretation"] < 60:
        gaps.append("Counsel's legal interpretation diverges significantly from internal position")
    if dim_scores["risk_assessment"] < 60:
        gaps.append("Risk tolerance mismatch: counsel sees higher/lower risk than internal assessment")
    if dim_scores["recommended_action"] < 60:
        gaps.append("Recommended actions are not aligned with business strategy")
    if dim_scores["timeline"] < 60:
        gaps.append("Timeline expectations differ materially")
    if not gaps:
        gaps.append("Minor differences in emphasis; fundamentally aligned")
    
    recs = [
        "Schedule working session to reconcile legal interpretation differences" if dim_scores["legal_interpretation"] < 70 else "Legal interpretation well-aligned",
        "Joint risk workshop recommended" if dim_scores["risk_assessment"] < 70 else "Risk assessment aligned",
        "Escalate to GC if action gap persists" if dim_scores["recommended_action"] < 50 else "Actions are compatible",
    ]
    
    return {
        "dimensions": [{"dimension": d, "alignment_score": s, "gap_description": None} for d, s in dim_scores.items()],
        "overall": overall,
        "gaps": gaps,
        "recommendations": [r for r in recs if not r.endswith("aligned") or dim_scores.get(r.split()[0].lower().replace('\"', ''), 100) >= 70],
    }


@router.post("/submit-memo", response_model=AlignmentResult)
async def submit_memo(req: CounselMemoSubmit, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    analysis = _analyze_alignment(req.memo_content, req.jurisdiction)
    
    result_id = str(uuid.uuid4())
    result = AlignmentResult(
        id=result_id,
        matter_id=req.matter_id,
        counsel_name=req.counsel_name,
        overall_alignment=analysis["overall"],
        dimensions=analysis["dimensions"],
        key_gaps=analysis["gaps"],
        recommendations=analysis["recommendations"],
        analyzed_at=datetime.utcnow(),
    )
    
    if db:
        await db.execute(
            "INSERT INTO alignment_results (id, matter_id, counsel_name, overall_alignment, dimensions, key_gaps, recommendations, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (result.id, result.matter_id, result.counsel_name, result.overall_alignment,
             json.dumps(result.dimensions), json.dumps(result.key_gaps),
             json.dumps(result.recommendations), result.analyzed_at.isoformat()),
        )
        await db.commit()
    
    return result


@router.get("/result/{result_id}")
async def get_alignment(result_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")
    
    row = await db.fetchone("SELECT * FROM alignment_results WHERE id = ?", (result_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Alignment result not found")
    
    rd = dict(row)
    return AlignmentResult(
        id=rd["id"],
        matter_id=rd["matter_id"],
        counsel_name=rd["counsel_name"],
        overall_alignment=rd["overall_alignment"],
        dimensions=json.loads(rd["dimensions"]),
        key_gaps=json.loads(rd["key_gaps"]),
        recommendations=json.loads(rd["recommendations"]),
        analyzed_at=datetime.fromisoformat(rd["analyzed_at"]),
    )


@router.get("/matter/{matter_id}")
async def alignments_for_matter(matter_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"alignments": []}
    
    rows = await db.fetchall(
        "SELECT * FROM alignment_results WHERE matter_id = ? ORDER BY analyzed_at DESC",
        (matter_id,),
    )
    return {"alignments": [dict(r) for r in rows], "count": len(rows)}


@router.get("/stats")
async def alignment_stats(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"total_analyzed": 0, "avg_alignment": 0}
    
    total = await db.fetchone("SELECT COUNT(*) as c FROM alignment_results")
    avg = await db.fetchone("SELECT AVG(overall_alignment) as avg FROM alignment_results")
    
    return {
        "total_analyzed": total["c"] if total else 0,
        "avg_alignment": round(avg["avg"] if avg and avg["avg"] else 0, 1),
    }
