from typing import Optional

from app.models.transaction_analyzer import TransactionAnalyzer

_analyzer: Optional[TransactionAnalyzer] = None


def _get_analyzer() -> TransactionAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TransactionAnalyzer()
    return _analyzer


def analyze_transaction(amount: float, is_new_receiver: int, transactions_today: int) -> dict:
    return _get_analyzer().analyze(amount, is_new_receiver, transactions_today)
