"""M3: downward closure (the minimiser depends on it) and symmetries.

The whole search strategy is "find something unsortable, then delete points
until you cannot".  That is only sound if sortability is closed downward.
It is (proof in docs/notes.md §4), but confirm it.

Symmetry reduction, by contrast, is NOT available: measured here, none of
reverse / complement / inverse / reverse-complement preserves sortability,
for one stack or for two.  Nothing in the codebase may assume otherwise.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unsortable import perms
from unsortable.encoding import solve
from unsortable.minimizer import delete_positions, minimise, sat_decider
from unsortable.simulator import is_sortable


# --- downward closure -------------------------------------------------------

@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_sortability_is_closed_downward(k, n):
    for p in perms.all_perms(n):
        if not is_sortable(p, k=k):
            continue
        for q in perms.one_point_deletions(p):
            assert is_sortable(q, k=k), (p, q, k)


def test_unsortability_is_closed_upward_k2():
    """The contrapositive, stated the way the search uses it."""
    bad = [p for p in perms.all_perms(7) if not is_sortable(p, k=2)]
    assert bad, "expected some length-7 permutations unsortable by 2 stacks"
    rng = random.Random(7)
    for q in bad[:6]:
        for _ in range(5):  # insert a random new maximum anywhere
            pos = rng.randrange(len(q) + 1)
            p = tuple(q[:pos]) + (len(q) + 1,) + tuple(q[pos:])
            assert not is_sortable(p, k=2), (q, p)


@pytest.mark.slow
def test_downward_closure_holds_for_long_k3_witnesses(k3_witness):
    """Same check for three stacks, where n<=7 has no unsortable cases."""
    d = sat_decider(3)
    p = k3_witness
    assert not d(p)
    sortable_deletions = [q for q in perms.one_point_deletions(p) if d(q)]
    # deleting a point may or may not restore sortability, but it must never
    # turn a sortable permutation unsortable -- check that direction:
    for q in sortable_deletions:
        for r in perms.one_point_deletions(q):
            assert d(r), (q, r)


# --- symmetries: measured, not assumed --------------------------------------

@pytest.mark.parametrize("k", [1, 2])
@pytest.mark.parametrize("name", sorted(perms.SYMMETRIES))
def test_no_symmetry_preserves_sortability(k, name):
    """All four fail.  Recorded so a future 'optimisation' cannot sneak in."""
    f = perms.SYMMETRIES[name]
    found = False
    for n in range(1, 8):
        for p in perms.all_perms(n):
            if is_sortable(p, k=k) != is_sortable(f(p), k=k):
                found = True
                break
        if found:
            break
    assert found, (f"{name} appeared to preserve {k}-stack sortability up to "
                   "n=7; if that survives larger n it could be used for "
                   "symmetry reduction, but it must be proved first")


def test_known_symmetry_counterexamples():
    assert not is_sortable((2, 3, 1), k=1)
    assert is_sortable(perms.reverse((2, 3, 1)), k=1)          # 132
    assert is_sortable(perms.complement((2, 3, 1)), k=1)       # 213
    assert is_sortable(perms.inverse((2, 3, 1)), k=1)          # 312
    assert is_sortable(perms.reverse_complement((2, 3, 1)), k=1)


# --- the minimiser itself ---------------------------------------------------

def test_minimiser_reaches_231_for_one_stack():
    rng = random.Random(1)
    for _ in range(10):
        p = list(range(1, 9))
        rng.shuffle(p)
        if is_sortable(tuple(p), k=1):
            continue
        rep = minimise(tuple(p), k=1, decide=lambda q: is_sortable(q, k=1))
        assert rep.result == (2, 3, 1), rep.result


def test_minimiser_output_is_minimal_k2():
    p = next(p for p in perms.all_perms(8) if not is_sortable(p, k=2))
    rep = minimise(p, k=2, decide=lambda q: is_sortable(q, k=2))
    assert not is_sortable(rep.result, k=2)
    for i in range(len(rep.result)):
        assert is_sortable(delete_positions(rep.result, [i]), k=2)


def test_minimiser_refuses_sortable_input():
    with pytest.raises(ValueError):
        minimise((1, 2, 3), k=3)
