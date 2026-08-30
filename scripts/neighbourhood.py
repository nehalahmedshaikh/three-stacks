"""Enumerate the FULL same-length neighbourhood of a witness, exhaustively.

A length-22 permutation has only about 700-900 neighbours under the move set,
so a 300-sample estimate covers barely a third.  This enumerates every one:
all transpositions, all single-point relocations, all adjacent-value swaps.
For n = 22 that is ~700 solver calls, about a minute across cores.

An unsortable neighbour is directly useful -- if it is non-minimal, its
unsortable deletion has length n-1 -- so each is checked for that.

    python scripts/neighbourhood.py --perm 6-14-2-... --k 3
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import worker_is_sortable
from unsortable.minimizer import delete_positions
from unsortable.perms import Perm, from_string, to_string


def all_neighbours(p: Perm) -> list[tuple[str, Perm]]:
    n = len(p)
    out: dict[Perm, str] = {}
    for i, j in combinations(range(n), 2):           # transpositions
        q = list(p); q[i], q[j] = q[j], q[i]
        out.setdefault(tuple(q), f"swap positions {i},{j}")
    for i in range(n):                                # point relocations
        for j in range(n):
            if i == j:
                continue
            q = list(p); q.insert(j, q.pop(i))
            out.setdefault(tuple(q), f"move position {i} -> {j}")
    for v in range(1, n):                              # adjacent-value swaps
        q = list(p)
        a, b = q.index(v), q.index(v + 1)
        q[a], q[b] = q[b], q[a]
        out.setdefault(tuple(q), f"swap values {v},{v+1}")
    out.pop(tuple(p), None)
    return [(why, q) for q, why in out.items()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args(argv)

    p = from_string(a.perm)
    nbrs = all_neighbours(p)
    print(f"{to_string(p)}  (n={len(p)})")
    print(f"{len(nbrs)} distinct same-length neighbours; deciding all ...\n",
          flush=True)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        verdicts = list(ex.map(worker_is_sortable, [q for _, q in nbrs], [a.k] * len(nbrs)))
        unsortable = [(why, q) for (why, q), s in zip(nbrs, verdicts) if not s]
        print(f"{len(unsortable)}/{len(nbrs)} neighbours are still unsortable "
              f"({len(unsortable)/len(nbrs):.2%})  [{time.time()-t0:.0f}s]\n",
              flush=True)

        shorter = []
        for why, q in unsortable:
            dels = [delete_positions(q, [i]) for i in range(len(q))]
            ds = list(ex.map(worker_is_sortable, dels, [a.k] * len(dels)))
            bad = [d for d, s in zip(dels, ds) if not s]
            tag = "BASIS" if not bad else f"NON-MINIMAL -> length {len(bad[0])}"
            print(f"  {why:<28} {to_string(q)}  [{tag}]", flush=True)
            shorter.extend(bad)

    if shorter:
        best = min(shorter, key=len)
        print(f"\n*** SHORTER WITNESS, length {len(best)} ***\n{to_string(best)}")
        return 0
    if unsortable:
        print(f"\nAll {len(unsortable)} unsortable neighbours are basis elements. "
              f"No length-{len(p)-1} witness in this neighbourhood,\nbut they are "
              f"new basis elements worth harvesting for structure.")
    else:
        print(f"\nNo neighbour of {to_string(p)} is unsortable -- it is an "
              f"isolated point\nunder this move set. Exhaustive, not sampled.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
