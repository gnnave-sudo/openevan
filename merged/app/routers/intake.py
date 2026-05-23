"""
OpenEvan L1: Regulatory Intake Router
Raw regulatory text ingestion with automated fact extraction.
"""

import json
import re
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Request

from app.models import FactPacket, RawInputCreate, RawInputResponse

router = APIRouter(prefix="/api/v1/intake", tags=["Intake"])

# ── Extraction Patterns ────────────────────────────────────────────────────

JURISDICTION_PATTERNS = {
    "Singapore": ["singapore", "sg", "mas", "monetary authority"],
    "Hong Kong": ["hong kong", "hk", "hkma", "sfc"],
    "UK": ["uk", "united kingdom", "fca"],
    "US": ["us", "united states", "sec", "cftc", "finra"],
    "EU": ["eu", "european union", "esma", "mica"],
    "Australia": ["australia", "asic"],
    "Japan": ["japan", "fsa japan"],
    "UAE": ["uae", "dubai", "var", "dfsa"],
    "Switzerland": ["switzerland", "finma"],
}

PRODUCT_PATTERNS = {
    "Virtual Asset Exchange": ["exchange", "trading platform"],
    "Custody": ["custody", "custodian", "wallet"],
    "DeFi": ["defi", "decentralized finance", "smart contract"],
    "Lending": ["lending", "borrow", "loan"],
    "Staking": ["staking", "stake", "yield"],
    "Payments": ["payment", "remittance"],
    "Derivatives": ["derivative", "future", "option"],
}

LICENSING_PATTERNS = {
    "DPT": ["digital payment token"],
    "VASP": ["virtual asset service provider"],
    "MPI": ["major payment institution"],
    "RFMC": ["registered fund management company"],
    "Banking": ["banking", "bank"],
}


def _extract_field(text: str, patterns: dict) -> str:
    text_lower = text.lower()
    for field, keywords in patterns.items():
        if any(kw in text_lower for kw in keywords):
            return field
    return "Unknown"


def _extract_fact_packet(raw: RawInputResponse) -> FactPacket:
    jurisdiction = _extract_field(raw.content, JURISDICTION_PATTERNS)
    product = _extract_field(raw.content, PRODUCT_PATTERNS)
    licensing = _extract_field(raw.content, LICENSING_PATTERNS)
    
    obligations = {}
    if "aml" in raw.content.lower() or "cft" in raw.content.lower():
        obligations["aml_cft"] = {
            "requirement": "Implement AML/CFT transaction monitoring",
            "applicable": True,
            "urgency": "high",
        }
    if "licens" in raw.content.lower() or "authoris" in raw.content.lower():
        obligations["licensing"] = {
            "requirement": f"Obtain {licensing} license",
            "applicable": True,
            "urgency": "critical",
        }
    if "consumer" in raw.content.lower() or "retail" in raw.content.lower():
        obligations["consumer_protection"] = {
            "requirement": "Implement retail investor safeguards",
            "applicable": True,
            "urgency": "high",
        }
    
    controls = {}
    if "kyc" in raw.content.lower():
        controls["kyc"] = {
            "control": "Customer due diligence and KYC procedures",
            "status": "required",
        }
    if "monitor" in raw.content.lower():
        controls["transaction_monitoring"] = {
            "control": "Real-time transaction monitoring system",
            "status": "required",
        }
    
    risk_signals = []
    if any(w in raw.content.lower() for w in ["enforcement", "fine", "penalty"]):
        risk_signals.append("Recent enforcement action in sector")
    if any(w in raw.content.lower() for w in ["prohibition", "ban", "restrict"]):
        risk_signals.append("Product or activity restriction signal")
    if any(w in raw.content.lower() for w in ["consultation", "proposed"]):
        risk_signals.append("Upcoming regulatory change expected")
    if not risk_signals:
        risk_signals.append("Standard regulatory monitoring required")
    
    regulator = {
        "Singapore": "MAS",
        "Hong Kong": "SFC",
        "UK": "FCA",
        "US": "SEC",
        "EU": "ESMA",
        "Australia": "ASIC",
        "Japan": "FSA Japan",
        "UAE": "VARA",
        "Switzerland": "FINMA",
    }.get(jurisdiction, "Unknown Regulator")
    
    return FactPacket(
        id=str(uuid.uuid4()),
        raw_input_id=raw.id,
        jurisdiction=jurisdiction,
        regulator=regulator,
        activity_type=product,
        product_class=product,
        target_user_type="institutional" if "institutional" in raw.content.lower() else "retail",
        licensing_category=licensing,
        revenue_model="Transaction Fees",
        custody_model="Third-Party Custody",
        cross_border_elements=[jurisdiction] if jurisdiction != "Unknown" else [],
        obligations=obligations,
        control_representations=controls,
        risk_signals=risk_signals,
        extracted_at=datetime.utcnow(),
    )


@router.post("/raw-input", response_model=RawInputResponse)
async def submit_raw_input(req: RawInputCreate, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    
    input_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    if db:
        await db.execute(
            "INSERT INTO raw_inputs (id, input_type, source, content, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)",
            (input_id, req.input_type, req.source, req.content, timestamp, "processed"),
        )
        await db.commit()
    
    raw = RawInputResponse(
        id=input_id,
        input_type=req.input_type,
        source=req.source,
        content=req.content,
        timestamp=datetime.fromisoformat(timestamp),
        status="processed",
    )
    
    # Auto-extract fact packet
    packet = _extract_fact_packet(raw)
    if db:
        await db.execute(
            "INSERT INTO fact_packets (id, raw_input_id, jurisdiction, regulator, activity_type, product_class, target_user_type, licensing_category, revenue_model, custody_model, cross_border_elements, obligations, control_representations, risk_signals, extracted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (packet.id, packet.raw_input_id, packet.jurisdiction, packet.regulator,
             packet.activity_type, packet.product_class, packet.target_user_type,
             packet.licensing_category, packet.revenue_model, packet.custody_model,
             json.dumps(packet.cross_border_elements),
             json.dumps(packet.obligations),
             json.dumps(packet.control_representations),
             json.dumps(packet.risk_signals),
             packet.extracted_at.isoformat()),
        )
        await db.commit()
    
    return raw


@router.get("/inputs", response_model=List[RawInputResponse])
async def list_inputs(status: str = None, limit: int = 100, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return []
    
    sql = "SELECT * FROM raw_inputs"
    params = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    rows = await db.fetchall(sql, tuple(params))
    return [RawInputResponse(**dict(r)) for r in rows]


@router.get("/fact-packet/{input_id}")
async def get_fact_packet(input_id: str, request: Request):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"detail": "Database not available"}
    
    row = await db.fetchone(
        "SELECT * FROM fact_packets WHERE raw_input_id = ? ORDER BY extracted_at DESC LIMIT 1",
        (input_id,),
    )
    if not row:
        return {"detail": "Fact packet not found"}
    
    rd = dict(row)
    return FactPacket(
        id=rd["id"],
        raw_input_id=rd["raw_input_id"],
        jurisdiction=rd["jurisdiction"],
        regulator=rd["regulator"],
        activity_type=rd["activity_type"],
        product_class=rd["product_class"],
        target_user_type=rd["target_user_type"],
        licensing_category=rd["licensing_category"],
        revenue_model=rd["revenue_model"],
        custody_model=rd["custody_model"],
        cross_border_elements=json.loads(rd["cross_border_elements"]),
        obligations=json.loads(rd["obligations"]),
        control_representations=json.loads(rd["control_representations"]),
        risk_signals=json.loads(rd["risk_signals"]),
        extracted_at=datetime.fromisoformat(rd["extracted_at"]),
    )


@router.get("/packets")
async def list_packets(jurisdiction: str = None, limit: int = 100, request: Request = None):
    db = request.app.state.db if hasattr(request.app.state, 'db') else None
    if not db:
        return {"packets": []}
    
    sql = "SELECT * FROM fact_packets"
    params = []
    if jurisdiction:
        sql += " WHERE jurisdiction = ?"
        params.append(jurisdiction)
    sql += " ORDER BY extracted_at DESC LIMIT ?"
    params.append(limit)
    
    rows = await db.fetchall(sql, tuple(params))
    return {"packets": [dict(r) for r in rows], "count": len(rows)}
