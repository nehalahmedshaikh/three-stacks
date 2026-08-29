"""M6: the search-free counting ceiling."""

from __future__ import annotations

import sys
from math import comb, factorial
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unsortable.counting import ballot_words, crossover
from unsortable.simulator import count_sortable


def catalan(n: int) -> int:
    return comb(2 * n, n) // (n + 1)


@pytest.mark.parametrize("n", range(0, 12))
def test_one_stack_ballot_words_are_catalan(n):
    assert ballot_words(n, k=1) == catalan(n)


@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7])
def test_ballot_words_bound_the_sortable_count(k, n):
    """The whole point: sortable(n) <= B_k(n)."""
    assert count_sortable(n, k=k) <= ballot_words(n, k)


def test_one_stack_bound_is_exactly_attained():
    """For one stack the map is a bijection, so the bound is tight."""
    for n in range(1, 9):
        assert count_sortable(n, k=1) == ballot_words(n, k=1)
    assert crossover(1) == 3  # and 231 really is the answer


def test_crossovers():
    assert crossover(1) == 3
    assert crossover(2) == 50
    assert crossover(3) == 642


def test_crossover_is_a_genuine_crossing():
    for k in (1, 2, 3):
        c = crossover(k)
        assert factorial(c) > ballot_words(c, k)
        assert factorial(c - 1) <= ballot_words(c - 1, k)


def test_counting_bound_is_weak_but_valid_for_k2():
    """k=2's true answer is 7; the bound only gets to 50.  Recorded honestly."""
    assert crossover(2) == 50
    assert count_sortable(7, k=2) < factorial(7)  # unsortable ones exist at 7
