"""Local Invoicebook draft documents with clear legal, issue, and payment evidence boundaries."""

from __future__ import annotations

import csv
import hashlib
import html
import json
from dataclasses import dataclass
from pathlib import Path

from invoicebook.config import LineItem
from invoicebook.service import InvoiceAssessment


@dataclass(frozen=True)
class InvoiceBundle:
    """New local artefacts; issue, payment, and legal completion stay unverified."""

    output_path: Path
    markdown_path: Path
    html_path: Path
    csv_path: Path
    checklist_path: Path
    document_path: Path
    manifest_path: Path


def money_text(cents: int, currency: str) -> str:
    """Format declared integer cents without validating currency or precision treatment."""

    sign = "-" if cents < 0 else ""
    whole, fraction = divmod(abs(cents), 100)
    return f"{currency} {sign}{whole:,}.{fraction:02d}"


def markdown_cell(value: object) -> str:
    """Keep declared text predictable in Markdown tables."""

    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def document(assessment: InvoiceAssessment) -> dict[str, object]:
    """Return only declared field values and exact totals, not legal/tax/payment evidence."""

    plan = assessment.plan
    invoice = plan.invoice
    return {
        "schema_version": 1,
        "status": assessment.status,
        "issue_status": "unverified",
        "payment_status": "unverified",
        "invoice": {
            "number": invoice.number,
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "issuer_name": invoice.issuer_name,
            "recipient_name": invoice.recipient_name,
            "currency": invoice.currency,
            "requirements_basis": invoice.requirements_basis,
            "payment_terms": invoice.payment_terms,
            "payment_instruction": invoice.payment_instruction,
            "notes": invoice.notes,
        },
        "line_items": [
            {
                "position": item.position,
                "id": item.id,
                "description": item.description,
                "net_cents": item.net_cents,
                "tax_cents": item.tax_cents,
                "gross_cents": item.net_cents + item.tax_cents,
                "tax_note": item.tax_note,
            }
            for item in plan.line_items
        ],
        "totals": {
            "net_cents": assessment.net_cents,
            "tax_cents": assessment.tax_cents,
            "gross_cents": assessment.gross_cents,
        },
        "scope_boundary": (
            "Declared integer-cent summation and draft rendering only; no validation of "
            "legal invoice completeness, client identity, tax treatment, currency "
            "treatment, contract scope, issue, delivery, payment instruction, payment "
            "evidence, accounting, or compliance."
        ),
    }


def render_markdown(assessment: InvoiceAssessment) -> str:
    """Render a readable draft that never represents itself as a finalized legal invoice."""

    invoice = assessment.plan.invoice
    lines = [
        f"# Invoice draft — {invoice.number}",
        "",
        "**State:** DRAFT — LEGAL, TAX, ISSUE, AND PAYMENT STATUS UNVERIFIED  ",
        f"**Issue date (declared):** {invoice.issue_date.isoformat()}  ",
        f"**Due date (declared):** {invoice.due_date.isoformat()}  ",
        f"**Currency (declared):** {invoice.currency}",
        "",
        "## Parties (declared)",
        "",
        f"**Issuer:** {invoice.issuer_name}  ",
        f"**Recipient:** {invoice.recipient_name}",
        "",
        "## Declared line items",
        "",
        "| # | ID | Description | Net | Declared tax | Gross | Declared tax note |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in assessment.plan.line_items:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.position),
                    f"`{item.id}`",
                    markdown_cell(item.description),
                    money_text(item.net_cents, invoice.currency),
                    money_text(item.tax_cents, invoice.currency),
                    money_text(item.net_cents + item.tax_cents, invoice.currency),
                    markdown_cell(item.tax_note),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            f"**Declared net total:** {money_text(assessment.net_cents, invoice.currency)}  ",
            f"**Declared tax total:** {money_text(assessment.tax_cents, invoice.currency)}  ",
            f"**Declared gross total:** {money_text(assessment.gross_cents, invoice.currency)}",
            "",
            "## Declared payment terms and notes",
            "",
            f"**Payment terms:** {invoice.payment_terms}  ",
            f"**Payment instruction:** {invoice.payment_instruction}  ",
            f"**Notes:** {invoice.notes}",
            "",
            "## Requirements basis",
            "",
            invoice.requirements_basis,
            "",
            "## Scope boundary",
            "",
            (
                "Invoicebook sums only the cents you declare and renders a local draft. "
                "It does not validate legal invoice completeness, client identity, tax "
                "treatment, currency treatment, contract scope, issue, delivery, payment "
                "instruction, payment evidence, accounting, or compliance. Complete the "
                "separate issue checklist before treating this as an actual invoice."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def html_item_row(item: LineItem, currency: str) -> str:
    """Return one safely escaped HTML table row for a declared invoice line item."""

    values = [
        str(item.position),
        item.id,
        item.description,
        money_text(item.net_cents, currency),
        money_text(item.tax_cents, currency),
        money_text(item.net_cents + item.tax_cents, currency),
        item.tax_note,
    ]
    cells = "".join(f"<td>{html.escape(value)}</td>" for value in values)
    return f"      <tr>{cells}</tr>"


def render_html(assessment: InvoiceAssessment) -> str:
    """Render a local print-friendly draft HTML document without a legal-completeness claim."""

    invoice = assessment.plan.invoice
    currency = invoice.currency
    rows = "\n".join(html_item_row(item, currency) for item in assessment.plan.line_items)
    values = {
        "number": html.escape(invoice.number),
        "issue_date": html.escape(invoice.issue_date.isoformat()),
        "due_date": html.escape(invoice.due_date.isoformat()),
        "issuer": html.escape(invoice.issuer_name),
        "recipient": html.escape(invoice.recipient_name),
        "terms": html.escape(invoice.payment_terms),
        "instruction": html.escape(invoice.payment_instruction),
        "notes": html.escape(invoice.notes),
        "basis": html.escape(invoice.requirements_basis),
        "net": html.escape(money_text(assessment.net_cents, currency)),
        "tax": html.escape(money_text(assessment.tax_cents, currency)),
        "gross": html.escape(money_text(assessment.gross_cents, currency)),
        "rows": rows,
    }
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Invoice draft — {number}</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ color: #202124; font: 15px/1.5 system-ui, sans-serif; margin: 0; }}
      main {{ margin: 0 auto; max-width: 880px; padding: 56px; }}
      h1 {{ font-size: 30px; margin: 0 0 8px; }}
      h2 {{ font-size: 16px; margin: 32px 0 8px; }}
      .state {{ border-left: 4px solid #b99a6a; padding-left: 12px; }}
      .parties {{ display: grid; gap: 16px; grid-template-columns: 1fr 1fr; }}
      table {{ border-collapse: collapse; margin-top: 12px; width: 100%; }}
      th, td {{ border-bottom: 1px solid #ddd7cd; padding: 9px 8px; text-align: left; }}
      th {{ background: #f2efe8; }}
      td:nth-child(4), td:nth-child(5), td:nth-child(6) {{ text-align: right; }}
      .totals {{ margin-left: auto; max-width: 330px; }}
      .totals p {{ display: flex; justify-content: space-between; margin: 5px 0; }}
      .gross {{ border-top: 2px solid #202124; font-weight: 700; padding-top: 8px; }}
      .boundary {{ background: #f2efe8; padding: 16px; }}
      @media print {{ main {{ padding: 24px; }} }}
    </style>
  </head>
  <body>
    <main>
      <p class="state">
        <strong>DRAFT</strong> — legal, tax, issue, and payment status unverified.
      </p>
      <h1>Invoice draft — {number}</h1>
      <p>Declared issue date: {issue_date}<br>Declared due date: {due_date}</p>
      <section class="parties">
        <div><h2>Issuer (declared)</h2><p>{issuer}</p></div>
        <div><h2>Recipient (declared)</h2><p>{recipient}</p></div>
      </section>
      <h2>Declared line items</h2>
      <table>
        <thead>
          <tr>
            <th>#</th><th>ID</th><th>Description</th><th>Net</th>
            <th>Tax</th><th>Gross</th><th>Tax note</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
      <section class="totals">
        <p><span>Declared net total</span><span>{net}</span></p>
        <p><span>Declared tax total</span><span>{tax}</span></p>
        <p class="gross"><span>Declared gross total</span><span>{gross}</span></p>
      </section>
      <h2>Declared terms</h2>
      <p><strong>Payment terms:</strong> {terms}</p>
      <p><strong>Payment instruction:</strong> {instruction}</p>
      <p><strong>Notes:</strong> {notes}</p>
      <h2>Requirements basis</h2>
      <p>{basis}</p>
      <p class="boundary">
        This is a local draft that sums declared cents. Verify legal completeness,
        tax treatment, client identity, payment details, issue, and payment evidence independently.
      </p>
    </main>
  </body>
</html>
""".format(**values)


def render_issue_checklist(assessment: InvoiceAssessment) -> str:
    """Render external evidence gates without claiming issuance or payment."""

    invoice = assessment.plan.invoice
    return "\n".join(
        [
            f"# Issue checklist — {invoice.number}",
            "",
            "**State:** ALL EXTERNAL GATES UNVERIFIED",
            "",
            "- [ ] **UNVERIFIED** — Issuer legal identity, address, registration, "
            "and required fields are correct for the applicable jurisdiction.",
            "- [ ] **UNVERIFIED** — Recipient identity and delivery details are "
            "correct for the actual client.",
            "- [ ] **UNVERIFIED** — Every declared net/tax cent amount and tax "
            "treatment has been checked against the real agreement and records.",
            "- [ ] **UNVERIFIED** — Currency, payment terms, due date, and payment "
            "instruction are correct for the real arrangement.",
            "- [ ] **UNVERIFIED** — Work scope, dates, invoice number, and "
            "requirements basis match the actual approved work.",
            "- [ ] **UNVERIFIED** — The final invoice was issued through the intended "
            "workflow and evidence was retained.",
            "- [ ] **UNVERIFIED** — Payment receipt or payment status has been "
            "independently checked; this draft does not establish it.",
            "",
            "Invoicebook cannot complete or verify any of these external gates.",
            "",
        ]
    )


def write_csv(assessment: InvoiceAssessment, path: Path) -> None:
    """Write declared lines and gross totals without calculating a tax rate."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "position",
                "id",
                "description",
                "net_cents",
                "tax_cents",
                "gross_cents",
                "tax_note",
            ],
        )
        writer.writeheader()
        for item in assessment.plan.line_items:
            writer.writerow(
                {
                    "position": item.position,
                    "id": item.id,
                    "description": item.description,
                    "net_cents": item.net_cents,
                    "tax_cents": item.tax_cents,
                    "gross_cents": item.net_cents + item.tax_cents,
                    "tax_note": item.tax_note,
                }
            )


def sha256(path: Path) -> str:
    """Return a generated-artifact fingerprint for the portable local manifest."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(assessment: InvoiceAssessment, output_path: Path) -> InvoiceBundle:
    """Create a new draft packet without overwriting a prior invoice-review directory."""

    if output_path.exists():
        raise FileExistsError(f"output directory already exists: {output_path}")
    output_path.mkdir(parents=True)
    markdown_path = output_path / "INVOICE_DRAFT.md"
    html_path = output_path / "INVOICE_DRAFT.html"
    csv_path = output_path / "line-items.csv"
    checklist_path = output_path / "ISSUE_CHECKLIST.md"
    document_path = output_path / "invoice.json"
    manifest_path = output_path / "manifest.json"
    markdown_path.write_text(render_markdown(assessment), encoding="utf-8")
    html_path.write_text(render_html(assessment), encoding="utf-8")
    write_csv(assessment, csv_path)
    checklist_path.write_text(render_issue_checklist(assessment), encoding="utf-8")
    document_path.write_text(
        json.dumps(document(assessment), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated_files = (markdown_path, html_path, csv_path, checklist_path, document_path)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": assessment.status,
                "source_plan": {
                    "file_name": assessment.plan.source_path.name,
                    "sha256": sha256(assessment.plan.source_path),
                },
                "generated_files": [
                    {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
                    for path in generated_files
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return InvoiceBundle(
        output_path=output_path,
        markdown_path=markdown_path,
        html_path=html_path,
        csv_path=csv_path,
        checklist_path=checklist_path,
        document_path=document_path,
        manifest_path=manifest_path,
    )
