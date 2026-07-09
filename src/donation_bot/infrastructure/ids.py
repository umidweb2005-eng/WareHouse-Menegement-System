"""UUID-based id generator adapter."""

from __future__ import annotations

import uuid

from donation_bot.application.ports.ids import IdGenerator


class UuidGenerator(IdGenerator):
    def new_id(self) -> str:
        return str(uuid.uuid4())
