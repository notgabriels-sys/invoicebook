"""Strict TOML parsing for Invoicebook’s declared invoice-draft schema."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a declared invoice draft is structurally invalid."""


IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CURRENCY = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class Invoice:
    """Declared draft context; it is not proof of an issued or legally complete invoice."""

    number: str
    issue_date: date
    due_date: date
    issuer_name: str
    recipient_name: str
    currency: str
    requirements_basis: str
    payment_terms: str
    payment_instruction: str
    notes: str


@dataclass(frozen=True)
class LineItem:
    """One declared service line with human-supplied net and tax cents."""

    position: int
    id: str
    description: str
    net_cents: int
    tax_cents: int
    tax_note: str


@dataclass(frozen=True)
class InvoicePlan:
    """A parsed local declaration with no legal, tax, payment, or external-system validation."""

    source_path: Path
    invoice: Invoice
    line_items: tuple[LineItem, ...]


def unexpected_fields(table: dict[str, Any], allowed: set[str], context: str) -> None:
    """Reject untracked fields so every draft value is visible in a compact schema."""

    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ConfigError(f"unexpected {context} field(s): {', '.join(unknown)}")


def require_table(value: object, context: str) -> dict[str, Any]:
    """Return a TOML table or raise a concise schema error."""

    if not isinstance(value, dict):
        raise ConfigError(f"{context} must be a TOML table")
    return value


def require_list(value: object, context: str) -> list[object]:
    """Return a nonempty TOML array without coercing strings or tables into items."""

    if not isinstance(value, list) or not value:
        raise ConfigError(f"{context} must be a nonempty TOML array")
    return value


def require_text(table: dict[str, Any], key: str, context: str) -> str:
    """Read one required nonblank draft text field."""

    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{context}.{key} must be a nonblank string")
    return value.strip()


def require_date(table: dict[str, Any], key: str, context: str) -> date:
    """Read a declared ISO date without inferring whether it is legally correct or appropriate."""

    value = require_text(table, key, context)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ConfigError(f"{context}.{key} must be an ISO date (YYYY-MM-DD)") from error


def require_position(table: dict[str, Any], context: str) -> int:
    """Read a positive item position while rejecting bool-to-int coercion."""

    value = table.get("position")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"{context}.position must be a positive integer")
    return value


def require_cents(table: dict[str, Any], key: str, context: str, *, positive: bool) -> int:
    """Read exact declared cents without calculating a tax rate or hidden rounding convention."""

    value = table.get(key)
    minimum = 1 if positive else 0
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        expectation = "positive" if positive else "nonnegative"
        raise ConfigError(f"{context}.{key} must be a {expectation} integer number of cents")
    return value


def parse_invoice(value: object) -> Invoice:
    """Parse context fields, keeping legal and tax validity outside the tool’s scope."""

    table = require_table(value, "invoice")
    unexpected_fields(
        table,
        {
            "number",
            "issue_date",
            "due_date",
            "issuer_name",
            "recipient_name",
            "currency",
            "requirements_basis",
            "payment_terms",
            "payment_instruction",
            "notes",
        },
        "invoice",
    )
    issue_date = require_date(table, "issue_date", "invoice")
    due_date = require_date(table, "due_date", "invoice")
    if due_date < issue_date:
        raise ConfigError("invoice.due_date must not precede invoice.issue_date")
    currency = require_text(table, "currency", "invoice")
    if not CURRENCY.fullmatch(currency):
        raise ConfigError("invoice.currency must be a three-letter uppercase declared code")
    return Invoice(
        number=require_text(table, "number", "invoice"),
        issue_date=issue_date,
        due_date=due_date,
        issuer_name=require_text(table, "issuer_name", "invoice"),
        recipient_name=require_text(table, "recipient_name", "invoice"),
        currency=currency,
        requirements_basis=require_text(table, "requirements_basis", "invoice"),
        payment_terms=require_text(table, "payment_terms", "invoice"),
        payment_instruction=require_text(table, "payment_instruction", "invoice"),
        notes=require_text(table, "notes", "invoice"),
    )


def parse_line_items(value: object) -> tuple[LineItem, ...]:
    """Parse ordered cent values that a human has already decided and declared."""

    items: list[LineItem] = []
    seen_ids: set[str] = set()
    seen_positions: set[int] = set()
    for index, raw in enumerate(require_list(value, "line_items"), start=1):
        context = f"line_items[{index}]"
        table = require_table(raw, context)
        unexpected_fields(
            table,
            {"position", "id", "description", "net_cents", "tax_cents", "tax_note"},
            context,
        )
        position = require_position(table, context)
        identifier = require_text(table, "id", context)
        if not IDENTIFIER.fullmatch(identifier):
            raise ConfigError(f"{context}.id must use lowercase kebab-case")
        if identifier in seen_ids:
            raise ConfigError(f"duplicate line item id: {identifier}")
        if position in seen_positions:
            raise ConfigError(f"duplicate line item position: {position}")
        seen_ids.add(identifier)
        seen_positions.add(position)
        items.append(
            LineItem(
                position=position,
                id=identifier,
                description=require_text(table, "description", context),
                net_cents=require_cents(table, "net_cents", context, positive=True),
                tax_cents=require_cents(table, "tax_cents", context, positive=False),
                tax_note=require_text(table, "tax_note", context),
            )
        )
    items.sort(key=lambda item: item.position)
    positions = [item.position for item in items]
    expected = list(range(1, len(items) + 1))
    if positions != expected:
        raise ConfigError("line item positions must run contiguously from 1")
    return tuple(items)


def load_invoice(path: Path) -> InvoicePlan:
    """Load one strict local TOML declaration for draft rendering and cent-total review."""

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"invoice file does not exist: {path}") from error
    except OSError as error:
        raise ConfigError(f"could not read invoice file: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"invalid TOML invoice: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigError("invoice root must be a TOML table")
    unexpected_fields(raw, {"invoice", "line_items"}, "top-level")
    if "invoice" not in raw or "line_items" not in raw:
        raise ConfigError(
            "invoice TOML must contain [invoice] and at least one [[line_items]] table"
        )
    return InvoicePlan(
        source_path=path.resolve(),
        invoice=parse_invoice(raw["invoice"]),
        line_items=parse_line_items(raw["line_items"]),
    )
