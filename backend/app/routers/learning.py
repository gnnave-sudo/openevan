"""
Router: Layer 6 — Continuous Learning
Drift detection, review scheduling, and historical comparison.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import DriftDetection
from app.services.learning_loop import LearningLoop

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/learning", tags=["Layer 6 — Continuous Learning"]
)
learning_loop = LearningLoop()


@router.post("/detect-drift/{product_id}", response_model=Dict[str, Any])
async def detect_drift(
    product_id: str, previous_score: float = None, current_score: float = 50.0
) -> Dict[str, Any]:
    """Detect risk drift for a product."""
    try:
        drift: DriftDetection = learning_loop.detect_drift(
            product_id=product_id,
            new_score=current_score,
            previous_score=previous_score,
        )
    except Exception as exc:
        logger.error("Drift detection failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Drift detection failed: {str(exc)}"
        )
    await db.save_drift_detection(drift.model_dump())
    logger.info(
        "Drift detected: product=%s drift=%s magnitude=%.1f",
        product_id,
        drift.drift_detected,
        drift.drift_magnitude,
    )
    return drift.model_dump()


@router.post("/schedule-review/{product_id}", response_model=Dict[str, Any])
async def schedule_review(product_id: str) -> Dict[str, Any]:
    """Schedule the next review cycle for a product."""
    try:
        schedule = learning_loop.schedule_review(product_id)
    except Exception as exc:
        logger.error("Review scheduling failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Review scheduling failed: {str(exc)}"
        )
    logger.info("Review scheduled for product %s", product_id)
    return schedule


@router.get("/history/{product_id}", response_model=Dict[str, Any])
async def get_history(product_id: str) -> Dict[str, Any]:
    """Get historical risk comparison for a product."""
    try:
        history = learning_loop.compare_history(product_id)
    except Exception as exc:
        logger.error("History comparison failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"History comparison failed: {str(exc)}"
        )
    db_drifts = await db.list_drift_detections(product_id)
    history["persisted_drifts"] = db_drifts
    return history
