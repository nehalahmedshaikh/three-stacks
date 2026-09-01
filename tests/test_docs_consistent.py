"""The prose must agree with the data.

The headline number lives in README.md, results.md and results/claims.json,
which drifted apart twice while the bound was coming down (24 -> 23 -> 22).
These tests make that a build failure.

Claims tagged ``external`` are verifications of other people's results (the
Pantone-Vatter length-21 witness) and are excluded when deciding what this
repo's own headline should be.
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


def own_claims(k: int = 3) -> list[dict]:
    claims = json.loads(CLAIMS.read_text())
    return [c for c in claims
            if c["k"] == k and not c["sortable"] and not c.get("external")]


def shortest_claim(k: int = 3) -> dict:
    own = own_claims(k)
    assert own, "no unsortable claims of our own recorded"
    return min(own, key=lambda c: c["n"])


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
    """A superseded witness may be mentioned, but not lead the document."""
    best = shortest_claim()
    text = doc.read_text(encoding="utf-8")
    head = text[:text.index(best["perm"])] if best["perm"] in text else text
    longer = [c["perm"] for c in own_claims() if c["n"] > best["n"]]
    for perm in longer:
        assert perm not in head, (
            f"{doc.name} leads with the superseded witness {perm}")


@pytest.mark.parametrize("doc", [README, RESULTS])
def test_stated_interval_matches_the_bound(doc):
    """Any '[14, N]' in the prose must use this repo's own best N."""
    best = shortest_claim()
    text = doc.read_text(encoding="utf-8")
    intervals = set(re.findall(r"\[14,\s*(\d+)\]", text))
    assert intervals, f"{doc.name} states no [14, N] interval"
    assert intervals == {str(best["n"])}, (
        f"{doc.name} states interval(s) {sorted(intervals)} but our shortest "
        f"certified witness has length {best['n']}")


def test_external_results_are_credited_and_linked():
    """A third-party witness must name its source and be linked from the README."""
    claims = json.loads(CLAIMS.read_text())
    ext = [c for c in claims if c.get("external")]
    if not ext:
        pytest.skip("no external claims recorded")
    readme = README.read_text(encoding="utf-8")
    for c in ext:
        assert c.get("source"), f"{c['id']} is external but names no source"
        assert c["perm"] in readme, (
            f"external witness {c['perm']} is certified but not shown in the README")
        assert "vincevatter.com/talks/2026-mathfest-stacks" in readme, (
            "the README must link the talk the external result comes from")


def test_readme_flags_the_result_as_superseded():
    readme = README.read_text(encoding="utf-8")
    head = readme[:1400]
    assert "superseded" in head.lower(), (
        "the README must say up front that the bound has been superseded")


def test_claims_and_basis_reports_agree():
    for bf in (ROOT / "results").glob("basis_k3_n*.json"):
        d = json.loads(bf.read_text())
        claims = {c["perm"] for c in json.loads(CLAIMS.read_text())}
        assert d["perm"] in claims, (
            f"{bf.name} certifies {d['perm']} but it is not in claims.json")
