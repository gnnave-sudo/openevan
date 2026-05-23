"""
Router: Layer 3 — Hermes Pattern Intelligence
Extracts patterns from stress results and manages risk indices.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import PatternExtract, RiskIndices, StressLabResult
from app.services.hermes_engine import HermesEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/patterns", tags=["Layer 3 — Pattern Intelligence"]
)
hermes_engine = HermesEngine()


@router.post("/extract/{stress_result_id}", response_model=Dict[str, Any])
async def extract_patterns(stress_result_id: str) -> Dict[str, Any]:
    """Run Hermes pattern extraction on a stress test result."""
    sr_dict = await db.get_stress_result(stress_result_id)
    if not sr_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Stress result {stress_result_id} not found",
        )
    stress_result = StressLabResult(**sr_dict)
    try:
        pattern: PatternExtract = hermes_engine.extract_patterns(stress_result)
    except Exception as exc:
        logger.error("Pattern extraction failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Pattern extraction failed: {str(exc)}"
        )
    indices = hermes_engine.update_risk_indices(pattern, stress_result)
    await db.save_pattern_extract(pattern.model_dump())
    await db.update_risk_indices(indices.model_dump())
    logger.info(
        "Pattern extracted: %s from stress result %s",
        pattern.id,
        stress_result_id,
    )
    return pattern.model_dump()


@router.get("/indices", response_model=Dict[str, Any])
async def get_risk_indices() -> Dict[str, Any]:
    """Get all current risk indices."""
    indices = await db.get_risk_indices()
    return indices
