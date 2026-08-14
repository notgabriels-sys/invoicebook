"""End-to-end Invoicebook command behaviour tests."""

from __future__ import annotations

import json

from invoicebook.cli import main
from tests.helpers import write_plan


def test_check_prints_machine_readable_declared_totals(tmp_path, capsys):
    plan = write_plan(tmp_path)

    assert main(["check", str(plan), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"]["gross_cents"] == 139000
    assert payload["issue_status"] == "unverified"


def test_build_creates_packet_and_refuses_existing_output(tmp_path, capsys):
    plan = write_plan(tmp_path)
    output = tmp_path / "packet"

    assert main(["build", str(plan), "--output", str(output)]) == 0
    assert (output / "INVOICE_DRAFT.html").is_file()
    assert main(["build", str(plan), "--output", str(output)]) == 1
    assert "already exists" in capsys.readouterr().err


def test_invalid_plan_returns_nonzero_without_traceback(tmp_path, capsys):
    plan = write_plan(tmp_path, '[invoice]\nnumber = "incomplete"\n')

    assert main(["check", str(plan)]) == 1
    assert capsys.readouterr().err.startswith("error:")
