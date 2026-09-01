"""Exhaustive census of basis elements, one length at a time.

At k = 3 the first basis element sits at length 17 or more, so a complete
census is out of reach and everything about the shape of these permutations
has to be inferred from a handful of witnesses.  At k = 2 the first one is at
length 7, and the whole picture is computable.

A permutation is unsortable iff it contains a basis element, so

    p of length n is a basis element  <=>  p is unsortable
                                           and no one-point deletion of p is

which gives a sieve: carry U_n, the unsortable set at length n, and a
permutation only needs a solver call when all of its deletions are sortable.
Upward closure settles everything else for free, which is most of S_n.

The length-7 row is a check against the literature rather than a discovery:
Atkinson (1992) found exactly 22 basis elements of length 7 for two stacks in
series, and this reproduces that number and the standard example 2435761.

    python scripts/census.py --k 2 --maxlen 10
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import FixedLengthDecider
from unsortable.perms import all_perms, one_point_deletions, to_string
from unsortable.simulator import is_sortable as brute_is_sortable


def census(maxlen: int, k: int, quiet: bool = False):
    """Every basis element of length <= maxlen, keyed by length."""
    unsort_prev: set[tuple[int, ...]] = set()
    basis: dict[int, list[tuple[int, ...]]] = {}

    for n in range(2, maxlen + 1):
        t0 = time.time()
        dec = FixedLengthDecider(n, k=k)
        unsort_now: set[tuple[int, ...]] = set()
        found: list[tuple[int, ...]] = []
        calls = 0

        for p in all_perms(n):
            if any(d in unsort_prev for d in one_point_deletions(p)):
                unsort_now.add(p)
                continue
            calls += 1
            if not dec.is_sortable(p):
                unsort_now.add(p)
                found.append(p)

        basis[n] = found
        # the final level's unsortable set is never consulted again
        unsort_prev = unsort_now if n < maxlen else set()
        if not quiet:
            print(f"n={n:>2}  unsortable={len(unsort_now):>9}  "
                  f"basis={len(found):>6}  solver calls={calls:>9}  "
                  f"{time.time() - t0:7.1f}s", flush=True)
    return basis


def cross_check(basis: dict, k: int) -> list[str]:
    """Re-decide the shortest level with the brute-force simulator."""
    lengths = [n for n in sorted(basis) if basis[n]]
    if not lengths:
        return []
    bad = []
    for p in basis[lengths[0]]:
        if brute_is_sortable(p, k=k):
            bad.append(f"{to_string(p)}: solver says unsortable, brute force "
                       f"sorts it")
        for d in one_point_deletions(p):
            if not brute_is_sortable(d, k=k):
                bad.append(f"{to_string(p)}: deletion {to_string(d)} is "
                           f"unsortable, so it is not minimal")
                break
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--maxlen", type=int, default=9)
    ap.add_argument("--out", default=None,
                    help="write the census to this JSON path")
    args = ap.parse_args(argv)

    basis = census(args.maxlen, args.k)

    bad = cross_check(basis, args.k)
    print("\nbrute-force cross-check of the shortest level:",
          "no disagreements" if not bad else "FAILED")
    for b in bad:
        print(f"  {b}")

    lengths = [n for n in sorted(basis) if basis[n]]
    if lengths:
        shortest = lengths[0]
        print(f"\nfirst basis element at length {shortest}: "
              f"{len(basis[shortest])} of them")

    out = args.out or ROOT / "results" / f"census_k{args.k}.json"
    payload = {"k": args.k, "maxlen": args.maxlen,
               "basis": {str(n): [to_string(p) for p in ps]
                         for n, ps in basis.items() if ps}}
    Path(out).write_text(json.dumps(payload, indent=1) + "\n")
    print(f"wrote {out}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
