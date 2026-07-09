"""Adapters: concrete implementations of ports for specific technologies.

Inbound (drivers): ``telegram`` (aiogram), ``scheduler``.
Outbound (driven): ``persistence`` (SQLAlchemy/PostgreSQL), ``backup``.
Future: ``external`` (bank/payment gateways, post-v1).
"""
