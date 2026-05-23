"""
OpenEvan v11 — Merged Unified Models
Combines x870 Evan-AI Compliance OS models with OpenEvan Analytical Engine models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── x870 Enums ──────────────────────────────────────────────────────────────

class MatterType(str, Enum):
    REGULATORY_CHANGE = "regulatory_change"
    LICENSING_APPLICATION = "licensing_application"
    ENFORCEMENT_ACTION = "enforcement_action"
    COMPLIANCE_REVIEW = "compliance_review"
    INTERNAL_AUDIT = "internal_audit"
    RISK_ASSESSMENT = "risk_assessment"
    ADVISORY = "advisory"
    POLICY_DEVELOPMENT = "policy_development"

class MatterStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    CLOSED = "closed"
    ARCHIVED = "archived"

class MatterPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class OutputStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

class OutputType(str, Enum):
    DECISION_MEMO = "decision_memo"
    RISK_ASSESSMENT = "risk_assessment"
    POLICY_BRIEF = "policy_brief"
    REGULATORY_RESPONSE = "regulatory_response"
    MANAGEMENT_UPDATE = "management_update"
    MEETING_MINUTES = "meeting_minutes"

class MemoryClass(str, Enum):
    REGULATORY_FACT = "regulatory_fact"
    BUSINESS_PRACTICE = "business_practice"
    PRECEDENT = "precedent"
    RISK_SIGNAL = "risk_signal"
    STAKEHOLDER_PREFERENCE = "stakeholder_preference"
    MARKET_INTELLIGENCE = "market_intelligence"

class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PrecedentType(str, Enum):
    REGULATORY_POSITION = "regulatory_position"
    RISK_FRAMEWORK = "risk_framework"
    APPROVAL_PATHWAY = "approval_pathway"
    ENFORCEMENT_RESPONSE = "enforcement_response"

class SimulationMode(str, Enum):
    STANDARD = "standard"
    ADVERSARIAL = "adversarial"
    REGULATOR_ONLY = "regulator_only"
    BUSINESS_ONLY = "business_only"
    TIME_BOXED = "time_boxed"
    CONSENSUS = "consensus"
    DEEP_DIVE = "deep_dive"

class Recommendation(str, Enum):
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    NO_GO = "NO-GO"

class EscalationPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

class CounselTier(str, Enum):
    ELITE = "Elite"
    ESTABLISHED = "Established"
    DEVELOPING = "Developing"
    MONITOR = "Monitor"


# ── x870 Matter Models ─────────────────────────────────────────────────────

class MatterCreate(BaseModel):
    matter_code: str
    title: str
    type: MatterType
    jurisdiction: str
    entity: str
    regulator: Optional[str] = None
    product: Optional[str] = None
    priority: MatterPriority = MatterPriority.MEDIUM
    status: MatterStatus = MatterStatus.OPEN
    summary: Optional[str] = None

class MatterUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[MatterPriority] = None
    status: Optional[MatterStatus] = None
    summary: Optional[str] = None
    working_position: Optional[str] = None
    current_risk: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[datetime] = None

class MatterEventCreate(BaseModel):
    event_type: str
    summary: str
    details_json: Optional[Dict[str, Any]] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)

class MatterResponse(BaseModel):
    id: str
    matter_code: str
    title: str
    type: MatterType
    jurisdiction: str
    entity: str
    regulator: Optional[str] = None
    product: Optional[str] = None
    priority: MatterPriority
    status: MatterStatus
    summary: Optional[str] = None
    working_position: Optional[str] = None
    current_risk: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ── x870 Document Models ───────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str

class DocumentResponse(BaseModel):
    id: str
    title: str
    doc_type: str
    matter_id: Optional[str] = None
    source_system: Optional[str] = None
    mime_type: str
    sensitivity_level: str = "internal"
    file_path: str
    version: int = 1
    checksum: str
    created_at: datetime
    updated_at: datetime


# ── x870 Memory Models ─────────────────────────────────────────────────────

class MemoryItemCreate(BaseModel):
    memory_class: MemoryClass
    title: str
    content: str
    tags: List[str] = []
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None

class MemoryItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    importance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    active: Optional[bool] = None

class MemoryItemResponse(MemoryItemCreate):
    id: str
    user_id: str
    active: bool
    created_at: datetime
    updated_at: datetime

class MemorySearchRequest(BaseModel):
    query: str
    memory_class: Optional[MemoryClass] = None
    limit: int = Field(default=10, le=50)

class MemorySearchResponse(BaseModel):
    items: List[MemoryItemResponse]
    scores: List[float]


# ── x870 Output Models ─────────────────────────────────────────────────────

class OutputResponse(BaseModel):
    id: str
    output_type: OutputType
    matter_id: Optional[str] = None
    audience: str
    title: str
    content: str
    format: str = "markdown"
    status: OutputStatus
    quality_rating: Optional[float] = None
    model_used: str
    created_at: datetime
    updated_at: datetime

class FeedbackCreate(BaseModel):
    feedback_type: str
    feedback_text: Optional[str] = None
    delta_summary: Optional[str] = None
    signal_strength: float = Field(default=0.5, ge=0.0, le=1.0)


# ── x870 Precedent Models ──────────────────────────────────────────────────

class PrecedentResponse(BaseModel):
    id: str
    title: str
    precedent_type: PrecedentType
    jurisdiction: str
    audience: str
    topic_tags: List[str] = []
    summary: str
    content: str
    user_id: str
    quality_score: float
    created_at: datetime
    updated_at: datetime

class PrecedentSearchRequest(BaseModel):
    query: str
    audience: Optional[str] = None
    precedent_type: Optional[PrecedentType] = None
    limit: int = Field(default=10, le=50)


# ── x870 Task Models ───────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    matter_id: Optional[str] = None
    owner: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    owner: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    blocker: Optional[str] = None
    notes: Optional[str] = None

class TaskResponse(TaskCreate):
    id: str
    status: TaskStatus
    blocker: Optional[str] = None
    created_at: datetime


# ── x870 Stakeholder Models ────────────────────────────────────────────────

class StakeholderCreate(BaseModel):
    name: str
    title: Optional[str] = None
    relationship_type: str
    tone_profile: Optional[str] = None
    decision_preference_summary: Optional[str] = None
    notes: Optional[str] = None

class StakeholderResponse(StakeholderCreate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# ── x870 Draft Models ──────────────────────────────────────────────────────

class DraftRequest(BaseModel):
    matter_id: Optional[str] = None
    matter_ids: Optional[List[str]] = None
    audience: Optional[str] = None
    output_type: str = "brief"
    additional_context: Optional[str] = None
    key_points: Optional[List[str]] = None

class DraftResponse(BaseModel):
    output_id: str
    content: str
    title: str


# ── x870 Research Models ───────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    matter_id: Optional[str] = None
    sources: List[str] = ["web"]

class ResearchResponse(BaseModel):
    research_id: str
    status: str
    message: str


# ── x870 Chat Models ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    matter_id: Optional[str] = None
    file_ids: Optional[List[str]] = None
    audience: Optional[str] = None
    output_type: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    output_id: Optional[str] = None


# ── x870 Preference Models ─────────────────────────────────────────────────

class PreferenceCreate(BaseModel):
    category: str
    key: str
    value_json: Dict[str, Any]
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_type: Optional[str] = None
    source_ref: Optional[str] = None

class PreferenceResponse(PreferenceCreate):
    id: str
    user_id: str
    active: bool
    last_confirmed_at: Optional[datetime] = None
    created_at: datetime


# ── OpenEvan L1: Regulatory Intake ─────────────────────────────────────────

class RawInputCreate(BaseModel):
    input_type: str = "regulatory_update"
    source: str
    content: str

class RawInputResponse(RawInputCreate):
    id: str
    timestamp: datetime
    status: str = "pending"

class FactPacket(BaseModel):
    id: str
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
    obligations: Dict[str, Any] = {}
    control_representations: Dict[str, Any] = {}
    risk_signals: List[str] = []
    extracted_at: datetime


# ── OpenEvan L2: CSL Stress Lab ────────────────────────────────────────────

class StressLabRunRequest(BaseModel):
    matter_id: Optional[str] = None
    fact_packet_id: Optional[str] = None
    mode: SimulationMode = SimulationMode.STANDARD
    context: Optional[str] = None
    product_class: Optional[str] = None
    jurisdiction: Optional[str] = None

class AgentPosition(BaseModel):
    agent: str
    position: str
    confidence: float
    key_arguments: List[str]

class RiskDimension(BaseModel):
    name: str
    score: float
    weight: float
    weighted_score: float

class SimulationScenario(BaseModel):
    scenario_id: str
    context: str
    agent_positions: List[AgentPosition]
    scenario_risk_score: float
    decisive_obligations: List[str]
    control_gaps: List[str]

class StressLabResult(BaseModel):
    id: str
    matter_id: Optional[str] = None
    fact_packet_id: Optional[str] = None
    mode: SimulationMode
    scenarios: List[SimulationScenario]
    overall_risk_score: float
    risk_dimensions: List[RiskDimension]
    final_recommendation: Recommendation
    decisive_obligations: List[str]
    key_control_gaps: List[str]
    evidence_checklist: List[str]
    regulator_objections: List[str]
    generated_at: datetime
    model_used: str


# ── OpenEvan L3: Pattern Extraction ────────────────────────────────────────

class PatternExtract(BaseModel):
    id: str
    stress_result_id: Optional[str] = None
    matter_id: Optional[str] = None
    recurring_obligations: List[Dict[str, Any]] = []
    risk_drivers: List[str] = []
    compliance_weaknesses: List[str] = []
    early_warning_signals: List[str] = []
    risk_index: Dict[str, float] = {}
    extracted_at: datetime

class RiskIndexQuery(BaseModel):
    jurisdiction: Optional[str] = None
    product_class: Optional[str] = None
    time_range_days: int = 90


# ── OpenEvan L4: Counsel Alignment ─────────────────────────────────────────

class CounselMemoSubmit(BaseModel):
    matter_id: Optional[str] = None
    counsel_name: str
    memo_content: str
    jurisdiction: Optional[str] = None
    product_area: Optional[str] = None

class AlignmentDimension(BaseModel):
    dimension: str
    alignment_score: float
    gap_description: Optional[str] = None

class AlignmentResult(BaseModel):
    id: str
    matter_id: Optional[str] = None
    counsel_name: str
    overall_alignment: float
    dimensions: List[AlignmentDimension]
    key_gaps: List[str]
    recommendations: List[str]
    analyzed_at: datetime


# ── OpenEvan L5: Workflow Outputs ──────────────────────────────────────────

class DecisionMemo(BaseModel):
    id: str
    matter_id: Optional[str] = None
    stress_result_id: Optional[str] = None
    executive_summary: str
    risk_assessment: str
    regulatory_position: str
    recommended_actions: List[str]
    approval_authority: str
    timeline: str
    generated_at: datetime

class RiskHeatmapItem(BaseModel):
    jurisdiction: str
    risk_score: float
    trend: str
    top_drivers: List[str]

class EscalationItem(BaseModel):
    id: str
    priority: EscalationPriority
    title: str
    description: str
    related_matter_id: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "open"
    created_at: datetime


# ── OpenEvan L6: Continuous Learning ───────────────────────────────────────

class PostureScore(BaseModel):
    id: str
    overall_score: float
    dimension_scores: Dict[str, float]
    trend: str
    assessed_at: datetime

class DriftEvent(BaseModel):
    id: str
    event_type: str
    description: str
    impact_score: float
    previous_posture: float
    new_posture: float
    detected_at: datetime


# ── OpenEvan CS: Credibility Scoring ───────────────────────────────────────

class CredibilityScoreRequest(BaseModel):
    counsel_name: str
    historical_accuracy: float = Field(ge=0, le=100)
    jurisdictional_depth: float = Field(ge=0, le=100)
    timeliness: float = Field(ge=0, le=100)
    communication_clarity: float = Field(ge=0, le=100)
    strategic_value: float = Field(ge=0, le=100)
    independence: float = Field(ge=0, le=100)
    matter_id: Optional[str] = None

class CredibilityScoreResponse(BaseModel):
    id: str
    counsel_name: str
    dimensions: Dict[str, float]
    overall_score: float
    tier: CounselTier
    track_record: Dict[str, Any]
    scored_at: datetime

class CounselLeaderboardEntry(BaseModel):
    rank: int
    counsel_name: str
    overall_score: float
    tier: CounselTier
    matter_count: int
    last_scored: datetime


# ── Admin / Status ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str = "openevan-v11"
    version: str = "11.0.0"
    timestamp: datetime
    services: Optional[Dict[str, Any]] = None

class MetricsResponse(BaseModel):
    total_matters: int = 0
    open_matters: int = 0
    total_outputs: int = 0
    total_memory_items: int = 0
    total_stress_runs: int = 0
    total_patterns: int = 0
    pending_tasks: int = 0
    token_usage_7d: Dict[str, int] = {}
    stresslab_stats: Dict[str, Any] = {}
    credibility_entries: int = 0

class SystemStatus(BaseModel):
    status: str = "healthy"
    version: str = "11.0.0"
    features: Dict[str, bool] = {
        "chat": True,
        "matters": True,
        "documents": True,
        "memory": True,
        "drafts": True,
        "research": True,
        "stresslab": True,
        "patterns": True,
        "credibility": True,
        "alignment": True,
        "learning": True,
        "intake": True,
    }
