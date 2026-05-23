"""
Layer 5: Management Output Generator
Produces decision memos, risk heatmaps, escalation lists, and control priorities.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models import (
    ControlInvestment,
    DecisionMemo,
    EscalationItem,
    StressLabResult,
)

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Generates management-ready outputs from stress test results."""

    def generate_decision_memo(
        self, stress_result: StressLabResult
    ) -> DecisionMemo:
        """Generate a decision memo from a stress test result."""
        logger.info(
            "Generating decision memo for stress result %s", stress_result.id
        )
        title = self._generate_title(stress_result)
        executive_summary = self._generate_executive_summary(stress_result)
        risk_assessment = self._generate_risk_assessment(stress_result)
        recommendations = self._generate_recommendations(stress_result)
        next_steps = self._generate_next_steps(stress_result)
        return DecisionMemo(
            stress_result_id=stress_result.id,
            title=title,
            executive_summary=executive_summary,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            next_steps=next_steps,
            generated_at=datetime.utcnow(),
        )

    def generate_risk_heatmap(
        self, stress_results: List[StressLabResult]
    ) -> List[Dict[str, Any]]:
        """Generate risk heatmap data from stress results."""
        jurisdiction_scores: Dict[str, List[float]] = {}
        for result in stress_results:
            for scenario in result.scenarios:
                jurisdiction = "Multi-Jurisdiction"
                for dim, val in scenario.risk_score.dimensions.items():
                    key = f"{jurisdiction}:{dim}"
                    if key not in jurisdiction_scores:
                        jurisdiction_scores[key] = []
                    jurisdiction_scores[key].append(val)
        heatmap: List[Dict[str, Any]] = []
        seen: set = set()
        for result in stress_results:
            for scenario in result.scenarios:
                jurisdiction = "Multi-Jurisdiction"
                if jurisdiction not in seen:
                    seen.add(jurisdiction)
                    for dim, val in scenario.risk_score.dimensions.items():
                        heatmap.append(
                            {
                                "jurisdiction": jurisdiction,
                                "dimension": dim,
                                "score": round(val, 1),
                                "risk_level": self._risk_level(val),
                                "recommendation": scenario.recommendation,
                            }
                        )
        return heatmap

    def generate_escalation_list(
        self, stress_results: List[StressLabResult]
    ) -> List[EscalationItem]:
        """Generate escalation items from stress results."""
        escalations: List[EscalationItem] = []
        for result in stress_results:
            if result.final_risk_rating > 70:
                escalations.append(
                    EscalationItem(
                        priority="P0",
                        title=f"Critical Risk: Composite {result.final_risk_rating:.0f}/100 — Immediate Board Escalation",
                        description=f"CSL stress test produced a composite risk score of {result.final_risk_rating:.0f}/100 with final recommendation {result.final_recommendation}. "
                        f"Decisive obligations: {', '.join(result.decisive_obligations[:2])}. "
                        f"Control gaps: {', '.join(result.key_control_gaps[:2])}.",
                        jurisdiction="Multi-Jurisdiction",
                        due_date=datetime.utcnow() + timedelta(days=3),
                        status="open",
                    )
                )
            elif result.final_risk_rating > 50:
                escalations.append(
                    EscalationItem(
                        priority="P1",
                        title=f"Elevated Risk: Composite {result.final_risk_rating:.0f}/100 — Senior Management Review",
                        description=f"CSL stress test produced a composite risk score of {result.final_risk_rating:.0f}/100. "
                        f"Recommendation: {result.final_recommendation}. Key gaps: {', '.join(result.key_control_gaps[:2])}.",
                        jurisdiction="Multi-Jurisdiction",
                        due_date=datetime.utcnow() + timedelta(days=7),
                        status="open",
                    )
                )
            for gap in result.key_control_gaps[:3]:
                if "material" in gap.lower() or "no " in gap.lower():
                    escalations.append(
                        EscalationItem(
                            priority="P1",
                            title=f"Control Gap: {gap[:80]}",
                            description=f"Identified control gap: {gap}. Remediation required before launch.",
                            jurisdiction="Multi-Jurisdiction",
                            due_date=datetime.utcnow() + timedelta(days=14),
                            status="open",
                        )
                    )
        return escalations

    def generate_control_priorities(
        self, stress_results: List[StressLabResult]
    ) -> List[ControlInvestment]:
        """Generate prioritized control investments from stress results."""
        controls: List[ControlInvestment] = []
        dimension_totals: Dict[str, float] = {}
        for result in stress_results:
            for scenario in result.scenarios:
                for dim, val in scenario.risk_score.dimensions.items():
                    dimension_totals[dim] = dimension_totals.get(dim, 0) + val
        sorted_dims = sorted(
            dimension_totals.items(), key=lambda x: x[1], reverse=True
        )
        control_map = {
            "licensing_risk": ("Enhanced Licensing Framework", "$150K-$300K"),
            "aml_risk": ("Advanced AML/CFT System", "$200K-$500K"),
            "conduct_risk": ("Conduct Risk Management Program", "$100K-$250K"),
            "operational_risk": ("Operational Resilience Framework", "$250K-$400K"),
            "reputational_risk": ("Reputational Risk Monitoring", "$80K-$150K"),
            "regulatory_risk": ("Regulatory Intelligence & Horizon Scanning", "$120K-$200K"),
            "financial_risk": ("Financial Risk Management & Capital Adequacy", "$180K-$350K"),
            "cross_border_risk": ("Multi-Jurisdiction Compliance Platform", "$300K-$600K"),
            "consumer_protection_risk": ("Consumer Protection & Disclosure Framework", "$100K-$200K"),
            "enforcement_risk": ("Enforcement Response & Legal Defense Protocol", "$150K-$300K"),
        }
        for rank, (dim, total) in enumerate(sorted_dims[:7], start=1):
            name, cost = control_map.get(dim, ("General Control Enhancement", "$100K-$200K"))
            controls.append(
                ControlInvestment(
                    control_name=name,
                    priority=rank,
                    estimated_cost=cost,
                    risk_reduction=round(
                        min(40.0, 5.0 + (total / max(len(stress_results), 1))), 2
                    ),
                    jurisdictions=["Multi-Jurisdiction"],
                )
            )
        return controls

    def _generate_title(self, result: StressLabResult) -> str:
        risk_label = "LOW" if result.final_risk_rating <= 30 else (
            "MODERATE" if result.final_risk_rating <= 60 else "HIGH"
        )
        return (
            f"Regulatory Risk Assessment — {risk_label} RISK "
            f"({result.final_risk_rating:.0f}/100) — Recommendation: {result.final_recommendation}"
        )

    def _generate_executive_summary(self, result: StressLabResult) -> str:
        scenario_summary = "\n".join(
            f"  - Scenario {s.scenario_number}: Risk={s.risk_score.overall:.0f}/100, "
            f"Decision={s.recommendation}"
            for s in result.scenarios
        )
        return (
            f"The Compliance Stress Lab (CSL) evaluated this proposal across "
            f"{len(result.scenarios)} scenarios with 4-agent adversarial simulation. "
            f"The composite risk score is {result.final_risk_rating:.0f}/100, resulting in a "
            f"{result.final_recommendation} recommendation.\n\n"
            f"Scenario Results:\n{scenario_summary}\n\n"
            f"Key decisive obligations: {len(result.decisive_obligations)}. "
            f"Control gaps identified: {len(result.key_control_gaps)}. "
            f"Regulator objections: {len(result.regulator_objections)}."
        )

    def _generate_risk_assessment(self, result: StressLabResult) -> str:
        lines: List[str] = [
            "## Composite Risk Assessment",
            "",
            f"**Overall Risk Rating:** {result.final_risk_rating:.0f}/100 ({self._risk_level(result.final_risk_rating)})",
            "",
            "### Dimension Breakdown",
            "",
        ]
        for scenario in result.scenarios:
            lines.append(
                f"#### Scenario {scenario.scenario_number} (Decision: {scenario.recommendation})"
            )
            for dim, val in scenario.risk_score.dimensions.items():
                lines.append(
                    f"- {dim}: {val:.0f}/100 [{self._risk_level(val)}]"
                )
            lines.append("")
        if result.decisive_obligations:
            lines.append("### Decisive Obligations")
            for obl in result.decisive_obligations:
                lines.append(f"- {obl}")
            lines.append("")
        if result.key_control_gaps:
            lines.append("### Key Control Gaps")
            for gap in result.key_control_gaps:
                lines.append(f"- {gap}")
        return "\n".join(lines)

    def _generate_recommendations(self, result: StressLabResult) -> List[str]:
        recs: List[str] = []
        if result.final_recommendation == "PROCEED":
            recs.append("Proceed with standard monitoring and quarterly risk reviews.")
            recs.append("Document all risk acceptance decisions with board sign-off.")
        elif result.final_recommendation == "HOLD":
            recs.append("HOLD launch pending remediation of top 2 risk dimensions.")
            recs.append("Engage external counsel for targeted legal opinion on decisive obligations.")
            recs.append("Implement enhanced controls for identified gaps before re-submission.")
            recs.append("Schedule follow-up CSL stress test within 60 days.")
        else:
            recs.append("NO-GO: Do not proceed with current structure.")
            recs.append("Fundamental restructuring required — engage counsel for alternative structure.")
            recs.append("Consider jurisdictional shift to lower-risk regulatory environment.")
            recs.append("Re-submit only after material control framework upgrade.")
        if result.final_risk_rating > 60:
            recs.append("Escalate to Board Risk Committee immediately.")
        return recs

    def _generate_next_steps(self, result: StressLabResult) -> List[str]:
        steps: List[str] = [
            f"1. Distribute decision memo to all stakeholders within 48 hours",
            f"2. Schedule CSL re-run in 30-60 days to verify remediation progress",
            f"3. Update risk register with {len(result.key_control_gaps)} new control items",
            f"4. Archive all simulation evidence for audit trail",
        ]
        if result.evidence_checklist:
            steps.append(
                f"5. Collect {len(result.evidence_checklist)} evidence items per checklist"
            )
        if result.regulator_objections:
            steps.append(
                f"6. Prepare response to {len(result.regulator_objections)} anticipated regulator objections"
            )
        steps.append(
            "7. Update regulatory intelligence dashboard with latest risk posture"
        )
        return steps

    def _risk_level(self, score: float) -> str:
        if score <= 30:
            return "LOW"
        elif score <= 45:
            return "MODERATE-LOW"
        elif score <= 60:
            return "MODERATE"
        elif score <= 75:
            return "HIGH"
        else:
            return "CRITICAL"
