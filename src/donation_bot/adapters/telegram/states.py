"""Finite-state-machine groups for guided Telegram flows (aiogram)."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class DonationFSM(StatesGroup):
    amount = State()
    source = State()
    note = State()


class ExpenseFSM(StatesGroup):
    amount = State()
    category = State()
    description = State()


class RegisterStaffFSM(StatesGroup):
    telegram_id = State()
    role = State()


class ConfigureAccountFSM(StatesGroup):
    label = State()
    account_type = State()
    value = State()
    holder = State()
