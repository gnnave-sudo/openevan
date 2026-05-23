"""
Router: Layer 2 — Compliance Stress Lab
Runs 4-agent CSL simulations and manages stress test results.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import FactPacket, StressLabResult
from app.services.csl_engine import CSLEngine
from app.services.simulation_router import get_simulation_router

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/stresslab", tags=["Layer 2 — Compliance Stress Lab"]
)
csl_engine = CSLEngine()
simulation_router = get_simulation_router()


@router.post("/run/{fact_packet_id}", response_model=Dict[str, Any])
async def run_stress_test(fact_packet_id: str) -> Dict[str, Any]:
    """Run a CSL stress test on a fact packet and save the result."""
    fp_dict = await db.get_fact_packet(fact_packet_id)
    if not fp_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Fact packet {fact_packet_id} not found",
        )
    fp = FactPacket(**fp_dict)
    try:
        result: StressLabResult = csl_engine.run_stress_test(fp)
    except Exception as exc:
        logger.error("Stress test failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Stress test failed: {str(exc)}"
        )
    result.fact_packet_id = fact_packet_id
    result_data = result.model_dump()
    await db.save_stress_result(result_data)
    for scenario in result.scenarios:
        scenario.stress_result_id = result.id
        await db.save_scenario(scenario.model_dump())
    await db.update_raw_input_status(fp.raw_input_id, "stressed")
    logger.info(
        "Stress test completed: %s for fact packet %s (risk=%.1f, rec=%s)",
        result.id,
        fact_packet_id,
        result.final_risk_rating,
        result.final_recommendation,
    )
    return result_data


@router.get("/result/{id}", response_model=Dict[str, Any])
async def get_stress_result(id: str) -> Dict[str, Any]:
    """Get a stress test result by ID."""
    result = await db.get_stress_result(id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Stress result {id} not found"
        )
    return result


@router.get("", response_model=List[Dict[str, Any]])
async def list_stress_results() -> List[Dict[str, Any]]:
    """List all stress test results, most recent first."""
    return await db.list_stress_results()


@router.get("/scenarios/{result_id}", response_model=List[Dict[str, Any]])
async def get_scenarios(result_id: str) -> List[Dict[str, Any]]:
    """Get all simulation scenarios for a stress test result."""
    result = await db.get_stress_result(result_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Stress result {result_id} not found",
        )
    return await db.list_scenarios(result_id)


# ── Simulation Mode Endpoints ─────────────────────────────────────────────────


@router.get("/modes", response_model=List[Dict[str, Any]])
async def list_simulation_modes() -> List[Dict[str, Any]]:
    """List all available simulation modes with their descriptions and configurations."""
    return simulation_router.list_modes()


@router.post("/detect-mode", response_model=Dict[str, Any])
async def detect_simulation_mode(request: Dict[str, Any]) -> Dict[str, Any]:
    """Detect the best simulation mode for the given input.

    Request body:
        - title: str — Title/description of the case
        - fact_pattern: str — The fact pattern text
        - risk_focus: str (optional) — Risk focus area

    Returns the best matching mode with confidence score and all candidate scores.
    """
    title = request.get("title", "")
    fact_pattern = request.get("fact_pattern", "")
    risk_focus = request.get("risk_focus")

    if not title and not fact_pattern:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'title' or 'fact_pattern' is required",
        )

    result = simulation_router.determine_mode(title, fact_pattern, risk_focus)
    logger.info(
        "Mode detection: '%s...' -> %s (confidence=%.2f)",
        title[:40] if title else fact_pattern[:40],
        result["mode_key"],
        result["confidence"],
    )
    return result
