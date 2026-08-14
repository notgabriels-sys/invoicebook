"""Fictional invoice-draft fixtures shared by Invoicebook tests."""

from __future__ import annotations

from pathlib import Path

VALID_PLAN = """\
[invoice]
number = "EXAMPLE-2026-001"
issue_date = "2026-08-14"
due_date = "2026-08-28"
issuer_name = "Example Studio"
recipient_name = "Example Client"
currency = "EUR"
requirements_basis = "Fictional test declaration; confirm legal, tax, and client facts directly."
payment_terms = "Fictional terms: payment due within 14 days."
payment_instruction = "Fictional instruction: verify payment details before issue."
notes = "Synthetic test invoice only."

[[line_items]]
position = 1
id = "mix-service"
description = "Fictional mixing service"
net_cents = 100000
tax_cents = 19000
tax_note = "Fictional declared tax amount; verify actual treatment."

[[line_items]]
position = 2
id = "prep-service"
description = "Fictional preparation service"
net_cents = 20000
tax_cents = 0
tax_note = "Fictional declared zero-tax line; verify actual treatment."
"""


def write_plan(tmp_path: Path, content: str = VALID_PLAN, name: str = "invoice.toml") -> Path:
    """Write a fictional invoice declaration for one isolated test."""

    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path
