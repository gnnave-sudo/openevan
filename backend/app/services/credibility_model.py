"""
Part II: Counsel Credibility Scoring Model
Scores external counsel on 6 dimensions, classifies into tiers,
and maintains track records with leaderboards.
"""

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List

from app.models import (
    DIMENSION_WEIGHTS,
    CredibilityDimension,
    CounselCredibilityScore,
    CounselTrackRecord,
)

logger = logging.getLogger(__name__)

TIER_THRESHOLDS = [
    (0, 40, "HIGH_RISK"),
    (41, 60, "WEAK"),
    (61, 75, "ACCEPTABLE"),
    (76, 90, "STRONG"),
    (91, 100, "HIGHLY_RELIABLE"),
]


class CredibilityModel:
    """Scores and tracks external counsel credibility across matters."""

    def __init__(self):
        self._scores: Dict[str, List[CounselCredibilityScore]] = {}

    def score_counsel(
        self,
        counsel_name: str,
        matter_id: str,
        dimension_scores: Dict[str, float],
    ) -> CounselCredibilityScore:
        """Score a counsel on a specific matter."""
        logger.info(
            "Scoring counsel %s for matter %s", counsel_name, matter_id
        )
        validated_scores = self._validate_dimensions(dimension_scores)
        weighted = 0.0
        for dim, weight in DIMENSION_WEIGHTS.items():
            score = validated_scores.get(dim.value, 50.0)
            weighted += score * weight
        weighted = round(weighted, 2)
        tier = self._classify_tier(weighted)
        score = CounselCredibilityScore(
            counsel_name=counsel_name,
            matter_id=matter_id,
            dimension_scores=validated_scores,
            weighted_score=weighted,
            risk_tier=tier,
            scored_at=datetime.utcnow(),
        )
        key = counsel_name.lower()
        if key not in self._scores:
            self._scores[key] = []
        self._scores[key].append(score)
        return score

    def get_track_record(
        self, counsel_name: str
    ) -> CounselTrackRecord:
        """Get the full track record for a counsel."""
        key = counsel_name.lower()
        scores_list = self._scores.get(key, [])
        if not scores_list:
            return CounselTrackRecord(
                counsel_name=counsel_name,
                average_score=0.0,
                scores_by_jurisdiction={},
                scores_over_time=[],
                enforcement_correlation=0.0,
                hindsight_accuracy=0.0,
            )
        avg_score = round(
            statistics.mean(s.weighted_score for s in scores_list), 2
        )
        scores_over_time = [
            {
                "matter_id": s.matter_id,
                "score": s.weighted_score,
                "tier": s.risk_tier,
                "scored_at": s.scored_at.isoformat(),
            }
            for s in scores_list
        ]
        enforcement_corr = self._calculate_enforcement_correlation(scores_list)
        hindsight = self._calculate_hindsight_accuracy(scores_list)
        return CounselTrackRecord(
            counsel_name=counsel_name,
            average_score=avg_score,
            scores_by_jurisdiction={"Global": avg_score},
            scores_over_time=scores_over_time,
            enforcement_correlation=enforcement_corr,
            hindsight_accuracy=hindsight,
        )

    def get_leaderboard(self) -> List[CounselTrackRecord]:
        """Get all counsel ranked by average score descending."""
        records: List[CounselTrackRecord] = []
        for name_lower, scores_list in self._scores.items():
            if not scores_list:
                continue
            actual_name = scores_list[0].counsel_name
            avg_score = round(
                statistics.mean(s.weighted_score for s in scores_list), 2
            )
            records.append(
                CounselTrackRecord(
                    counsel_name=actual_name,
                    average_score=avg_score,
                    scores_by_jurisdiction={"Global": avg_score},
                    scores_over_time=[
                        {
                            "matter_id": s.matter_id,
                            "score": s.weighted_score,
                            "tier": s.risk_tier,
                            "scored_at": s.scored_at.isoformat(),
                        }
                        for s in scores_list
                    ],
                    enforcement_correlation=self._calculate_enforcement_correlation(
                        scores_list
                    ),
                    hindsight_accuracy=self._calculate_hindsight_accuracy(
                        scores_list
                    ),
                )
            )
        records.sort(key=lambda r: r.average_score, reverse=True)
        return records

    def _validate_dimensions(
        self, dimension_scores: Dict[str, float]
    ) -> Dict[str, float]:
        validated: Dict[str, float] = {}
        for dim in CredibilityDimension:
            raw = dimension_scores.get(dim.value)
            if raw is None:
                raw = 0.5
            raw = float(raw)
            # Auto-detect 0-1 scale and convert to 0-100
            if 0.0 <= raw <= 1.0:
                raw = raw * 100.0
            validated[dim.value] = max(0.0, min(100.0, raw))
        return validated

    def _classify_tier(self, weighted_score: float) -> str:
        for lo, hi, tier in TIER_THRESHOLDS:
            if lo <= weighted_score <= hi:
                return tier
        return "HIGHLY_RELIABLE" if weighted_score > 100 else "HIGH_RISK"

    def _calculate_enforcement_correlation(
        self, scores: List[CounselCredibilityScore]
    ) -> float:
        if len(scores) < 2:
            return 0.0
        high_risk_count = sum(
            1 for s in scores if s.weighted_score < 50
        )
        return round(high_risk_count / len(scores) * 100, 2)

    def _calculate_hindsight_accuracy(
        self, scores: List[CounselCredibilityScore]
    ) -> float:
        if not scores:
            return 0.0
        strong_scores = sum(
            1 for s in scores if s.weighted_score >= 70
        )
        return round(strong_scores / len(scores) * 100, 2)
