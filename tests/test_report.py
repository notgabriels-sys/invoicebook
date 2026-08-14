"""Tests for local Invoicebook draft packets."""

from __future__ import annotations

import csv
import hashlib
import json

import pytest

from invoicebook.config import load_invoice
from invoicebook.report import document, write_bundle
from invoicebook.service import calculate
from tests.helpers import VALID_PLAN, write_plan


def test_document_keeps_issue_and_payment_unverified(tmp_path):
    assessment = calculate(load_invoice(write_plan(tmp_path)))
    payload = document(assessment)

    assert payload["status"] == "draft_external_completeness_unverified"
    assert payload["issue_status"] == "unverified"
    assert payload["payment_status"] == "unverified"


def test_build_writes_escaped_hashed_draft_packet(tmp_path):
    html_sensitive = VALID_PLAN.replace("Fictional mixing service", "Fictional mixing & prep")
    assessment = calculate(load_invoice(write_plan(tmp_path, html_sensitive)))
    bundle = write_bundle(assessment, tmp_path / "packet")

    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    assert {entry["path"] for entry in manifest["generated_files"]} == {
        "INVOICE_DRAFT.md",
        "INVOICE_DRAFT.html",
        "ISSUE_CHECKLIST.md",
        "invoice.json",
        "line-items.csv",
    }
    for entry in manifest["generated_files"]:
        artifact = bundle.output_path / entry["path"]
        assert artifact.stat().st_size == entry["bytes"]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == entry["sha256"]
    assert "Fictional mixing &amp; prep" in bundle.html_path.read_text(encoding="utf-8")
    with bundle.csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["id"] for row in rows] == ["mix-service", "prep-service"]
    assert "UNVERIFIED" in bundle.checklist_path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        write_bundle(assessment, bundle.output_path)
