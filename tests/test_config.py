"""Tests for strict declared invoice-draft parsing."""

from __future__ import annotations

import pytest

from invoicebook.config import ConfigError, load_invoice
from tests.helpers import VALID_PLAN, write_plan


def test_loads_a_complete_fictional_invoice_declaration(tmp_path):
    plan = load_invoice(write_plan(tmp_path))

    assert plan.invoice.number == "EXAMPLE-2026-001"
    assert plan.invoice.currency == "EUR"
    assert [item.id for item in plan.line_items] == ["mix-service", "prep-service"]


def test_rejects_noncontiguous_line_item_positions(tmp_path):
    invalid = VALID_PLAN.replace("position = 2", "position = 3")

    with pytest.raises(ConfigError, match="contiguously"):
        load_invoice(write_plan(tmp_path, invalid))


def test_rejects_due_date_before_declared_issue_date(tmp_path):
    invalid = VALID_PLAN.replace('due_date = "2026-08-28"', 'due_date = "2026-08-13"')

    with pytest.raises(ConfigError, match="not precede"):
        load_invoice(write_plan(tmp_path, invalid))


def test_rejects_negative_declared_tax_cents(tmp_path):
    invalid = VALID_PLAN.replace("tax_cents = 19000", "tax_cents = -1")

    with pytest.raises(ConfigError, match="nonnegative integer"):
        load_invoice(write_plan(tmp_path, invalid))


def test_rejects_unknown_invoice_fields(tmp_path):
    invalid = VALID_PLAN.replace(
        'notes = "Synthetic test invoice only."', 'untracked = "not allowed"'
    )

    with pytest.raises(ConfigError, match="unexpected invoice"):
        load_invoice(write_plan(tmp_path, invalid))
