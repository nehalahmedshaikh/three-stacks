"""M3: shrink an unsortable permutation to a minimal one.

Sortability is closed downward under pattern containment (proof in
``docs/notes.md`` §4), so unsortability is closed *upward*: if ``pi`` is
unsortable, so is anything containing it.  Consequently the shortest
unsortable permutation is a basis element of the sortable class, and any
unsortable witness can be shrunk towards one by deleting points.

``minimise`` returns a permutation that is unsortable and all of whose
one-point deletions are sortable.  That is a *locally* minimal witness -- a
genuine basis element -- not necessarily the globally shortest one.

Ordering matters.  Delta-debugging's largest-bite-first heuristic is wrong
here: deleting a big block usually destroys the obstruction, so those calls
almost always fail, and they are the expensive ones because the candidate is
still long.  Single-point deletions succeed often and shrink the instance
immediately, making every later call cheaper.  The descent is therefore
single-point-first, in randomised order.

Most of the work is the failed candidates in each scan.  They are
independent, so the scan parallelises across cores (``workers``); as soon as
one candidate comes back unsortable the rest of the wave is cancelled.

Once no single point can be removed the permutation is a basis element and
the job is done -- and it is done in a strong sense.  Deleting *more* points
cannot help, ever:

    Let p be a basis element and q a two-point deletion of p.  Then q is a
    one-point deletion of some one-point deletion p' of p.  p' is sortable
    (p is a basis element), and sortability is closed downward, so q is
    sortable.  By induction every deletion of every size is sortable.

So there is no "deep" escape to search for, and this module does not offer
one.  The only route to a shorter witness is a *different* basis element,
which is what ``search.perturb`` plus a fresh descent provides (basin
hopping in ``scripts/hunt.py hop``).
"""

from __future__ import annotations

import random
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Iterable, Iterator, Sequence

from .perms import Perm, check, standardise

Decider = Callable[[Perm], bool]  # True iff sortable


# --- deciders ---------------------------------------------------------------

def _solve_one(perm: Perm, k: int, mode: str) -> bool:
    """Module-level so it can be shipped to a worker process."""
    from .encoding import solve
    return solve(perm, k=k, mode=mode).sortable


def sat_decider(k: int = 3, mode: str = "reduced", cache: dict | None = None) -> Decider:
    store = cache if cache is not None else {}

    def decide(p: Perm) -> bool:
        key = (p, k)
        if key not in store:
            store[key] = _solve_one(p, k, mode)
        return store[key]

    return decide


def brute_decider(k: int = 3, cache: dict | None = None) -> Decider:
    from .simulator import is_sortable
    store = cache if cache is not None else {}

    def decide(p: Perm) -> bool:
        key = (p, k)
        if key not in store:
            store[key] = is_sortable(p, k=k)
        return store[key]

    return decide


# --- deletion candidates ----------------------------------------------------

def delete_positions(perm: Sequence[int], positions: Iterable[int]) -> Perm:
    drop = set(positions)
    return standardise([v for i, v in enumerate(perm) if i not in drop])


def delete_values(perm: Sequence[int], values: Iterable[int]) -> Perm:
    drop = set(values)
    return standardise([v for v in perm if v not in drop])


def _single_points(perm: Perm, rng: random.Random) -> list[tuple[str, Perm]]:
    order = list(range(len(perm)))
    rng.shuffle(order)
    return [(f"position {i} (value {perm[i]})", delete_positions(perm, [i]))
            for i in order]


def _subsets(perm: Perm, size: int, rng: random.Random,
             cap: int | None = None) -> list[tuple[str, Perm]]:
    combos = list(combinations(range(len(perm)), size))
    rng.shuffle(combos)
    if cap is not None:
        combos = combos[:cap]
    return [(f"positions {list(idx)}", delete_positions(perm, idx)) for idx in combos]


# --- the minimiser ----------------------------------------------------------

@dataclass
class MinimiseReport:
    start: Perm
    result: Perm
    k: int
    steps: list[tuple[int, str]] = field(default_factory=list)
    decisions: int = 0

    @property
    def start_length(self) -> int:
        return len(self.start)

    @property
    def length(self) -> int:
        return len(self.result)


class _Scanner:
    """Finds the first unsortable candidate in a list, sequentially or in parallel."""

    def __init__(self, decide: Decider, k: int, mode: str, workers: int,
                 pool: ProcessPoolExecutor | None):
        self.decide, self.k, self.mode = decide, k, mode
        self.workers, self.pool = workers, pool
        self.calls = 0

    def first_unsortable(self, cands: Sequence[tuple[str, Perm]]):
        if self.pool is None or len(cands) < 2:
            for how, c in cands:
                self.calls += 1
                if not self.decide(c):
                    return how, c
            return None

        pending = {}
        it = iter(cands)
        hit = None

        def submit_more():
            while len(pending) < self.workers * 2:
                nxt = next(it, None)
                if nxt is None:
                    return
                how, c = nxt
                pending[self.pool.submit(_solve_one, c, self.k, self.mode)] = (how, c)

        submit_more()
        while pending and hit is None:
            done, _ = wait(list(pending), return_when=FIRST_COMPLETED)
            for f in done:
                how, c = pending.pop(f)
                self.calls += 1
                try:
                    sortable = f.result()
                except Exception:
                    continue
                if not sortable and hit is None:
                    hit = (how, c)
            if hit is None:
                submit_more()
        for f in pending:
            f.cancel()
        return hit


def minimise(
    perm: Sequence[int],
    k: int = 3,
    decide: Decider | None = None,
    on_step: Callable[[Perm, str], None] | None = None,
    rng: random.Random | None = None,
    workers: int = 1,
    mode: str = "reduced",
) -> MinimiseReport:
    """Shrink an unsortable permutation until every one-point deletion sorts.

    The result is a basis element, and by the argument in this module's
    docstring no further deletion of any size can shorten it.
    ``workers`` > 1 scans candidates across that many processes.
    """
    cur = check(perm)
    rng = rng or random.Random(0)
    decide = decide or sat_decider(k, mode=mode)

    if decide(cur):
        raise ValueError(f"{cur} is sortable by {k} stacks; nothing to minimise")

    report = MinimiseReport(start=cur, result=cur, k=k)
    pool = ProcessPoolExecutor(max_workers=workers) if workers > 1 else None
    scan = _Scanner(decide, k, mode, workers, pool)

    def take(cand: Perm, how: str) -> None:
        nonlocal cur
        cur = cand
        report.steps.append((len(cur), how))
        if on_step:
            on_step(cur, how)

    try:
        while True:
            hit = scan.first_unsortable(_single_points(cur, rng))
            if hit is None:
                break
            take(hit[1], hit[0])
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)

    report.result = cur
    report.decisions = scan.calls
    return report


def is_minimal_unsortable(perm: Sequence[int], k: int = 3,
                          decide: Decider | None = None) -> bool:
    """Unsortable, but every one-point deletion is sortable."""
    p = check(perm)
    d = decide or sat_decider(k)
    if d(p):
        return False
    return all(d(delete_positions(p, [i])) for i in range(len(p)))


# --- downward closure, checked rather than assumed --------------------------

def closure_violations(perm: Sequence[int], k: int = 3,
                       decide: Decider | None = None) -> list[Perm]:
    """One-point deletions of a *sortable* permutation that are unsortable.

    Should always be empty.  If it ever isn't, the theory in docs/notes.md
    §4 is wrong and the minimiser is unsound.
    """
    p = check(perm)
    d = decide or sat_decider(k)
    if not d(p):
        return []
    return [q for i in range(len(p))
            if not d(q := delete_positions(p, [i]))]
