"""The promoted basis elements must stay well-formed and stay honest.

`results/basis_found.json` exists because the search log it came from is
git-ignored, so these permutations would not survive a fresh clone.  Since
they are recorded as basis elements without certificates, the provenance note
is part of the data and is checked here too.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable import perms
from unsortable.encoding import FixedLengthDecider

FOUND = ROOT / "results" / "basis_found.json"
CLAIMS = ROOT / "results" / "claims.json"

pytestmark = pytest.mark.skipif(
    not FOUND.exists(), reason="run scripts/promote_witnesses.py")


def data():
    return json.loads(FOUND.read_text())


def test_every_entry_is_a_permutation_of_its_stated_length():
    for k, levels in data()["basis"].items():
        for n, ps in levels.items():
            for s in ps:
                p = perms.from_string(s)
                assert len(p) == int(n), (k, n, s)
                assert sorted(p) == list(range(1, int(n) + 1)), s


def test_no_duplicates_within_a_level():
    for k, levels in data()["basis"].items():
        for n, ps in levels.items():
            assert len(ps) == len(set(ps)), (k, n)


def test_provenance_disclaims_certification():
    """These are solver verdicts; only claims.json entries have certificates."""
    prov = data()["provenance"].lower()
    assert "not" in prov and "certif" in prov
    assert "claims.json" in prov


def test_certified_claims_that_are_minimal_appear_here():
    claims = json.loads(CLAIMS.read_text())
    everything = {s for levels in data()["basis"].values()
                  for ps in levels.values() for s in ps}
    for c in claims:
        if c["k"] == 3 and not c["sortable"] and c["n"] <= 24:
            assert c["perm"] in everything, (
                f"{c['perm']} is a certified basis element but is missing "
                f"from basis_found.json")


@pytest.mark.slow
def test_shortest_promoted_element_really_is_minimal():
    """Re-decide the shortest own witness end to end."""
    levels = data()["basis"]["3"]
    n = min(int(x) for x in levels)
    for s in levels[str(n)]:
        p = perms.from_string(s)
        assert not FixedLengthDecider(n, k=3).is_sortable(p)
        dec = FixedLengthDecider(n - 1, k=3)
        for q in set(perms.one_point_deletions(p)):
            assert dec.is_sortable(q), (s, q)
