"""Test the machine model itself against the literature.

The worry this answers: our answer could be wrong not because the solver is
buggy but because we are *modelling the wrong machine*.  If our machine were
more restrictive than "three stacks in series" as the literature means it,
permutations would look unsortable that really are sortable, and every bound
here would be worthless.

The literature gives a sharp, falsifiable prediction to test against:

    Atkinson: every permutation of length <= 13 is sortable by three stacks
    in series.

So if our model is too restrictive, sampling length-12 and length-13
permutations must eventually turn up one our encoding calls unsortable.  If
thousands come back sortable -- each with an operation word that *replays*
and really does sort -- the model is behaving as the literature says it
should, right up to the edge of the known-sortable range.

The same logic pins the other end.  For two stacks the literature says the
shortest unsortable permutation has length exactly 7; we reproduce 7, not 6
(too restrictive) and not 8 (too permissive).  And one stack must give
exactly Av(231) and the Catalan numbers.  A model error would have to break
all of these at once while leaving them individually consistent.

    python scripts/validate_model.py --n 12 13 --trials 400
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify  # independent replayer
from unsortable.encoding import solve
from unsortable.perms import to_string


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, nargs="+", default=[12, 13])
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260830)
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)
    total_bad = 0
    for n in a.n:
        t0 = time.time()
        bad = replay_fail = 0
        for _ in range(a.trials):
            p = list(range(1, n + 1))
            rng.shuffle(p)
            p = tuple(p)
            r = solve(p, k=a.k, mode="reduced")
            if not r.sortable:
                bad += 1
                print(f"  *** CONTRADICTS ATKINSON: {to_string(p)} (n={n}) "
                      f"called unsortable ***", flush=True)
                continue
            # a SAT verdict is only worth anything if the run really sorts
            if not verify.sorts(list(p), r.ops, k=a.k):
                replay_fail += 1
                print(f"  *** REPLAY FAILED: {to_string(p)} ***", flush=True)
        dt = time.time() - t0
        status = "OK" if bad == 0 and replay_fail == 0 else "PROBLEM"
        print(f"n={n:>3}  {a.trials} random permutations  "
              f"unsortable={bad}  replay_failures={replay_fail}  "
              f"[{dt:.0f}s]  {status}", flush=True)
        total_bad += bad + replay_fail

    print()
    if total_bad == 0:
        print("Model consistent with Atkinson: every sampled permutation of "
              "length <= 13 was\nsortable, and every operation word replayed "
              "correctly on an independent simulator.")
        return 0
    print(f"{total_bad} inconsistencies -- the model or the encoding is wrong. "
          "Stop and fix before\ntrusting any bound in this repo.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
