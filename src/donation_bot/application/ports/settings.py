"""Settings port: runtime policy values the use cases need.

Backed by the ``settings`` table in production; a simple provider in tests. See
``docs/CONFIGURATION.md`` §3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LedgerLimits:
    amount_max_minor: int
    backdate_window_days: int
    block_overspend: bool


class SettingsProvider(ABC):
    @abstractmethod
    def ledger_limits(self) -> LedgerLimits: ...

    @abstractmethod
    def org_timezone(self) -> str: ...
