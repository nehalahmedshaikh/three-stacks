"""M3: downward closure (the minimiser depends on it) and symmetries.

The search strategy is "find something unsortable, then delete points until
you cannot", which is sound only if sortability is closed downward.  It is
(proof in docs/notes.md §4); these tests confirm it.

None of reverse / complement / inverse / reverse-complement preserves
sortability on its own, for one stack or for two.  Their composition
inverse o reverse o complement does -- the sorting dual, Proposition 5.2 of
Vatter, arXiv:2602.16355 -- and it is the only symmetry the codebase may
assume.  Both halves are tested here so neither can drift.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unsortable import perms
from unsortable.encoding import FixedLengthDecider, solve
from unsortable.minimizer import delete_positions, minimise
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
    p = k3_witness
    assert not solve(p, k=3, mode="reduced").sortable
    # The remaining work is in batches at two fixed lengths. Reuse each base
    # formula instead of rebuilding and transferring it for every deletion.
    with FixedLengthDecider(len(p) - 1, k=3) as middle:
        sortable_deletions = [
            q for q in perms.one_point_deletions(p) if middle.is_sortable(q)
        ]
    with FixedLengthDecider(len(p) - 2, k=3) as bottom:
        # deleting a point may or may not restore sortability, but it must
        # never turn a sortable permutation unsortable -- check that direction
        for q in sortable_deletions:
            for r in perms.one_point_deletions(q):
                assert bottom.is_sortable(r), (q, r)


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


@pytest.mark.parametrize("k", [1, 2, 3])
def test_sorting_dual_preserves_sortability(k):
    """Exhaustive over S_n, against brute force.  The one symmetry that holds.

    n <= 6 keeps this cheap; length 7 is where unsortable permutations first
    appear for k = 2, so the k = 2 case is extended by one to give it teeth.
    """
    top = 8 if k == 2 else 7
    for n in range(1, top):
        for p in perms.all_perms(n):
            assert is_sortable(p, k=k) == \
                is_sortable(perms.sorting_dual(p), k=k), (k, p)


@pytest.mark.slow
def test_sorting_dual_preserves_sortability_on_long_permutations():
    """k = 3 at lengths where the witnesses actually live."""
    from unsortable.encoding import FixedLengthDecider
    rng = random.Random(11)
    for n in (12, 16, 22):
        dec = FixedLengthDecider(n, k=3)
        for _ in range(60):
            p = list(range(1, n + 1))
            rng.shuffle(p)
            p = tuple(p)
            assert dec.is_sortable(p) == dec.is_sortable(perms.sorting_dual(p))


def test_sorting_dual_is_an_involution():
    for n in range(1, 7):
        for p in perms.all_perms(n):
            assert perms.sorting_dual(perms.sorting_dual(p)) == p


def test_self_dual_permutations_are_complements_of_involutions():
    """The characterisation that makes the fixed set I(n) rather than n!."""
    involution_numbers = [1, 1, 2, 4, 10, 26, 76, 232]
    for n in range(1, 8):
        fixed = [p for p in perms.all_perms(n) if perms.is_self_dual(p)]
        assert len(fixed) == involution_numbers[n]
        for p in fixed:
            c = perms.complement(p)
            assert perms.inverse(c) == c, (p, c)


def test_the_length_21_witness_is_self_dual():
    """Forced: the basis is dual-closed and Pantone-Vatter report exactly one
    minimal permutation at length 21, so the dual has nowhere else to send it.
    Checking it agrees is a cross-check of their uniqueness claim."""
    pv = perms.from_string(
        "6-3-12-8-17-5-2-11-7-19-14-10-4-18-13-21-16-9-20-15-1")
    assert perms.is_self_dual(pv)
    c = perms.complement(pv)
    assert perms.inverse(c) == c


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
