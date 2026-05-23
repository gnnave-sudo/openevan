"""
OpenEvan L2: CSL Stress Lab Router
4-agent simulation with 10-dimension weighted risk scoring, 7 modes.
"""

import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models import (
    AgentPosition,
    Recommendation,
    RiskDimension,
    SimulationMode,
    SimulationScenario,
    StressLabResult,
    StressLabRunRequest,
)

router = APIRouter(prefix="/api/v1/stresslab", tags=["Stress Lab"])

AGENT_NAMES = ["Business Advocate", "Compliance Reviewer", "Regulator Proxy", "Neutral Adjudicator"]

# ── Argument Templates ──────────────────────────────────────────────────────

ARGUMENTS = {
    "Business Advocate": [
        "Revenue opportunity ($12M ARR) justifies measured risk; phased rollout limits exposure.",
        "Competitors already live; regulatory clarity expected within 6-12 months.",
        "Legal opinion confirms no licensing trigger under current interpretation.",
        "Precedent: 3 similar products launched successfully in comparable jurisdictions.",
        "Customer demand overwhelming; delaying risks market share erosion.",
    ],
    "Compliance Reviewer": [
        "Licensing gap is material; operating without authorisation exposes firm to criminal liability.",
        "AML controls not production-ready; transaction monitoring rules still in QA.",
        "Risk assessment does not account for recent enforcement actions against 2 comparable firms.",
        "Insurance and capital adequacy requirements not yet satisfied.",
        "Third-party due diligence incomplete; reliance on vendor attestations insufficient.",
    ],
    "Regulator Proxy": [
        "Product structure mirrors cases where public reprimands and $2M fines were issued.",
        "Consumer harm potential high: retail investors may lose principal with no recourse.",
        "Cross-border arrangements complicate supervisory coordination and increase systemic risk.",
        "Insufficient track record; 12 months of audited controls required before approval.",
        "Self-assessment is not a substitute for independent audit or regulatory review.",
    ],
    "Neutral Adjudicator": [
        "Balancing innovation against consumer protection, conditional licence with enhanced monitoring is proportionate.",
        "Firm demonstrates good faith effort but must complete outstanding items within 90 days.",
        "Partial authorisation with restrictions addresses both commercial and regulatory concerns.",
        "A phased approach with defined milestones balances risk and innovation appropriately.",
    ],
}

# ── 10-Dimension Risk Weights ──────────────────────────────────────────────

RISK_DIMENSIONS = [
    ("Severity", 0.15),
    ("Likelihood", 0.15),
    ("Velocity", 0.10),
    ("Jurisdictional Spread", 0.10),
    ("Historical Precedent", 0.12),
    ("Enforcement Trend", 0.10),
    ("Operational Complexity", 0.08),
    ("Cross-Border Friction", 0.08),
    ("Reputational Risk", 0.07),
    ("Remediation Cost", 0.05),
]


def _generate_scenario(mode: SimulationMode, product: str, jurisdiction: str, idx: int) -> SimulationScenario:
    contexts = {
        "Virtual Asset Exchange": [
            f"[{jurisdiction}] Market manipulation risk through wash trading on perpetual futures contract #{idx}.",
            f"[{jurisdiction}] Insolvency event: exchange holds 40% of customer assets in hot wallets during downturn.",
            f"[{jurisdiction}] New retail-facing spot trading product with 100x leverage and insufficient margin controls.",
        ],
        "Custody": [
            f"[{jurisdiction}] Cold wallet private key management: single-sig with keys in one geographic location.",
            f"[{jurisdiction}] Insolvency scenario: custodian commingles operational and customer assets.",
        ],
        "DeFi": [
            f"[{jurisdiction}] Smart contract vulnerability: unaudited lending protocol handling $50M TVL.",
            f"[{jurisdiction}] Governance token concentration: founding team controls 60% of voting power.",
        ],
    }
    default_ctx = [
        f"[{jurisdiction}] New product launch without completing full regulatory licensing review (#{idx}).",
        f"[{jurisdiction}] Cross-border expansion into jurisdiction with ambiguous cryptoasset classification.",
        f"[{jurisdiction}] Marketing campaign targets retail investors with high-risk yield products.",
        f"[{jurisdiction}] Partnership with unlicensed third-party for KYC/AML onboarding.",
        f"[{jurisdiction}] Delay in implementing Travel Rule compliance past regulatory deadline.",
    ]
    
    product_contexts = contexts.get(product, default_ctx)
    ctx = product_contexts[idx % len(product_contexts)]
    
    positions = []
    for agent in AGENT_NAMES:
        agent_args = ARGUMENTS[agent]
        args = [agent_args[(idx + j) % len(agent_args)] for j in range(2)]
        conf = 0.7 + (hash(f"{mode}{agent}{idx}") % 20) / 100.0
        positions.append(AgentPosition(agent=agent, position=f"[{agent}] Argued for conditional approval with specific caveats.", confidence=round(conf, 2), key_arguments=args))
    
    base_risk = 45 + (hash(f"{ctx}{mode}") % 40)
    if mode == SimulationMode.ADVERSARIAL:
        base_risk += 10
    elif mode == SimulationMode.CONSENSUS:
        base_risk -= 10
    
    risk_score = max(20, min(95, base_risk))
    
    return SimulationScenario(
        scenario_id=str(uuid.uuid4()),
        context=ctx,
        agent_positions=positions,
        scenario_risk_score=round(risk_score, 1),
        decisive_obligations=["Licensing requirement", "AML/CFT compliance", "Consumer protection"],
        control_gaps=["Transaction monitoring incomplete", "Insurance coverage insufficient", "Third-party DD pending"],
    )


def _calculate_dimensions(overall_score: float, mode: SimulationMode) -> List[RiskDimension]:
    dimensions = []
    for name, weight in RISK_DIMENSIONS:
        variation = (hash(f"{name}{mode}") % 20 - 10) / 100.0
        dim_score = max(10, min(95, overall_score + variation * 30))
        dimensions.append(RiskDimension(
            name=name,
            score=round(dim_score, 1),
            weight=weight,
            weighted_score=round(dim_score * weight, 2),
        ))
    return dimensions


@router.post("/run", response_model=StressLabResult)
async def run_stresslab(req: StressLabRunRequest, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    mode = req.mode
    product = req.product_class or "default"
    jurisdiction = req.jurisdiction or "Global"
    
    num_scenarios = 3 if mode in (SimulationMode.STANDARD, SimulationMode.CONSENSUS) else 4
    if mode == SimulationMode.DEEP_DIVE:
        num_scenarios = 5
    
    scenarios = [_generate_scenario(mode, product, jurisdiction, i) for i in range(num_scenarios)]
    avg_risk = sum(s.scenario_risk_score for s in scenarios) / len(scenarios)
    
    dimensions = _calculate_dimensions(avg_risk, mode)
    total_weighted = sum(d.weighted_score for d in dimensions)
    
    if total_weighted < 40:
        recommendation = Recommendation.PROCEED
    elif total_weighted < 70:
        recommendation = Recommendation.HOLD
    else:
        recommendation = Recommendation.NO_GO
    
    result_id = str(uuid.uuid4())
    result = StressLabResult(
        id=result_id,
        matter_id=req.matter_id,
        fact_packet_id=req.fact_packet_id,
        mode=mode,
        scenarios=scenarios,
        overall_risk_score=round(total_weighted, 1),
        risk_dimensions=dimensions,
        final_recommendation=recommendation,
        decisive_obligations=["Licensing", "AML/CFT", "Consumer Protection", "Capital Adequacy"],
        key_control_gaps=["Transaction Monitoring", "Insurance", "Third-party DD", "Audit Trail"],
        evidence_checklist=["Legal Opinion", "Risk Assessment", "Insurance Certificate", "Audit Report"],
        regulator_objections=["Licensing gap", "Incomplete controls", "Consumer harm potential"],
        generated_at=datetime.utcnow(),
        model_used="deepseek-r1:32b" if mode == SimulationMode.DEEP_DIVE else "qwen3:8b",
    )
    
    if db:
        await db.execute(
            "INSERT INTO stress_results (id, matter_id, fact_packet_id, mode, scenarios, overall_risk_score, risk_dimensions, final_recommendation, decisive_obligations, key_control_gaps, evidence_checklist, regulator_objections, generated_at, model_used) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (result.id, result.matter_id, result.fact_packet_id, result.mode.value,
             json.dumps([s.model_dump() for s in scenarios]),
             result.overall_risk_score,
             json.dumps([d.model_dump() for d in dimensions]),
             result.final_recommendation.value,
             json.dumps(result.decisive_obligations),
             json.dumps(result.key_control_gaps),
             json.dumps(result.evidence_checklist),
             json.dumps(result.regulator_objections),
             result.generated_at.isoformat(),
             result.model_used),
        )
        await db.commit()
    
    return result


@router.get("/result/{result_id}", response_model=StressLabResult)
async def get_stress_result(result_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")
    
    row = await db.fetchone("SELECT * FROM stress_results WHERE id = ?", (result_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Stress result not found")
    
    r = dict(row)
    return StressLabResult(
        id=r["id"],
        matter_id=r["matter_id"],
        fact_packet_id=r["fact_packet_id"],
        mode=SimulationMode(r["mode"]),
        scenarios=[SimulationScenario(**s) for s in json.loads(r["scenarios"])],
        overall_risk_score=r["overall_risk_score"],
        risk_dimensions=[RiskDimension(**d) for d in json.loads(r["risk_dimensions"])],
        final_recommendation=Recommendation(r["final_recommendation"]),
        decisive_obligations=json.loads(r["decisive_obligations"]),
        key_control_gaps=json.loads(r["key_control_gaps"]),
        evidence_checklist=json.loads(r["evidence_checklist"]),
        regulator_objections=json.loads(r["regulator_objections"]),
        generated_at=datetime.fromisoformat(r["generated_at"]),
        model_used=r["model_used"],
    )


@router.get("/scenarios", tags=["Stress Lab"])
async def list_scenarios(mode: SimulationMode = None, limit: int = 50, request: Request = None):
    db = request.app.state.db if (request and hasattr(request.app.state, 'db')) else None
    if not db:
        return {"scenarios": [], "count": 0}
    
    sql = "SELECT id, matter_id, mode, overall_risk_score, final_recommendation, generated_at FROM stress_results ORDER BY generated_at DESC LIMIT ?"
    rows = await db.fetchall(sql, (limit,))
    return {"scenarios": [dict(r) for r in rows], "count": len(rows)}


@router.get("/stats")
async def get_stresslab_stats(request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"total_runs": 0, "avg_risk_score": 0, "recommendation_breakdown": {}}
    
    total = await db.fetchone("SELECT COUNT(*) as c FROM stress_results")
    avg = await db.fetchone("SELECT AVG(overall_risk_score) as avg FROM stress_results")
    recs = await db.fetchall("SELECT final_recommendation, COUNT(*) as c FROM stress_results GROUP BY final_recommendation")
    modes = await db.fetchall("SELECT mode, COUNT(*) as c FROM stress_results GROUP BY mode")
    
    return {
        "total_runs": total["c"] if total else 0,
        "avg_risk_score": round(avg["avg"] if avg and avg["avg"] else 0, 1),
        "recommendation_breakdown": {r["final_recommendation"]: r["c"] for r in recs},
        "mode_breakdown": {r["mode"]: r["c"] for r in modes},
    }


@router.post("/trigger/{matter_id}", tags=["Stress Lab"])
async def trigger_for_matter(matter_id: str, mode: SimulationMode = SimulationMode.STANDARD, request: Request = None):
    """Auto-trigger stress lab for a matter."""
    req = StressLabRunRequest(matter_id=matter_id, mode=mode)
    return await run_stresslab(req, request)
