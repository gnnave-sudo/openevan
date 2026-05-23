"""
Centralized mock data factory for simulation pipeline stages.

Eliminates duplicated mock data blocks across service files.
Uses a registry pattern for maintainable, testable mock generation.
"""

import random
import logging
from typing import Any, Dict, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Registry ────────────────────────────────────────────────────────────────

_MOCK_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_mock(name: str) -> Callable:
    """Decorator to register a mock data generator."""
    def decorator(func: Callable) -> Callable:
        _MOCK_REGISTRY[name] = func
        return func
    return decorator


def get_mock(name: str, **kwargs) -> Any:
    """Generate mock data by name."""
    if name not in _MOCK_REGISTRY:
        raise KeyError(f"No mock generator registered for '{name}'")
    return _MOCK_REGISTRY[name](**kwargs)


# ── Normalized Case Mock ────────────────────────────────────────────────────

@register_mock("normalized_case")
def mock_normalized_case(**kwargs) -> Dict[str, Any]:
    """Mock normalized case facts."""
    return {
        "activity_name": kwargs.get("activity_name", "Test Activity"),
        "activity_summary": kwargs.get("activity_summary", "A test activity for mock simulation"),
        "entities": kwargs.get("entities", []),
        "target_users": kwargs.get("target_users", ["retail"]),
        "key_flows": {
            "user_flow": kwargs.get("user_flow", "User signs up → deposits funds → trades"),
            "money_flow": kwargs.get("money_flow", "Fiat → Crypto wallet → Exchange"),
            "custody_flow": kwargs.get("custody_flow", "Third-party custodian holds assets"),
            "marketing_flow": kwargs.get("marketing_flow", "Social media ads → Landing page"),
        },
        "controls_in_place": kwargs.get("controls_in_place", []),
        "assumptions": kwargs.get("assumptions", []),
        "known_unknowns": kwargs.get("known_unknowns", ["Regulatory interpretation pending"]),
    }


# ── Obligations Mock ────────────────────────────────────────────────────────

@register_mock("obligations")
def mock_obligations(jurisdiction: str = "SG", **kwargs) -> List[Dict[str, Any]]:
    """Mock obligations for a jurisdiction."""
    templates = {
        "SG": [
            {
                "id": "gen-001",
                "jurisdiction": "SG",
                "regulator": "MAS",
                "source_type": "Act",
                "source_name": "Payment Services Act",
                "citation": "Section 5(1)",
                "obligation_title": "License Requirement",
                "obligation_text": "No person shall carry on a business of providing payment services unless licensed",
                "trigger_conditions": ["payment_service", "regulated_activity"],
                "required_controls": ["licensing", "compliance_officer"],
                "required_evidence": ["license_certificate", "compliance_framework"],
                "severity": "high",
                "tags": ["licensing", "mandatory"],
            },
        ],
        "HK": [
            {
                "id": "gen-002",
                "jurisdiction": "HK",
                "regulator": "SFC",
                "source_type": "Guideline",
                "source_name": "VATP Guidelines",
                "citation": "Paragraph 3.2",
                "obligation_title": "Custody of Client Assets",
                "obligation_text": "Virtual asset trading platform operators must establish robust custody arrangements",
                "trigger_conditions": ["custody", "client_assets"],
                "required_controls": ["cold_storage", "multi_sig"],
                "required_evidence": ["custody_policy", "insurance_coverage"],
                "severity": "high",
                "tags": ["custody", "security"],
            },
        ],
    }
    return templates.get(jurisdiction, templates["SG"])


# ── Scenarios Mock ──────────────────────────────────────────────────────────

@register_mock("scenarios")
def mock_scenarios(**kwargs) -> List[Dict[str, Any]]:
    """Mock generated scenarios."""
    return [
        {
            "scenario_name": "Licensing Perimeter Stress Test",
            "scenario_type": "licensing",
            "scenario_description": "Tests whether the proposed activity requires a license",
            "trigger_event": "Regulator requests licensing status verification",
            "seriousness": "high",
            "affected_obligation_ids": ["gen-001"],
            "timeline_pressure": "short",
        },
        {
            "scenario_name": "AML/CFT Exposure Test",
            "scenario_type": "aml",
            "scenario_description": "Evaluates money laundering risks in the activity design",
            "trigger_event": "Unusual transaction pattern detected",
            "seriousness": "critical",
            "affected_obligation_ids": ["gen-001", "gen-002"],
            "timeline_pressure": "immediate",
        },
        {
            "scenario_name": "Marketing & Consumer Protection",
            "scenario_type": "marketing",
            "scenario_description": "Assesses marketing compliance with consumer protection rules",
            "trigger_event": "Marketing campaign launched targeting retail users",
            "seriousness": "medium",
            "affected_obligation_ids": ["gen-001"],
            "timeline_pressure": "medium",
        },
    ]


# ── Agent Outputs Mock ──────────────────────────────────────────────────────

@register_mock("agent_outputs")
def mock_agent_outputs(scenario: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Mock agent execution results for a scenario."""
    scen_name = scenario.get("scenario_name", "Unknown")
    return {
        "agents": {
            "business_advocate": {
                "output": {
                    "position_summary": f"Business case supports proceeding with {scen_name}",
                    "key_points": ["Revenue opportunity", "Market demand", "Competitive necessity"],
                    "supporting_obligations": [],
                    "control_analysis": [],
                    "assumptions_relied_on": [],
                    "vulnerabilities": [],
                    "recommended_outcome": "proceed",
                },
                "raw_output": "Mock business advocate output",
                "error": None,
            },
            "compliance_reviewer": {
                "output": {
                    "position_summary": f"Compliance gaps identified in {scen_name}",
                    "key_points": ["KYC gap", "Monitoring deficiency", "Policy outdated"],
                    "supporting_obligations": [{"obligation_id": "gen-001", "citation": "Section 5(1)", "relevance": "direct"}],
                    "control_analysis": [{"control_name": "KYC", "assessment": "partial", "reason": "Missing PEP checks"}],
                    "assumptions_relied_on": [],
                    "vulnerabilities": ["PEP screening gap"],
                    "recommended_outcome": "hold",
                },
                "raw_output": "Mock compliance reviewer output",
                "error": None,
            },
            "regulator_proxy": {
                "output": {
                    "position_summary": f"Regulator likely to object to {scen_name}",
                    "key_points": ["No license", "Inadequate custody", "Weak AML controls"],
                    "supporting_obligations": [{"obligation_id": "gen-001", "citation": "Section 5(1)", "relevance": "direct"}],
                    "control_analysis": [{"control_name": "Custody", "assessment": "weak", "reason": "Third-party without insurance"}],
                    "assumptions_relied_on": [],
                    "vulnerabilities": ["No insurance", "Single custodian"],
                    "recommended_outcome": "no_go",
                },
                "raw_output": "Mock regulator proxy output",
                "error": None,
            },
        }
    }


# ── Adjudication Mock ───────────────────────────────────────────────────────

@register_mock("adjudication")
def mock_adjudication(scenario: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Mock adjudication result."""
    seriousness = scenario.get("seriousness", "medium")
    rating_map = {"low": "low", "medium": "medium", "high": "high", "critical": "critical"}
    rec_map = {"low": "proceed", "medium": "proceed_with_conditions", "high": "hold", "critical": "no_go"}
    return {
        "scenario_name": scenario.get("scenario_name", "Unknown"),
        "risk_rating": rating_map.get(seriousness, "medium"),
        "likely_regulatory_concern": "Licensing and AML compliance gaps",
        "decisive_facts": ["No current license", "Third-party custody without insurance"],
        "decisive_obligations": [{"obligation_id": "gen-001", "citation": "Section 5(1)", "reason": "Primary licensing requirement"}],
        "key_control_gaps": ["KYC PEP screening", "Custody insurance", "Transaction monitoring"],
        "evidence_needed": ["License application status", "Custody insurance policy", "AML policy"],
        "remediation_actions": [
            {"action": "Apply for payment services license", "priority": "P0", "owner": "Legal"},
            {"action": "Obtain custody insurance", "priority": "P1", "owner": "Ops"},
        ],
        "recommendation": rec_map.get(seriousness, "hold"),
        "confidence_score": 0.75,
    }


# ── Final Report Mock ────────────────────────────────────────────────────────

@register_mock("final_report")
def mock_final_report(**kwargs) -> Dict[str, Any]:
    """Mock final synthesized report."""
    return {
        "executive_summary": "Mock executive summary: The proposed activity presents high regulatory risk due to licensing gaps and inadequate AML controls. Proceed only after obtaining MAS license and implementing required controls.",
        "overall_risk_rating": "high",
        "final_recommendation": "hold",
        "cross_scenario_findings": [
            "Licensing gap consistent across all scenarios",
            "AML controls universally rated as weak",
            "Custody arrangements need strengthening",
        ],
        "top_risks": [
            "Operating without required license (CRITICAL)",
            "Inadequate AML transaction monitoring (HIGH)",
            "Insufficient custody insurance coverage (HIGH)",
        ],
        "required_controls": [
            "Apply for and obtain MAS payment services license",
            "Implement real-time transaction monitoring with SAR filing",
            "Obtain comprehensive custody insurance policy",
            "Enhance KYC with PEP/sanctions screening",
        ],
        "evidence_checklist": [
            "License application acknowledgment",
            "Updated AML/CFT policy",
            "Custody insurance certificate",
            "KYC procedure documentation",
        ],
        "management_conditions": [
            "Do not launch until license obtained",
            "Quarterly compliance review",
            "External audit within 6 months",
        ],
        "open_questions": [
            "What is expected timeline for license approval?",
            "Can operations commence under exemption?",
        ],
    }
