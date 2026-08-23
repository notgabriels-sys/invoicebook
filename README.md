# Invoicebook

Invoicebook is an offline invoice-*draft* packet builder for freelance work. You declare parties, dates, payment text, line-item net cents, and already-decided tax cents in one local TOML file; it checks the internal structure and arithmetic, then creates editable Markdown and print-friendly HTML drafts plus CSV/JSON review records.

It is useful for turning already-reviewed work/fee values into a consistent draft before you issue an invoice through the actual legal, accounting, and payment workflow.

## The output is intentionally a draft

Every generated document begins with:

```text
DRAFT — LEGAL, TAX, ISSUE, AND PAYMENT STATUS UNVERIFIED
```

A valid Invoicebook file and a correct arithmetic total do not establish legal invoice completeness, client identity, tax treatment, payment instruction, issue, delivery, or payment. The included `ISSUE_CHECKLIST.md` leaves all of those external gates `UNVERIFIED` for a person to check against the applicable agreement, jurisdiction, records, and workflow.

## What it checks and calculates

- Required declared draft fields: number, issue date, due date, issuer, recipient, currency, basis, terms, instruction, and notes.
- ISO issue/due dates, with the due date not before the issue date.
- Ordered, contiguous, unique lower-kebab-case line item IDs.
- Positive declared `net_cents` and nonnegative declared `tax_cents` for every line.
- Exact net, tax, and gross totals from integer cents only.
- A local HTML draft with escaped declared text, Markdown draft, line-item CSV, JSON record, issue checklist, and generated-file hash manifest.

```text
invoice-draft-packet/
├── INVOICE_DRAFT.md
├── INVOICE_DRAFT.html
├── line-items.csv
├── invoice.json
├── ISSUE_CHECKLIST.md
└── manifest.json
```

## What it does not do

Invoicebook does **not** calculate tax, select a rate, validate a tax/currency treatment, convert currency, determine required invoice fields, verify parties, send an invoice, issue an invoice, create an accounting entry, contact a client, inspect a bank/payment provider, or mark anything paid.

The `tax_cents` field is an explicit amount you have already chosen and need to verify separately. This avoids hiding tax assumptions or rounding conventions inside the tool. Read the full [scope boundary](docs/scope-boundary.md).

## Install

Requires Python 3.11 or later.

```sh
uv tool install .
```

For development:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

## Use

Start with the fictional example and replace every field only after checking the actual facts yourself.

```sh
invoicebook check examples/invoice-example.toml
invoicebook check examples/invoice-example.toml --json
invoicebook build examples/invoice-example.toml --output ./delivery/invoice-draft-001
```

`check` is read-only. `build` refuses to overwrite an existing output directory and returns:

- `0` — the declared schema and cent arithmetic are internally consistent; all external facts remain unverified.
- `1` — invalid/missing TOML, invalid declared fields, or an existing output directory.

## Input format

```toml
[invoice]
number = "EXAMPLE-2026-001"
issue_date = "2026-08-14"
due_date = "2026-08-28"
issuer_name = "Example Studio"
recipient_name = "Example Client"
currency = "EUR"
requirements_basis = "Fictional example only; verify actual facts directly."
payment_terms = "Fictional terms: payment due within 14 days."
payment_instruction = "Fictional instruction: add verified payment details before issue."
notes = "Synthetic example invoice draft only."

[[line_items]]
position = 1
id = "mix-service"
description = "Fictional mixing service"
net_cents = 100000
tax_cents = 19000
tax_note = "Fictional declared tax amount; verify actual treatment."
```

`currency` is only a declared three-letter uppercase code for display. Amounts are always declared integer cents. Invoicebook does not verify that this representation, the code, the tax amount, or the line belongs in a real invoice.

## Practical review sequence

1. Confirm the real work scope, agreement, recipient, tax/currency treatment, and payment terms outside Invoicebook.
2. Enter the already-reviewed line net and tax amounts as integer cents, recording the source in `requirements_basis`.
3. Run `invoicebook check`, then inspect the local Markdown/HTML draft and the calculated totals.
4. Complete every external gate in `ISSUE_CHECKLIST.md` before issuing through the intended workflow.
5. Record actual issue and payment evidence in the appropriate accounting/payment system, not by treating this draft as proof.

## Development

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

Invoicebook uses Python’s standard library only. It has no network, browser, email, accounting-system, payment, upload, or destructive-file capability.

---

---

<!-- funnel-footer -->
Part of the Gabriel Tools + Code catalog — [browse all tools, products, repositories, and services](https://gabriel-tools-and-code.notgabriels960914.chatgpt.site/).

Free and open source: [theme-contrast](https://github.com/notgabriels-sys/theme-contrast) (WCAG contrast checking for colour themes) · [htmlshot](https://github.com/notgabriels-sys/htmlshot) (HTML → exact-size PNG/PDF) · [50 dark themes for Claude Code](https://github.com/notgabriels-sys/claude-code-50-dark-themes).

Hologram People soundware and Gabriel audio/product work are linked from the master catalog above.

Mixing and mastering enquiries — [public preview](https://gabriel-mixing-and-mastering-d1dmyt.v2.appdeploy.ai/).
