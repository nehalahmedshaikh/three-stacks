"""The published claims must keep checking out.

These guard the headline result against regressions in the encoder,
minimiser, or verifier.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify
from unsortable.encoding import solve
from unsortable.minimizer import delete_positions
from unsortable.perms import from_string

# The headline witness.  See results.md.
WITNESS_24 = from_string(
    "6-15-2-17-9-4-19-7-13-3-18-10-24-5-20-12-23-8-16-21-11-14-22-1")

BASIS_FILE = ROOT / "results" / "basis_k3_n24.json"
CLAIMS_FILE = ROOT / "results" / "claims.json"


@pytest.mark.slow
def test_witness_is_unsortable():
    assert not solve(WITNESS_24, k=3, mode="reduced").sortable


@pytest.mark.slow
def test_witness_is_a_basis_element():
    for i in range(len(WITNESS_24)):
        q = delete_positions(WITNESS_24, [i])
        r = solve(q, k=3, mode="reduced")
        assert r.sortable, f"deleting position {i} leaves an unsortable {q}"
        assert verify.sorts(list(q), r.ops, k=3)


@pytest.mark.skipif(not BASIS_FILE.exists(), reason="run scripts/verify_basis.py")
def test_recorded_basis_operation_words_all_replay():
    """Every stored deletion witness really sorts -- no solver needed."""
    data = json.loads(BASIS_FILE.read_text())
    assert data["is_basis_element"] is True
    assert data["n"] == len(WITNESS_24)
    assert len(data["deletions"]) == len(WITNESS_24)
    for d in data["deletions"]:
        q = from_string(d["pattern"])
        assert d["ops"], d
        assert verify.sorts(list(q), verify.parse_ops(d["ops"]), k=data["k"]), d


@pytest.mark.skipif(not CLAIMS_FILE.exists(), reason="run scripts/certify.py")
def test_claims_file_is_self_consistent():
    claims = json.loads(CLAIMS_FILE.read_text())
    assert claims, "no claims recorded"
    for c in claims:
        assert (ROOT / c["cnf"]).exists(), c["id"]
        if c["sortable"]:
            perm = from_string(c["perm"])
            assert verify.sorts(list(perm), verify.parse_ops(c["ops"]), k=c["k"])
        else:
            assert (ROOT / c["drat"]).exists(), c["id"]
            second = c.get("second_solver", {})
            assert second.get("agrees") is not False, c["id"]


@pytest.mark.skipif(not CLAIMS_FILE.exists(), reason="run scripts/certify.py")
def test_best_claim_beats_the_previous_record():
    """Atkinson 1992 held 38; anything we publish should be shorter."""
    claims = json.loads(CLAIMS_FILE.read_text())
    unsat = [c for c in claims if not c["sortable"] and c["k"] == 3]
    assert unsat, "no k=3 unsortable claims"
    assert min(c["n"] for c in unsat) <= 24
