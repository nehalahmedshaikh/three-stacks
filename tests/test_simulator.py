"""M0: the simulator is the ground truth, so it gets the strictest tests."""

from __future__ import annotations

import sys
from math import comb
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify  # standalone independent checker
from unsortable import perms
from unsortable.simulator import (
    count_sortable,
    is_sortable,
    sorting_sequence,
)

SLOW_N7 = pytest.param(7, marks=pytest.mark.slow)
SLOW_N8 = pytest.param(8, marks=pytest.mark.slow)


def catalan(n: int) -> int:
    return comb(2 * n, n) // (n + 1)


# --- one stack: the fact everything else rests on ---------------------------

@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, SLOW_N7])
def test_one_stack_is_exactly_av231(n):
    for p in perms.all_perms(n):
        assert is_sortable(p, k=1) == perms.avoids(p, (2, 3, 1)), p


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, SLOW_N7, SLOW_N8])
def test_one_stack_counts_are_catalan(n):
    assert count_sortable(n, k=1) == catalan(n)


def test_231_is_the_smallest_one_stack_obstruction():
    assert not is_sortable((2, 3, 1), k=1)
    assert is_sortable((2, 3, 1), k=2)
    for n in (1, 2):
        assert all(is_sortable(p, k=1) for p in perms.all_perms(n))


# --- pruning soundness ------------------------------------------------------
# P1 and P2 are the only non-obvious parts of the search.  Check them against
# the unpruned search exhaustively.

@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_pruning_agrees_with_unpruned(k, n):
    for p in perms.all_perms(n):
        assert is_sortable(p, k=k, prune=True) == is_sortable(p, k=k, prune=False), (p, k)


# --- agreement with the independent checker ---------------------------------

@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_agrees_with_independent_exhaustive_search(k, n):
    for p in perms.all_perms(n):
        mine = sorting_sequence(p, k=k)
        theirs = verify.exhaust(list(p), k=k)
        assert (mine is None) == (theirs is None), (p, k)


@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, SLOW_N7])
def test_every_witness_replays(k, n):
    """Every op sequence the searcher returns really sorts the permutation."""
    for p in perms.all_perms(n):
        ops = sorting_sequence(p, k=k)
        if ops is None:
            continue
        assert len(ops) == (k + 1) * n
        assert verify.sorts(list(p), ops, k=k), (p, k, ops)


# --- three stacks: the regime we actually care about ------------------------

@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, SLOW_N7])
def test_three_stacks_sorts_everything_small(n):
    """Atkinson: everything up to length 13 is 3-stack-sortable.  Spot-check."""
    for p in perms.all_perms(n):
        assert is_sortable(p, k=3), p


def test_more_stacks_never_hurts():
    for n in range(1, 7):
        for p in perms.all_perms(n):
            if is_sortable(p, k=1):
                assert is_sortable(p, k=2)
            if is_sortable(p, k=2):
                assert is_sortable(p, k=3)
