"""Give the search a gradient, by counting instead of deciding.

Every method so far has been blind, because sortability is a yes/no answer:
at length 21 every permutation we try is sortable, and they all look
identical to the search.  There is nothing to climb.

So measure something real-valued instead.  For a permutation `p` of length
L, define

    f(p) = how many of its one-point extensions (length L+1) are unsortable

f is a genuine "how nearly unsortable is this" score.  It is positive
exactly when `p` sits inside a length-(L+1) obstruction, and larger when it
sits inside many.  The 22 one-point deletions of our length-22 witness all
have f >= 1 by construction, so there is somewhere to start.

Two payoffs, and the second is the one that matters right now:

  * hill-climbing f at length 21 walks towards permutations that are close
    to being obstructions, which is the direction a length-21 witness lies
    in, if one exists;
  * **every unsortable extension found is a new length-22 basis element.**
    We have exactly one, and its entire 651-neighbour ball is empty, so new
    ones are the bottleneck for finding a 21.  This manufactures them.

Cost: f needs (L+1)^2 decisions at length L+1 -- 484 at L=21.  That is only
affordable because of FixedLengthDecider (118 ms each, shared CNF), and it
is why this could not have been tried before that landed.

    python scripts/gradient.py --length 21 --workers 12
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable import search
from unsortable.encoding import worker_is_sortable
from unsortable.minimizer import delete_positions
from unsortable.perms import Perm, from_string, to_string

WITNESSES = ROOT / "results" / "witnesses.jsonl"


def record(kind: str, perm: Perm, k: int, minimal: bool, extra=None) -> None:
    row = {"perm": to_string(perm), "n": len(perm), "k": k,
           "minimal": minimal, "kind": kind}
    if extra:
        row.update(extra)
    with WITNESSES.open("a", newline="\n") as fh:
        fh.write(json.dumps(row) + "\n")


def extensions(p: Perm) -> list[Perm]:
    """Every permutation of length n+1 whose deletion of one point gives p."""
    n = len(p)
    out: dict[Perm, None] = {}
    for v in range(1, n + 2):
        lifted = tuple(x + (1 if x >= v else 0) for x in p)
        for pos in range(n + 1):
            out[lifted[:pos] + (v,) + lifted[pos:]] = None
    return list(out)


def score(ex, p: Perm, k: int) -> tuple[int, list[Perm]]:
    """f(p), plus the unsortable extensions themselves."""
    exts = extensions(p)
    verdicts = list(ex.map(worker_is_sortable, exts, [k] * len(exts)))
    bad = [q for q, s in zip(exts, verdicts) if not s]
    return len(bad), bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--length", type=int, default=21)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--neighbours", type=int, default=10,
                    help="candidate moves evaluated per hill-climbing step")
    ap.add_argument("--steps", type=int, default=100000)
    ap.add_argument("--plateau", type=float, default=0.8)
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)
    L = a.length

    # Start from the deletions of the shortest witness we have: each of them
    # has f >= 1 by construction, since deleting from it and putting the point
    # back is an unsortable extension.
    best22 = None
    if WITNESSES.exists():
        cands = []
        for line in WITNESSES.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            if o.get("k") == a.k and o.get("minimal") and o["n"] == L + 1:
                cands.append(from_string(o["perm"]))
        if cands:
            best22 = cands[0]
    if best22 is None:
        print(f"need a length-{L+1} witness on disk to seed from")
        return 1

    cur = delete_positions(best22, [rng.randrange(len(best22))])
    seen_witnesses: set[Perm] = set()
    print(f"hill-climbing f at length {L}, seeded from a deletion of\n"
          f"  {to_string(best22)}\n", flush=True)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        cur_f, bad = score(ex, cur, a.k)
        for q in bad:
            seen_witnesses.add(q)
        print(f"start f={cur_f}  {to_string(cur)}", flush=True)

        for step in range(a.steps):
            cands = search.neighbours(cur, rng, a.neighbours)
            best_c, best_f = None, -1
            fresh_total = 0
            for c in cands:
                # a length-L candidate that is itself unsortable is the prize
                if not worker_is_sortable(c, a.k):
                    print(f"\n*** LENGTH {L} UNSORTABLE ***\n{to_string(c)}\n",
                          flush=True)
                    record("gradient-shorter", c, a.k, True, {})
                    return 0
                f, bd = score(ex, c, a.k)
                # Every unsortable extension is a length-(L+1) witness, whether
                # or not its parent wins the step.  These are the scarce thing,
                # so harvest them from every candidate evaluated.
                for q in bd:
                    if q not in seen_witnesses:
                        seen_witnesses.add(q)
                        fresh_total += 1
                        record("gradient-witness", q, a.k, True,
                               {"f_of_parent": f, "step": step})
                if f > best_f:
                    best_c, best_f = c, f

            # accept improvements, and drift across equal-f plateaus -- without
            # that the walk re-perturbs one point forever (the same failure the
            # basin hop had before plateau moves went in)
            if best_f > cur_f or (best_f == cur_f and rng.random() < a.plateau):
                cur, cur_f = best_c, best_f
            print(f"[{step}] f={cur_f:<4} best_seen={best_f:<4} "
                  f"+{fresh_total} new length-{L+1} witnesses "
                  f"({len(seen_witnesses)} total, {time.time()-t0:.0f}s)",
                  flush=True)
    print(f"\n{len(seen_witnesses)} distinct length-{L+1} witnesses harvested")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
