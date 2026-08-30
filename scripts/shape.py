"""Is there a common *shape* to the basis elements, and does it scale?

Two questions, both testable:

1. Do particular positions prefer particular value bands?  Rescale every
   basis element to the unit square -- position i/n against value v/n -- and
   the elements of different lengths become directly comparable.  If they
   share a shape, the overlaid points will concentrate rather than fill.

2. If they do share a shape, can it be *resampled* to a length we have never
   seen?  A witness of length 23 resampled to 21 is a concrete candidate, and
   candidates are cheap to test.  This is the only route to a shorter witness
   that does not depend on stumbling across one.

Also reports plain positional statistics: where the small values sit, where
the large ones sit, and how sharply that is determined.

    python scripts/shape.py --min-length 22 --max-length 26
    python scripts/shape.py --resample-to 21 --test
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.collect_witnesses import collect
from unsortable.perms import Perm, check, from_string, standardise, to_string

BANDS = 6  # how many position buckets when summarising


def load(k: int, lo: int, hi: int) -> list[Perm]:
    seen = {}
    for e in collect(k):
        if lo <= e["n"] <= hi:
            seen[from_string(e["perm"])] = None
    wf = ROOT / "results" / "witnesses.jsonl"
    if wf.exists():
        for line in wf.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("k") == k and row.get("minimal") and lo <= row["n"] <= hi:
                seen[from_string(row["perm"])] = None
    return sorted(seen, key=len)


def band_profile(els: list[Perm]) -> list[tuple[float, float, int]]:
    """(mean normalised value, stdev, count) per normalised position band."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for p in els:
        n = len(p)
        for i, v in enumerate(p):
            b = min(BANDS - 1, int(i / n * BANDS))
            buckets[b].append((v - 0.5) / n)
    out = []
    for b in range(BANDS):
        xs = buckets[b]
        m = sum(xs) / len(xs)
        var = sum((x - m) ** 2 for x in xs) / len(xs)
        out.append((m, var ** 0.5, len(xs)))
    return out


def resample(p: Perm, m: int) -> Perm:
    """Rescale a permutation to length m, preserving its normalised shape.

    Take m evenly spaced sample points of the normalised plot and rank the
    sampled values.  This is the natural 'same shape, different size' map.
    """
    n = len(p)
    pts = []
    for j in range(m):
        i = min(n - 1, int((j + 0.5) * n / m))
        pts.append(p[i])
    # ties are possible after sampling; break them by original position
    order = sorted(range(m), key=lambda j: (pts[j], j))
    out = [0] * m
    for rank, j in enumerate(order, start=1):
        out[j] = rank
    return tuple(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-length", type=int, default=0)
    ap.add_argument("--max-length", type=int, default=10 ** 6)
    ap.add_argument("--resample-to", type=int, default=None)
    ap.add_argument("--test", action="store_true",
                    help="decide the resampled candidates with the SAT encoding")
    a = ap.parse_args(argv)

    els = load(a.k, a.min_length, a.max_length)
    if not els:
        print("no basis elements in that range")
        return 1
    print(f"{len(els)} basis elements, lengths "
          f"{sorted({len(p) for p in els})}\n")

    # --- where do the extreme values sit? ---
    print("position of the smallest and largest values (as a fraction of n):")
    for label, pick in (("value 1", lambda p: p.index(1)),
                        ("value 2", lambda p: p.index(2)),
                        ("value n", lambda p: p.index(len(p))),
                        ("value n-1", lambda p: p.index(len(p) - 1))):
        fr = sorted(pick(p) / (len(p) - 1) for p in els)
        print(f"  {label:<9} median {fr[len(fr)//2]:.2f}   "
              f"range {fr[0]:.2f}-{fr[-1]:.2f}")
    print()

    print("first entry, as a fraction of n:")
    fr = sorted(p[0] / len(p) for p in els)
    print(f"  median {fr[len(fr)//2]:.2f}   range {fr[0]:.2f}-{fr[-1]:.2f}")
    firsts = sorted({p[0] for p in els})
    print(f"  raw first entries seen: {firsts}\n")

    # --- normalised shape ---
    print(f"normalised value by position band (0 = start, 1 = end):")
    print(f"  {'band':<12} {'mean':>6} {'stdev':>7}   {'':<20}")
    for b, (m, sd, cnt) in enumerate(band_profile(els)):
        lo, hi = b / BANDS, (b + 1) / BANDS
        bar = "#" * int(m * 20)
        print(f"  {lo:.2f}-{hi:.2f}   {m:>6.3f} {sd:>7.3f}   {bar:<20}")
    print("  (a uniform random permutation would give mean 0.500, stdev 0.289"
          " in every band)\n")

    # --- ascent/descent signature ---
    print("descent pattern (fraction of positions that are descents):")
    for p in els[:6]:
        d = sum(1 for i in range(len(p) - 1) if p[i] > p[i + 1]) / (len(p) - 1)
        alt = sum(1 for i in range(len(p) - 2)
                  if (p[i] > p[i + 1]) != (p[i + 1] > p[i + 2])) / (len(p) - 2)
        print(f"  n={len(p):<3} descents {d:.2f}   alternation {alt:.2f}   "
              f"{to_string(p)[:44]}")
    print("  (uniform random: descents 0.50, alternation 0.67)\n")

    if a.resample_to:
        m = a.resample_to
        print(f"resampling every basis element to length {m}:\n")
        cands = {}
        for p in els:
            q = resample(p, m)
            cands.setdefault(q, []).append(len(p))
        print(f"  {len(cands)} distinct candidates from {len(els)} sources")
        if a.test:
            from unsortable.encoding import solve
            hits = 0
            for q, srcs in cands.items():
                r = solve(q, k=a.k, mode="reduced")
                mark = "UNSORTABLE  <<<<<" if not r.sortable else "sortable"
                if not r.sortable:
                    hits += 1
                print(f"  {to_string(q)}  from n={srcs}  {mark}", flush=True)
            print(f"\n  {hits}/{len(cands)} candidates unsortable")
        else:
            for q, srcs in list(cands.items())[:10]:
                print(f"  {to_string(q)}  from n={srcs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
