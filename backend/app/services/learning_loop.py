"""
Layer 6: Continuous Learning Loop
Detects risk drift, schedules reviews, and compares historical risk postures.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models import DriftDetection

logger = logging.getLogger(__name__)

# Drift thresholds
DRIFT_ABSOLUTE_THRESHOLD = 10.0  # Score change that triggers drift
DRIFT_PERCENTAGE_THRESHOLD = 0.20  # 20% relative change


class LearningLoop:
    """Continuous learning and drift detection for regulatory risk."""

    def __init__(self):
        self._drift_history: Dict[str, List[Dict[str, Any]]] = {}

    def detect_drift(
        self,
        product_id: str,
        new_score: float,
        previous_score: float = None,
    ) -> DriftDetection:
        """Detect whether a significant risk drift has occurred."""
        logger.info(
            "Detecting drift for product %s: new_score=%.1f",
            product_id,
            new_score,
        )
        if previous_score is None:
            previous_score = self._get_last_score(product_id)
        if previous_score is None:
            previous_score = new_score
        drift_magnitude = abs(new_score - previous_score)
        drift_pct = (
            drift_magnitude / previous_score if previous_score > 0 else 0
        )
        drift_detected = (
            drift_magnitude >= DRIFT_ABSOLUTE_THRESHOLD
            or drift_pct >= DRIFT_PERCENTAGE_THRESHOLD
        )
        if new_score > previous_score:
            posture_change = f"Risk INCREASED from {previous_score:.1f} to {new_score:.1f} (+{drift_magnitude:.1f})"
        elif new_score < previous_score:
            posture_change = f"Risk DECREASED from {previous_score:.1f} to {new_score:.1f} (-{drift_magnitude:.1f})"
        else:
            posture_change = f"Risk UNCHANGED at {new_score:.1f}"
        drift = DriftDetection(
            product_id=product_id,
            previous_score=round(previous_score, 2),
            current_score=round(new_score, 2),
            drift_detected=drift_detected,
            drift_magnitude=round(drift_magnitude, 2),
            posture_change=posture_change,
            detected_at=datetime.utcnow(),
        )
        self._record_history(product_id, drift)
        return drift

    def schedule_review(
        self, product_id: str
    ) -> Dict[str, Any]:
        """Schedule the next review cycle."""
        next_monthly = datetime.utcnow() + timedelta(days=30)
        next_quarterly = datetime.utcnow() + timedelta(days=90)
        logger.info(
            "Scheduled review for product %s: monthly=%s, quarterly=%s",
            product_id,
            next_monthly.isoformat(),
            next_quarterly.isoformat(),
        )
        return {
            "product_id": product_id,
            "monthly_review_date": next_monthly.isoformat(),
            "quarterly_review_date": next_quarterly.isoformat(),
            "recommended_actions": [
                "Run fresh CSL stress test",
                "Update fact packet with latest regulatory developments",
                "Re-analyze counsel alignment scores",
                "Review and update control investment priorities",
                "Generate updated decision memo",
            ],
            "alert_threshold": "Score change > 10 points or > 20% relative",
        }

    def compare_history(self, product_id: str) -> Dict[str, Any]:
        """Compare current posture against historical trend."""
        history = self._drift_history.get(product_id, [])
        if not history:
            return {
                "product_id": product_id,
                "history_length": 0,
                "message": "No historical data available",
                "trend": "unknown",
                "average_score": None,
                "score_volatility": None,
            }
        scores = [h["current_score"] for h in history]
        avg_score = sum(scores) / len(scores) if scores else 0
        if len(scores) >= 2:
            variance = sum(
                (s - avg_score) ** 2 for s in scores
            ) / len(scores)
            volatility = variance ** 0.5
        else:
            volatility = 0.0
        if len(scores) >= 2:
            recent = scores[-3:]
            if all(
                recent[i] <= recent[i + 1] for i in range(len(recent) - 1)
            ):
                trend = "increasing_risk"
            elif all(
                recent[i] >= recent[i + 1] for i in range(len(recent) - 1)
            ):
                trend = "decreasing_risk"
            else:
                trend = "fluctuating"
        else:
            trend = "insufficient_data"
        latest = history[-1]
        return {
            "product_id": product_id,
            "history_length": len(history),
            "trend": trend,
            "average_score": round(avg_score, 2),
            "score_volatility": round(volatility, 2),
            "latest_score": latest["current_score"],
            "latest_drift": latest["drift_detected"],
            "latest_posture_change": latest["posture_change"],
            "history": [
                {
                    "detected_at": h["detected_at"],
                    "score": h["current_score"],
                    "drift": h["drift_detected"],
                }
                for h in history
            ],
        }

    def _get_last_score(self, product_id: str) -> float:
        history = self._drift_history.get(product_id, [])
        if history:
            return history[-1]["current_score"]
        return None

    def _record_history(
        self, product_id: str, drift: DriftDetection
    ) -> None:
        if product_id not in self._drift_history:
            self._drift_history[product_id] = []
        self._drift_history[product_id].append(
            {
                "previous_score": drift.previous_score,
                "current_score": drift.current_score,
                "drift_detected": drift.drift_detected,
                "drift_magnitude": drift.drift_magnitude,
                "posture_change": drift.posture_change,
                "detected_at": drift.detected_at.isoformat(),
            }
        )
