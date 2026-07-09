"""Annotations domain: optional, private (staff-only) free text on ledger entries.

Annotations are append-only; the only permitted mutation is a PII redaction that
overwrites the content. See ``docs/adr/0009-public-private-and-pii-erasure.md``.
"""
