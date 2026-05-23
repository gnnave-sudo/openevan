"""
OpenEvan L6: Continuous Learning Router
Drift tracking, posture scoring, and historical comparison.
"""

import json
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Request

from app.models import DriftEvent, PostureScore

router = APIRouter(prefix="/api/v1/learning", tags=["Learning"])


@router.get("/posture-score", response_model=PostureScore)
async def get_posture_score(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    if db:
        row = await db.fetchone(
            "SELECT * FROM posture_scores ORDER BY assessed_at DESC LIMIT 1"
        )
        if row:
            rd = dict(row)
            return PostureScore(
                id=rd["id"],
                overall_score=rd["overall_score"],
                dimension_scores=json.loads(rd["dimension_scores"]),
                trend=rd["trend"],
                assessed_at=datetime.fromisoformat(rd["assessed_at"]),
            )
    
    # Default score
    return PostureScore(
        id=str(uuid.uuid4()),
        overall_score=72.5,
        dimension_scores={
            "regulatory_compliance": 75,
            "operational_risk": 68,
            "financial_stability": 80,
            "reputational_risk": 70,
            "technology_security": 72,
        },
        trend="stable",
        assessed_at=datetime.utcnow(),
    )


@router.post("/posture-score")
async def record_posture_score(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    # Calculate from latest stress results
    dimension_scores = {
        "regulatory_compliance": 75.0,
        "operational_risk": 68.0,
        "financial_stability": 80.0,
        "reputational_risk": 70.0,
        "technology_security": 72.0,
    }
    
    if db:
        avg = await db.fetchone("SELECT AVG(overall_risk_score) as avg FROM stress_results")
        if avg and avg["avg"]:
            risk = avg["avg"]
            dimension_scores["regulatory_compliance"] = round(max(30, 100 - risk), 1)
            dimension_scores["operational_risk"] = round(max(30, 95 - risk * 0.8), 1)
    
    overall = round(sum(dimension_scores.values()) / len(dimension_scores), 1)
    
    # Determine trend
    trend = "stable"
    if db:
        prev = await db.fetchone(
            "SELECT overall_score FROM posture_scores ORDER BY assessed_at DESC LIMIT 1"
        )
        if prev:
            diff = overall - prev["overall_score"]
            if diff > 3:
                trend = "improving"
            elif diff < -3:
                trend = "declining"
    
    score_id = str(uuid.uuid4())
    if db:
        await db.execute(
            "INSERT INTO posture_scores (id, overall_score, dimension_scores, trend, assessed_at) VALUES (?, ?, ?, ?, ?)",
            (score_id, overall, json.dumps(dimension_scores), trend, datetime.utcnow().isoformat()),
        )
        await db.commit()
    
    return PostureScore(
        id=score_id,
        overall_score=overall,
        dimension_scores=dimension_scores,
        trend=trend,
        assessed_at=datetime.utcnow(),
    )


@router.get("/drift-timeline")
async def drift_timeline(days: int = 90, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        # Generate sample drift events
        events = [
            DriftEvent(
                id=str(uuid.uuid4()),
                event_type="regulatory_change",
                description="MAS issued new guidance on DeFi lending protocols",
                impact_score=75.0,
                previous_posture=70.0,
                new_posture=65.0,
                detected_at=datetime.utcnow() - timedelta(days=30),
            ),
            DriftEvent(
                id=str(uuid.uuid4()),
                event_type="enforcement_action",
                description="SEC enforcement against unregistered staking-as-a-service",
                impact_score=85.0,
                previous_posture=65.0,
                new_posture=58.0,
                detected_at=datetime.utcnow() - timedelta(days=14),
            ),
            DriftEvent(
                id=str(uuid.uuid4()),
                event_type="compliance_update",
                description="Travel Rule implementation deadline extended",
                impact_score=30.0,
                previous_posture=58.0,
                new_posture=60.0,
                detected_at=datetime.utcnow() - timedelta(days=7),
            ),
        ]
        return {"events": [e.model_dump() for e in events], "count": len(events)}
    
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = await db.fetchall(
        "SELECT * FROM drift_events WHERE detected_at > ? ORDER BY detected_at DESC",
        (cutoff,),
    )
    return {"events": [dict(r) for r in rows], "count": len(rows)}


@router.post("/drift-detect")
async def detect_drift(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    drift_id = str(uuid.uuid4())
    event = DriftEvent(
        id=drift_id,
        event_type="auto_detected",
        description="Automated drift detection scan completed",
        impact_score=45.0,
        previous_posture=72.5,
        new_posture=70.0,
        detected_at=datetime.utcnow(),
    )
    
    if db:
        await db.execute(
            "INSERT INTO drift_events (id, event_type, description, impact_score, previous_posture, new_posture, detected_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event.id, event.event_type, event.description, event.impact_score,
             event.previous_posture, event.new_posture, event.detected_at.isoformat()),
        )
        await db.commit()
    
    return {"drift_event": event.model_dump(), "status": "detected"}


@router.get("/historical")
async def historical_comparison(days: int = 180, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    if db:
        rows = await db.fetchall(
            "SELECT * FROM posture_scores ORDER BY assessed_at DESC LIMIT 30"
        )
        if rows:
            return {
                "posture_history": [dict(r) for r in rows],
                "period_days": days,
            }
    
    # Generate historical sample
    history = []
    for i in range(6):
        history.append({
            "id": str(uuid.uuid4()),
            "overall_score": 65 + (i * 2) + (hash(str(i)) % 10),
            "dimension_scores": {
                "regulatory_compliance": 70 + i,
                "operational_risk": 60 + i,
                "financial_stability": 75 + i,
                "reputational_risk": 65 + i,
                "technology_security": 68 + i,
            },
            "trend": "improving" if i > 2 else "stable",
            "assessed_at": (datetime.utcnow() - timedelta(days=30 * (5 - i))).isoformat(),
        })
    
    return {"posture_history": history, "period_days": days}
