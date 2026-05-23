"""
Router: Layer 5 — Management Output
Generates decision memos, risk heatmaps, escalation lists, and control priorities.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import DecisionMemo, EscalationItem, StressLabResult
from app.services.output_generator import OutputGenerator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/outputs", tags=["Layer 5 — Management Output"]
)
output_generator = OutputGenerator()


@router.post("/generate-memo/{stress_result_id}", response_model=Dict[str, Any])
async def generate_decision_memo(stress_result_id: str) -> Dict[str, Any]:
    """Generate a decision memo from a stress test result."""
    sr_dict = await db.get_stress_result(stress_result_id)
    if not sr_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Stress result {stress_result_id} not found",
        )
    stress_result = StressLabResult(**sr_dict)
    try:
        memo: DecisionMemo = output_generator.generate_decision_memo(
            stress_result
        )
    except Exception as exc:
        logger.error("Decision memo generation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Decision memo generation failed: {str(exc)}",
        )
    await db.save_decision_memo(memo.model_dump())
    logger.info(
        "Decision memo generated: %s for stress result %s",
        memo.id,
        stress_result_id,
    )
    return memo.model_dump()


@router.get("/heatmap", response_model=List[Dict[str, Any]])
async def get_risk_heatmap() -> List[Dict[str, Any]]:
    """Get risk heatmap data across all stress test results."""
    results = await db.list_stress_results()
    stress_results = [StressLabResult(**r) for r in results]
    if not stress_results:
        return []
    return output_generator.generate_risk_heatmap(stress_results)


@router.get("/escalations", response_model=List[Dict[str, Any]])
async def get_escalations() -> List[Dict[str, Any]]:
    """Get all escalation items."""
    results = await db.list_stress_results()
    stress_results = [StressLabResult(**r) for r in results]
    if not stress_results:
        db_escalations = await db.list_escalation_items()
        return db_escalations
    escalations = output_generator.generate_escalation_list(stress_results)
    for esc in escalations:
        await db.save_escalation_item(esc.model_dump())
    return [esc.model_dump() for esc in escalations]


@router.get("/control-priorities", response_model=List[Dict[str, Any]])
async def get_control_priorities() -> List[Dict[str, Any]]:
    """Get prioritized control investments."""
    results = await db.list_stress_results()
    stress_results = [StressLabResult(**r) for r in results]
    if not stress_results:
        db_controls = await db.list_control_investments()
        return db_controls
    controls = output_generator.generate_control_priorities(stress_results)
    for ctrl in controls:
        await db.save_control_investment(ctrl.model_dump())
    return [ctrl.model_dump() for ctrl in controls]
