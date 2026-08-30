"""Consolidate every unsortable permutation found into one committed record.

The search writes to results/witnesses.jsonl, an append-only scratch log full
of intermediate descent steps, gitignored.  This distils it into
results/basis_elements.json: one entry per distinct basis element with its
verification status, so the repo carries a permanent record of everything
found.

Verification status per entry:

  certified        DRAT certificate on disk, drat-trim verified
  basis-verified   all n one-point deletions checked with replayed operation
                   words (scripts/verify_basis.py)
  search-only      found by the minimiser, which checks unsortability and
                   every one-point deletion with the SAT encoding, but whose
                   result has not been separately certified

    python scripts/collect_witnesses.py            # rebuild the record
    python scripts/collect_witnesses.py --recheck  # re-decide each with SAT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import solve
from unsortable.perms import from_string, to_string

RESULTS = ROOT / "results"
PROOFS = ROOT / "proofs"
OUT = RESULTS / "basis_elements.json"


def collect(k: int) -> list[dict]:
    entries: dict[str, dict] = {}

    # 1. the scratch log: minimiser results and hop bests
    wf = RESULTS / "witnesses.jsonl"
    if wf.exists():
        for line in wf.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("k") != k or not row.get("minimal"):
                continue
            entries.setdefault(row["perm"], {
                "perm": row["perm"], "n": row["n"], "k": k,
                "status": "search-only",
                "found_by": row.get("kind", "search"),
            })

    # 2. full basis reports (all deletions replayed)
    for bf in sorted(RESULTS.glob(f"basis_k{k}_n*.json")):
        d = json.loads(bf.read_text())
        if not d.get("is_basis_element"):
            continue
        e = entries.setdefault(d["perm"], {"perm": d["perm"], "n": d["n"], "k": k})
        e["status"] = "basis-verified"
        e["deletions_replayed"] = sum(1 for x in d["deletions"] if x["replay_sorts"])
        e["basis_report"] = str(bf.relative_to(ROOT)).replace("\\", "/")

    # 3. certificates
    cf = RESULTS / "claims.json"
    if cf.exists():
        for c in json.loads(cf.read_text()):
            if c["k"] != k or c["sortable"]:
                continue
            e = entries.setdefault(c["perm"], {"perm": c["perm"], "n": c["n"], "k": k})
            e["certificate_id"] = c["id"]
            e["cnf"] = c["cnf"]
            e["drat"] = c["drat"]
            e["artifacts_committed"] = (ROOT / c["cnf"]).exists() and (ROOT / c["drat"]).exists()
            e["second_solver_agrees"] = c.get("second_solver", {}).get("agrees")
            if e.get("status") != "basis-verified":
                e["status"] = "certified"
            else:
                e["status"] = "certified + basis-verified"

    return sorted(entries.values(), key=lambda e: (e["n"], e["perm"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--recheck", action="store_true",
                    help="re-decide every entry with the SAT encoding")
    a = ap.parse_args(argv)

    entries = collect(a.k)
    if not entries:
        print("nothing recorded yet")
        return 1

    if a.recheck:
        print(f"re-deciding {len(entries)} permutations ...", flush=True)
        for e in entries:
            r = solve(from_string(e["perm"]), k=a.k, mode="reduced")
            e["recheck_unsortable"] = not r.sortable
            flag = "" if not r.sortable else "   <-- SORTABLE?!"
            print(f"  n={e['n']:>3}  unsortable={not r.sortable}{flag}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"k": a.k, "count": len(entries),
                               "basis_elements": entries}, indent=2) + "\n")

    print(f"\n{len(entries)} distinct basis elements for k={a.k}\n")
    print(f"{'n':>4}  {'status':<28} perm")
    for e in entries:
        print(f"{e['n']:>4}  {e['status']:<28} {e['perm']}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
