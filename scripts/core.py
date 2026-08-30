"""Ask the solver *why* a permutation is unsortable.

We have DRAT refutations, but a refutation is a proof, not an explanation.
drat-trim's ``-c`` flag emits the **unsatisfiable core**: the subset of the
original clauses that actually participate in the contradiction.  Mapping
those clauses back to the constraints they encode says which stack, which
values, and which occupancy intervals are jointly impossible.

That matters because the search is stuck for a structural reason.  Local
methods have no gradient (f = 0 everywhere off the witness) and there is no
short obstruction to prune with, so the only way below the current bound is
to understand *why* one witness works and build another.  This is the
cheapest available route to that: the solver already found the reason, it
just prints it as 5 MB of resolution steps.

Reported per core clause:

  input order      value v must enter before value w
  output order     value v must leave before value w
  phase order      value v enters S_{s+1} only after leaving S_s
  non-crossing     on stack s, values v and w may not cross
  transitivity     ordering consistency among three events

The interesting rows are the non-crossing ones: those are the LIFO
obstructions, and which pairs appear -- and how often each value appears --
is the shape of the contradiction.

    python scripts/core.py --perm 6-14-2-... --k 3
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import _Builder
from unsortable.perms import from_string, to_string


def labelled_clauses(perm, k: int):
    """Rebuild the full-mode CNF, tagging every clause with what it means."""
    b = _Builder(perm, k, "full")
    tags: dict[frozenset, str] = {}
    n = len(perm)

    def ev_name(e):
        v, p = e // (k + 1) + 1, e % (k + 1)
        return f"t{p+1}[{v}]"

    # units, in the same order build() emits them
    for v in range(1, n + 1):
        for p in range(k):
            c = [b.lit(b.ev(v, p), b.ev(v, p + 1))]
            tags.setdefault(frozenset(c), f"phase   {ev_name(b.ev(v,p))} < {ev_name(b.ev(v,p+1))}")
            b.clauses.append(c)
    for i in range(n - 1):
        c = [b.lit(b.ev(perm[i], 0), b.ev(perm[i + 1], 0))]
        tags.setdefault(frozenset(c), f"input   {perm[i]} before {perm[i+1]}")
        b.clauses.append(c)
    for v in range(1, n):
        c = [b.lit(b.ev(v, k), b.ev(v + 1, k))]
        tags.setdefault(frozenset(c), f"output  {v} before {v+1}")
        b.clauses.append(c)

    before = len(b.clauses)
    b._transitivity()
    for c in b.clauses[before:]:
        tags.setdefault(frozenset(c), "transitivity")

    before = len(b.clauses)
    b._noncrossing()
    # regenerate the non-crossing tags with their (stack, v, w)
    idx = before
    for s in range(k):
        for v in range(1, n + 1):
            av, bv = b.ev(v, s), b.ev(v, s + 1)
            for w in range(1, n + 1):
                if w == v:
                    continue
                aw = b.ev(w, s)
                c = b.clauses[idx]
                tags.setdefault(frozenset(c),
                                f"noncross S{s+1}: {v},{w}")
                idx += 1
    return b, tags


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--solver", default=str(ROOT / "tools" / "cadical.exe"))
    ap.add_argument("--drat-trim", default=str(ROOT / "tools" / "drat-trim.exe"))
    a = ap.parse_args(argv)

    perm = from_string(a.perm)
    n = len(perm)
    b, tags = labelled_clauses(perm, a.k)
    print(f"{to_string(perm)}  (n={n}, k={a.k})")
    print(f"full encoding: {b.n_vars:,} vars, {len(b.clauses):,} clauses\n",
          flush=True)

    tmp = Path(tempfile.mkdtemp(prefix="core"))
    cnf, drat, core = tmp / "f.cnf", tmp / "f.drat", tmp / "f.core"
    with cnf.open("w", newline="\n") as fh:
        fh.write(f"p cnf {b.n_vars} {len(b.clauses)}\n")
        for c in b.clauses:
            fh.write(" ".join(map(str, c)) + " 0\n")

    print("solving ...", flush=True)
    r = subprocess.run([a.solver, "--no-binary", str(cnf), str(drat)],
                       capture_output=True, text=True)
    if r.returncode != 20:
        print(f"solver returned {r.returncode}; expected UNSAT (20)")
        return 1
    print("extracting core ...", flush=True)
    subprocess.run([a.drat_trim, str(cnf), str(drat), "-c", str(core)],
                   capture_output=True, text=True, timeout=7200)
    if not core.exists():
        print("drat-trim produced no core file")
        return 1

    kinds: Counter = Counter()
    noncross: list[tuple[int, int, int]] = []
    involved: Counter = Counter()
    total = 0
    for line in core.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("p", "c")):
            continue
        lits = frozenset(int(x) for x in line.split() if x != "0")
        if not lits:
            continue
        total += 1
        tag = tags.get(lits, "?unmapped")
        kind = tag.split()[0]
        kinds[kind] += 1
        if kind == "noncross":
            s = int(tag.split()[1][1])  # already 1-based from the tag
            v, w = (int(x) for x in tag.split(":")[1].split(","))
            noncross.append((s, v, w))
            involved[v] += 1
            involved[w] += 1

    print(f"\ncore: {total:,} of {len(b.clauses):,} clauses "
          f"({total/len(b.clauses):.1%})\n")
    for kind, cnt in kinds.most_common():
        print(f"  {kind:<14} {cnt:>7,}")

    if noncross:
        per_stack = Counter(s for s, _, _ in noncross)
        print(f"\nnon-crossing constraints in the core, by stack:")
        for s in sorted(per_stack):
            print(f"  S{s}: {per_stack[s]:,}")
        print(f"\nvalues by how often they appear in a core non-crossing "
              f"constraint:")
        ranked = involved.most_common()
        for v, c in ranked:
            pos = perm.index(v) + 1
            print(f"  value {v:>3} (position {pos:>3}): {c:>5}")
        missing = [v for v in range(1, n + 1) if v not in involved]
        print(f"\nvalues absent from every core non-crossing constraint: "
              f"{missing if missing else 'none -- all are needed'}")
    print(f"\ncore written to {core}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
