"""`verify_basis.py` is the entry point a visitor with a candidate would use.

It once reported the identity permutation as a basis element: `--skip-certificate`
skipped the unsortability check rather than just the DRAT artifacts, and the
verdict was computed from the deletions alone.  Every deletion of the identity
is sortable, so it passed.  These tests exist so that cannot come back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import verify_basis


def run(perm, k, tmp_path, monkeypatch, extra=()):
    """Run main() with results/ redirected so tests never touch the repo."""
    monkeypatch.setattr(verify_basis, "RESULTS", tmp_path)
    argv = ["--perm", perm, "--k", str(k), "--skip-certificate", *extra]
    return verify_basis.main(argv)


@pytest.mark.parametrize("perm", ["1-2-3-4-5-6-7", "2-1-3", "1-2-3"])
def test_sortable_permutations_are_rejected(perm, tmp_path, monkeypatch):
    assert run(perm, 2, tmp_path, monkeypatch) == 1


def test_a_real_witness_is_accepted(tmp_path, monkeypatch):
    assert run("2435761", 2, tmp_path, monkeypatch) == 0


def test_a_non_minimal_witness_is_rejected(tmp_path, monkeypatch):
    """2435761 with a point inserted: unsortable, but not minimal."""
    assert run("2-4-3-5-7-6-1-8", 2, tmp_path, monkeypatch) == 1


def test_report_records_whether_a_certificate_was_made(tmp_path, monkeypatch):
    run("2435761", 2, tmp_path, monkeypatch)
    written = list(tmp_path.glob("basis_k2_n7*.json"))
    assert written, "no report was written"
    d = json.loads(written[0].read_text())
    assert d["is_basis_element"] is True
    assert d["unsortable_claim"]["certified"] is False, (
        "a run without a DRAT certificate must not claim to be certified")


def test_other_peoples_permutations_do_not_clobber_our_reports(tmp_path,
                                                               monkeypatch):
    """A visitor's run must not land on the filename the tests expect to
    match claims.json."""
    run("2435761", 2, tmp_path, monkeypatch)
    assert not (tmp_path / "basis_k2_n7.json").exists()
    assert list(tmp_path.glob("basis_k2_n7_*.json"))
