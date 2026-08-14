"""Command-line entry point for local Invoicebook draft validation and packet creation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from invoicebook.config import ConfigError, InvoicePlan, load_invoice
from invoicebook.report import document, write_bundle
from invoicebook.service import InvoiceAssessment, calculate


def build_parser() -> argparse.ArgumentParser:
    """Create small explicit check/build commands for local invoice-draft work only."""

    parser = argparse.ArgumentParser(
        prog="invoicebook",
        description=(
            "Build declared local invoice drafts without legal, tax, issue, or payment validation."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "build"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("plan", type=Path, help="Declared TOML invoice-draft plan")
        subparser.add_argument(
            "--json", action="store_true", help="Print machine-readable draft data"
        )
        if command == "build":
            subparser.add_argument(
                "--output",
                required=True,
                type=Path,
                help="New local invoice-draft output directory",
            )
    return parser


def concise_text(plan: InvoicePlan, assessment: InvoiceAssessment) -> str:
    """Render a compact draft summary while keeping all external completion unverified."""

    return "\n".join(
        [
            f"Invoice draft: {plan.invoice.number}",
            "State: DRAFT — LEGAL, TAX, ISSUE, AND PAYMENT STATUS UNVERIFIED",
            f"Declared gross cents: {assessment.gross_cents}",
            "Invoicebook does not validate legal completeness, tax, payment, or issue evidence.",
        ]
    )


def run(plan_path: Path) -> tuple[InvoicePlan, InvoiceAssessment]:
    """Load and sum one local declaration without contacting or changing any outside system."""

    plan = load_invoice(plan_path)
    return plan, calculate(plan)


def main(argv: Sequence[str] | None = None) -> int:
    """Run local validation or create a new invoice-draft review packet."""

    args = build_parser().parse_args(argv)
    try:
        plan, assessment = run(args.plan)
        if args.command == "build":
            bundle = write_bundle(assessment, args.output)
            payload = document(assessment)
            payload["output_directory"] = str(bundle.output_path)
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"Wrote local invoice-draft packet: {bundle.output_path}")
                print(concise_text(plan, assessment))
        elif args.json:
            print(json.dumps(document(assessment), indent=2, sort_keys=True))
        else:
            print(concise_text(plan, assessment))
        return 0
    except (ConfigError, FileExistsError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
