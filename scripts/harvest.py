"""Breadth-first search over the basis-element graph at a fixed length.

Two things we want, and one search that gets both.

*Shorter witnesses.*  A length-L basis element has no unsortable deletion by
definition, so it cannot be shortened.  But a *different* length-L unsortable
permutation might be non-minimal, and then its unsortable deletion has length
L-1.  So: from a known witness, enumerate every same-length neighbour, keep
the unsortable ones, and check each for non-minimality.

*Structure.*  Every unsortable neighbour that turns out to be minimal is a
new basis element, and structure cannot be inferred from one example.  The
exhaustive neighbourhood of the length-23 witness yielded four new ones in
under three minutes.

The frontier is explored oldest-first, so the population stays spread around
the starting witness instead of drilling down one branch.  Everything found
is appended to results/witnesses.jsonl as it happens.

    python scripts/harvest.py --perm 6-11-4-... --k 3 --workers 12
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.neighbourhood import all_neighbours
from unsortable.minimizer import _solve_one, delete_positions
from unsortable.perms import Perm, from_string, to_string

WITNESSES = ROOT / "results" / "witnesses.jsonl"


def record(kind: str, perm: Perm, k: int, minimal: bool, extra=None) -> None:
    WITNESSES.parent.mkdir(parents=True, exist_ok=True)
    row = {"perm": to_string(perm), "n": len(perm), "k": k,
           "minimal": minimal, "kind": kind}
    if extra:
        row.update(extra)
    with WITNESSES.open("a", newline="\n") as fh:
        fh.write(json.dumps(row) + "\n")


def decide_many(ex, perms, k):
    perms = list(perms)
    if not perms:
        return []
    return list(ex.map(_solve_one, perms, [k] * len(perms),
                       ["reduced"] * len(perms)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--max-nodes", type=int, default=100000)
    a = ap.parse_args(argv)

    start = from_string(a.perm)
    L = len(start)
    seen: set[Perm] = {start}
    frontier: deque[Perm] = deque([start])
    basis_found = 1
    shortest = start
    t0 = time.time()

    print(f"harvesting basis elements at length {L} from {to_string(start)}\n",
          flush=True)

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        nodes = 0
        while frontier and nodes < a.max_nodes:
            cur = frontier.popleft()
            nodes += 1
            nbrs = all_neighbours(cur)
            verdicts = decide_many(ex, [q for _, q in nbrs], a.k)
            unsortable = [q for (_, q), s in zip(nbrs, verdicts)
                          if not s and q not in seen]

            for q in unsortable:
                seen.add(q)
                dels = [delete_positions(q, [i]) for i in range(len(q))]
                ds = decide_many(ex, dels, a.k)
                bad = [d for d, s in zip(dels, ds) if not s]
                if bad:
                    best = min(bad, key=len)
                    print(f"\n*** SHORTER WITNESS, length {len(best)} ***",
                          flush=True)
                    print(f"{to_string(best)}\n", flush=True)
                    record("harvest-shorter", best, a.k, True,
                           {"from": to_string(q)})
                    if len(best) < len(shortest):
                        shortest = best
                    # restart the harvest at the new length
                    seen, frontier = {best}, deque([best])
                    L = len(best)
                    basis_found = 1
                    break
                basis_found += 1
                record("harvest-basis", q, a.k, True, {"from": to_string(cur)})
                frontier.append(q)
            else:
                print(f"[{nodes}] node {to_string(cur)[:40]}...  "
                      f"{len(unsortable)} new  |  {basis_found} basis elements, "
                      f"frontier {len(frontier)}, {time.time()-t0:.0f}s",
                      flush=True)

    print(f"\n{basis_found} basis elements at length {L}; "
          f"shortest found {len(shortest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
