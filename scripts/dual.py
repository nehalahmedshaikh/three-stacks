"""The sorting dual: verify it, then sweep the permutations it fixes.

Vatter's survey (arXiv:2602.16355), Proposition 5.2, for symbol-oblivious
reversible machines: if M sorts pi then the reversed machine M^r sorts
(pi^rc)^-1.  For k stacks in series the reversed machine is the same machine,
so sortability is invariant under

    D(pi) = inverse(reverse_complement(pi))

which reflects the plot of pi about the anti-diagonal.  Section 6 of
docs/notes.md derives it inside the interval encoding, where it is just time
reversal: negate every event time and the stack order flips, while nesting and
disjointness of occupancy intervals survive negation untouched.

Two consequences turn an impossible sweep into an affordable one.

*D-fixed means "complement is an involution."*  Fixedness says the point set
of pi is symmetric about the anti-diagonal, and complementing turns that into
symmetry about the main diagonal.  So there are I(n) self-dual permutations,
not n!.

*Atkinson (1992): every shortest unsortable permutation ends in 1.*  That pins
the anti-diagonal point (n, 1) and leaves I(n-1) candidates:

    length 17: I(16) =    46,206,736
    length 18: I(17) =   211,799,312
    length 19: I(18) =   997,313,824
    length 20: I(19) = 4,809,701,440

Restricting to self-dual permutations is a conjecture, not a theorem, and a
miss only rules out self-dual witnesses.  What supports it: at k = 1 the unique
shortest witness 231 is self-dual, and at k = 2 four of the twenty-two
shortest witnesses are, so the restriction finds the correct shortest length in
both cases where the answer is known.  The length-21 witness of Pantone and
Vatter is self-dual too, but that one is forced -- the basis is D-closed and
they report exactly one permutation at that length, so there is nowhere else
for D to send it.

    python scripts/dual.py verify --k 2 --maxlen 8
    python scripts/dual.py sweep --n 17 --workers 12
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import FixedLengthDecider
from unsortable.perms import (all_perms, inverse, reverse_complement,
                              to_string)

_DEC: dict = {}


def dual(p):
    """inverse o reverse o complement -- reflection about the anti-diagonal."""
    return tuple(inverse(reverse_complement(p)))


def is_self_dual(p) -> bool:
    return dual(p) == tuple(p)


def involutions(m: int, pair=None, i: int = 1):
    """Every involution of {1..m}, yielded as a reused 1-indexed list."""
    if pair is None:
        pair = [0] * (m + 1)
    while i <= m and pair[i]:
        i += 1
    if i > m:
        yield pair
        return
    pair[i] = i
    yield from involutions(m, pair, i + 1)
    pair[i] = 0
    for j in range(i + 1, m + 1):
        if not pair[j]:
            pair[i], pair[j] = j, i
            yield from involutions(m, pair, i + 1)
            pair[i] = pair[j] = 0


def self_dual_ending_in_one(n: int):
    """Every self-dual permutation of length n whose last entry is 1.

    pi is self-dual with pi_n = 1 iff complement(pi) is an involution fixing
    n, so this enumerates involutions of {1..n-1} and complements them.
    """
    m = n - 1
    for inv in involutions(m):
        yield tuple([n + 1 - inv[v] for v in range(1, m + 1)] + [1])


def _prefixes(m: int, depth: int):
    """Partial matchings after `depth` decisions, used as parallel work units."""
    out = []

    def rec(pair, i, d):
        while i <= m and pair[i]:
            i += 1
        if i > m or d == 0:
            out.append((list(pair), i))
            return
        pair[i] = i
        rec(pair, i + 1, d - 1)
        pair[i] = 0
        for j in range(i + 1, m + 1):
            if not pair[j]:
                pair[i], pair[j] = j, i
                rec(pair, i + 1, d - 1)
                pair[i] = pair[j] = 0

    rec([0] * (m + 1), 1, depth)
    return out


def _scan(task):
    pair, start, m, n, k = task
    dec = _DEC.get((n, k))
    if dec is None:
        dec = _DEC[(n, k)] = FixedLengthDecider(n, k=k)
    checked, hits = 0, []
    for inv in involutions(m, list(pair), start):
        perm = tuple([n + 1 - inv[v] for v in range(1, m + 1)] + [1])
        checked += 1
        if not dec.is_sortable(perm):
            hits.append(to_string(perm))
    return checked, hits


def verify(maxlen: int, k: int) -> bool:
    """Check that D preserves sortability across all of S_n, exhaustively."""
    ok = True
    for n in range(2, maxlen + 1):
        dec = FixedLengthDecider(n, k=k)
        bad = sum(1 for p in all_perms(n)
                  if dec.is_sortable(p) != dec.is_sortable(dual(p)))
        ok &= not bad
        print(f"  n={n:>2}: {'agrees on all of S_n' if not bad else f'{bad} MISMATCHES'}"
              f"   ({dec.calls} decisions)", flush=True)
    fixed = [sum(1 for p in all_perms(n) if is_self_dual(p))
             for n in range(1, min(maxlen, 9) + 1)]
    print(f"  self-dual counts, n=1..{len(fixed)}: {fixed}")
    print("  (these are the involution numbers, as the characterisation "
          "predicts)")
    return bool(ok)


def _choose_depth(m: int, workers: int, target: int = 25000) -> int:
    """Pick a splitting depth that keeps the work-unit count sane.

    Too few units and the tail is one worker finishing a huge subtree while
    eleven sit idle; too many and the parent spends all its time pickling
    them and starves the pool -- at length 18, depth 5 produced 351,316 units
    and the workers accumulated 29 seconds of CPU in 79 minutes while the
    parent burned 1,937.  Anything from a few thousand to a few tens of
    thousands behaves.
    """
    best = 2
    for d in range(2, m):
        count = len(_prefixes(m, d))
        best = d
        if count >= max(target, workers * 200):
            break
    return best


def sweep(n: int, k: int, depth: int | None, workers: int) -> list[str]:
    m = n - 1
    if depth is None:
        depth = _choose_depth(m, workers)
        print(f"chose --depth {depth} automatically", flush=True)
    tasks = [(p, i, n - 1, n, k) for p, i in _prefixes(m, depth)]
    if len(tasks) > 120000:
        print(f"warning: {len(tasks):,} work units is enough for the parent "
              f"to starve the pool; consider a smaller --depth", flush=True)
    print(f"length {n}, k={k}: sweeping every self-dual permutation ending "
          f"in 1 (I({n-1}) of them) in {len(tasks)} work units on {workers} "
          f"workers", flush=True)
    t0, done, hits = time.time(), 0, []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for idx, (checked, hs) in enumerate(
                ex.map(_scan, tasks, chunksize=1), start=1):
            done += checked
            hits += hs
            for h in hs:
                print(f"  *** UNSORTABLE at length {n}: {h}", flush=True)
            if idx % 200 == 0 or idx == len(tasks):
                el = time.time() - t0
                print(f"  [{idx}/{len(tasks)}] {done:,} decided  "
                      f"{done/max(el,1e-9):,.0f}/s  {el/60:.1f}m", flush=True)
    el = time.time() - t0
    print(f"\n{done:,} self-dual candidates decided in {el/60:.1f} min")
    if hits:
        print(f"unsortable found: {len(hits)}")
    else:
        print(f"=> no self-dual permutation of length {n} ending in 1 is "
              f"unsortable by {k} stacks in series")
        print(f"   so if the shortest witness has length {n}, the basis at "
              f"that length contains no\n   self-dual element, and therefore "
              f"has even size (D pairs it up).")
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--k", type=int, default=3)

    v = sub.add_parser("verify", parents=[common])
    v.add_argument("--maxlen", type=int, default=8)

    s = sub.add_parser("sweep", parents=[common])
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--depth", type=int, default=None,
                   help="how many matching decisions define a work unit "
                        "(default: chosen automatically)")
    s.add_argument("--workers", type=int, default=8)

    args = ap.parse_args(argv)
    if args.cmd == "verify":
        return 0 if verify(args.maxlen, args.k) else 1
    sweep(args.n, args.k, args.depth, args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
