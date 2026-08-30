"""M1: the SAT encoding must agree with the simulator, exactly, always.

If any test here fails the encoding is wrong and nothing downstream means
anything.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify
from unsortable import encoding, perms
from unsortable.simulator import is_sortable as brute_sortable


@pytest.mark.parametrize("mode", ["full", "reduced"])
@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_exhaustive_agreement_small(mode, k, n):
    for p in perms.all_perms(n):
        got = encoding.solve(p, k=k, mode=mode)
        assert got.sortable == brute_sortable(p, k=k), (p, k, mode)


@pytest.mark.parametrize("mode", ["full", "reduced"])
@pytest.mark.parametrize("k", [1, 2, 3])
def test_exhaustive_agreement_n7(mode, k):
    for p in perms.all_perms(7):
        got = encoding.solve(p, k=k, mode=mode)
        assert got.sortable == brute_sortable(p, k=k), (p, k, mode)


@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [8, 9, 10, 11])
def test_sampled_agreement_larger(k, n):
    rng = random.Random(20260829 + 100 * n + k)
    pool = list(range(1, n + 1))
    for _ in range(60):
        rng.shuffle(pool)
        p = tuple(pool)
        got = encoding.solve(p, k=k, mode="reduced")
        assert got.sortable == brute_sortable(p, k=k), (p, k)


@pytest.mark.parametrize("mode", ["full", "reduced"])
@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7])
def test_sat_models_decode_to_real_sorting_runs(mode, k, n):
    """A SAT verdict must come with an operation word that actually sorts."""
    for p in perms.all_perms(n):
        r = encoding.solve(p, k=k, mode=mode)
        if not r.sortable:
            continue
        assert r.ops is not None
        assert verify.sorts(list(p), r.ops, k=k), (p, k, mode, r.ops)


def test_231_one_stack_is_unsat():
    r = encoding.solve((2, 3, 1), k=1)
    assert not r.sortable
    assert encoding.solve((2, 3, 1), k=2).sortable


def test_full_and_reduced_agree_on_n7_k2():
    for p in perms.all_perms(7):
        a = encoding.solve(p, k=2, mode="full").sortable
        b = encoding.solve(p, k=2, mode="reduced").sortable
        assert a == b, p


# --- the incremental fixed-length decider -----------------------------------
# Only the input order depends on the permutation, so one CNF serves every
# permutation of a given length with the input order passed as assumptions.
# 18x faster on a neighbourhood probe; it must agree exactly.

@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7])
def test_fixed_length_decider_matches_brute_force(k, n):
    from unsortable.encoding import FixedLengthDecider
    with FixedLengthDecider(n, k=k) as d:
        for p in perms.all_perms(n):
            assert d.is_sortable(p) == brute_sortable(p, k=k), (p, k, n)


@pytest.mark.parametrize("k", [1, 2, 3])
@pytest.mark.parametrize("n", [6, 7])
def test_fixed_length_decider_matches_one_shot(k, n):
    from unsortable.encoding import FixedLengthDecider
    with FixedLengthDecider(n, k=k) as d:
        for p in perms.all_perms(n):
            assert d.is_sortable(p) == encoding.solve(p, k=k, mode="reduced").sortable


@pytest.mark.parametrize("k", [1, 2, 3])
def test_fixed_length_decider_ops_replay(k):
    from unsortable.encoding import FixedLengthDecider
    with FixedLengthDecider(6, k=k) as d:
        for p in perms.all_perms(6):
            ops = d.ops(p)
            if ops is None:
                assert not brute_sortable(p, k=k)
            else:
                assert verify.sorts(list(p), ops, k=k), (p, k, ops)
