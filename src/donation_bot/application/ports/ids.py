"""IdGenerator port: produces opaque unique identifiers for entities."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IdGenerator(ABC):
    @abstractmethod
    def new_id(self) -> str:
        """Return a new unique identifier (e.g., a UUID string)."""
