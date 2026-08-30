"""M4: hunting for unsortable permutations.

The empirically useful route is "descend from above": random permutations of
length ~40 are unsortable a good fraction of the time and the solver decides
them in seconds, so a witness is cheap to find.  The work is then all in the
minimiser (M3), which turns a long witness into a basis element.

Also here: structured families worth trying, and a local search that walks a
sortable permutation towards unsortability.
"""

from __future__ import annotations

import random
from typing import Callable, Iterator, Sequence

from .perms import Perm, check, standardise

Decider = Callable[[Perm], bool]  # True iff sortable


def random_perm(n: int, rng: random.Random) -> Perm:
    p = list(range(1, n + 1))
    rng.shuffle(p)
    return tuple(p)


def find_random_unsortable(
    n: int,
    decide: Decider,
    rng: random.Random,
    trials: int = 100,
    on_trial: Callable[[int, Perm, bool], None] | None = None,
) -> Perm | None:
    for t in range(trials):
        p = random_perm(n, rng)
        ok = decide(p)
        if on_trial:
            on_trial(t, p, ok)
        if not ok:
            return p
    return None


# --- structured families ----------------------------------------------------

def direct_sum(*blocks: Sequence[int]) -> Perm:
    out: list[int] = []
    shift = 0
    for b in blocks:
        out.extend(v + shift for v in b)
        shift += len(b)
    return tuple(out)


def skew_sum(*blocks: Sequence[int]) -> Perm:
    total = sum(len(b) for b in blocks)
    out: list[int] = []
    top = total
    for b in blocks:
        out.extend(v + top - len(b) for v in b)
        top -= len(b)
    return tuple(out)


def layered(parts: Sequence[int]) -> Perm:
    """Layered permutation: decreasing runs of the given sizes, increasing between."""
    out: list[int] = []
    start = 1
    for m in parts:
        out.extend(range(start + m - 1, start - 1, -1))
        start += m
    return tuple(out)


def families(max_n: int = 60) -> Iterator[tuple[str, Perm]]:
    """Structured candidates, shortest first."""
    seen: set[Perm] = set()

    def emit(name: str, p: Perm):
        p = check(p)
        if len(p) <= max_n and p not in seen:
            seen.add(p)
            return (name, p)
        return None

    # iterated direct/skew sums of the small obstruction 231 and its relatives
    seeds = {
        "231": (2, 3, 1),
        "312": (3, 1, 2),
        "2413": (2, 4, 1, 3),
        "3142": (3, 1, 4, 2),
    }
    out: list[tuple[str, Perm]] = []
    for name, seed in seeds.items():
        for reps in range(2, max_n // len(seed) + 1):
            r = emit(f"{name}^(+{reps})", direct_sum(*([seed] * reps)))
            if r:
                out.append(r)
            r = emit(f"{name}^(-{reps})", skew_sum(*([seed] * reps)))
            if r:
                out.append(r)
    # layered permutations with uniform layers
    for m in range(2, 9):
        for reps in range(2, max_n // m + 1):
            r = emit(f"layered({m}x{reps})", layered([m] * reps))
            if r:
                out.append(r)
    out.sort(key=lambda t: len(t[1]))
    yield from out


# --- basin hopping over basis elements --------------------------------------
# Greedy descent stops at whatever basis element its random deletion order
# happens to reach, and those are not all the same length.  Upward closure
# gives a free way to escape: inserting points into an unsortable permutation
# keeps it unsortable, so we can climb a few steps *with no search at all*
# and descend again along a different path.  Every iterate is a guaranteed
# witness; the only question is how short.

def insert_random_point(p: Perm, rng: random.Random) -> Perm:
    """Insert one new entry at a random position with a random value."""
    n = len(p)
    v = rng.randint(1, n + 1)
    lifted = tuple(x + (1 if x >= v else 0) for x in p)
    pos = rng.randrange(n + 1)
    return lifted[:pos] + (v,) + lifted[pos:]


def perturb(p: Perm, count: int, rng: random.Random) -> Perm:
    for _ in range(count):
        p = insert_random_point(p, rng)
    return p


# --- same-length plateau walk -----------------------------------------------
# Basin hopping moves along the plateau of length-L basis elements by climbing
# a few points and descending again, which costs 100-200 solver calls, most of
# them at lengths 25-30 where each is slow.  But a *same-length* move needs no
# climb: one transposition, one solver call at length L.  If the result is
# still unsortable we have moved sideways for ~1% of the price, and the only
# thing that matters is whether it is non-minimal -- because a non-minimal
# unsortable permutation of length L has an unsortable deletion of length L-1,
# which is the whole objective.

def same_length_neighbour(p: Perm, rng: random.Random) -> Perm:
    """A random permutation one small move away, same length."""
    n = len(p)
    q = list(p)
    r = rng.random()
    i, j = rng.randrange(n), rng.randrange(n)
    if i == j:
        j = (i + 1) % n
    if r < 0.45:                      # transpose two entries
        q[i], q[j] = q[j], q[i]
    elif r < 0.75:                    # move one entry elsewhere
        q.insert(j, q.pop(i))
    elif r < 0.90:                    # reverse a short segment
        a, b = min(i, j), max(i, j)
        b = min(b, a + 4)
        q[a:b + 1] = reversed(q[a:b + 1])
    else:                             # swap two adjacent *values*
        v = rng.randrange(1, n)
        a, b = q.index(v), q.index(v + 1)
        q[a], q[b] = q[b], q[a]
    return tuple(q)


def neighbours(p: Perm, rng: random.Random, count: int) -> list[Perm]:
    out, seen = [], {p}
    while len(out) < count:
        q = same_length_neighbour(p, rng)
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


# --- local search -----------------------------------------------------------

def _neighbours(p: Perm, rng: random.Random, count: int) -> Iterator[Perm]:
    n = len(p)
    for _ in range(count):
        q = list(p)
        move = rng.random()
        i, j = rng.randrange(n), rng.randrange(n)
        if i == j:
            continue
        if move < 0.5:  # transposition
            q[i], q[j] = q[j], q[i]
        elif move < 0.8:  # move one entry elsewhere
            v = q.pop(i)
            q.insert(j, v)
        else:  # reverse a segment
            a, b = min(i, j), max(i, j)
            q[a:b + 1] = reversed(q[a:b + 1])
        yield tuple(q)


def local_search_unsortable(
    n: int,
    decide: Decider,
    rng: random.Random,
    restarts: int = 5,
    steps: int = 200,
    neighbours: int = 12,
    score: Callable[[Perm], float] | None = None,
) -> Perm | None:
    """Walk towards unsortability.

    Without a graded objective this is really just a randomised sweep of the
    neighbourhood; ``score`` can supply one (e.g. solver conflicts) if a
    cheaper proxy for "nearly unsortable" is found.
    """
    for _ in range(restarts):
        cur = random_perm(n, rng)
        if not decide(cur):
            return cur
        for _ in range(steps):
            moved = False
            for q in _neighbours(cur, rng, neighbours):
                if not decide(q):
                    return q
                if score is not None and score(q) > score(cur):
                    cur, moved = q, True
                    break
            if not moved:
                cur = next(iter(_neighbours(cur, rng, 1)), cur)
    return None
