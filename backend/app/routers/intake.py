"""
Router: Layer 1 — Intake & Structuring
Handles raw input submission, retrieval, and Ollama-powered fact extraction.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import db
from app.models import (
    FactPacket,
    IntakeSubmitRequest,
    RawInput,
)
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intake", tags=["Layer 1 — Intake & Structuring"])
ollama_service = OllamaService()


@router.post("/submit", response_model=Dict[str, Any])
async def submit_raw_input(req: IntakeSubmitRequest) -> Dict[str, Any]:
    """Submit a new raw regulatory input for processing."""
    raw = RawInput(
        input_type=req.input_type,
        source=req.source,
        content=req.content,
    )
    await db.save_raw_input(raw.model_dump())
    logger.info("Raw input submitted: %s (type=%s)", raw.id, raw.input_type)
    return raw.model_dump()


@router.get("/{id}", response_model=Dict[str, Any])
async def get_raw_input(id: str) -> Dict[str, Any]:
    """Get a raw input by ID."""
    result = await db.get_raw_input(id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Raw input {id} not found")
    return result


@router.get("", response_model=List[Dict[str, Any]])
async def list_raw_inputs() -> List[Dict[str, Any]]:
    """List all raw inputs, most recent first."""
    return await db.list_raw_inputs()


@router.post("/{id}/structure", response_model=Dict[str, Any])
async def structure_raw_input(id: str) -> Dict[str, Any]:
    """Run Ollama structuring on a raw input and save the resulting fact packet."""
    raw_dict = await db.get_raw_input(id)
    if not raw_dict:
        raise HTTPException(status_code=404, detail=f"Raw input {id} not found")
    raw = RawInput(**raw_dict)
    try:
        fact_packet: FactPacket = await ollama_service.extract_fact_packet(raw)
    except Exception as exc:
        logger.error("Fact extraction failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Fact extraction failed: {str(exc)}")
    await db.save_fact_packet(fact_packet.model_dump())
    await db.update_raw_input_status(id, "structured")
    logger.info(
        "Fact packet extracted and saved: %s for raw input %s",
        fact_packet.id,
        id,
    )
    return fact_packet.model_dump()


@router.get("/{id}/fact-packet", response_model=Dict[str, Any])
async def get_fact_packet_for_raw(id: str) -> Dict[str, Any]:
    """Get the fact packet associated with a raw input."""
    fp = await db.get_fact_packet_by_raw(id)
    if not fp:
        raise HTTPException(
            status_code=404,
            detail=f"No fact packet found for raw input {id}",
        )
    return fp
