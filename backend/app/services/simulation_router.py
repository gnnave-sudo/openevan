"""
Simulation Router — Decides which CSL simulation mode to run based on input.

Extracted from the Hermes Bridge. Provides 7 simulation modes with
keyword-based and LLM-based mode detection.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SimulationRouter:
    """Decides which CSL simulation mode to run based on input characteristics."""

    MODES = [
        {
            "key": "product_launch",
            "name": "Product Launch Stress Test",
            "description": "Comprehensive stress test for new product launches",
            "trigger_keywords": ["launch", "product", "new", "introduce", "offer"],
            "required_inputs": ["fact_pattern", "jurisdictions", "product_types"],
            "default_agents": ["business_advocate", "compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "general"
        },
        {
            "key": "licensing_perimeter",
            "name": "Licensing Perimeter Stress Test",
            "description": "Tests whether current licenses cover proposed activities",
            "trigger_keywords": ["license", "perimeter", "authorization", "regulated", "permission"],
            "required_inputs": ["fact_pattern", "jurisdictions"],
            "default_agents": ["compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "licensing"
        },
        {
            "key": "regulator_letter",
            "name": "Regulator Letter Response",
            "description": "Prepares response to regulatory inquiry or letter",
            "trigger_keywords": ["letter", "inquiry", "response", "MAS", "SFC", "FCA", "question"],
            "required_inputs": ["fact_pattern", "jurisdictions", "risk_focus"],
            "default_agents": ["compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "regulatory_engagement"
        },
        {
            "key": "incident_breach",
            "name": "Incident / Breach Simulation",
            "description": "Simulates regulator response to security incident or breach",
            "trigger_keywords": ["breach", "incident", "hack", "loss", "exploit", "failure"],
            "required_inputs": ["fact_pattern", "jurisdictions"],
            "default_agents": ["compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "technology_risk"
        },
        {
            "key": "marketing_review",
            "name": "Marketing Campaign Review",
            "description": "Reviews marketing materials for compliance with fair dealing rules",
            "trigger_keywords": ["marketing", "advertising", "campaign", "promotion", "social media"],
            "required_inputs": ["fact_pattern", "jurisdictions"],
            "default_agents": ["business_advocate", "compliance_reviewer", "regulator_proxy"],
            "default_risk_focus": "marketing"
        },
        {
            "key": "vendor_risk",
            "name": "Outsourcing / Vendor Risk Review",
            "description": "Evaluates third-party and outsourcing arrangements",
            "trigger_keywords": ["vendor", "outsource", "third party", "custody", "Fireblocks", "service provider"],
            "required_inputs": ["fact_pattern", "jurisdictions"],
            "default_agents": ["compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "operational"
        },
        {
            "key": "counsel_challenge",
            "name": "Counsel Memo Challenge Review",
            "description": "Compares counsel advice against structured stress-test output",
            "trigger_keywords": ["counsel", "memo", "advice", "opinion", "legal advice"],
            "required_inputs": ["fact_pattern", "jurisdictions", "counsel_memo"],
            "default_agents": ["compliance_reviewer", "regulator_proxy", "adjudicator"],
            "default_risk_focus": "general"
        }
    ]

    def __init__(self):
        pass

    def determine_mode(self, title: str, fact_pattern: str, risk_focus: Optional[str] = None) -> Dict[str, Any]:
        """Determine which simulation mode to use based on input text."""

        text = f"{title} {fact_pattern}".lower()

        # Score each mode
        mode_scores = []
        for mode in self.MODES:
            score = 0
            for keyword in mode["trigger_keywords"]:
                if keyword.lower() in text:
                    score += 1
            if risk_focus and risk_focus.lower() in mode["key"]:
                score += 2
            mode_scores.append({"mode": mode, "score": score})

        # Sort by score
        mode_scores.sort(key=lambda x: x["score"], reverse=True)

        best = mode_scores[0]

        return {
            "mode_key": best["mode"]["key"],
            "mode_name": best["mode"]["name"],
            "confidence": min(best["score"] / 3, 1.0),
            "all_scores": [
                {"key": m["mode"]["key"], "name": m["mode"]["name"], "score": m["score"]}
                for m in mode_scores[:3]
            ],
            "default_agents": best["mode"]["default_agents"],
            "default_risk_focus": best["mode"]["default_risk_focus"],
            "required_inputs": best["mode"]["required_inputs"]
        }

    def list_modes(self) -> List[Dict[str, Any]]:
        """Return all available simulation modes."""
        return [
            {
                "key": mode["key"],
                "name": mode["name"],
                "description": mode["description"],
                "required_inputs": mode["required_inputs"],
                "default_agents": mode["default_agents"],
                "default_risk_focus": mode["default_risk_focus"],
            }
            for mode in self.MODES
        ]


# Singleton
_simulation_router: Optional[SimulationRouter] = None


def get_simulation_router() -> SimulationRouter:
    global _simulation_router
    if _simulation_router is None:
        _simulation_router = SimulationRouter()
    return _simulation_router
