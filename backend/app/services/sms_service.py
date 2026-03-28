from typing import Optional

from app.models.sms_detector import SMSDetector

_detector: Optional[SMSDetector] = None


def _get_detector() -> SMSDetector:
    global _detector
    if _detector is None:
        _detector = SMSDetector()
    return _detector


def analyze_sms(message: str) -> dict:
    return _get_detector().predict(message)
