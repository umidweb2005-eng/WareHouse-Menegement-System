"""Persistence adapter: SQLAlchemy models, repositories, and Unit of Work.

Implements the repository/read-model ports against PostgreSQL. Enforces the
mutability matrix via schema constraints, triggers, and a least-privilege role
(see ``docs/DATABASE_DESIGN.md``).
"""
