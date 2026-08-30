"""The prose must agree with the data.

The headline number lives in README.md, results.md and results/claims.json,
which drifted apart twice while the bound was coming down (24 -> 23 -> 22).
These tests make that a build failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CLAIMS = ROOT / "results" / "claims.json"
README = ROOT / "README.md"
RESULTS = ROOT / "results.md"


def shortest_claim(k: int = 3) -> dict:
    claims = json.loads(CLAIMS.read_text())
    unsat = [c for c in claims if c["k"] == k and not c["sortable"]]
    assert unsat, "no unsortable claims recorded"
    return min(unsat, key=lambda c: c["n"])


pytestmark = pytest.mark.skipif(not CLAIMS.exists(), reason="run scripts/certify.py")


@pytest.mark.parametrize("doc", [README, RESULTS])
def test_headline_permutation_is_the_shortest_certified_one(doc):
    best = shortest_claim()
    text = doc.read_text(encoding="utf-8")
    assert best["perm"] in text, (
        f"{doc.name} does not contain the shortest certified witness "
        f"{best['perm']} (n={best['n']})")


@pytest.mark.parametrize("doc", [README, RESULTS])
def test_no_stale_longer_witness_presented_as_the_headline(doc):
    """A superseded witness may be *mentioned*, but not in the first heading."""
    best = shortest_claim()
    head = doc.read_text(encoding="utf-8")[:1200]
    claims = json.loads(CLAIMS.read_text())
    longer = [c["perm"] for c in claims
              if c["k"] == 3 and not c["sortable"] and c["n"] > best["n"]]
    for perm in longer:
        assert perm not in head, (
            f"{doc.name} leads with the superseded length-{len(perm.split('-'))} "
            f"witness {perm}")


@pytest.mark.parametrize("doc", [README, RESULTS])
def test_stated_interval_matches_the_bound(doc):
    """Any '[14, N]' in the prose must use the current best N."""
    best = shortest_claim()
    text = doc.read_text(encoding="utf-8")
    intervals = set(re.findall(r"\[14,\s*(\d+)\]", text))
    assert intervals, f"{doc.name} states no [14, N] interval"
    assert intervals == {str(best["n"])}, (
        f"{doc.name} states interval(s) {sorted(intervals)} but the shortest "
        f"certified witness has length {best['n']}")


def test_claims_and_basis_reports_agree():
    """Every basis report should correspond to a recorded claim."""
    for bf in (ROOT / "results").glob("basis_k3_n*.json"):
        d = json.loads(bf.read_text())
        claims = {c["perm"] for c in json.loads(CLAIMS.read_text())}
        assert d["perm"] in claims, (
            f"{bf.name} certifies {d['perm']} but it is not in claims.json")
