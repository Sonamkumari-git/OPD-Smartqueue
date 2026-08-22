"""Pure queue tests run without a MongoDB dependency."""
from datetime import datetime, timedelta
from app.queue.ordering import ordered_tokens, waiting_patients_ahead


def token(identifier: str, priority: str, minutes: int, status: str = "WAITING") -> dict:
    return {"_id": identifier, "priority": priority, "created_at": datetime(2026, 8, 22, 9, 0) + timedelta(minutes=minutes), "status": status}


def test_priority_precedes_fifo_and_fifo_is_stable_within_priority():
    records = [token("normal-first", "NORMAL", 0), token("high-later", "HIGH", 20), token("high-first", "HIGH", 10), token("emergency", "EMERGENCY", 40)]
    assert [record["_id"] for record in ordered_tokens(records)] == ["emergency", "high-first", "high-later", "normal-first"]


def test_patients_ahead_excludes_the_current_in_consultation_token():
    records = [token("current", "NORMAL", 0, "IN_CONSULTATION"), token("first-waiting", "NORMAL", 1), token("second-waiting", "NORMAL", 2), token("target", "NORMAL", 3)]
    assert waiting_patients_ahead(records, "target") == 2
