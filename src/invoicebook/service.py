"""Transparent integer-cent aggregation for declared Invoicebook draft fields."""

from __future__ import annotations

from dataclasses import dataclass

from invoicebook.config import InvoicePlan


@dataclass(frozen=True)
class InvoiceAssessment:
    """A calculated draft total with external completion explicitly unverified."""

    plan: InvoicePlan
    net_cents: int
    tax_cents: int
    gross_cents: int
    status: str


def calculate(plan: InvoicePlan) -> InvoiceAssessment:
    """Sum human-declared cents only; no rate, tax, currency, or legal treatment is inferred."""

    net_cents = sum(item.net_cents for item in plan.line_items)
    tax_cents = sum(item.tax_cents for item in plan.line_items)
    return InvoiceAssessment(
        plan=plan,
        net_cents=net_cents,
        tax_cents=tax_cents,
        gross_cents=net_cents + tax_cents,
        status="draft_external_completeness_unverified",
    )
