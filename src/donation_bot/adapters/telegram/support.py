"""Small framework-independent helpers for the Telegram adapter."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from donation_bot.application.ports.clock import Clock
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.infrastructure.i18n.translator import Translator

# Preset expense categories for the in-memory bot (no category table yet).
EXPENSE_CATEGORIES: dict[int, str] = {
    1: "Ehson (yordam)",
    2: "Kommunal",
    3: "Qurilish",
    4: "Boshqa",
}


def local_today(clock: Clock, org_timezone: str) -> date:
    return clock.now().astimezone(ZoneInfo(org_timezone)).date()


def role_label(actor: StaffUser | None, translator: Translator) -> str:
    if actor is None:
        return ""
    if actor.has_permission(Permission.USER_MANAGE):
        return translator.t("staff.role_admin")
    return translator.t("staff.role_treasurer")
