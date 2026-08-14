"""Tests for transparent invoice-draft cent arithmetic."""

from __future__ import annotations

from invoicebook.config import load_invoice
from invoicebook.service import calculate
from tests.helpers import write_plan


def test_sums_only_declared_net_and_tax_cents(tmp_path):
    assessment = calculate(load_invoice(write_plan(tmp_path)))

    assert assessment.net_cents == 120000
    assert assessment.tax_cents == 19000
    assert assessment.gross_cents == 139000
    assert assessment.status == "draft_external_completeness_unverified"
