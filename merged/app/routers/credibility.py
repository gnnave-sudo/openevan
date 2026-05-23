"""
OpenEvan CS: Counsel Credibility Scoring Router
6-dimension scoring with auto-scale detection and tier classification.
"""

import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models import (
    CounselLeaderboardEntry,
    CounselTier,
    CredibilityScoreRequest,
    CredibilityScoreResponse,
)

router = APIRouter(prefix="/api/v1/credibility", tags=["Credibility"])


def _detect_scale(raw: float) -> float:
    """Auto-detect 0-1 vs 0-100 scale and normalize to 0-100."""
    if 0.0 <= raw <= 1.0:
        return raw * 100
    return min(100, max(0, raw))


def _calculate_tier(overall: float) -> CounselTier:
    if overall >= 85:
        return CounselTier.ELITE
    elif overall >= 70:
        return CounselTier.ESTABLISHED
    elif overall >= 50:
        return CounselTier.DEVELOPING
    return CounselTier.MONITOR


@router.post("/score", response_model=CredibilityScoreResponse)
async def score_counsel(req: CredibilityScoreRequest, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    dims = {
        "historical_accuracy": _detect_scale(req.historical_accuracy),
        "jurisdictional_depth": _detect_scale(req.jurisdictional_depth),
        "timeliness": _detect_scale(req.timeliness),
        "communication_clarity": _detect_scale(req.communication_clarity),
        "strategic_value": _detect_scale(req.strategic_value),
        "independence": _detect_scale(req.independence),
    }
    
    weights = {
        "historical_accuracy": 0.25,
        "jurisdictional_depth": 0.20,
        "timeliness": 0.15,
        "communication_clarity": 0.15,
        "strategic_value": 0.15,
        "independence": 0.10,
    }
    
    overall = round(sum(dims[k] * weights[k] for k in dims), 1)
    tier = _calculate_tier(overall)
    
    score_id = str(uuid.uuid4())
    track = {
        "total_scores": 1,
        "avg_overall": overall,
        "last_matter": req.matter_id,
        "strongest_dim": max(dims, key=dims.get),
        "weakest_dim": min(dims, key=dims.get),
    }
    
    result = CredibilityScoreResponse(
        id=score_id,
        counsel_name=req.counsel_name,
        dimensions=dims,
        overall_score=overall,
        tier=tier,
        track_record=track,
        scored_at=datetime.utcnow(),
    )
    
    if db:
        await db.execute(
            "INSERT INTO credibility_scores (id, counsel_name, dimensions, overall_score, tier, track_record, matter_id, scored_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (result.id, result.counsel_name, json.dumps(result.dimensions),
             result.overall_score, result.tier.value,
             json.dumps(result.track_record), req.matter_id,
             result.scored_at.isoformat()),
        )
        await db.commit()
    
    return result


@router.get("/leaderboard", response_model=List[CounselLeaderboardEntry])
async def leaderboard(tier: CounselTier = None, limit: int = 50, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return []
    
    sql = "SELECT * FROM credibility_scores"
    params = []
    if tier:
        sql += " WHERE tier = ?"
        params.append(tier.value)
    sql += " ORDER BY overall_score DESC LIMIT ?"
    params.append(limit)
    
    rows = await db.fetchall(sql, tuple(params))
    entries = []
    for rank, r in enumerate(rows, 1):
        rd = dict(r)
        entries.append(CounselLeaderboardEntry(
            rank=rank,
            counsel_name=rd["counsel_name"],
            overall_score=rd["overall_score"],
            tier=CounselTier(rd["tier"]),
            matter_count=json.loads(rd.get("track_record", "{}")).get("total_scores", 1),
            last_scored=datetime.fromisoformat(rd["scored_at"]),
        ))
    return entries


@router.get("/counsel/{counsel_name}")
async def get_counsel_history(counsel_name: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"scores": []}
    
    rows = await db.fetchall(
        "SELECT * FROM credibility_scores WHERE counsel_name = ? ORDER BY scored_at DESC",
        (counsel_name,),
    )
    
    scores = []
    trend = []
    for r in rows:
        rd = dict(r)
        dims = json.loads(rd["dimensions"])
        scores.append({
            "id": rd["id"],
            "overall": rd["overall_score"],
            "tier": rd["tier"],
            "dimensions": dims,
            "matter_id": rd["matter_id"],
            "scored_at": rd["scored_at"],
        })
        trend.append(rd["overall_score"])
    
    avg = round(sum(trend) / len(trend), 1) if trend else 0
    
    return {
        "counsel_name": counsel_name,
        "score_count": len(scores),
        "average_score": avg,
        "current_tier": scores[0]["tier"] if scores else "Monitor",
        "scores": scores,
        "trend": trend,
    }


@router.get("/stats")
async def credibility_stats(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"total_scored": 0, "tier_breakdown": {}}
    
    total = await db.fetchone("SELECT COUNT(*) as c FROM credibility_scores")
    tier_breakdown = await db.fetchall(
        "SELECT tier, COUNT(*) as c, AVG(overall_score) as avg FROM credibility_scores GROUP BY tier"
    )
    
    return {
        "total_scored": total["c"] if total else 0,
        "tier_breakdown": {
            r["tier"]: {"count": r["c"], "avg_score": round(r["avg"], 1)} 
            for r in tier_breakdown
        },
    }


@router.delete("/{score_id}")
async def delete_score(score_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if db:
        await db.execute("DELETE FROM credibility_scores WHERE id = ?", (score_id,))
        await db.commit()
    return {"score_id": score_id, "status": "deleted"}
