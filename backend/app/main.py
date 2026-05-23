"""
Evan Legal Quant Workflow Stack — FastAPI Application
7-Layer regulatory intelligence system with full API.

Enhanced with structured logging, correlation IDs, rate limiting,
request size validation, and error handling middleware.
"""

import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import db
from app.models import (
    ControlRepresentations,
    CounselMemoInput,
    Obligations,
    RawInput,
    SystemStatus,
)
from app.routers import (
    alignment,
    credibility,
    intake,
    learning,
    outputs,
    patterns,
    stresslab,
)
from app.services.llm_client import get_llm_client

# ── Structured Logging Setup ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s",
)
logger = logging.getLogger(__name__)


class CorrelationIdFilter(logging.Filter):
    """Inject correlation_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


# Apply filter to root handlers so ALL log records get correlation_id
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())
logger.addFilter(CorrelationIdFilter())


# ── Request Context ───────────────────────────────────────────────────────────

class RequestContext:
    """Holds per-request context for logging and tracing."""

    correlation_id: str = "-"
    start_time: float = 0.0


REQUEST_CTX = RequestContext()


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class SimpleRateLimiter:
    """
    In-memory sliding-window rate limiter.
    Production deployments should replace with Redis-backed limiter.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        # Remove stale entries
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True


_RATE_LIMITER = SimpleRateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)


# ── Middleware ────────────────────────────────────────────────────────────────

async def correlation_middleware(request: Request, call_next):
    """Attach correlation ID and log request lifecycle."""
    cid = request.headers.get("x-correlation-id", str(uuid.uuid4())[:8])
    REQUEST_CTX.correlation_id = cid
    REQUEST_CTX.start_time = time.time()

    logger.info(
        "-> %s %s",
        request.method,
        request.url.path,
        extra={"correlation_id": cid},
    )

    response: Response = await call_next(request)
    elapsed = (time.time() - REQUEST_CTX.start_time) * 1000

    response.headers["x-correlation-id"] = cid
    response.headers["x-response-time-ms"] = f"{elapsed:.2f}"

    logger.info(
        "<- %s %s | %d | %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
        extra={"correlation_id": cid},
    )

    return response


async def error_handling_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return structured errors."""
    try:
        return await call_next(request)
    except Exception as exc:
        cid = REQUEST_CTX.correlation_id
        logger.exception(
            "Unhandled exception in %s %s",
            request.method,
            request.url.path,
            extra={"correlation_id": cid},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. The incident has been logged.",
                "correlation_id": cid,
            },
            headers={"x-correlation-id": cid},
        )


async def rate_limit_middleware(request: Request, call_next):
    """Rate limit by client IP on state-modifying endpoints."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"{client_ip}:{path}"
        if not _RATE_LIMITER.is_allowed(key):
            logger.warning("Rate limit exceeded: %s", key)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please slow down.",
                },
                headers={"x-correlation-id": REQUEST_CTX.correlation_id},
            )
    return await call_next(request)


async def request_size_middleware(request: Request, call_next):
    """Enforce maximum request body size."""
    max_size = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "1048576"))  # 1 MB default
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if len(body) > max_size:
            logger.warning("Request body too large: %d bytes", len(body))
            return JSONResponse(
                status_code=413,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": f"Request body exceeds {max_size} bytes limit.",
                },
            )
        # Re-populate body so downstream can read it
        request._body = body
    return await call_next(request)


# ── App Factory ───────────────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    application = FastAPI(
        title="Evan Legal Quant Workflow Stack",
        description="Comprehensive 7-Layer Regulatory Intelligence System",
        version="2.0.0",
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (add in reverse order of execution)
    application.middleware("http")(error_handling_middleware)
    application.middleware("http")(correlation_middleware)
    application.middleware("http")(rate_limit_middleware)
    application.middleware("http")(request_size_middleware)

    # Routers
    application.include_router(intake.router)
    application.include_router(stresslab.router)
    application.include_router(patterns.router)
    application.include_router(alignment.router)
    application.include_router(outputs.router)
    application.include_router(learning.router)
    application.include_router(credibility.router)

    return application


app = create_application()


# ── Startup ───────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Initialize database, load mock data, and log system status on startup."""
    logger.info("Starting Evan Legal Quant Workflow Stack...")
    await db.init_db()
    logger.info("Database initialized.")
    await _load_mock_data()
    # Log available LLM providers
    try:
        llm = get_llm_client()
        logger.info(
            "LLM providers available: %s | mock_mode=%s",
            llm.available_providers,
            llm.is_mock,
        )
    except Exception:
        logger.debug("LLM client not initialized at startup")
    logger.info("Startup complete. System ready.")


async def _load_mock_data():
    """Load sample data to demonstrate system functionality."""
    existing = await db.list_raw_inputs()
    if existing:
        logger.info("Mock data already present (%d records). Skipping.", len(existing))
        return
    logger.info("Loading mock data...")
    # Sample 1: Product proposal for a crypto exchange
    raw1 = RawInput(
        input_type="product_proposal",
        source="Business Development Team",
        content="""We are proposing to launch a new virtual asset exchange platform targeting retail investors in Singapore. 
The platform will offer spot trading of BTC, ETH, and 15 other digital payment tokens. 
Revenue will be generated through transaction fees (0.1% per trade) and withdrawal fees. 
Customer assets will be held in third-party custody with Fireblocks. 
We plan to apply for the DPT license under the Payment Services Act. 
AML controls include customer due diligence, transaction monitoring, and suspicious activity reporting. 
We have a compliance officer with 5 years of experience. The platform will use a matching engine 
with throughput of 100,000 TPS. We plan to launch in Q3 2024 pending regulatory approval.
Cross-border elements: we will allow users from Hong Kong and Malaysia to access the platform.
Marketing will target retail investors through social media campaigns.""",
    )
    await db.save_raw_input(raw1.model_dump())
    # Sample 2: Licensing idea for DeFi protocol
    raw2 = RawInput(
        input_type="licensing_idea",
        source="Legal Counsel",
        content="""We are exploring a decentralized lending protocol that would allow users to lend and borrow 
virtual assets without an intermediary. The protocol would be governed by a DAO structure with 
governance tokens distributed to early users. We are considering launching this in the UK under 
FCA guidance on DeFi. The protocol would use smart contracts for collateral management and 
liquidation. Revenue would come from protocol fees (0.05% per transaction). We plan to conduct 
a security audit with CertiK before launch. The target user base is institutional investors 
initially, with retail access restricted to accredited investors. We need to assess whether 
this structure triggers VASP licensing requirements under the Financial Promotions Regime. 
AML considerations include wallet screening and sanctions checks. We assume that the DAO 
structure does not constitute a legal entity requiring direct licensing.""",
    )
    await db.save_raw_input(raw2.model_dump())
    # Create a sample fact packet for raw1
    fp1_id = str(uuid4())
    await db.save_fact_packet({
        "id": fp1_id,
        "raw_input_id": raw1.id,
        "jurisdiction": "Singapore",
        "regulator": "MAS",
        "activity_type": "Virtual Asset Exchange",
        "product_class": "Virtual Asset Exchange",
        "target_user_type": "Retail",
        "licensing_category": "DPT",
        "revenue_model": "Transaction Fees",
        "custody_model": "Third-Party Custody",
        "cross_border_elements": [
            "Cross-border access: Hong Kong",
            "Cross-border access: Malaysia",
            "Multi-jurisdiction marketing",
        ],
        "obligations": {
            "licensing_triggers": [
                "DPT license required under Payment Services Act",
                "Cross-border service provision may trigger additional licensing",
            ],
            "aml_triggers": [
                "CDD required for all customers",
                "Transaction monitoring for suspicious activity",
                "SAR filing obligations",
                "Travel Rule compliance for transfers",
            ],
            "reporting_triggers": [
                "Annual compliance reports to MAS",
                "Incident reporting within 24 hours",
            ],
            "disclosure_requirements": [
                "Risk disclosure to retail customers",
                "Fee structure transparency",
                "Terms and conditions compliance",
            ],
        },
        "control_representations": {
            "claimed": [
                "Compliance officer in place",
                "Third-party custody with Fireblocks",
                "Matching engine operational",
            ],
            "planned": [
                "Enhanced transaction monitoring system",
                "Independent compliance audit",
                "Insurance coverage for cyber risks",
            ],
            "assumed": [
                "DPT license will be approved",
                "Cross-border arrangement accepted by regulators",
            ],
        },
        "extracted_at": datetime.utcnow().isoformat(),
    })
    # Create a sample stress result
    sr1_id = str(uuid4())
    await db.save_stress_result({
        "id": sr1_id,
        "fact_packet_id": fp1_id,
        "scenarios": [
            {
                "id": str(uuid4()),
                "fact_packet_id": fp1_id,
                "scenario_number": 1,
                "agent_positions": {
                    "business_advocate": "Revenue opportunity of $12M ARR justifies measured risk. Phased rollout limits exposure.",
                    "compliance_reviewer": "Licensing gap is material. AML controls not production-ready. Insurance incomplete.",
                    "regulator_proxy": "Product structure mirrors cases with $2M fines. Consumer harm potential is high for retail.",
                    "neutral_adjudicator": "Balancing innovation vs protection: conditional licence with enhanced monitoring is proportionate. Composite: 58/100. HOLD.",
                },
                "risk_score": {
                    "overall": 58.0,
                    "dimensions": {
                        "licensing_risk": 72.0,
                        "aml_risk": 65.0,
                        "conduct_risk": 55.0,
                        "operational_risk": 48.0,
                        "reputational_risk": 45.0,
                        "regulatory_risk": 68.0,
                        "financial_risk": 42.0,
                        "cross_border_risk": 75.0,
                        "consumer_protection_risk": 80.0,
                        "enforcement_risk": 62.0,
                    },
                },
                "recommendation": "HOLD",
            },
            {
                "id": str(uuid4()),
                "fact_packet_id": fp1_id,
                "scenario_number": 2,
                "agent_positions": {
                    "business_advocate": "Customer demand is overwhelming. Delaying risks market share erosion to competitors.",
                    "compliance_reviewer": "Third-party due diligence incomplete. Reliance on vendor attestations insufficient.",
                    "regulator_proxy": "Cross-border arrangements complicate supervisory coordination. Self-assessment not a substitute for audit.",
                    "neutral_adjudicator": "Risk profile shows 2 dimensions below 40, 4 in HOLD range, 4 above 65. Decision: NO-GO. Score: 71/100.",
                },
                "risk_score": {
                    "overall": 71.0,
                    "dimensions": {
                        "licensing_risk": 78.0,
                        "aml_risk": 72.0,
                        "conduct_risk": 68.0,
                        "operational_risk": 65.0,
                        "reputational_risk": 58.0,
                        "regulatory_risk": 75.0,
                        "financial_risk": 55.0,
                        "cross_border_risk": 82.0,
                        "consumer_protection_risk": 85.0,
                        "enforcement_risk": 70.0,
                    },
                },
                "recommendation": "NO-GO",
            },
        ],
        "final_risk_rating": 64.5,
        "decisive_obligations": [
            "LICENSING: DPT license required under Payment Services Act",
            "LICENSING: Cross-border service provision may trigger additional licensing",
            "AML: CDD required for all customers",
            "AML: Transaction monitoring for suspicious activity",
            "AGGREGATE_RISK: Composite 64.5/100 exceeds threshold for DPT",
        ],
        "key_control_gaps": [
            "No planned remediation controls — regulatory expectation gap",
            "High cross_border_risk: 78.5/100 — requires targeted control",
            "High consumer_protection_risk: 82.5/100 — requires targeted control",
            "Multi-jurisdiction exposure exceeds standard control framework",
        ],
        "evidence_checklist": [
            "Legal opinion confirming licensing status (or exemption basis)",
            "AML/CFT policy documentation and risk assessment",
            "Technical audit report for underlying infrastructure",
            "Insurance policy documentation and coverage schedule",
            "Board risk appetite statement and approval minutes",
            "Consumer protection impact assessment",
            "Marketing material compliance review",
            "Cross-border legal opinions per jurisdiction",
            "Regulatory correspondence with foreign regulators",
            "Financial projections and capital adequacy analysis",
            "Independent compliance audit within last 12 months",
        ],
        "regulator_objections": [
            "Scenario 1: MAS perspective: Consumer harm potential is high for retail investors...",
            "Scenario 2: Cross-border arrangements complicate supervisory coordination...",
        ],
        "final_recommendation": "HOLD",
        "generated_at": datetime.utcnow().isoformat(),
    })
    # Create sample counsel memo
    memo1 = CounselMemoInput(
        counsel_name="Norton Rose Fulbright",
        memo_content="""RE: Legal Opinion on DPT Licence Application for Virtual Asset Exchange

We have reviewed the proposed virtual asset exchange platform and provide the following opinion:

1. LICENSING: The platform clearly triggers DPT licensing requirements under the Payment Services Act. 
   The application should be straightforward given the existing compliance framework.

2. AML: The AML controls described (CDD, transaction monitoring, SAR filing) meet MAS expectations. 
   No additional measures are required beyond standard practice.

3. CROSS-BORDER: The extension to Hong Kong and Malaysia users should not trigger additional licensing 
   provided the Singapore entity remains the contracting party.

4. RISK ASSESSMENT: We assess the overall regulatory risk as moderate. The licensing pathway is clear 
   and MAS has been supportive of responsible innovation in the digital asset space.

5. RECOMMENDATION: Proceed with the DPT licence application. We estimate approval within 6 months.

This opinion is based on current MAS guidelines and our understanding of the proposed business model.""",
        related_fact_packet_id=fp1_id,
    )
    await db.save_counsel_memo(memo1.model_dump())
    # Create a sample credibility score
    await db.save_credibility_score({
        "id": str(uuid4()),
        "counsel_name": "Norton Rose Fulbright",
        "matter_id": "SG-DPT-2024-001",
        "dimension_scores": {
            "obligation_identification": 72.0,
            "risk_classification": 58.0,
            "evidence_sufficiency": 65.0,
            "assumption_transparency": 45.0,
            "regulator_posture_realism": 52.0,
            "control_practicality": 68.0,
        },
        "weighted_score": 60.85,
        "risk_tier": "ACCEPTABLE",
        "scored_at": datetime.utcnow().isoformat(),
    })
    await db.update_counsel_track_record({
        "counsel_name": "Norton Rose Fulbright",
        "average_score": 60.85,
        "scores_by_jurisdiction": {"Singapore": 60.85},
        "scores_over_time": [
            {
                "matter_id": "SG-DPT-2024-001",
                "score": 60.85,
                "tier": "ACCEPTABLE",
                "scored_at": datetime.utcnow().isoformat(),
            }
        ],
        "enforcement_correlation": 0.0,
        "hindsight_accuracy": 0.0,
    })
    # Create sample escalation items
    await db.save_escalation_item({
        "id": str(uuid4()),
        "priority": "P1",
        "title": "DPT Licence Application — Retail Investor Safeguards Required",
        "description": "MAS has indicated that retail-facing DPT platforms require enhanced safeguards including suitability assessments and loss limits.",
        "jurisdiction": "Singapore",
        "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
        "status": "open",
    })
    await db.save_escalation_item({
        "id": str(uuid4()),
        "priority": "P2",
        "title": "Cross-Border Access — Hong Kong SFC Notification",
        "description": "Hong Kong users accessing the platform may trigger SFC notification requirements under the Securities and Futures Ordinance.",
        "jurisdiction": "Hong Kong",
        "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "status": "open",
    })
    # Create sample control investments
    await db.save_control_investment({
        "control_name": "Enhanced Consumer Protection Framework",
        "priority": 1,
        "estimated_cost": "$150K-$300K",
        "risk_reduction": 35.0,
        "jurisdictions": ["Singapore", "Hong Kong"],
    })
    await db.save_control_investment({
        "control_name": "Multi-Jurisdiction Compliance Platform",
        "priority": 2,
        "estimated_cost": "$300K-$600K",
        "risk_reduction": 28.0,
        "jurisdictions": ["Singapore", "Hong Kong", "Malaysia"],
    })
    # Create sample drift detection
    await db.save_drift_detection({
        "id": str(uuid4()),
        "product_id": "SG-DPT-EXCHANGE-001",
        "previous_score": 45.0,
        "current_score": 64.5,
        "drift_detected": True,
        "drift_magnitude": 19.5,
        "posture_change": "Risk INCREASED from 45.0 to 64.5 (+19.5) — MAS enforcement action against competitor elevated risk profile",
        "detected_at": datetime.utcnow().isoformat(),
    })
    logger.info("Mock data loaded successfully.")


# ── Root endpoint ─────────────────────────────────────────────────────────────


@app.get("/", response_model=SystemStatus)
async def root() -> SystemStatus:
    """Return system status with enhanced feature flags."""
    # Get LLM provider info
    providers = []
    try:
        llm = get_llm_client()
        providers = llm.available_providers
    except Exception:
        pass

    return SystemStatus(
        status="operational",
        version="2.0.0",
        layers_active=[
            "Layer 0 — Raw Input",
            "Layer 1 — Intake & Structuring",
            "Layer 2 — Compliance Stress Lab",
            "Layer 3 — Pattern Intelligence",
            "Layer 4 — Counsel Alignment",
            "Layer 5 — Management Output",
            "Layer 6 — Continuous Learning",
            "Part II — Counsel Credibility",
            "Multi-Provider LLM",
            "Risk Scoring Engine",
            "Simulation Router",
        ],
        uptime="active",
    )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "evan-legal-quant"}
