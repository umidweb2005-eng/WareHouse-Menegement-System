"""Ledger domain: immutable donation/expense entries and reversal rules.

Financial facts are append-only. Corrections are reversals whose effect is
*derived* from the original entry (a reversal never stores its own amount). See
``docs/BUSINESS_RULES.md`` and ``docs/adr/0010-annotations-and-derived-reversal.md``.
"""
