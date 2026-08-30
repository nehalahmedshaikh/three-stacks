"""Exhaustively sweep permutations of a length with some positions pinned.

A full n! sweep is out of reach (14! is ~63 days on 16 cores even at 1 ms a
permutation).  Pinning a few positions cuts it by n(n-1)(n-2)...: pinning
three at n = 14 leaves 11! = 39,916,800, which is well under an hour.

A witness certifies itself, so any unsortable permutation this turns up
stands regardless of the heuristic restriction.  Finding nothing proves
nothing: the pins come from the measured profile of the basis elements we
happen to have (`scripts/shape.py`), a tendency rather than a theorem -- two
of our thirteen violate even the strongest of them -- so the excluded
permutations are simply untested.

Work is split by the values assigned to the first two free positions, so
branches are independent and each worker enumerates its own slice locally.

    python scripts/sweep.py --n 14 --pin 1=4 --pin 3=2 --pin 14=1 --workers 14
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import FixedLengthDecider
from unsortable.perms import to_string


def _branch(args):
    """Enumerate one slice and return any unsortable permutations in it."""
    n, k, pins, free_pos, free_vals, head = args
    d = FixedLengthDecider(n, k=k)
    base = [0] * n
    for pos, val in pins.items():
        base[pos] = val
    rest_pos = free_pos[len(head):]
    rest_vals = [v for v in free_vals if v not in head]
    for i, v in enumerate(head):
        base[free_pos[i]] = v
    found = []
    checked = 0
    for tail in permutations(rest_vals):
        for pos, v in zip(rest_pos, tail):
            base[pos] = v
        checked += 1
        if not d.is_sortable(tuple(base)):
            found.append(tuple(base))
    d.close()
    return checked, found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--pin", action="append", default=[],
                    help="POSITION=VALUE, both 1-indexed; repeatable")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)

    pins: dict[int, int] = {}
    for spec in a.pin:
        pos, val = spec.split("=")
        pins[int(pos) - 1] = int(val)
    if len(set(pins.values())) != len(pins):
        ap.error("pinned values must be distinct")
    if any(not (1 <= v <= a.n) for v in pins.values()):
        ap.error("pinned values out of range")

    free_pos = [i for i in range(a.n) if i not in pins]
    free_vals = [v for v in range(1, a.n + 1) if v not in pins.values()]
    total = 1
    for i in range(len(free_vals)):
        total *= (i + 1)

    heads = [h for h in permutations(free_vals, 2)]
    print(f"n={a.n}, k={a.k}, pinned "
          + ", ".join(f"pos{p+1}={v}" for p, v in sorted(pins.items())))
    print(f"{total:,} permutations in {len(heads)} branches, "
          f"{a.workers} workers\n", flush=True)

    t0 = time.time()
    done = 0
    hits: list = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        jobs = [(a.n, a.k, pins, free_pos, free_vals, h) for h in heads]
        for i, (checked, found) in enumerate(ex.map(_branch, jobs), start=1):
            done += checked
            hits.extend(found)
            if found:
                for p in found:
                    print(f"\n*** UNSORTABLE, length {a.n} ***\n{to_string(p)}\n",
                          flush=True)
            el = time.time() - t0
            rate = done / el if el else 0
            eta = (total - done) / rate if rate else 0
            print(f"  branch {i}/{len(heads)}  {done:,}/{total:,}  "
                  f"{rate:,.0f}/s  elapsed {el/60:.1f}m  eta {eta/60:.1f}m",
                  flush=True)

    el = time.time() - t0
    print(f"\nswept {done:,} permutations in {el/60:.1f} minutes "
          f"({done/el:,.0f}/s)")
    if hits:
        print(f"{len(hits)} UNSORTABLE found -- upper bound is now {a.n}")
        return 0
    print(f"none unsortable in this slice.  This does NOT bound anything: "
          f"the pins\nare heuristic, so the permutations excluded are "
          f"untested.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
