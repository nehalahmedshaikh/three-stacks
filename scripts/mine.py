"""Mine for new shortest witnesses, and probe each one immediately.

The bottleneck is not compute, it is that we have exactly **one** basis
element at the current best length, and its full 651-neighbour ball contains
nothing unsortable.  A second one would give a second ball to probe, and any
*non-minimal* unsortable permutation in any of those balls yields a witness
one shorter.

So this loops:

  1. pick a starting basis element from the pool on disk
  2. perturb it upward and descend again (the only move that has ever
     produced a drop) until it lands at the target length or below
  3. if that is a permutation we have not seen, enumerate its **entire**
     same-length neighbourhood
  4. any unsortable neighbour is checked for non-minimality -- and a
     non-minimal one is exactly a witness of length-1

Everything is appended to results/witnesses.jsonl as it happens, so the pool
grows across runs and an interrupted run loses at most one descent.

    python scripts/mine.py --target 22 --workers 12
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from concurrent.futures import ProcessPoolExecutor

from scripts.neighbourhood import all_neighbours
from unsortable import search
from unsortable.encoding import worker_is_sortable
from unsortable.minimizer import delete_positions, minimise
from unsortable.perms import Perm, from_string, to_string

WITNESSES = ROOT / "results" / "witnesses.jsonl"


def record(kind: str, perm: Perm, k: int, minimal: bool, extra=None) -> None:
    row = {"perm": to_string(perm), "n": len(perm), "k": k,
           "minimal": minimal, "kind": kind}
    if extra:
        row.update(extra)
    with WITNESSES.open("a", newline="\n") as fh:
        fh.write(json.dumps(row) + "\n")


def pool_of(k: int, lo: int, hi: int) -> list[Perm]:
    seen: dict[Perm, None] = {}
    if WITNESSES.exists():
        for line in WITNESSES.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            if o.get("k") == k and o.get("minimal") and lo <= o["n"] <= hi:
                seen[from_string(o["perm"])] = None
    return list(seen)


def probe(ex, q: Perm, k: int) -> Perm | None:
    """Enumerate q's whole neighbourhood; return a shorter witness if any."""
    nbrs = all_neighbours(q)
    verdicts = list(ex.map(worker_is_sortable, [x for _, x in nbrs], [k] * len(nbrs)))
    unsortable = [x for (_, x), s in zip(nbrs, verdicts) if not s]
    print(f"    neighbourhood: {len(unsortable)}/{len(nbrs)} unsortable",
          flush=True)
    for x in unsortable:
        dels = [delete_positions(x, [i]) for i in range(len(x))]
        ds = list(ex.map(worker_is_sortable, dels, [k] * len(dels)))
        bad = [d for d, s in zip(dels, ds) if not s]
        if bad:
            return min(bad, key=len)
        record("mine-basis", x, k, True, {"from": to_string(q)})
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--target", type=int, required=True,
                    help="length at which to probe neighbourhoods")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=100000)
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)
    target = a.target
    starts = pool_of(a.k, target, target + 3)
    if not starts:
        print("no starting basis elements on disk")
        return 1
    probed: set[Perm] = set()
    found_at_target = {p for p in starts if len(p) == target}
    print(f"pool: {len(starts)} basis elements of length {target}-{target+3}; "
          f"{len(found_at_target)} already at {target}\n", flush=True)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        # probe what we already have before generating anything new
        for q in sorted(found_at_target, key=to_string):
            if q in probed:
                continue
            probed.add(q)
            print(f"probing known {to_string(q)}", flush=True)
            hit = probe(ex, q, a.k)
            if hit is not None:
                print(f"\n*** LENGTH {len(hit)} ***\n{to_string(hit)}\n", flush=True)
                record("mine-shorter", hit, a.k, True, {"from": to_string(q)})
                return 0

        for rnd in range(a.rounds):
            start = rng.choice(starts)
            climb = rng.randint(2, 6)
            perturbed = search.perturb(start, climb, rng)
            rep = minimise(perturbed, k=a.k, workers=a.workers,
                           rng=random.Random(rng.randrange(10 ** 6)))
            q = rep.result
            if len(q) > target:
                continue
            if q in probed:
                continue
            probed.add(q)
            if q not in starts:
                starts.append(q)
                record("mine-new", q, a.k, True,
                       {"length": len(q), "round": rnd})
            print(f"[{rnd}] new length-{len(q)} basis element after "
                  f"{time.time()-t0:.0f}s\n    {to_string(q)}", flush=True)
            hit = probe(ex, q, a.k)
            if hit is not None:
                print(f"\n*** LENGTH {len(hit)} ***\n{to_string(hit)}\n", flush=True)
                record("mine-shorter", hit, a.k, True, {"from": to_string(q)})
                return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
