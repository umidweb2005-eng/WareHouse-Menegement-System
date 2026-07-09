"""Deterministic in-memory id generator."""

from __future__ import annotations

from donation_bot.application.ports.ids import IdGenerator


class SequentialIdGenerator(IdGenerator):
    """Yields ``id-1``, ``id-2``, ... — predictable ids for tests."""

    def __init__(self, prefix: str = "id") -> None:
        self._prefix = prefix
        self._n = 0

    def new_id(self) -> str:
        self._n += 1
        return f"{self._prefix}-{self._n}"
