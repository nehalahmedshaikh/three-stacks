"""Brute-force ground truth: sortability by k stacks in series.

Machine::

    input -> S1 -> S2 -> ... -> Sk -> output

Operations.  Each element performs each of these exactly once, in order:

    r_1         move the next input element onto S1
    r_j  (2..k) pop S_{j-1}, push onto S_j
    r_{k+1}     pop S_k, append to the output

A permutation is *k-stack-sortable in series* if some legal operation
sequence leaves the identity in the output.  Every sorting run performs
exactly (k+1)*n operations.

Two prunings are used, both proved in ``docs/notes.md`` and regression-tested
against the unpruned search (``prune=False``) in ``tests/test_simulator.py``:

P1 (last-stack monotonicity)
    S_k must be strictly increasing from top to bottom at all times, since
    S_k pops directly to the output and the output must come out
    increasing.  So a push onto S_k is legal only when the pushed value is
    smaller than the current top of S_k.

P2 (forced output)
    If the top of S_k is exactly the next value the output wants, popping
    it immediately is safe.  By P1, anything pushed on top of it would have
    to be smaller -- but every smaller value has already been output.  So
    nothing can ever go on top of it, and delaying the pop enables nothing.

The search is a memoised DFS.  The state (i, stacks) determines the number
of operations performed so far, so the state graph is acyclic and a plain
visited-set is a sound memo for "no completion from here".
"""

from __future__ import annotations

import sys
from typing import Iterator, Sequence

from .perms import Perm, all_perms, check

# An operation sequence is a tuple of ints in 1..k+1.
Ops = tuple[int, ...]


def ops_to_string(ops: Sequence[int]) -> str:
    return "".join(str(o) for o in ops)


def ops_from_string(s: str) -> Ops:
    return tuple(int(c) for c in s.strip() if not c.isspace())


def sorting_sequence(
    perm: Sequence[int],
    k: int = 3,
    prune: bool = True,
    node_limit: int | None = None,
) -> Ops | None:
    """Return a witnessing operation sequence, or None if unsortable.

    Raises SearchLimitExceeded if node_limit is set and reached.
    """
    p = check(perm)
    n = len(p)
    if n == 0:
        return ()
    if k < 1:
        raise ValueError("k must be >= 1")

    sys.setrecursionlimit(max(10_000, 8 * (k + 1) * n))

    empty: tuple[tuple[int, ...], ...] = tuple(() for _ in range(k))
    seen: set[tuple[int, tuple[tuple[int, ...], ...]]] = set()
    ops: list[int] = []
    nodes = 0
    last = k - 1  # index of S_k

    def rec(i: int, stacks: tuple[tuple[int, ...], ...], out_count: int) -> bool:
        nonlocal nodes
        if out_count == n:
            return True
        key = (i, stacks)
        if key in seen:
            return False
        seen.add(key)
        nodes += 1
        if node_limit is not None and nodes > node_limit:
            raise SearchLimitExceeded(nodes)

        # P2: forced output.
        if prune and stacks[last] and stacks[last][-1] == out_count + 1:
            new = list(stacks)
            new[last] = stacks[last][:-1]
            ops.append(k + 1)
            if rec(i, tuple(new), out_count + 1):
                return True
            ops.pop()
            return False

        # r_{k+1}: pop S_k to the output.
        if stacks[last] and stacks[last][-1] == out_count + 1:
            new = list(stacks)
            new[last] = stacks[last][:-1]
            ops.append(k + 1)
            if rec(i, tuple(new), out_count + 1):
                return True
            ops.pop()

        # r_j for j = k .. 2: pop S_{j-1}, push onto S_j.
        # Tried deepest-first: moving elements towards the output tends to
        # reach a solution sooner.
        for j in range(k, 1, -1):
            src, dst = j - 2, j - 1
            if not stacks[src]:
                continue
            v = stacks[src][-1]
            if prune and dst == last and stacks[last] and v > stacks[last][-1]:
                continue  # P1
            new = list(stacks)
            new[src] = stacks[src][:-1]
            new[dst] = stacks[dst] + (v,)
            ops.append(j)
            if rec(i, tuple(new), out_count):
                return True
            ops.pop()

        # r_1: read the next input element onto S1.
        if i < n:
            v = p[i]
            if not (prune and k == 1 and stacks[0] and v > stacks[0][-1]):
                new = list(stacks)
                new[0] = stacks[0] + (v,)
                ops.append(1)
                if rec(i + 1, tuple(new), out_count):
                    return True
                ops.pop()

        return False

    if rec(0, empty, 0):
        return tuple(ops)
    return None


class SearchLimitExceeded(Exception):
    """Raised when the brute-force search exceeds its node budget."""


def is_sortable(perm: Sequence[int], k: int = 3, prune: bool = True,
                node_limit: int | None = None) -> bool:
    return sorting_sequence(perm, k=k, prune=prune, node_limit=node_limit) is not None


def count_sortable(n: int, k: int = 3, prune: bool = True) -> int:
    return sum(1 for p in all_perms(n) if is_sortable(p, k=k, prune=prune))


def unsortable_perms(n: int, k: int = 3) -> Iterator[Perm]:
    for p in all_perms(n):
        if not is_sortable(p, k=k):
            yield p
