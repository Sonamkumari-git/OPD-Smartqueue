"""Deterministic priority-aware FIFO ordering used by the MongoDB queue index and tests."""
from collections.abc import Iterable

PRIORITY_RANK = {"EMERGENCY": 0, "HIGH": 1, "NORMAL": 2}


def ordered_tokens(tokens: Iterable[dict]) -> list[dict]:
    return sorted(tokens, key=lambda token: (PRIORITY_RANK[token["priority"]], token["created_at"]))


def waiting_patients_ahead(tokens: Iterable[dict], token_id: str) -> int:
    ordered = ordered_tokens(tokens)
    target_index = next((index for index, token in enumerate(ordered) if str(token.get("_id")) == token_id), None)
    if target_index is None:
        return 0
    return sum(1 for token in ordered[:target_index] if token.get("status") in {"WAITING", "CALLED", "IN_CONSULTATION"})
