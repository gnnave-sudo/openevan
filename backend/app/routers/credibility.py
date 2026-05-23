"""
Router: Part II — Counsel Credibility Scoring
Scores counsel, retrieves track records, and provides leaderboards.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import CredibilityScoreRequest
from app.services.credibility_model import CredibilityModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/credibility", tags=["Part II — Counsel Credibility"]
)
credibility_model = CredibilityModel()


@router.post("/score", response_model=Dict[str, Any])
async def score_counsel(req: CredibilityScoreRequest) -> Dict[str, Any]:
    """Score an external counsel on a matter."""
    try:
        score = credibility_model.score_counsel(
            counsel_name=req.counsel_name,
            matter_id=req.matter_id,
            dimension_scores=req.dimension_scores,
        )
    except Exception as exc:
        logger.error("Credibility scoring failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Scoring failed: {str(exc)}"
        )
    await db.save_credibility_score(score.model_dump())
    track = credibility_model.get_track_record(req.counsel_name)
    await db.update_counsel_track_record(track.model_dump())
    logger.info(
        "Counsel scored: %s matter=%s score=%.1f tier=%s",
        req.counsel_name,
        req.matter_id,
        score.weighted_score,
        score.risk_tier,
    )
    return score.model_dump()


@router.get("/counsel/{name}", response_model=Dict[str, Any])
async def get_counsel_track_record(name: str) -> Dict[str, Any]:
    """Get the track record for a named counsel."""
    db_record = await db.get_counsel_track_record(name)
    if db_record:
        return db_record
    track = credibility_model.get_track_record(name)
    if track.average_score == 0.0 and not track.scores_over_time:
        raise HTTPException(
            status_code=404,
            detail=f"No track record found for counsel '{name}'",
        )
    await db.update_counsel_track_record(track.model_dump())
    return track.model_dump()


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard() -> List[Dict[str, Any]]:
    """Get the counsel leaderboard ranked by average score."""
    leaderboard = credibility_model.get_leaderboard()
    if not leaderboard:
        db_records = await db.list_counsel_leaderboard()
        if db_records:
            return db_records
    return [record.model_dump() for record in leaderboard]
