"""
OpenEvan v12 — Cross-App Workflow Engine
5 agent-driven workflows orchestrating the 6 legal apps + analytical layers.
Each workflow is a DAG of tool calls with conditional branching and result aggregation.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WorkflowType(str, Enum):
    EXTRACT_VISUALIZE = "extract_visualize"      # Tabular → ChartAI
    COMPARE_SIMULATE = "compare_simulate"         # RedlineNow → Contract Sim → StressLab
    REVIEW_SIGN = "review_sign"                   # Tabular verify → SigPack
    FULL_PIPELINE = "full_pipeline"               # All 6 apps
    RISK_ASSESSMENT = "risk_assessment"           # Intake → StressLab → Patterns → Credibility


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class WorkflowStep:
    id: str
    skill: str           # e.g., "evan.redlinenow"
    tool: str            # e.g., "compareDocuments"
    input_params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    output: Optional[Dict[str, Any]] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WorkflowInstance:
    id: str
    type: WorkflowType
    description: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    final_output: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


class WorkflowEngine:
    """
    Orchestrates cross-app workflows using a DAG executor.
    Each workflow chains multiple MCP skill calls with data flowing between steps.
    """

    WORKFLOW_DEFINITIONS: Dict[WorkflowType, Dict] = {
        WorkflowType.EXTRACT_VISUALIZE: {
            "description": "Extract party data from document and visualize entity structure",
            "steps": [
                {"skill": "evan.tabular", "tool": "extractFromDocument", "params": {"columns": ["party_name", "role", "ownership_pct", "jurisdiction"]}},
                {"skill": "evan.chartai", "tool": "parseStructure", "params": {"structure_type": "entity_hierarchy"}},
                {"skill": "evan.chartai", "tool": "visualize", "params": {"layout": "elk_hierarchical"}},
            ],
        },
        WorkflowType.COMPARE_SIMULATE: {
            "description": "Compare document versions, assess risks, simulate disputes, suggest amendments",
            "steps": [
                {"skill": "evan.redlinenow", "tool": "compareDocuments", "params": {}},
                {"skill": "evan.contract_sim", "tool": "assessRisk", "params": {"dimensions": ["regulatory", "financial", "operational"]}},
                {"skill": "evan.stresslab", "tool": "run_simulation", "params": {"mode": "standard", "agents": 4}},
                {"skill": "evan.patterns", "tool": "extract", "params": {}},
                {"skill": "evan.contract_sim", "tool": "suggestAmendments", "params": {"style": "balanced"}},
            ],
        },
        WorkflowType.REVIEW_SIGN: {
            "description": "Verify extraction, prepare signature pages, create signing order, export packet",
            "steps": [
                {"skill": "evan.tabular", "tool": "verifyExtraction", "params": {"confidence_threshold": 0.85}},
                {"skill": "evan.sigpack", "tool": "extractSignatures", "params": {}},
                {"skill": "evan.sigpack", "tool": "groupByParty", "params": {}},
                {"skill": "evan.sigpack", "tool": "createSigningOrder", "params": {"workflow_type": "sequential"}},
                {"skill": "evan.sigpack", "tool": "exportPacket", "params": {"format": "zip"}},
            ],
        },
        WorkflowType.FULL_PIPELINE: {
            "description": "Complete contract lifecycle: compare, extract, visualize, simulate, sign",
            "steps": [
                {"skill": "evan.redlinenow", "tool": "compareDocuments", "params": {}},
                {"skill": "evan.tabular", "tool": "extractFromDocument", "params": {"columns": ["all"]}},
                {"skill": "evan.chartai", "tool": "parseStructure", "params": {"structure_type": "full"}},
                {"skill": "evan.chartai", "tool": "visualize", "params": {}},
                {"skill": "evan.contract_sim", "tool": "simulateDispute", "params": {"arbiter_count": 3, "depth": "standard"}},
                {"skill": "evan.stresslab", "tool": "run_simulation", "params": {"mode": "deep_dive"}},
                {"skill": "evan.patterns", "tool": "extract", "params": {}},
                {"skill": "evan.sigpack", "tool": "extractSignatures", "params": {}},
                {"skill": "evan.sigpack", "tool": "createSigningOrder", "params": {}},
                {"skill": "evan.sigpack", "tool": "exportPacket", "params": {}},
            ],
        },
        WorkflowType.RISK_ASSESSMENT: {
            "description": "Full risk assessment: intake regulatory text, stress lab, extract patterns, score credibility",
            "steps": [
                {"skill": "evan.intake", "tool": "submit", "params": {"input_type": "regulatory_update"}},
                {"skill": "evan.stresslab", "tool": "run_simulation", "params": {"mode": "standard"}},
                {"skill": "evan.patterns", "tool": "extract", "params": {}},
                {"skill": "evan.patterns", "tool": "risk_index", "params": {}},
                {"skill": "evan.learning", "tool": "posture", "params": {}},
                {"skill": "evan.learning", "tool": "detect_drift", "params": {}},
            ],
        },
    }

    def __init__(self):
        self._executions: Dict[str, WorkflowInstance] = {}

    def create(self, workflow_type: WorkflowType, context: Dict[str, Any] = None) -> WorkflowInstance:
        """Create a new workflow instance from a template."""
        definition = self.WORKFLOW_DEFINITIONS[workflow_type]
        steps = []
        for i, step_def in enumerate(definition["steps"]):
            step = WorkflowStep(
                id=f"step_{i}_{uuid.uuid4().hex[:8]}",
                skill=step_def["skill"],
                tool=step_def["tool"],
                input_params={**step_def.get("params", {}), **(context or {})},
                depends_on=[s.id for s in steps] if i > 0 else [],
            )
            steps.append(step)

        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            type=workflow_type,
            description=definition["description"],
            steps=steps,
            context=context or {},
        )
        self._executions[instance.id] = instance
        return instance

    def execute(self, instance_id: str, tool_executor: Callable[[str, str, Dict], Dict]) -> WorkflowInstance:
        """Execute a workflow instance using the provided tool executor."""
        instance = self._executions.get(instance_id)
        if not instance:
            raise ValueError(f"Workflow {instance_id} not found")

        instance.status = WorkflowStatus.RUNNING

        for step in instance.steps:
            if step.status != WorkflowStatus.PENDING:
                continue

            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.utcnow().isoformat()

            try:
                # Merge outputs from previous steps into context
                merged_params = dict(step.input_params)
                for prev_step in instance.steps:
                    if prev_step.id in step.depends_on and prev_step.output:
                        merged_params["previous_output"] = prev_step.output

                # Execute tool
                result = tool_executor(step.skill, step.tool, merged_params)
                step.output = result
                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.utcnow().isoformat()

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                instance.status = WorkflowStatus.PARTIAL

        # Determine final status
        failed_steps = [s for s in instance.steps if s.status == WorkflowStatus.FAILED]
        if failed_steps:
            instance.status = WorkflowStatus.PARTIAL if any(s.status == WorkflowStatus.COMPLETED for s in instance.steps) else WorkflowStatus.FAILED
        else:
            instance.status = WorkflowStatus.COMPLETED

        instance.completed_at = datetime.utcnow().isoformat()
        instance.final_output = self._aggregate_outputs(instance)
        return instance

    def _aggregate_outputs(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Aggregate all step outputs into a final result."""
        return {
            "workflow_id": instance.id,
            "workflow_type": instance.type.value,
            "description": instance.description,
            "status": instance.status.value,
            "step_results": [
                {
                    "skill": s.skill,
                    "tool": s.tool,
                    "status": s.status.value,
                    "output": s.output,
                    "error": s.error,
                    "duration_ms": self._duration_ms(s),
                }
                for s in instance.steps
            ],
            "summary": {
                "total_steps": len(instance.steps),
                "completed": sum(1 for s in instance.steps if s.status == WorkflowStatus.COMPLETED),
                "failed": sum(1 for s in instance.steps if s.status == WorkflowStatus.FAILED),
            },
        }

    def _duration_ms(self, step: WorkflowStep) -> Optional[int]:
        if step.started_at and step.completed_at:
            try:
                start = datetime.fromisoformat(step.started_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(step.completed_at.replace('Z', '+00:00'))
                return int((end - start).total_seconds() * 1000)
            except:
                return None
        return None

    def get_status(self, instance_id: str) -> Optional[WorkflowInstance]:
        return self._executions.get(instance_id)

    def list_workflows(self) -> List[WorkflowInstance]:
        return list(self._executions.values())


# ── FastAPI Router ─────────────────────────────────────────────────────────

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])

# Global engine instance
_engine = WorkflowEngine()


class CreateWorkflowRequest(BaseModel):
    workflow_type: str  # extract_visualize | compare_simulate | review_sign | full_pipeline | risk_assessment
    context: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    description: str
    steps_completed: int
    steps_total: int
    created_at: str
    completed_at: Optional[str] = None


@router.post("/create")
async def create_workflow(req: CreateWorkflowRequest):
    try:
        wf_type = WorkflowType(req.workflow_type)
    except ValueError:
        return {"error": f"Unknown workflow type: {req.workflow_type}. Available: {[t.value for t in WorkflowType]}"}

    instance = _engine.create(wf_type, req.context or {})
    return {
        "workflow_id": instance.id,
        "type": instance.type.value,
        "description": instance.description,
        "steps": [{"id": s.id, "skill": s.skill, "tool": s.tool, "status": s.status.value} for s in instance.steps],
        "status": instance.status.value,
        "created_at": instance.created_at,
    }


@router.post("/execute/{workflow_id}")
async def execute_workflow(workflow_id: str):
    """Execute a workflow. In production, this calls actual MCP tools."""
    instance = _engine.get_status(workflow_id)
    if not instance:
        return {"error": "Workflow not found"}

    # Mock executor — in production this calls VOS API / OpenClaw gateway
    def mock_executor(skill: str, tool: str, params: Dict) -> Dict:
        return {
            "skill": skill,
            "tool": tool,
            "executed": True,
            "mock": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    result = _engine.execute(workflow_id, mock_executor)
    return result.final_output


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    instance = _engine.get_status(workflow_id)
    if not instance:
        return {"error": "Workflow not found"}
    return {
        "workflow_id": instance.id,
        "type": instance.type.value,
        "status": instance.status.value,
        "description": instance.description,
        "steps": [{"id": s.id, "skill": s.skill, "tool": s.tool, "status": s.status.value} for s in instance.steps],
        "created_at": instance.created_at,
        "completed_at": instance.completed_at,
    }


@router.get("/list")
async def list_workflows():
    workflows = _engine.list_workflows()
    return {
        "workflows": [
            {
                "id": w.id,
                "type": w.type.value,
                "status": w.status.value,
                "description": w.description,
                "steps_completed": sum(1 for s in w.steps if s.status == WorkflowStatus.COMPLETED),
                "steps_total": len(w.steps),
            }
            for w in workflows
        ]
    }


@router.get("/definitions")
async def list_definitions():
    """List all available workflow templates."""
    return {
        "workflows": [
            {
                "type": wt.value,
                "description": defn["description"],
                "steps": [{"skill": s["skill"], "tool": s["tool"]} for s in defn["steps"]],
            }
            for wt, defn in WorkflowEngine.WORKFLOW_DEFINITIONS.items()
        ]
    }
