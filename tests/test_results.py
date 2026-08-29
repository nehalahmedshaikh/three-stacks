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
WITNESS = from_string(
    "6-11-4-16-2-8-19-5-14-9-17-12-20-3-15-7-23-10-21-18-13-22-1")

BASIS_FILE = ROOT / "results" / "basis_k3_n23.json"
CLAIMS_FILE = ROOT / "results" / "claims.json"


@pytest.mark.slow
def test_witness_is_unsortable():
    assert not solve(WITNESS, k=3, mode="reduced").sortable


@pytest.mark.slow
def test_witness_is_a_basis_element():
    for i in range(len(WITNESS)):
        q = delete_positions(WITNESS, [i])
        r = solve(q, k=3, mode="reduced")
        assert r.sortable, f"deleting position {i} leaves an unsortable {q}"
        assert verify.sorts(list(q), r.ops, k=3)


@pytest.mark.skipif(not BASIS_FILE.exists(), reason="run scripts/verify_basis.py")
def test_recorded_basis_operation_words_all_replay():
    """Every stored deletion witness really sorts -- no solver needed."""
    data = json.loads(BASIS_FILE.read_text())
    assert data["is_basis_element"] is True
    assert data["n"] == len(WITNESS)
    assert len(data["deletions"]) == len(WITNESS)
    for d in data["deletions"]:
        q = from_string(d["pattern"])
        assert d["ops"], d
        assert verify.sorts(list(q), verify.parse_ops(d["ops"]), k=data["k"]), d


@pytest.mark.skipif(not CLAIMS_FILE.exists(), reason="run scripts/certify.py")
def test_claims_file_is_self_consistent():
    """Every claim is coherent, and every shipped artifact is where it says.

    Only the shortest witnesses ship their (large) CNF/DRAT pair; the rest
    are gitignored because they regenerate deterministically from the
    permutation.  So a missing artifact is not a failure -- but a claim that
    contradicts itself is.
    """
    claims = json.loads(CLAIMS_FILE.read_text())
    assert claims, "no claims recorded"
    for c in claims:
        second = c.get("second_solver", {})
        assert second.get("agrees") is not False, f"{c['id']}: solvers disagree"
        bf = c.get("brute_force") or {}
        assert bf.get("agrees") is not False, f"{c['id']}: brute force disagrees"
        if c["sortable"]:
            perm = from_string(c["perm"])
            assert verify.sorts(list(perm), verify.parse_ops(c["ops"]), k=c["k"])
        else:
            assert c.get("drat"), c["id"]
            if (ROOT / c["cnf"]).exists():
                # if the CNF ships, its header must match the recorded sizes
                head = (ROOT / c["cnf"]).read_text().splitlines()
                pline = next(l for l in head if l.startswith("p cnf"))
                _, _, nv, nc = pline.split()
                assert int(nv) == c["n_vars"] and int(nc) == c["n_clauses"], c["id"]


@pytest.mark.skipif(not CLAIMS_FILE.exists(), reason="run scripts/certify.py")
def test_shortest_witness_ships_its_certificate():
    """A reader must be able to check the headline claim without a solver."""
    claims = json.loads(CLAIMS_FILE.read_text())
    unsat = [c for c in claims if not c["sortable"] and c["k"] == 3]
    best = min(unsat, key=lambda c: c["n"])
    assert (ROOT / best["cnf"]).exists(), (
        f"{best['id']} is the headline claim but its CNF is not committed")
    assert (ROOT / best["drat"]).exists(), (
        f"{best['id']} is the headline claim but its DRAT is not committed")


@pytest.mark.skipif(not CLAIMS_FILE.exists(), reason="run scripts/certify.py")
def test_best_claim_beats_the_previous_record():
    """Atkinson 1992 held 38; anything we publish should be shorter."""
    claims = json.loads(CLAIMS_FILE.read_text())
    unsat = [c for c in claims if not c["sortable"] and c["k"] == 3]
    assert unsat, "no k=3 unsortable claims"
    assert min(c["n"] for c in unsat) <= 23
