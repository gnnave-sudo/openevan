"""
Evan Legal Quant Workflow Stack - Pydantic Models
Comprehensive regulatory intelligence system models across 7 layers + Part II.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 0 — Raw Input
# ═══════════════════════════════════════════════════════════════════════════════

class RawInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    input_type: Literal[
        "product_proposal",
        "licensing_idea",
        "marketing_campaign",
        "incident_report",
        "regulator_letter",
        "counsel_memo",
        "co_report",
        "audit_finding",
        "enforcement_action",
    ]
    source: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "structured", "stressed", "completed"] = "pending"


class Obligations(BaseModel):
    licensing_triggers: List[str] = []
    aml_triggers: List[str] = []
    reporting_triggers: List[str] = []
    disclosure_requirements: List[str] = []


class ControlRepresentations(BaseModel):
    claimed: List[str] = []
    planned: List[str] = []
    assumed: List[str] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Fact Packet
# ═══════════════════════════════════════════════════════════════════════════════

class FactPacket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    raw_input_id: str
    jurisdiction: str
    regulator: str
    activity_type: str
    product_class: str
    target_user_type: str
    licensing_category: str
    revenue_model: str
    custody_model: str
    cross_border_elements: List[str] = []
    obligations: Obligations = Field(default_factory=Obligations)
    control_representations: ControlRepresentations = Field(
        default_factory=ControlRepresentations
    )
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2 — CSL Simulation
# ═══════════════════════════════════════════════════════════════════════════════

class AgentPositions(BaseModel):
    business_advocate: str
    compliance_reviewer: str
    regulator_proxy: str
    neutral_adjudicator: str


class RiskScore(BaseModel):
    overall: float = 0.0
    dimensions: Dict[str, float] = Field(
        default_factory=lambda: {
            "licensing_risk": 0.0,
            "aml_risk": 0.0,
            "conduct_risk": 0.0,
            "operational_risk": 0.0,
            "reputational_risk": 0.0,
            "regulatory_risk": 0.0,
            "financial_risk": 0.0,
            "cross_border_risk": 0.0,
            "consumer_protection_risk": 0.0,
            "enforcement_risk": 0.0,
        }
    )


class SimulationScenario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    fact_packet_id: str = ""
    scenario_number: int = 0
    agent_positions: AgentPositions
    risk_score: RiskScore
    recommendation: Literal["PROCEED", "HOLD", "NO-GO"]
    stress_result_id: Optional[str] = None


class StressLabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    fact_packet_id: str
    scenarios: List[SimulationScenario] = []
    final_risk_rating: float = 0.0
    decisive_obligations: List[str] = []
    key_control_gaps: List[str] = []
    evidence_checklist: List[str] = []
    regulator_objections: List[str] = []
    final_recommendation: Literal["PROCEED", "HOLD", "NO-GO"] = "HOLD"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3 — Hermes Pattern Intelligence
# ═══════════════════════════════════════════════════════════════════════════════

class PatternExtract(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    stress_result_id: str
    jurisdiction: str
    product_type: str
    risk_drivers: List[str] = []
    recurrent_obligations: List[str] = []
    recurring_control_weaknesses: List[str] = []
    regulatory_posture_signals: List[str] = []
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class RiskIndices(BaseModel):
    jurisdiction_risk_index: Dict[str, float] = {}
    obligation_frequency: Dict[str, int] = {}
    control_failure_frequency: Dict[str, int] = {}
    counsel_alignment_index: Dict[str, float] = {}
    escalation_likelihood: Dict[str, float] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 4 — Counsel Alignment
# ═══════════════════════════════════════════════════════════════════════════════

class CounselMemoInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    counsel_name: str
    memo_content: str
    related_fact_packet_id: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class AlignmentResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    memo_id: str
    alignment_score: float = 0.0
    dimension_scores: Dict[str, float] = {}
    missing_regulator_objections: List[str] = []
    missing_evidence_hooks: List[str] = []
    overconfidence_flags: List[str] = []
    suggested_clarification_questions: List[str] = []
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 5 — Management Output
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionMemo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    stress_result_id: str
    title: str
    executive_summary: str
    risk_assessment: str
    recommendations: List[str] = []
    next_steps: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EscalationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    priority: Literal["P0", "P1", "P2"]
    title: str
    description: str
    jurisdiction: str
    due_date: Optional[datetime] = None
    status: Literal["open", "in_progress", "resolved"] = "open"


class ControlInvestment(BaseModel):
    control_name: str
    priority: int = 0
    estimated_cost: str = ""
    risk_reduction: float = 0.0
    jurisdictions: List[str] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 6 — Continuous Learning
# ═══════════════════════════════════════════════════════════════════════════════

class DriftDetection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    product_id: str
    previous_score: float = 0.0
    current_score: float = 0.0
    drift_detected: bool = False
    drift_magnitude: float = 0.0
    posture_change: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Part II — Counsel Credibility
# ═══════════════════════════════════════════════════════════════════════════════

class CredibilityDimension(str, Enum):
    OBLIGATION_IDENTIFICATION = "obligation_identification"
    RISK_CLASSIFICATION = "risk_classification"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    ASSUMPTION_TRANSPARENCY = "assumption_transparency"
    REGULATOR_POSTURE_REALISM = "regulator_posture_realism"
    CONTROL_PRACTICALITY = "control_practicality"


DIMENSION_WEIGHTS = {
    CredibilityDimension.OBLIGATION_IDENTIFICATION: 0.25,
    CredibilityDimension.RISK_CLASSIFICATION: 0.20,
    CredibilityDimension.EVIDENCE_SUFFICIENCY: 0.15,
    CredibilityDimension.ASSUMPTION_TRANSPARENCY: 0.15,
    CredibilityDimension.REGULATOR_POSTURE_REALISM: 0.15,
    CredibilityDimension.CONTROL_PRACTICALITY: 0.10,
}


class CounselCredibilityScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    counsel_name: str
    matter_id: str
    dimension_scores: Dict[str, float] = {}
    weighted_score: float = 0.0
    risk_tier: Literal[
        "HIGH_RISK", "WEAK", "ACCEPTABLE", "STRONG", "HIGHLY_RELIABLE"
    ] = "WEAK"
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class CounselTrackRecord(BaseModel):
    counsel_name: str
    average_score: float = 0.0
    scores_by_jurisdiction: Dict[str, float] = {}
    scores_over_time: List[Dict[str, Any]] = []
    enforcement_correlation: float = 0.0
    hindsight_accuracy: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response helpers
# ═══════════════════════════════════════════════════════════════════════════════

class IntakeSubmitRequest(BaseModel):
    input_type: Literal[
        "product_proposal",
        "licensing_idea",
        "marketing_campaign",
        "incident_report",
        "regulator_letter",
        "counsel_memo",
        "co_report",
        "audit_finding",
        "enforcement_action",
    ]
    source: str
    content: str


class CounselMemoSubmitRequest(BaseModel):
    counsel_name: str
    memo_content: str
    related_fact_packet_id: Optional[str] = None


class CredibilityScoreRequest(BaseModel):
    counsel_name: str
    matter_id: str
    dimension_scores: Dict[str, float]


class SystemStatus(BaseModel):
    status: str
    version: str
    layers_active: List[str]
    uptime: str
