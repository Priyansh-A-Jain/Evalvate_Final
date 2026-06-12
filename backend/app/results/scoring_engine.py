"""
Evalvate Interview Scoring Engine.

All component scores are 0-10. The overall score is a weighted
composite (0-100). Every formula here is documented and defensible —
no random numbers, no static returns.

Component sources:
    technical      — Gemini evaluation scores per answered question
    communication  — Hume prosody (confidence/clarity/pace/energy) with
                     transcript-derived fallback
    eye_contact    — MediaPipe iris-based engagement (continuous, 0-100)
    emotion        — DeepFace frame emotions (confident vs nervous ratio)
    structure      — answer clarity proxy from evaluation scores
"""

from typing import Any


class InterviewScoringEngine:

    WEIGHTS = {
        "technical": 0.35,
        "communication": 0.25,
        "eye_contact": 0.20,
        "emotion": 0.10,
        "structure": 0.10,
    }

    CONFIDENT_EMOTIONS = {"happy", "neutral"}
    NERVOUS_EMOTIONS = {"fear", "sad"}

    def calculate(
        self,
        *,
        response_scores: list[int],
        session_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute component scores + weighted overall from session data."""
        scores = {
            "technical": self._technical_score(response_scores),
            "communication": self._communication_score(session_analysis),
            "eye_contact": self._eye_contact_score(session_analysis),
            "emotion": self._emotion_score(session_analysis),
            "structure": self._structure_score(response_scores),
        }

        overall = sum(scores[key] * weight for key, weight in self.WEIGHTS.items())
        overall_pct = round(overall * 10.0, 1)  # 0-10 weighted -> 0-100

        return {
            "overall_score": overall_pct,
            "component_scores": {key: round(value, 2) for key, value in scores.items()},
            "weights_used": dict(self.WEIGHTS),
            "grade": self._grade(overall),
        }

    @staticmethod
    def _technical_score(response_scores: list[int]) -> float:
        """Average Gemini evaluation score (1-10) across answered questions."""
        if not response_scores:
            return 5.0
        return sum(response_scores) / len(response_scores)

    @staticmethod
    def _communication_score(session: dict[str, Any]) -> float:
        """Composite from Hume prosody; transcript clarity fallback."""
        prosody = session.get("prosody") or {}
        if prosody.get("source") == "hume":
            confidence = float(prosody.get("confidence") or 0.5)
            energy = float(prosody.get("energy") or 0.5)
            pace = float(prosody.get("pace_score") or 0.5)
            clarity = float(prosody.get("clarity_score") or 0.5)
            composite = confidence * 0.30 + clarity * 0.30 + pace * 0.25 + energy * 0.15
            return max(0.0, min(10.0, composite * 10.0))

        # Fallback: transcript-derived clarity + pace only
        pace = prosody.get("pace_score")
        clarity = prosody.get("clarity_score")
        if pace is not None or clarity is not None:
            composite = (float(pace or 0.5) + float(clarity or 0.5)) / 2.0
            return max(0.0, min(10.0, composite * 10.0))

        confidence_pct = session.get("confidence")
        if confidence_pct is not None:
            return max(0.0, min(10.0, float(confidence_pct) / 10.0))
        return 5.0

    @staticmethod
    def _eye_contact_score(session: dict[str, Any]) -> float:
        """Continuous gaze engagement (0-100) -> 0-10. 80%+ engagement = 10."""
        gaze_pct = session.get("gaze_score")
        if gaze_pct is None:
            return 5.0
        return min(10.0, (float(gaze_pct) / 80.0) * 10.0)

    def _emotion_score(self, session: dict[str, Any]) -> float:
        """Confident-frame ratio bonus minus nervous-frame ratio penalty."""
        timeline = session.get("video_timeline") or []
        labels = [str(item.get("label") or "").lower() for item in timeline if isinstance(item, dict)]
        labels = [label for label in labels if label]
        if not labels:
            return 5.0

        total = len(labels)
        confident = sum(1 for label in labels if label in self.CONFIDENT_EMOTIONS)
        nervous = sum(1 for label in labels if label in self.NERVOUS_EMOTIONS)

        score = (confident / total) * 10.0 - (nervous / total) * 5.0
        return max(0.0, min(10.0, score))

    @staticmethod
    def _structure_score(response_scores: list[int]) -> float:
        """
        Structure proxy: consistency of answer quality. High average with low
        variance indicates structured, complete answers. (Part 3 replaces this
        with a dedicated Gemini structure rubric per answer.)
        """
        if not response_scores:
            return 5.0
        avg = sum(response_scores) / len(response_scores)
        if len(response_scores) > 1:
            variance = sum((s - avg) ** 2 for s in response_scores) / len(response_scores)
            consistency_penalty = min(2.0, variance / 4.0)
        else:
            consistency_penalty = 0.0
        return max(0.0, min(10.0, avg - consistency_penalty))

    @staticmethod
    def _grade(overall_0_10: float) -> str:
        if overall_0_10 >= 9.0:
            return "S"
        if overall_0_10 >= 8.0:
            return "A"
        if overall_0_10 >= 7.0:
            return "B"
        if overall_0_10 >= 5.5:
            return "C"
        if overall_0_10 >= 4.0:
            return "D"
        return "F"


scoring_engine = InterviewScoringEngine()
