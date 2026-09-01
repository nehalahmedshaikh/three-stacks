"""The k=2 census, checked against the literature and against itself.

Atkinson (1992) found exactly 22 basis elements of length 7 for two stacks in
series.  That is an external number this project did not produce, so it is the
strongest single check available on the census machinery -- and, through it, on
the encoding.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable import perms
from unsortable.simulator import is_sortable

CENSUS = ROOT / "results" / "census_k2.json"

pytestmark = pytest.mark.skipif(
    not CENSUS.exists(), reason="run scripts/census.py --k 2 --maxlen 10")


def census():
    d = json.loads(CENSUS.read_text())
    return {int(n): [perms.from_string(s) for s in ps]
            for n, ps in d["basis"].items()}


def test_atkinson_count_of_22_at_length_seven():
    assert len(census()[7]) == 22


def test_the_standard_example_is_present():
    """2435761 is the example quoted in the literature for two stacks."""
    assert perms.from_string("2435761") in census()[7]


def test_counts_are_stable():
    got = {n: len(ps) for n, ps in census().items()}
    assert got == {7: 22, 8: 51, 9: 146, 10: 604}


def test_shortest_level_is_minimal_under_brute_force():
    """Independent of the solver: brute force re-decides the whole level."""
    for p in census()[7]:
        assert not is_sortable(p, k=2)
        for d in perms.one_point_deletions(p):
            assert is_sortable(d, k=2), (p, d)


def test_every_shortest_witness_ends_in_one():
    """Atkinson's theorem, on the complete set rather than a sample."""
    assert all(p[-1] == 1 for p in census()[7])


def test_ends_in_one_decays_above_the_shortest_length():
    """So the pattern belongs to the shortest length, not to basis elements."""
    c = census()
    rate = {n: sum(1 for p in ps if p[-1] == 1) / len(ps)
            for n, ps in c.items()}
    assert rate[7] == 1.0
    assert rate[10] < 0.1
    assert rate[7] > rate[9] > rate[10]


@pytest.mark.parametrize("n", [7, 8, 9, 10])
def test_basis_is_closed_under_the_sorting_dual(n):
    level = set(census()[n])
    for p in level:
        assert perms.sorting_dual(p) in level, p


def test_four_shortest_witnesses_are_self_dual():
    """What justifies restricting a sweep to self-dual permutations."""
    fixed = sorted(p for p in census()[7] if perms.is_self_dual(p))
    assert [perms.to_string(p) for p in fixed] == [
        "3254761", "3624751", "4257361", "4627351"]
    assert all(p[-1] == 1 for p in fixed)
