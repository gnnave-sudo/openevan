"""
Risk scoring service for Compliance Stress Lab.

Implements a weighted scoring model for regulatory risk assessment.
"""

from typing import Dict, List, Any


class RiskScoringModel:
    """
    Weighted risk scoring model for regulatory decisions.

    Dimensions and weights:
    - Regulatory trigger severity: 20%
    - Licensing uncertainty: 15%
    - Enforcement sensitivity: 15%
    - Control maturity gap: 15%
    - Evidence readiness gap: 10%
    - Cross-border complexity: 10%
    - Customer harm/conduct risk: 5%
    - AML/sanctions exposure: 5%
    - Marketing misrepresentation risk: 3%
    - Strategic materiality: 2%
    """

    DIMENSION_WEIGHTS = {
        "regulatory_trigger_severity": 0.20,
        "licensing_uncertainty": 0.15,
        "enforcement_sensitivity": 0.15,
        "control_maturity_gap": 0.15,
        "evidence_readiness_gap": 0.10,
        "cross_border_complexity": 0.10,
        "customer_harm_risk": 0.05,
        "aml_sanctions_exposure": 0.05,
        "marketing_misrepresentation_risk": 0.03,
        "strategic_materiality": 0.02,
    }

    @classmethod
    def calculate_score(
        cls,
        dimensions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate overall risk score from individual dimensions.

        Args:
            dimensions: Dict mapping dimension name to {"score": 1-5, "explanation": str}

        Returns:
            Dict with overall_score, risk_tier, dimension_breakdown, and explanation
        """
        dimension_results = []
        weighted_sum = 0.0

        for dim_name, weight in cls.DIMENSION_WEIGHTS.items():
            dim_data = dimensions.get(dim_name, {"score": 3, "explanation": "Not assessed"})
            score = max(1.0, min(5.0, float(dim_data.get("score", 3))))
            explanation = dim_data.get("explanation", "No explanation provided")

            dimension_results.append({
                "name": dim_name,
                "score": score,
                "weight": weight,
                "weighted_contribution": score * weight,
                "explanation": explanation
            })

            weighted_sum += score * weight

        # Determine risk tier
        risk_tier = cls._get_risk_tier(weighted_sum)

        return {
            "overall_score": round(weighted_sum, 2),
            "risk_tier": risk_tier,
            "max_possible": 5.0,
            "dimension_breakdown": dimension_results,
            "summary": cls._generate_summary(dimension_results, risk_tier)
        }

    @staticmethod
    def _get_risk_tier(score: float) -> str:
        """Map score to risk tier."""
        if score < 2.0:
            return "low"
        elif score < 3.0:
            return "medium"
        elif score < 4.0:
            return "high"
        else:
            return "critical"

    @staticmethod
    def _generate_summary(dimensions: List[Dict], risk_tier: str) -> str:
        """Generate a human-readable summary of the risk assessment."""
        # Find highest contributing dimensions
        sorted_dims = sorted(dimensions, key=lambda d: d["weighted_contribution"], reverse=True)
        top_3 = sorted_dims[:3]

        summary = f"Overall risk assessment: {risk_tier.upper()}. "
        summary += "Primary risk drivers: "

        drivers = []
        for dim in top_3:
            name = dim["name"].replace("_", " ").title()
            drivers.append(f"{name} (score: {dim['score']})")

        summary += "; ".join(drivers) + "."

        return summary

    @classmethod
    def get_default_dimensions(cls) -> Dict[str, Dict[str, Any]]:
        """Get default dimension structure with neutral scores."""
        return {
            dim: {"score": 3, "explanation": "Default assessment"}
            for dim in cls.DIMENSION_WEIGHTS.keys()
        }


def _map_risk_rating_to_score(risk_rating: str) -> float:
    """Map risk rating string to numeric score."""
    mapping = {
        "low": 1.5,
        "medium": 2.5,
        "high": 4.0,
        "critical": 5.0
    }
    return mapping.get(risk_rating.lower(), 3.0)


def _estimate_control_gap_score(control_gaps: List[str]) -> float:
    """Estimate control maturity gap score from number/severity of gaps."""
    count = len(control_gaps)
    if count == 0:
        return 1.0
    elif count <= 2:
        return 2.5
    elif count <= 4:
        return 3.5
    else:
        return 4.5


def _estimate_evidence_gap_score(evidence_needed: List[str]) -> float:
    """Estimate evidence readiness gap score from evidence requirements."""
    count = len(evidence_needed)
    if count == 0:
        return 1.0
    elif count <= 3:
        return 2.5
    elif count <= 6:
        return 3.5
    else:
        return 4.5


def _estimate_action_urgency_score(actions: list) -> float:
    """Estimate urgency from remediation actions."""
    count = len(actions)
    p0_count = sum(1 for a in actions if isinstance(a, dict) and a.get("priority") == "P0")
    if count == 0:
        return 1.0
    if p0_count > 0:
        return min(5.0, 3.5 + p0_count * 0.5)
    return min(5.0, 2.0 + count * 0.3)


def _estimate_obligation_severity_score(obligations: list) -> float:
    """Estimate severity from decisive obligations."""
    count = len(obligations)
    if count == 0:
        return 1.0
    if count >= 3:
        return 4.5
    if count >= 2:
        return 3.5
    return 2.5


def score_from_adjudication(adjudication: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive risk scores from an adjudication result.

    This is a helper to convert adjudication outputs into structured
    risk dimension scores for consistency.
    """
    dimensions = {
        "regulatory_trigger_severity": {
            "score": _map_risk_rating_to_score(adjudication.get("risk_rating", "medium")),
            "explanation": f"Risk rating: {adjudication.get('risk_rating', 'unknown')}"
        },
        "control_maturity_gap": {
            "score": _estimate_control_gap_score(adjudication.get("key_control_gaps", [])),
            "explanation": f"Control gaps identified: {len(adjudication.get('key_control_gaps', []))}"
        },
        "evidence_readiness_gap": {
            "score": _estimate_evidence_gap_score(adjudication.get("evidence_needed", [])),
            "explanation": f"Evidence items needed: {len(adjudication.get('evidence_needed', []))}"
        },
        # Default values for dimensions not directly inferable
        "licensing_uncertainty": {"score": 3, "explanation": "Not directly assessed"},
        "enforcement_sensitivity": {"score": 3, "explanation": "Not directly assessed"},
        "cross_border_complexity": {"score": 3, "explanation": "Not directly assessed"},
        "customer_harm_risk": {"score": 3, "explanation": "Not directly assessed"},
        "aml_sanctions_exposure": {"score": 3, "explanation": "Not directly assessed"},
        "marketing_misrepresentation_risk": {"score": 3, "explanation": "Not directly assessed"},
        "strategic_materiality": {"score": 3, "explanation": "Not directly assessed"},
    }

    return RiskScoringModel.calculate_score(dimensions)


class RiskScoringEngine:
    """
    Production risk scoring engine with per-dimension inference from adjudications.

    Provides the interface expected by the scoring API endpoint.
    """

    dimensions = list(RiskScoringModel.DIMENSION_WEIGHTS.keys())
    weights = RiskScoringModel.DIMENSION_WEIGHTS

    def calculate_dimension_scores(
        self,
        risk_rating: str,
        key_control_gaps: list,
        evidence_needed: list,
        remediation_actions: list = None,
        decisive_obligations: list = None,
    ) -> dict:
        """
        Infer dimension scores from adjudication data.

        Args:
            risk_rating: low/medium/high/critical
            key_control_gaps: List of control gap descriptions
            evidence_needed: List of evidence items
            remediation_actions: List of remediation actions
            decisive_obligations: List of decisive obligations

        Returns:
            Dict of dimension name -> score (0-5)
        """
        base = _map_risk_rating_to_score(risk_rating)
        control_score = _estimate_control_gap_score(key_control_gaps)
        evidence_score = _estimate_evidence_gap_score(evidence_needed)
        action_score = _estimate_action_urgency_score(remediation_actions or [])
        obligation_score = _estimate_obligation_severity_score(decisive_obligations or [])

        return {
            "regulatory_trigger_severity": round(base, 2),
            "licensing_uncertainty": round(min(5.0, base * 0.9), 2),
            "enforcement_sensitivity": round(min(5.0, base * 0.95), 2),
            "control_maturity_gap": round(control_score, 2),
            "evidence_readiness_gap": round(evidence_score, 2),
            "cross_border_complexity": round(3.0, 2),  # Default until jurisdiction data wired
            "customer_harm_risk": round(min(5.0, base * 0.7), 2),
            "aml_sanctions_exposure": round(min(5.0, base * 0.85), 2),
            "marketing_misrepresentation_risk": round(3.0, 2),
            "strategic_materiality": round(min(5.0, obligation_score), 2),
        }

    def calculate_weighted_score(self, dimension_scores: dict) -> float:
        """Calculate weighted overall score from dimension scores."""
        total = 0.0
        for dim, weight in self.weights.items():
            total += dimension_scores.get(dim, 0) * weight
        return round(total, 2)

    def get_risk_rating(self, overall_score: float) -> str:
        """Map overall score to risk rating."""
        return RiskScoringModel._get_risk_tier(overall_score)

    def generate_risk_summary(self, dimension_scores: dict) -> dict:
        """Generate human-readable risk summary."""
        sorted_dims = sorted(
            dimension_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_3 = sorted_dims[:3]
        top_concerns = [
            f"{name.replace('_', ' ').title()}: {score}"
            for name, score in top_3
        ]

        overall = self.calculate_weighted_score(dimension_scores)
        rating = self.get_risk_rating(overall)

        rec_map = {
            "low": "proceed",
            "medium": "proceed_with_conditions",
            "high": "hold",
            "critical": "no_go",
        }

        return {
            "overall_score": overall,
            "risk_rating": rating,
            "top_concerns": top_concerns,
            "recommendation": rec_map.get(rating, "hold"),
            "explanation": f"Overall risk: {rating.upper()}. Primary drivers: {'; '.join(top_concerns)}.",
        }


def calculate_overall_rating(adjudications: list) -> dict:
    """Aggregate risk ratings across all adjudications."""
    if not adjudications:
        return {"risk_rating": "medium", "recommendation": "hold", "top_risks": [], "required_controls": []}

    ratings = [a.get("risk_rating", "medium") for a in adjudications]
    recommendations = [a.get("recommendation", "hold") for a in adjudications]

    # Map to numeric
    rmap = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    scores = [rmap.get(r, 2) for r in ratings]
    avg = sum(scores) / len(scores)

    # Determine overall rating
    if avg >= 3.5:
        overall = "critical"
    elif avg >= 2.5:
        overall = "high"
    elif avg >= 1.5:
        overall = "medium"
    else:
        overall = "low"

    # Determine recommendation (most conservative)
    rec_priority = {"no_go": 4, "hold": 3, "proceed_with_conditions": 2, "proceed": 1, "escalate": 5}
    best_rec = min(recommendations, key=lambda r: rec_priority.get(r, 3))

    # Collect top risks and controls
    all_risks = []
    all_controls = []
    for a in adjudications:
        all_risks.extend(a.get("key_control_gaps", []))
        all_controls.extend([ra.get("action") for ra in a.get("remediation_actions", []) if isinstance(ra, dict)])

    return {
        "risk_rating": overall,
        "recommendation": best_rec,
        "top_risks": list(dict.fromkeys(all_risks))[:5],
        "required_controls": list(dict.fromkeys(all_controls))[:5],
    }
