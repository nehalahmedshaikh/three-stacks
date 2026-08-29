"""Look for shared structure among the basis elements we have found.

A pile of short basis elements is data; a *pattern* among them would be
mathematics.  This script asks the obvious questions of whatever is recorded
in results/witnesses.jsonl:

  * how are the lengths distributed, and how many distinct ones did we see?
  * are any two related by a symmetry?  (none of the four symmetries
    preserves sortability, so any coincidence here would be notable)
  * what do their plots look like -- descents, inversions, left-to-right
    maxima, longest increasing/decreasing runs?
  * do they share small patterns more often than random permutations of the
    same length do?  That is the first place an infinite family would show.

    python scripts/analyse_basis.py --min-length 24 --max-length 26
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable import perms
from unsortable.perms import Perm, from_string, standardise, to_string


def load_basis_elements(min_len: int, max_len: int, k: int) -> list[Perm]:
    seen: dict[Perm, None] = {}
    wf = ROOT / "results" / "witnesses.jsonl"
    if wf.exists():
        for line in wf.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("k") != k or not row.get("minimal"):
                continue
            if min_len <= row["n"] <= max_len:
                seen[from_string(row["perm"])] = None
    bf = ROOT / "results" / "basis_k3_n24.json"
    if bf.exists():
        d = json.loads(bf.read_text())
        if d.get("is_basis_element") and min_len <= d["n"] <= max_len:
            seen[from_string(d["perm"])] = None
    return list(seen)


def stats(p: Perm) -> dict:
    n = len(p)
    desc = sum(1 for i in range(n - 1) if p[i] > p[i + 1])
    inv = sum(1 for i, j in combinations(range(n), 2) if p[i] > p[j])
    ltr_max = 0
    best = 0
    for v in p:
        if v > best:
            best, ltr_max = v, ltr_max + 1
    fixed = sum(1 for i, v in enumerate(p, start=1) if i == v)
    return {"n": n, "descents": desc, "inversions": inv,
            "inv_density": inv / (n * (n - 1) / 2),
            "ltr_maxima": ltr_max, "fixed_points": fixed}


def pattern_profile(p: Perm, size: int, cap: int, rng: random.Random) -> Counter:
    """Frequency of each length-`size` pattern, sampled if there are many."""
    n = len(p)
    idxs = list(combinations(range(n), size))
    if len(idxs) > cap:
        idxs = rng.sample(idxs, cap)
    return Counter(standardise([p[i] for i in idx]) for idx in idxs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-length", type=int, default=0)
    ap.add_argument("--max-length", type=int, default=10 ** 6)
    ap.add_argument("--pattern-size", type=int, default=4)
    ap.add_argument("--cap", type=int, default=20000)
    a = ap.parse_args(argv)

    rng = random.Random(0)
    els = load_basis_elements(a.min_length, a.max_length, a.k)
    if not els:
        print("no recorded basis elements in that range; run scripts/hunt.py first")
        return 1
    els.sort(key=len)

    by_len = Counter(len(p) for p in els)
    print(f"{len(els)} distinct basis elements, k={a.k}")
    print("lengths:", ", ".join(f"{n}x{c}" for n, c in sorted(by_len.items())))
    print()

    print(f"{'perm':<58} {'desc':>5} {'inv':>5} {'dens':>6} {'ltrmax':>7} {'fix':>4}")
    for p in els:
        s = stats(p)
        print(f"{to_string(p):<58} {s['descents']:>5} {s['inversions']:>5} "
              f"{s['inv_density']:>6.3f} {s['ltr_maxima']:>7} {s['fixed_points']:>4}")
    print()

    # random baseline for the same lengths
    print("random permutations of the same lengths, for comparison:")
    for n in sorted(by_len):
        ds, ivs = [], []
        for _ in range(200):
            q = list(range(1, n + 1))
            rng.shuffle(q)
            s = stats(tuple(q))
            ds.append(s["descents"])
            ivs.append(s["inv_density"])
        print(f"  n={n}: descents ~ {sum(ds)/len(ds):.1f}, "
              f"inversion density ~ {sum(ivs)/len(ivs):.3f}")
    print()

    # symmetry coincidences
    hits = []
    pool = set(els)
    for p in els:
        for name, f in perms.SYMMETRIES.items():
            q = f(p)
            if q in pool and q != p:
                hits.append((to_string(p), name, to_string(q)))
    print(f"symmetry-related pairs among them: {len(hits)}")
    for h in hits[:10]:
        print("   ", h)
    print()

    # shared small patterns
    if len(els) >= 2:
        size = a.pattern_size
        profiles = [pattern_profile(p, size, a.cap, rng) for p in els]
        universe = set().union(*profiles)
        print(f"length-{size} patterns: {len(universe)} distinct seen across all "
              f"basis elements (of {len(list(perms.all_perms(size)))} possible)")
        missing = [q for q in perms.all_perms(size)
                   if all(q not in prof for prof in profiles)]
        if missing:
            print(f"  patterns absent from EVERY basis element ({len(missing)}): "
                  + ", ".join(to_string(q) for q in missing[:20]))
        else:
            print("  every pattern of that size occurs in at least one")
        common = [q for q in universe if all(q in prof for prof in profiles)]
        print(f"  patterns present in every basis element: {len(common)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
