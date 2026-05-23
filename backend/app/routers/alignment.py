"""
Router: Layer 4 — Counsel Alignment
Submits counsel memos and analyzes alignment against CSL results.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import (
    AlignmentResult,
    CounselMemoInput,
    CounselMemoSubmitRequest,
    FactPacket,
    StressLabResult,
)
from app.services.counsel_alignment import CounselAlignmentEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/alignment", tags=["Layer 4 — Counsel Alignment"]
)
alignment_engine = CounselAlignmentEngine()


@router.post("/submit-memo", response_model=Dict[str, Any])
async def submit_counsel_memo(req: CounselMemoSubmitRequest) -> Dict[str, Any]:
    """Submit an external counsel memo for analysis."""
    memo = CounselMemoInput(
        counsel_name=req.counsel_name,
        memo_content=req.memo_content,
        related_fact_packet_id=req.related_fact_packet_id,
    )
    await db.save_counsel_memo(memo.model_dump())
    logger.info("Counsel memo submitted: %s by %s", memo.id, memo.counsel_name)
    return memo.model_dump()


@router.post("/analyze/{memo_id}", response_model=Dict[str, Any])
async def analyze_counsel_memo(memo_id: str) -> Dict[str, Any]:
    """Run alignment analysis on a counsel memo."""
    memo_dict = await db.get_counsel_memo(memo_id)
    if not memo_dict:
        raise HTTPException(
            status_code=404, detail=f"Counsel memo {memo_id} not found"
        )
    memo = CounselMemoInput(**memo_dict)
    fact_packet: Optional[FactPacket] = None
    stress_result: Optional[StressLabResult] = None
    if memo.related_fact_packet_id:
        fp_dict = await db.get_fact_packet(memo.related_fact_packet_id)
        if fp_dict:
            fact_packet = FactPacket(**fp_dict)
            stress_results = await db.list_stress_results()
            for sr in stress_results:
                if sr["fact_packet_id"] == memo.related_fact_packet_id:
                    stress_result = StressLabResult(**sr)
                    break
    try:
        result: AlignmentResult = await alignment_engine.analyze_alignment(
            memo, fact_packet, stress_result
        )
    except Exception as exc:
        logger.error("Alignment analysis failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Alignment analysis failed: {str(exc)}"
        )
    await db.save_alignment_result(result.model_dump())
    logger.info(
        "Alignment analyzed: %s for memo %s (score=%.1f)",
        result.id,
        memo_id,
        result.alignment_score,
    )
    return result.model_dump()


@router.get("/result/{id}", response_model=Dict[str, Any])
async def get_alignment_result(id: str) -> Dict[str, Any]:
    """Get an alignment result by ID."""
    result = await db.get_alignment_result(id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Alignment result {id} not found"
        )
    return result


@router.get("/memo/{memo_id}/result", response_model=Dict[str, Any])
async def get_alignment_by_memo(memo_id: str) -> Dict[str, Any]:
    """Get alignment result for a specific counsel memo."""
    result = await db.get_alignment_by_memo(memo_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No alignment result found for memo {memo_id}",
        )
    return result
