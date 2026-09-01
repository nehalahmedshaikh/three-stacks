"""Permutation utilities.

Permutations are 1-indexed tuples of values, e.g. (2, 3, 1) is the
permutation sending position 1 to value 2, position 2 to value 3, ...
"""

from __future__ import annotations

from itertools import permutations as _itertools_permutations
from typing import Iterable, Iterator, Sequence

Perm = tuple[int, ...]


def check(p: Sequence[int]) -> Perm:
    """Return p as a validated permutation tuple of 1..n."""
    p = tuple(int(x) for x in p)
    if sorted(p) != list(range(1, len(p) + 1)):
        raise ValueError(f"not a permutation of 1..{len(p)}: {p}")
    return p


def all_perms(n: int) -> Iterator[Perm]:
    return _itertools_permutations(range(1, n + 1))


def to_string(p: Sequence[int]) -> str:
    """Compact one-line form.  Values <10 concatenate, otherwise dash-joined."""
    if len(p) and max(p) < 10:
        return "".join(str(x) for x in p)
    return "-".join(str(x) for x in p)


def from_string(s: str) -> Perm:
    s = s.strip()
    if "-" in s or "," in s or " " in s:
        parts = [t for t in s.replace(",", " ").replace("-", " ").split() if t]
        return check(int(t) for t in parts)
    return check(int(c) for c in s)


# --- symmetries -------------------------------------------------------------
# NOTE: which of these preserve k-stack-in-series sortability is an empirical
# question settled in tests/test_symmetry.py (milestone M3).  Nothing in this
# module assumes any of them do.

def reverse(p: Sequence[int]) -> Perm:
    return tuple(reversed(p))


def complement(p: Sequence[int]) -> Perm:
    n = len(p)
    return tuple(n + 1 - x for x in p)


def inverse(p: Sequence[int]) -> Perm:
    n = len(p)
    out = [0] * n
    for i, v in enumerate(p, start=1):
        out[v - 1] = i
    return tuple(out)


def reverse_complement(p: Sequence[int]) -> Perm:
    return reverse(complement(p))


SYMMETRIES = {
    "reverse": reverse,
    "complement": complement,
    "inverse": inverse,
    "reverse_complement": reverse_complement,
}


def sorting_dual(p: Sequence[int]) -> Perm:
    """Reflection of the plot of p about the anti-diagonal.

    Unlike the four maps above, this one *does* preserve k-stack-in-series
    sortability: it is Proposition 5.2 of Vatter, arXiv:2602.16355, and
    docs/notes.md §6 derives it inside the interval encoding as time
    reversal.  It is the only symmetry available for search reduction.
    """
    return inverse(reverse_complement(p))


def is_self_dual(p: Sequence[int]) -> bool:
    """True iff sorting_dual fixes p.  Equivalently, complement(p) is an
    involution -- so there are I(n) such permutations, not n!."""
    return sorting_dual(p) == tuple(p)


# --- patterns ---------------------------------------------------------------

def standardise(seq: Sequence[int]) -> Perm:
    """Replace values by their ranks, giving a permutation of 1..len(seq)."""
    order = sorted(range(len(seq)), key=lambda i: seq[i])
    out = [0] * len(seq)
    for rank, i in enumerate(order, start=1):
        out[i] = rank
    return tuple(out)


def delete_position(p: Sequence[int], i: int) -> Perm:
    """The pattern obtained by deleting position i (0-indexed) from p."""
    return standardise(tuple(p[:i]) + tuple(p[i + 1:]))


def one_point_deletions(p: Sequence[int]) -> list[Perm]:
    """All patterns obtained by deleting a single entry.  May contain repeats."""
    return [delete_position(p, i) for i in range(len(p))]


def contains(p: Sequence[int], pattern: Sequence[int]) -> bool:
    """Classical pattern containment (brute force; fine for tiny patterns)."""
    from itertools import combinations
    m = len(pattern)
    pat = standardise(pattern)
    for idx in combinations(range(len(p)), m):
        if standardise([p[i] for i in idx]) == pat:
            return True
    return False


def avoids(p: Sequence[int], pattern: Sequence[int]) -> bool:
    return not contains(p, pattern)
