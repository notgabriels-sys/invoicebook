# Invoicebook scope boundary

Invoicebook is a local draft-rendering and integer-cent summation tool. A clean check proves only that its compact TOML schema is internally consistent: declared required text is nonblank, declared issue/due dates use ISO form and are in order, line positions are contiguous, declared net cents are positive, declared tax cents are nonnegative, and the printed totals equal the declared line amounts.

It does not calculate a tax rate, choose a tax treatment, apply a jurisdiction’s rounding method, validate a currency code, convert currency, or decide whether any value should be charged. Each line’s `net_cents` and `tax_cents` must already be human-decided and declared. The tool adds those values transparently; it is not an accounting or tax system.

The fields deliberately do not claim to be a complete legal invoice schema. Check the actual required issuer/recipient identity, address, registration, tax, numbering, date, payment, retention, and jurisdiction-specific fields directly before issue. A generated `INVOICE_DRAFT.html` is a print-friendly local draft, not evidence of an issued invoice.

Every generated packet includes `ISSUE_CHECKLIST.md` with all external gates marked `UNVERIFIED`, including legal completeness, client identity, tax treatment, payment instruction, actual issue, and actual payment. Neither a successful command nor a filled-looking draft proves any of those things.

Invoicebook makes no network request, logs into no accounting/payment system, sends no invoice, accepts no money, and never changes the source TOML. `build` writes a new local output directory only and refuses to overwrite an existing directory.
