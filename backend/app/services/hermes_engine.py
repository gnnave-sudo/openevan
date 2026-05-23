"""
Layer 3: Hermes Pattern Intelligence Engine
Extracts patterns from stress test results and maintains 5 risk indices.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models import PatternExtract, RiskIndices, SimulationScenario, StressLabResult

logger = logging.getLogger(__name__)


class HermesEngine:
    """Pattern extraction and risk index maintenance engine."""

    def __init__(self):
        self._local_indices: RiskIndices = RiskIndices()

    def extract_patterns(
        self, stress_result: StressLabResult
    ) -> PatternExtract:
        """Extract regulatory patterns from a stress test result."""
        logger.info(
            "Extracting patterns from stress result %s", stress_result.id
        )
        risk_drivers = self._identify_risk_drivers(stress_result)
        recurrent_obligations = self._extract_recurrent_obligations(
            stress_result
        )
        recurring_weaknesses = self._extract_control_weaknesses(
            stress_result
        )
        posture_signals = self._extract_posture_signals(stress_result)
        return PatternExtract(
            stress_result_id=stress_result.id,
            jurisdiction=self._infer_jurisdiction(stress_result),
            product_type=self._infer_product_type(stress_result),
            risk_drivers=risk_drivers,
            recurrent_obligations=recurrent_obligations,
            recurring_control_weaknesses=recurring_weaknesses,
            regulatory_posture_signals=posture_signals,
            extracted_at=datetime.utcnow(),
        )

    def update_risk_indices(
        self,
        pattern_extract: PatternExtract,
        stress_result: StressLabResult,
    ) -> RiskIndices:
        """Update all 5 risk indices based on a new pattern extract."""
        idx = self._local_indices
        jurisdiction = pattern_extract.jurisdiction
        overall_risk = stress_result.final_risk_rating
        if jurisdiction in idx.jurisdiction_risk_index:
            existing = idx.jurisdiction_risk_index[jurisdiction]
            idx.jurisdiction_risk_index[jurisdiction] = round(
                (existing + overall_risk) / 2, 2
            )
        else:
            idx.jurisdiction_risk_index[jurisdiction] = round(
                overall_risk, 2
            )
        for obligation in pattern_extract.recurrent_obligations:
            key = obligation[:80]
            idx.obligation_frequency[key] = (
                idx.obligation_frequency.get(key, 0) + 1
            )
        for weakness in pattern_extract.recurring_control_weaknesses:
            key = weakness[:80]
            idx.control_failure_frequency[key] = (
                idx.control_failure_frequency.get(key, 0) + 1
            )
        if overall_risk > 60:
            idx.escalation_likelihood[jurisdiction] = round(
                min(95.0, idx.escalation_likelihood.get(jurisdiction, 0) + 15.0),
                2,
            )
        elif overall_risk > 40:
            idx.escalation_likelihood[jurisdiction] = round(
                min(70.0, idx.escalation_likelihood.get(jurisdiction, 0) + 8.0),
                2,
            )
        else:
            idx.escalation_likelihood[jurisdiction] = round(
                max(5.0, idx.escalation_likelihood.get(jurisdiction, 0) - 5.0),
                2,
            )
        return idx

    def set_indices(self, indices: RiskIndices) -> None:
        """Restore indices from persistence."""
        self._local_indices = indices

    def _identify_risk_drivers(
        self, result: StressLabResult
    ) -> List[str]:
        drivers: List[str] = []
        if result.final_risk_rating > 50:
            drivers.append(
                f"High composite risk ({result.final_risk_rating:.0f}/100) elevates regulatory exposure"
            )
        if result.final_recommendation == "NO-GO":
            drivers.append(
                "NO-GO recommendation signals fundamental structural concerns"
            )
        elif result.final_recommendation == "HOLD":
            drivers.append(
                "HOLD recommendation indicates conditional viability pending remediation"
            )
        for obligation in result.decisive_obligations[:3]:
            drivers.append(f"Decisive obligation: {obligation}")
        for gap in result.key_control_gaps[:2]:
            drivers.append(f"Control gap: {gap}")
        if not drivers:
            drivers.append("No primary risk drivers identified")
        return drivers

    def _extract_recurrent_obligations(
        self, result: StressLabResult
    ) -> List[str]:
        obligations: List[str] = []
        for obligation in result.decisive_obligations:
            obligations.append(obligation)
        for obj in result.regulator_objections[:2]:
            obligations.append(f"Regulator objection: {obj}")
        return obligations if obligations else ["No recurrent obligations pattern"]

    def _extract_control_weaknesses(
        self, result: StressLabResult
    ) -> List[str]:
        return (
            result.key_control_gaps
            if result.key_control_gaps
            else ["No control weaknesses identified"]
        )

    def _extract_posture_signals(
        self, result: StressLabResult
    ) -> List[str]:
        signals: List[str] = []
        for scenario in result.scenarios:
            if scenario.recommendation == "NO-GO":
                signals.append(
                    f"Scenario {scenario.scenario_number}: All agents converged on NO-GO"
                )
            elif scenario.recommendation == "HOLD":
                signals.append(
                    f"Scenario {scenario.scenario_number}: Agents split — adjudicator recommended HOLD"
                )
            elif scenario.recommendation == "PROCEED":
                signals.append(
                    f"Scenario {scenario.scenario_number}: Business case accepted with reservations"
                )
        nogo_count = sum(
            1 for s in result.scenarios if s.recommendation == "NO-GO"
        )
        if nogo_count >= 2:
            signals.append(
                f"Multiple NO-GO scenarios ({nogo_count}/{len(result.scenarios)}) indicate hostile regulatory posture"
            )
        if result.final_risk_rating > 70:
            signals.append(
                "Extreme risk score (>70) suggests imminent enforcement exposure"
            )
        return signals if signals else ["Neutral regulatory posture"]

    def _infer_jurisdiction(self, result: StressLabResult) -> str:
        for scenario in result.scenarios:
            if hasattr(scenario, "_jurisdiction"):
                return getattr(scenario, "_jurisdiction", "Multi-Jurisdiction")
        return "Multi-Jurisdiction"

    def _infer_product_type(self, result: StressLabResult) -> str:
        return "General"
