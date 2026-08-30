"""Is the observed structure usable as a search bias?

The basis elements are not uniform permutations.  Measured over 25 of them
(`scripts/shape.py`):

  * value 1 sits at the very end          (median position 1.00 of the way)
  * value 2 sits early                    (median 0.18)
  * the first entry is about 0.27n
  * alternation is 0.81-0.90 against 0.67 for a uniform permutation --
    they are strongly zigzag

If that profile is causal, sampling from it should turn up unsortable
permutations at a higher rate than sampling uniformly.  This measures it:
same length, same budget, three distributions, count the unsortable ones.

Uniform sampling finds nothing below length ~38, so the comparison runs at a
length where the uniform rate is non-zero and a ratio is meaningful.  A much
higher structured rate there justifies pointing the same bias at lengths
20-21, where uniform sampling is hopeless.

    python scripts/structured_search.py --compare-at 38 --trials 120
    python scripts/structured_search.py --hunt-at 21 --trials 4000
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.minimizer import _solve_one
from unsortable.perms import Perm, to_string


def uniform(n: int, rng: random.Random) -> Perm:
    q = list(range(1, n + 1))
    rng.shuffle(q)
    return tuple(q)


def one_last(n: int, rng: random.Random) -> Perm:
    """Uniform, but with value 1 forced into the final position."""
    q = list(range(2, n + 1))
    rng.shuffle(q)
    return tuple(q) + (1,)


def zigzag_one_last(n: int, rng: random.Random) -> Perm:
    """Strongly alternating, value 1 last, first entry near 0.27n.

    Built by putting large values in the peak positions and small ones in the
    valleys, which forces alternation, then relaxing a few positions at
    random so the sample is not degenerate.
    """
    body = n - 1                     # positions 0..n-2, value 1 goes last
    vals = list(range(2, n + 1))
    lo = vals[: body // 2]
    hi = vals[body // 2:]
    rng.shuffle(lo)
    rng.shuffle(hi)
    out: list[int] = []
    li = hi_i = 0
    for i in range(body):
        if i % 2 == 0 and li < len(lo):
            out.append(lo[li]); li += 1
        elif hi_i < len(hi):
            out.append(hi[hi_i]); hi_i += 1
        else:
            out.append(lo[li]); li += 1
    for _ in range(rng.randint(0, 3)):        # relax a little
        i, j = rng.randrange(body), rng.randrange(body)
        out[i], out[j] = out[j], out[i]
    return tuple(out) + (1,)


GENERATORS = {
    "uniform": uniform,
    "one-last": one_last,
    "zigzag+one-last": zigzag_one_last,
}


def run(gen, n, trials, k, workers, rng, label, show=False):
    ps = [gen(n, rng) for _ in range(trials)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        verdicts = list(ex.map(_solve_one, ps, [k] * len(ps), ["reduced"] * len(ps)))
    bad = [p for p, s in zip(ps, verdicts) if not s]
    print(f"  {label:<18} {len(bad):>4}/{trials}  ({len(bad)/trials:6.2%})"
          f"  [{time.time()-t0:.0f}s]", flush=True)
    if show:
        for p in bad[:5]:
            print(f"      {to_string(p)}", flush=True)
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--trials", type=int, default=120)
    ap.add_argument("--compare-at", type=int, default=None)
    ap.add_argument("--hunt-at", type=int, default=None)
    ap.add_argument("--seed", type=int, default=20260830)
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)

    if a.compare_at:
        n = a.compare_at
        print(f"unsortable rate at length {n}, {a.trials} samples each:\n")
        for label, gen in GENERATORS.items():
            run(gen, n, a.trials, a.k, a.workers, rng, label)
        print("\nIf the structured rows beat uniform by a wide margin, the "
              "profile is causal\nand worth pointing at shorter lengths.")

    if a.hunt_at:
        n = a.hunt_at
        print(f"\nhunting at length {n} with the structured distribution, "
              f"{a.trials} samples:\n")
        bad = run(zigzag_one_last, n, a.trials, a.k, a.workers, rng,
                  "zigzag+one-last", show=True)
        if bad:
            print(f"\n*** {len(bad)} unsortable permutations of length {n} ***")
            return 0
        print(f"\nnone found -- the rate at length {n} is below "
              f"1/{a.trials} even under the structured distribution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
