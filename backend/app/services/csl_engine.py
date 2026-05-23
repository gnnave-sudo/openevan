"""
Layer 2: Compliance Stress Lab (CSL) — 4-Agent Simulation Engine
Generates 3-5 regulatory stress-test scenarios with full agent positions,
10-dimension risk scoring, and weighted aggregation.

Integrates RiskScoringEngine for proper weighted 10-dimension risk scoring.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.models import (
    AgentPositions,
    FactPacket,
    RiskScore,
    SimulationScenario,
    StressLabResult,
)
from app.services.scoring_service import RiskScoringEngine

logger = logging.getLogger(__name__)

# ── Scenario templates by product type ────────────────────────────────────────

SCENARIO_CONTEXTS = {
    "Virtual Asset Exchange": [
        "Market manipulation risk through wash trading and layering on a new BTC-USD perpetual futures contract.",
        "Insolvency event scenario: exchange holds 40% of customer assets in hot wallets during a market downturn.",
        "New retail-facing spot trading product with 100x leverage and insufficient margin controls.",
        "Cross-listing of unregistered securities tokens across 3 jurisdictions simultaneously.",
        "Introduction of staking-as-a-service without clear custody segregation.",
    ],
    "Custody": [
        "Cold wallet private key management: single-sig scheme with keys stored in one geographic location.",
        "Insolvency scenario: custodian commingles operational and customer assets.",
        "Insurance coverage gap: only 30% of AUM covered against theft/hack events.",
        "Sub-custody arrangement with unregulated third-party in offshore jurisdiction.",
    ],
    "DeFi": [
        "Smart contract vulnerability: unaudited lending protocol handling $50M TVL.",
        "Governance token concentration: founding team controls 60% of voting power.",
        "Regulatory capture scenario: DAO structure deemed to require VASP licensing.",
    ],
    "default": [
        "New product launch without completing full regulatory licensing review.",
        "Cross-border expansion into jurisdiction with ambiguous cryptoasset classification.",
        "Marketing campaign targets retail investors with high-risk yield products.",
        "Partnership with unlicensed third-party for KYC/AML onboarding.",
        "Delay in implementing Travel Rule compliance past regulatory deadline.",
    ],
}

BUSINESS_ARGUMENTS = [
    "The revenue opportunity ($12M ARR) justifies the measured risk, and our phased rollout limits exposure.",
    "Competitors are already live in this segment; regulatory clarity is expected within 6-12 months.",
    "Our legal opinion confirms no licensing trigger applies under current interpretation.",
    "We have precedent: 3 similar products launched successfully in comparable jurisdictions.",
    "Customer demand is overwhelming; delaying further risks market share erosion.",
]

COMPLIANCE_ARGUMENTS = [
    "The licensing gap is material: operating without authorisation exposes the firm to criminal liability.",
    "AML controls are not production-ready; transaction monitoring rules are still in QA.",
    "The risk assessment does not account for recent enforcement actions against 2 comparable firms.",
    "Insurance and capital adequacy requirements are not yet satisfied.",
    "Third-party due diligence is incomplete; reliance on vendor attestations is insufficient.",
]

REGULATOR_ARGUMENTS = [
    "This product structure mirrors cases where we issued public reprimands and $2M fines.",
    "Consumer harm potential is high: retail investors may lose principal with no recourse.",
    "Cross-border arrangements complicate supervisory coordination and increase systemic risk.",
    "The firm has insufficient track record: we would require 12 months of audited controls before approval.",
    "Self-assessment is not a substitute for independent audit or regulatory review.",
]

ADJUDICATOR_ARGUMENTS = [
    "Balancing innovation against consumer protection, a conditional licence with enhanced monitoring is the proportionate outcome.",
    "The business case is compelling but the control gaps are real; phased approval with milestones is appropriate.",
    "Prima facie, the licensing requirement is engaged; the firm should seek in-principle approval before launch.",
    "Given enforcement precedent, proceeding without remediation carries unacceptable regulatory risk.",
    "The risk matrix supports a conditional PROCEED only if specific remedial conditions are met within 90 days.",
]

RISK_DIMENSIONS = [
    "licensing_risk",
    "aml_risk",
    "conduct_risk",
    "operational_risk",
    "reputational_risk",
    "regulatory_risk",
    "financial_risk",
    "cross_border_risk",
    "consumer_protection_risk",
    "enforcement_risk",
]


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _pick_contexts(product_class: str, n: int) -> List[str]:
    pool = SCENARIO_CONTEXTS.get(product_class, SCENARIO_CONTEXTS["default"])
    if len(pool) >= n:
        return random.sample(pool, n)
    extended = pool * ((n // len(pool)) + 1)
    return random.sample(extended, n)


class CSLEngine:
    """4-agent compliance stress-test simulation engine."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self._scoring_engine = RiskScoringEngine()

    def run_stress_test(self, fact_packet: FactPacket) -> StressLabResult:
        """Run a full CSL stress test on a FactPacket."""
        logger.info(
            "Running CSL stress test for fact packet %s (%s)",
            fact_packet.id,
            fact_packet.product_class,
        )
        num_scenarios = random.randint(3, 5)
        contexts = _pick_contexts(
            fact_packet.product_class, num_scenarios
        )
        scenarios: List[SimulationScenario] = []
        all_decisive_obligations: List[str] = []
        all_control_gaps: List[str] = []
        all_evidence: List[str] = []
        all_regulator_objections: List[str] = []
        for i, ctx in enumerate(contexts, start=1):
            scenario = self._build_scenario(fact_packet, i, ctx)
            scenarios.append(scenario)
            all_regulator_objections.append(
                f"Scenario {i}: {scenario.agent_positions.regulator_proxy[:120]}..."
            )
        final_risk = self._aggregate_risk(scenarios)
        recommendation = self._classify_recommendation(final_risk)
        all_decisive_obligations = self._extract_decisive_obligations(
            fact_packet, scenarios
        )
        all_control_gaps = self._extract_control_gaps(fact_packet, scenarios)
        all_evidence = self._build_evidence_checklist(fact_packet, scenarios)

        # Compute weighted risk assessment using RiskScoringEngine
        weighted_assessment = None
        if scenarios:
            avg_dimensions: Dict[str, float] = {}
            for dim in RISK_DIMENSIONS:
                avg_dimensions[dim] = sum(
                    s.risk_score.dimensions.get(dim, 50.0) for s in scenarios
                ) / len(scenarios)
            weighted_assessment = self._enhance_with_weighted_scoring(
                fact_packet, avg_dimensions, final_risk
            )

        result = StressLabResult(
            fact_packet_id=fact_packet.id,
            scenarios=scenarios,
            final_risk_rating=round(final_risk, 2),
            decisive_obligations=all_decisive_obligations,
            key_control_gaps=all_control_gaps,
            evidence_checklist=all_evidence,
            regulator_objections=all_regulator_objections,
            final_recommendation=recommendation,
            generated_at=datetime.utcnow(),
        )

        # Attach weighted assessment metadata (non-breaking)
        if weighted_assessment:
            result._weighted_assessment = weighted_assessment

        return result

    def _build_scenario(
        self, fp: FactPacket, num: int, context: str
    ) -> SimulationScenario:
        base_risk = self._base_risk_from_packet(fp)
        scenario_variance = random.uniform(-15.0, 15.0)
        context_multiplier = 1.0 + (random.random() * 0.4 - 0.1)
        dimensions: Dict[str, float] = {}
        for dim in RISK_DIMENSIONS:
            dim_base = base_risk * context_multiplier
            dim_noise = random.uniform(-10.0, 10.0)
            dim_boost = 0.0
            if dim == "licensing_risk" and fp.licensing_category not in ["General", "Unspecified"]:
                dim_boost = 15.0
            elif dim == "aml_risk" and fp.obligations.aml_triggers:
                dim_boost = 12.0
            elif dim == "cross_border_risk" and len(fp.cross_border_elements) > 1:
                dim_boost = 18.0
            elif dim == "consumer_protection_risk" and fp.target_user_type == "Retail":
                dim_boost = 20.0
            elif dim == "enforcement_risk" and any(
                "enforcement" in str(v).lower() for v in [
                    fp.jurisdiction, fp.regulator, fp.activity_type, fp.product_class
                ]
            ):
                dim_boost = 10.0
            dimensions[dim] = _clamp(dim_base + dim_noise + dim_boost + scenario_variance)
        overall = round(sum(dimensions.values()) / len(dimensions), 2)
        recommendation = self._classify_recommendation(overall)
        agent_positions = AgentPositions(
            business_advocate=self._generate_business_advocate(fp, context, overall),
            compliance_reviewer=self._generate_compliance_reviewer(fp, context, dimensions),
            regulator_proxy=self._generate_regulator_proxy(fp, context, overall),
            neutral_adjudicator=self._generate_adjudicator(fp, context, overall, dimensions),
        )
        return SimulationScenario(
            fact_packet_id=fp.id,
            scenario_number=num,
            agent_positions=agent_positions,
            risk_score=RiskScore(overall=overall, dimensions=dimensions),
            recommendation=recommendation,
        )

    def _base_risk_from_packet(self, fp: FactPacket) -> float:
        base = 35.0
        if fp.licensing_category != "General":
            base += 10.0
        if len(fp.cross_border_elements) > 1:
            base += 8.0
        if fp.target_user_type == "Retail":
            base += 12.0
        if fp.custody_model == "Self-Custody":
            base += 5.0
        if fp.target_user_type == "Institutional":
            base -= 8.0
        return _clamp(base)

    def _generate_business_advocate(
        self, fp: FactPacket, context: str, risk_score: float
    ) -> str:
        arg = random.choice(BUSINESS_ARGUMENTS)
        return (
            f"BUSINESS ADVOCATE (Scenario context: {context[:80]}...): "
            f"{arg} We assess the net risk score at {risk_score:.0f}/100, "
            f"which falls within our risk appetite for {fp.product_class} products. "
            f"Recommended action: PROCEED with standard monitoring."
        )

    def _generate_compliance_reviewer(
        self, fp: FactPacket, context: str, dimensions: Dict[str, float]
    ) -> str:
        top_risks = sorted(
            dimensions.items(), key=lambda x: x[1], reverse=True
        )[:3]
        risk_str = ", ".join(f"{k}={v:.0f}" for k, v in top_risks)
        return (
            f"COMPLIANCE REVIEWER: The highest risk dimensions are {risk_str}. "
            f"Licensing triggers: {len(fp.obligations.licensing_triggers)} identified. "
            f"AML obligations: {len(fp.obligations.aml_triggers)} active. "
            f"Control representations show {len(fp.control_representations.claimed)} claimed, "
            f"{len(fp.control_representations.planned)} planned, "
            f"{len(fp.control_representations.assumed)} assumed. "
            f"A HOLD recommendation is advised pending remediation of top 2 risk dimensions."
        )

    def _generate_regulator_proxy(
        self, fp: FactPacket, context: str, risk_score: float
    ) -> str:
        arg = random.choice(REGULATOR_ARGUMENTS)
        return (
            f"REGULATOR PROXY ({fp.regulator} perspective): {arg} "
            f"The composite risk score of {risk_score:.0f}/100 significantly exceeds "
            f"the threshold we typically accept for {fp.jurisdiction} authorisations. "
            f"We would likely object on grounds of insufficient consumer safeguards "
            f"and inadequate capital requirements. Position: NO-GO without material remediation."
        )

    def _generate_adjudicator(
        self, fp: FactPacket, context: str, overall: float, dimensions: Dict[str, float]
    ) -> str:
        arg = random.choice(ADJUDICATOR_ARGUMENTS)
        proceed_dims = sum(1 for v in dimensions.values() if v < 40)
        hold_dims = sum(1 for v in dimensions.values() if 40 <= v <= 65)
        nogo_dims = sum(1 for v in dimensions.values() if v > 65)
        return (
            f"NEUTRAL ADJUDICATOR: Risk profile shows {proceed_dims} dimensions below 40, "
            f"{hold_dims} in HOLD range (40-65), and {nogo_dims} above 65. "
            f"{arg} Overall composite: {overall:.0f}/100. "
            f"Decision: {self._classify_recommendation(overall)}."
        )

    def _classify_recommendation(self, score: float) -> str:
        if score <= 30:
            return "PROCEED"
        elif score <= 60:
            return "HOLD"
        else:
            return "NO-GO"

    def _enhance_with_weighted_scoring(
        self,
        fp: FactPacket,
        dimensions: Dict[str, float],
        overall: float,
    ) -> Dict[str, Any]:
        """Use RiskScoringEngine for proper 10-dimension weighted scoring.

        Maps the existing 0-100 dimension scores to the RiskScoringEngine's
        0-5 scale and produces a weighted risk summary. This enriches the
        scenario output without changing the core simulation logic.
        """
        # Map existing 0-100 dimension scores to 0-5 scale for the engine
        # The RiskScoringEngine uses: 1-5 scale (low=1.5, medium=2.5, high=4.0, critical=5.0)
        # Map 0-100 to 1-5 linearly
        dim_scores = {}
        for dim_name, dim_value in dimensions.items():
            scaled = max(1.0, min(5.0, 1.0 + (dim_value / 100.0) * 4.0))
            dim_scores[dim_name] = round(scaled, 2)

        # Map to RiskScoringEngine dimensions where possible
        engine_input = {
            "regulatory_trigger_severity": dim_scores.get("regulatory_risk", 3.0),
            "licensing_uncertainty": dim_scores.get("licensing_risk", 3.0),
            "enforcement_sensitivity": dim_scores.get("enforcement_risk", 3.0),
            "control_maturity_gap": dim_scores.get("operational_risk", 3.0),
            "evidence_readiness_gap": dim_scores.get("conduct_risk", 3.0),
            "cross_border_complexity": dim_scores.get("cross_border_risk", 3.0),
            "customer_harm_risk": dim_scores.get("consumer_protection_risk", 3.0),
            "aml_sanctions_exposure": dim_scores.get("aml_risk", 3.0),
            "marketing_misrepresentation_risk": dim_scores.get("reputational_risk", 3.0),
            "strategic_materiality": dim_scores.get("financial_risk", 3.0),
        }

        # Apply fact-packet specific adjustments
        if fp.licensing_category not in ["General", "Unspecified"]:
            engine_input["licensing_uncertainty"] = min(5.0, engine_input["licensing_uncertainty"] + 0.5)
        if fp.obligations.aml_triggers:
            engine_input["aml_sanctions_exposure"] = min(5.0, engine_input["aml_sanctions_exposure"] + 0.5)
        if len(fp.cross_border_elements) > 1:
            engine_input["cross_border_complexity"] = min(5.0, engine_input["cross_border_complexity"] + 0.5)
        if fp.target_user_type == "Retail":
            engine_input["customer_harm_risk"] = min(5.0, engine_input["customer_harm_risk"] + 0.5)

        try:
            risk_summary = self._scoring_engine.generate_risk_summary(engine_input)
            return {
                "risk_scoring_engine_used": True,
                "weighted_score": risk_summary.get("overall_score", overall / 20.0),
                "weighted_rating": risk_summary.get("risk_rating", "medium"),
                "top_concerns": risk_summary.get("top_concerns", []),
                "weighted_recommendation": risk_summary.get("recommendation", "hold"),
            }
        except Exception as exc:
            logger.debug("RiskScoringEngine enhancement failed: %s", exc)
            return {
                "risk_scoring_engine_used": False,
                "weighted_score": overall / 20.0,
                "weighted_rating": self._scoring_engine.get_risk_rating(overall / 20.0) if hasattr(self, '_scoring_engine') else "medium",
            }

    def _aggregate_risk(self, scenarios: List[SimulationScenario]) -> float:
        if not scenarios:
            return 0.0
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        sorted_scenarios = sorted(
            scenarios, key=lambda s: s.risk_score.overall, reverse=True
        )
        total_weight = 0.0
        weighted_sum = 0.0
        for i, s in enumerate(sorted_scenarios):
            w = weights[i] if i < len(weights) else 0.05
            weighted_sum += s.risk_score.overall * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _extract_decisive_obligations(
        self, fp: FactPacket, scenarios: List[SimulationScenario]
    ) -> List[str]:
        obligations: List[str] = []
        if fp.obligations.licensing_triggers:
            obligations.extend(
                [f"LICENSING: {t}" for t in fp.obligations.licensing_triggers[:3]]
            )
        if fp.obligations.aml_triggers:
            obligations.extend(
                [f"AML: {t}" for t in fp.obligations.aml_triggers[:3]]
            )
        if fp.obligations.reporting_triggers:
            obligations.extend(
                [f"REPORTING: {t}" for t in fp.obligations.reporting_triggers[:2]]
            )
        if fp.obligations.disclosure_requirements:
            obligations.extend(
                [f"DISCLOSURE: {t}" for t in fp.obligations.disclosure_requirements[:2]]
            )
        avg_risk = sum(s.risk_score.overall for s in scenarios) / len(scenarios)
        obligations.append(
            f"AGGREGATE_RISK: Composite {avg_risk:.1f}/100 exceeds threshold for {fp.licensing_category}"
        )
        return obligations

    def _extract_control_gaps(
        self, fp: FactPacket, scenarios: List[SimulationScenario]
    ) -> List[str]:
        gaps: List[str] = []
        if not fp.control_representations.claimed or fp.control_representations.claimed == ["No explicit claimed controls identified"]:
            gaps.append("No claimed controls documented — material gap")
        if not fp.control_representations.planned or fp.control_representations.planned == ["No explicit planned controls identified"]:
            gaps.append("No planned remediation controls — regulatory expectation gap")
        high_risk_dims = []
        for s in scenarios:
            for dim, val in s.risk_score.dimensions.items():
                if val > 60 and dim not in [d for d, _ in high_risk_dims]:
                    high_risk_dims.append((dim, val))
        for dim, val in sorted(high_risk_dims, key=lambda x: x[1], reverse=True)[:4]:
            gaps.append(f"High {dim}: {val:.0f}/100 — requires targeted control")
        if len(fp.cross_border_elements) > 2:
            gaps.append("Multi-jurisdiction exposure exceeds standard control framework")
        return gaps

    def _build_evidence_checklist(
        self, fp: FactPacket, scenarios: List[SimulationScenario]
    ) -> List[str]:
        evidence: List[str] = [
            "Legal opinion confirming licensing status (or exemption basis)",
            "AML/CFT policy documentation and risk assessment",
            "Technical audit report for underlying infrastructure",
            "Insurance policy documentation and coverage schedule",
            "Board risk appetite statement and approval minutes",
        ]
        if fp.target_user_type == "Retail":
            evidence.append("Consumer protection impact assessment")
            evidence.append("Marketing material compliance review")
        if len(fp.cross_border_elements) > 1:
            evidence.append("Cross-border legal opinions per jurisdiction")
            evidence.append("Regulatory correspondence with foreign regulators")
        evidence.append("Financial projections and capital adequacy analysis")
        evidence.append("Independent compliance audit within last 12 months")
        return evidence
