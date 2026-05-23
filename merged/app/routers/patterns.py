"""
OpenEvan L3: Pattern Extraction Router (Hermes Engine)
Extracts recurring obligations, risk drivers, compliance weaknesses, early warning signals.
"""

import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models import PatternExtract, RiskIndexQuery

router = APIRouter(prefix="/api/v1/patterns", tags=["Patterns"])


def _extract_from_stress_result(stress_data: dict) -> dict:
    """Simulate Hermes pattern extraction from stress result data."""
    obligations = []
    drivers = []
    weaknesses = []
    signals = []
    
    scenarios = json.loads(stress_data.get("scenarios", "[]"))
    for s in scenarios:
        ctx = s.get("context", "")
        if "licensing" in ctx.lower() or "authorisation" in ctx.lower():
            obligations.append({"obligation": "Obtain proper licensing before launch", "frequency": "recurring", "severity": "high"})
        if "aml" in ctx.lower() or "cft" in ctx.lower():
            obligations.append({"obligation": "Implement AML/CFT transaction monitoring", "frequency": "recurring", "severity": "critical"})
        if "consumer" in ctx.lower() or "retail" in ctx.lower():
            obligations.append({"obligation": "Retail investor protection measures", "frequency": "recurring", "severity": "high"})
        
        if "cross-border" in ctx.lower() or "jurisdiction" in ctx.lower():
            drivers.append("Cross-border regulatory complexity")
        if "insolvency" in ctx.lower() or "custody" in ctx.lower():
            drivers.append("Custody and asset protection gaps")
        if "smart contract" in ctx.lower() or "defi" in ctx.lower():
            drivers.append("DeFi protocol security risks")
        
        weaknesses.append("Incomplete third-party due diligence")
        weaknesses.append("Insufficient insurance coverage")
        
        signals.append("Regulatory consultation in similar jurisdiction")
        signals.append("Competitor enforcement action")
    
    return {
        "obligations": obligations[:5],
        "drivers": list(set(drivers))[:5],
        "weaknesses": list(set(weaknesses))[:5],
        "signals": list(set(signals))[:5],
    }


@router.post("/extract", response_model=PatternExtract)
async def extract_patterns(request: Request, stress_result_id: str = None, matter_id: str = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    # If stress_result_id provided, extract from it
    stress_data = None
    if stress_result_id and db:
        stress_data = await db.fetchone("SELECT * FROM stress_results WHERE id = ?", (stress_result_id,))
    elif matter_id and db:
        stress_data = await db.fetchone(
            "SELECT * FROM stress_results WHERE matter_id = ? ORDER BY generated_at DESC LIMIT 1",
            (matter_id,),
        )
    
    extracted = _extract_from_stress_result(dict(stress_data) if stress_data else {})
    
    # Build risk index
    risk_index = {
        "regulatory_compliance": 75.0 + (hash(str(stress_result_id)) % 20 - 10),
        "operational_risk": 60.0 + (hash(str(matter_id)) % 20 - 10),
        "financial_stability": 55.0 + (hash(str(stress_result_id or matter_id)) % 30 - 15),
        "reputational_risk": 45.0 + (hash(str(matter_id)) % 20 - 10),
        "technology_security": 65.0 + (hash(str(stress_result_id)) % 20 - 10),
    }
    
    pattern_id = str(uuid.uuid4())
    result = PatternExtract(
        id=pattern_id,
        stress_result_id=stress_result_id,
        matter_id=matter_id,
        recurring_obligations=extracted["obligations"],
        risk_drivers=extracted["drivers"],
        compliance_weaknesses=extracted["weaknesses"],
        early_warning_signals=extracted["signals"],
        risk_index=risk_index,
        extracted_at=datetime.utcnow(),
    )
    
    if db:
        await db.execute(
            "INSERT INTO patterns (id, stress_result_id, matter_id, recurring_obligations, risk_drivers, compliance_weaknesses, early_warning_signals, risk_index, extracted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (result.id, result.stress_result_id, result.matter_id,
             json.dumps(result.recurring_obligations),
             json.dumps(result.risk_drivers),
             json.dumps(result.compliance_weaknesses),
             json.dumps(result.early_warning_signals),
             json.dumps(result.risk_index),
             result.extracted_at.isoformat()),
        )
        await db.commit()
    
    return result


@router.get("/library", response_model=List[PatternExtract])
async def pattern_library(matter_id: str = None, limit: int = 50, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return []
    
    sql = "SELECT * FROM patterns"
    params = []
    if matter_id:
        sql += " WHERE matter_id = ?"
        params.append(matter_id)
    sql += " ORDER BY extracted_at DESC LIMIT ?"
    params.append(limit)
    
    rows = await db.fetchall(sql, tuple(params))
    results = []
    for r in rows:
        rd = dict(r)
        results.append(PatternExtract(
            id=rd["id"],
            stress_result_id=rd["stress_result_id"],
            matter_id=rd["matter_id"],
            recurring_obligations=json.loads(rd["recurring_obligations"]),
            risk_drivers=json.loads(rd["risk_drivers"]),
            compliance_weaknesses=json.loads(rd["compliance_weaknesses"]),
            early_warning_signals=json.loads(rd["early_warning_signals"]),
            risk_index=json.loads(rd["risk_index"]),
            extracted_at=datetime.fromisoformat(rd["extracted_at"]),
        ))
    return results


@router.post("/risk-index")
async def risk_index_query(query: RiskIndexQuery, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"indices": [], "message": "Database not available"}
    
    sql = "SELECT * FROM patterns"
    rows = await db.fetchall(sql)
    
    indices = []
    for r in rows:
        rd = dict(r)
        ri = json.loads(rd.get("risk_index", "{}"))
        if ri:
            indices.append({
                "pattern_id": rd["id"],
                "matter_id": rd["matter_id"],
                "risk_index": ri,
                "extracted_at": rd["extracted_at"],
            })
    
    # Aggregate by dimension
    dimension_totals = {}
    dimension_counts = {}
    for idx in indices:
        for dim, val in idx["risk_index"].items():
            dimension_totals[dim] = dimension_totals.get(dim, 0) + val
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
    
    dimension_avg = {dim: round(dimension_totals[dim] / dimension_counts[dim], 1) 
                     for dim in dimension_totals}
    
    return {
        "indices": indices[:query.limit],
        "dimension_averages": dimension_avg,
        "total_patterns": len(indices),
        "time_range_days": query.time_range_days,
    }


@router.get("/obligations")
async def recurring_obligations(matter_id: str = None, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"obligations": []}
    
    sql = "SELECT recurring_obligations FROM patterns"
    if matter_id:
        sql += " WHERE matter_id = ?"
        rows = await db.fetchall(sql, (matter_id,))
    else:
        rows = await db.fetchall(sql)
    
    all_obligations = []
    for r in rows:
        obs = json.loads(r["recurring_obligations"])
        all_obligations.extend(obs)
    
    # Deduplicate by obligation text
    seen = set()
    unique = []
    for o in all_obligations:
        text = o.get("obligation", "")
        if text and text not in seen:
            seen.add(text)
            unique.append(o)
    
    return {"obligations": unique, "count": len(unique)}


@router.get("/{pattern_id}", response_model=PatternExtract)
async def get_pattern(pattern_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")
    
    row = await db.fetchone("SELECT * FROM patterns WHERE id = ?", (pattern_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    rd = dict(row)
    return PatternExtract(
        id=rd["id"],
        stress_result_id=rd["stress_result_id"],
        matter_id=rd["matter_id"],
        recurring_obligations=json.loads(rd["recurring_obligations"]),
        risk_drivers=json.loads(rd["risk_drivers"]),
        compliance_weaknesses=json.loads(rd["compliance_weaknesses"]),
        early_warning_signals=json.loads(rd["early_warning_signals"]),
        risk_index=json.loads(rd["risk_index"]),
        extracted_at=datetime.fromisoformat(rd["extracted_at"]),
    )
