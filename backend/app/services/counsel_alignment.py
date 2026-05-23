"""
Layer 4: Counsel Alignment Engine
Compares external counsel memos against CSL stress test results to assess
alignment, identify blind spots, and flag overconfidence.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.models import (
    AlignmentResult,
    CounselMemoInput,
    FactPacket,
    StressLabResult,
)

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

NEGATIVE_SIGNALS = [
    "no risk", "minimal risk", "negligible", "immaterial",
    "not applicable", "does not apply", "no issue", "clean",
    "straightforward", "simple compliance",
]

POSITIVE_DEPTH_SIGNALS = [
    "however", "nevertheless", "notwithstanding", "caveat",
    "important to note", "material consideration", "significant risk",
    "contingent upon", "subject to", "prerequisite",
]

RISK_DIMENSION_WEIGHTS = {
    "obligation_coverage": 0.25,
    "risk_assessment_alignment": 0.25,
    "evidence_quality": 0.20,
    "regulator_perspective": 0.20,
    "control_completeness": 0.10,
}


class CounselAlignmentEngine:
    """Analyzes alignment between counsel memos and stress test results."""

    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url

    async def analyze_alignment(
        self,
        memo: CounselMemoInput,
        fact_packet: Optional[FactPacket] = None,
        stress_result: Optional[StressLabResult] = None,
    ) -> AlignmentResult:
        """Analyze a counsel memo against stress test results."""
        logger.info("Analyzing alignment for memo %s by %s", memo.id, memo.counsel_name)
        memo_lower = memo.memo_content.lower()
        dimension_scores: Dict[str, float] = {}
        if stress_result:
            dimension_scores["obligation_coverage"] = self._score_obligation_coverage(
                memo_lower, stress_result
            )
            dimension_scores["risk_assessment_alignment"] = (
                self._score_risk_alignment(memo_lower, stress_result)
            )
            dimension_scores["evidence_quality"] = self._score_evidence_quality(
                memo_lower
            )
            dimension_scores["regulator_perspective"] = (
                self._score_regulator_perspective(memo_lower, stress_result)
            )
            dimension_scores["control_completeness"] = (
                self._score_control_completeness(memo_lower, stress_result)
            )
            missing_objections = self._find_missing_objections(
                memo_lower, stress_result
            )
            missing_evidence = self._find_missing_evidence(
                memo_lower, stress_result
            )
            overconfidence = self._flag_overconfidence(memo_lower, stress_result)
            clarification = self._suggest_clarifications(
                memo_lower, stress_result
            )
        else:
            dimension_scores = {k: 50.0 for k in RISK_DIMENSION_WEIGHTS}
            missing_objections = ["No stress result available for comparison"]
            missing_evidence = ["No evidence checklist available"]
            overconfidence = ["Cannot assess without stress result"]
            clarification = ["Submit for CSL stress test to enable full alignment analysis"]
        alignment_score = round(
            sum(
                dimension_scores.get(k, 0) * w
                for k, w in RISK_DIMENSION_WEIGHTS.items()
            ),
            2,
        )
        return AlignmentResult(
            memo_id=memo.id,
            alignment_score=alignment_score,
            dimension_scores=dimension_scores,
            missing_regulator_objections=missing_objections,
            missing_evidence_hooks=missing_evidence,
            overconfidence_flags=overconfidence,
            suggested_clarification_questions=clarification,
            analyzed_at=datetime.utcnow(),
        )

    async def _ollama_extract_position(
        self, memo_content: str
    ) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                prompt = f"""Analyze this legal memo and extract:
1. The counsel's primary legal position (one sentence)
2. Key risk factors identified (list)
3. Assumptions made (list)
4. Confidence level (High/Medium/Low)
5. Any caveats or qualifications noted

MEMO:
{memo_content[:3000]}

Return ONLY valid JSON with keys: position, risk_factors, assumptions, confidence, caveats."""
                response = await client.post(
                    self.ollama_url,
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                result = response.json()
                import json as jsonlib
                text = result.get("response", "").strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                return jsonlib.loads(text)
        except Exception as exc:
            logger.warning("Ollama extraction failed: %s", exc)
            return None

    def _score_obligation_coverage(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> float:
        score = 50.0
        obligations = stress_result.decisive_obligations
        if not obligations:
            return score
        covered = 0
        for obligation in obligations:
            key_terms = [w for w in obligation.lower().split() if len(w) > 4]
            if any(term in memo_lower for term in key_terms[:3]):
                covered += 1
        coverage_ratio = covered / len(obligations)
        score = 30.0 + (coverage_ratio * 60.0)
        if "licensing" in memo_lower or "registration" in memo_lower:
            score += 5.0
        return min(100.0, score)

    def _score_risk_alignment(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> float:
        score = 50.0
        if stress_result.final_risk_rating > 60:
            if any(
                signal in memo_lower
                for signal in ["high risk", "material risk", "significant risk"]
            ):
                score += 30.0
            elif any(
                signal in memo_lower
                for signal in ["moderate risk", "manageable"]
            ):
                score += 10.0
            else:
                score -= 15.0
        elif stress_result.final_risk_rating > 40:
            if any(
                signal in memo_lower
                for signal in ["moderate", "material", "conditional"]
            ):
                score += 20.0
        else:
            if any(
                signal in memo_lower
                for signal in ["low risk", "minimal", "routine"]
            ):
                score += 20.0
        if stress_result.final_recommendation == "NO-GO":
            if "no-go" in memo_lower or "not proceed" in memo_lower:
                score += 15.0
            elif "proceed" in memo_lower:
                score -= 20.0
        return max(0.0, min(100.0, score))

    def _score_evidence_quality(self, memo_lower: str) -> float:
        score = 50.0
        evidence_signals = [
            "document", "report", "audit", "assessment", "analysis",
            "opinion", "legal opinion", "technical review",
            "independent", "third-party", "verification",
        ]
        for signal in evidence_signals:
            if signal in memo_lower:
                score += 3.0
        score = min(100.0, score)
        if "reference" in memo_lower or "citation" in memo_lower or "section" in memo_lower:
            score += 5.0
        if len(memo_lower) < 500:
            score -= 15.0
        return max(0.0, score)

    def _score_regulator_perspective(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> float:
        score = 40.0
        regulator_signals = [
            "regulator", "supervisor", "authority", "enforcement",
            "guideline", "expectation", "posture", "approach",
            "fca", "mas", "sec", "cftc", "esma", "hkma",
        ]
        for signal in regulator_signals:
            if signal in memo_lower:
                score += 4.0
        score = min(100.0, score)
        if stress_result.regulator_objections:
            objections_lower = " ".join(stress_result.regulator_objections).lower()
            overlap = sum(
                1 for signal in regulator_signals if signal in objections_lower
            )
            score += overlap * 2.0
        return min(100.0, score)

    def _score_control_completeness(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> float:
        score = 40.0
        control_signals = [
            "control", "mitigation", "safeguard", "measure",
            "framework", "policy", "procedure", "monitoring",
            "governance", "oversight", "compliance program",
        ]
        for signal in control_signals:
            if signal in memo_lower:
                score += 3.0
        score = min(100.0, score)
        if "gap" in memo_lower or "weakness" in memo_lower:
            score += 5.0
        return min(100.0, score)

    def _find_missing_objections(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> List[str]:
        missing: List[str] = []
        for objection in stress_result.regulator_objections:
            key_words = [
                w for w in objection.lower().split() if len(w) > 5
            ]
            if not any(kw in memo_lower for kw in key_words[:2]):
                missing.append(f"Not addressed: {objection[:120]}")
        return missing if missing else ["All major objections appear to be addressed"]

    def _find_missing_evidence(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> List[str]:
        missing: List[str] = []
        for item in stress_result.evidence_checklist:
            key_words = [
                w for w in item.lower().split() if len(w) > 4
            ]
            if not any(kw in memo_lower for kw in key_words[:2]):
                missing.append(f"Evidence gap: {item}")
        return missing if missing else ["All required evidence appears to be referenced"]

    def _flag_overconfidence(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> List[str]:
        flags: List[str] = []
        if stress_result.final_risk_rating > 60:
            if any(sig in memo_lower for sig in NEGATIVE_SIGNALS):
                flags.append(
                    "Counsel dismisses risk despite CSL composite >60 — overconfidence"
                )
        confidence_phrases = [
            "clearly", "unequivocally", "without doubt", "certainly",
            "definitely", "absolutely", "undoubtedly",
        ]
        confidence_count = sum(
            1 for phrase in confidence_phrases if phrase in memo_lower
        )
        if confidence_count >= 3:
            flags.append(
                f"Excessive certainty language ({confidence_count} instances) — confidence may exceed rigor"
            )
        if "no issues" in memo_lower or "no concerns" in memo_lower:
            flags.append("Absolute statements ('no issues') contradict stress test findings")
        if len(stress_result.scenarios) >= 3 and stress_result.final_recommendation == "NO-GO":
            if "proceed" in memo_lower and "not proceed" not in memo_lower:
                flags.append(
                    "Counsel recommends PROCEED despite 3+ NO-GO scenarios — fundamental misalignment"
                )
        return flags if flags else ["No overconfidence indicators detected"]

    def _suggest_clarifications(
        self, memo_lower: str, stress_result: StressLabResult
    ) -> List[str]:
        questions: List[str] = []
        if "assumption" not in memo_lower:
            questions.append(
                "What are the key assumptions underlying this legal opinion?"
            )
        if "contingency" not in memo_lower and "scenario" not in memo_lower:
            questions.append(
                "What contingency plans exist if the regulator takes a stricter position?"
            )
        if stress_result.final_risk_rating > 50:
            questions.append(
                f"Given the CSL risk score of {stress_result.final_risk_rating:.0f}/100, "
                "what additional controls would change the risk profile?"
            )
        if len(stress_result.key_control_gaps) > 2:
            questions.append(
                f"How does counsel address the {len(stress_result.key_control_gaps)} identified control gaps?"
            )
        if "timeline" not in memo_lower and "schedule" not in memo_lower:
            questions.append("What is the recommended timeline for remediation?")
        if stress_result.final_recommendation != "PROCEED":
            questions.append(
                f"The CSL recommends {stress_result.final_recommendation}. "
                "Does counsel agree, and if not, on what basis?"
            )
        questions.append(
            "Has this opinion been peer-reviewed or challenged internally?"
        )
        return questions
