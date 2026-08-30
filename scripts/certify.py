"""M2: turn a claim into shippable, machine-checkable artifacts.

For a permutation claimed UNSORTABLE this writes

    proofs/<id>.cnf     the full-mode DIMACS encoding
    proofs/<id>.drat    the solver's refutation of exactly that CNF
    proofs/<id>.json    metadata (permutation, k, sizes, solver, timings)

and appends an entry to results/claims.json.  ``proofcheck.py`` then hands
the pair to drat-trim, and ``verify.py`` re-decides small cases from scratch.

For a permutation claimed SORTABLE the artifact is just the operation word,
which ``verify.py replay`` checks completely on its own.

The proof comes from a **solver binary writing DRAT directly to a file**.
PySAT's in-memory capture truncates the proof stream: for the length-33
witness it returned 15 MB of a proof lingeling reported writing as 6.1 MB,
and drat-trim rejected the result on an instance that really is
unsatisfiable.  A truncated proof that still verifies is sound -- drat-trim
checks every step -- but one that fails is indistinguishable from a wrong
answer.

drat-trim proves *the CNF is unsatisfiable*.  That the CNF asks the
sortability question is established separately, by the proof in
docs/notes.md §3 and by exhaustive agreement with the brute-force simulator
in tests/test_encoding.py.

    python scripts/certify.py --perm 2435761 --k 2
    python scripts/certify.py --from-witnesses --minimal-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import _model_to_ops, encode
from unsortable.perms import from_string, to_string
from unsortable.simulator import SearchLimitExceeded, sorting_sequence

PROOFS = ROOT / "proofs"
CLAIMS = ROOT / "results" / "claims.json"
BRUTE_FORCE_LIMIT_NODES = 5_000_000


def claim_id(perm, k: int) -> str:
    h = hashlib.sha256(to_string(perm).encode()).hexdigest()[:8]
    return f"k{k}_n{len(perm)}_{h}"


def find_solver(explicit: str | None = None) -> str | None:
    for cand in (explicit, os.environ.get("THREE_STACKS_CADICAL")):
        if cand and Path(cand).exists():
            return str(Path(cand).resolve())
    for name in ("cadical.exe", "cadical"):
        local = ROOT / "tools" / name
        if local.exists():
            return str(local.resolve())
    return shutil.which("cadical")


def run_solver(binary: str, cnf: Path, drat: Path, timeout: int | None):
    """Run the solver, proof straight to file.  Returns (sat, model, seconds)."""
    t0 = time.perf_counter()
    proc = subprocess.run([binary, "--no-binary", str(cnf), str(drat)],
                          capture_output=True, text=True, timeout=timeout)
    dt = time.perf_counter() - t0
    out = proc.stdout or ""
    if proc.returncode == 10:
        model: list[int] = []
        for line in out.splitlines():
            if line.startswith("v "):
                model.extend(int(t) for t in line[2:].split() if t != "0")
        return True, model, dt
    if proc.returncode == 20:
        return False, None, dt
    raise RuntimeError(
        f"solver returned {proc.returncode}\n{out[-2000:]}\n{(proc.stderr or '')[-2000:]}")


def certify(perm, k: int = 3, brute_force: bool = True,
            solver: str | None = None, timeout: int | None = None) -> dict:
    cid = claim_id(perm, k)
    PROOFS.mkdir(parents=True, exist_ok=True)
    inst = encode(perm, k=k, mode="full")

    cnf_path = PROOFS / f"{cid}.cnf"
    drat_path = PROOFS / f"{cid}.drat"
    inst.write_dimacs(cnf_path)

    entry = {
        "id": cid,
        "perm": to_string(perm),
        "n": len(perm),
        "k": k,
        "encoding": "full",
        "n_vars": inst.n_vars,
        "n_clauses": inst.n_clauses,
        "cnf": str(cnf_path.relative_to(ROOT)).replace("\\", "/"),
    }

    binary = find_solver(solver)
    if binary is None:
        raise SystemExit(
            "No cadical binary found.  Build one and put it in tools/, or set\n"
            "  THREE_STACKS_CADICAL=...\\cadical.exe\n"
            "  git clone --depth 1 https://github.com/arminbiere/cadical\n"
            "  cd cadical && ./configure && make cadical")

    sat, model, dt = run_solver(binary, cnf_path, drat_path, timeout)
    entry["sortable"] = sat
    entry["solver"] = f"{Path(binary).name} (external, file-backed proof)"
    entry["solve_seconds"] = round(dt, 3)

    if sat:
        drat_path.unlink(missing_ok=True)
        entry["ops"] = "".join(map(str, _model_to_ops(inst, model)))
        entry["evidence"] = "operation word (replay with verify.py)"
    else:
        entry["drat"] = str(drat_path.relative_to(ROOT)).replace("\\", "/")
        entry["drat_bytes"] = drat_path.stat().st_size
        entry["evidence"] = "DRAT certificate (check with proofcheck.py)"

    # independent second solver: a different implementation on the same CNF
    try:
        from pysat.formula import CNF
        from pysat.solvers import Solver
        with Solver(name="glucose4", bootstrap_with=CNF(from_clauses=inst.clauses)) as s2:
            sat2 = s2.solve()
        entry["second_solver"] = {"name": "glucose4 (pysat)", "sortable": bool(sat2),
                                  "agrees": bool(sat2) == bool(sat)}
    except Exception as e:  # pragma: no cover
        entry["second_solver"] = {"name": "glucose4 (pysat)", "error": str(e)}

    if brute_force:
        try:
            t1 = time.perf_counter()
            ops = sorting_sequence(perm, k=k, node_limit=BRUTE_FORCE_LIMIT_NODES)
            entry["brute_force"] = {
                "sortable": ops is not None,
                "agrees": (ops is not None) == sat,
                "seconds": round(time.perf_counter() - t1, 3),
            }
        except SearchLimitExceeded as e:
            entry["brute_force"] = {"sortable": None, "agrees": None,
                                    "note": f"gave up after {e.args[0]} nodes"}

    (PROOFS / f"{cid}.json").write_text(json.dumps(entry, indent=2) + "\n")
    claims = [c for c in load_claims() if c.get("id") != cid]
    claims.append(entry)
    claims.sort(key=lambda c: (c["k"], c["n"], c["perm"]))
    save_claims(claims)
    return entry


def load_claims() -> list[dict]:
    return json.loads(CLAIMS.read_text()) if CLAIMS.exists() else []


def save_claims(claims: list[dict]) -> None:
    CLAIMS.parent.mkdir(parents=True, exist_ok=True)
    CLAIMS.write_text(json.dumps(claims, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", action="append", default=[])
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--from-witnesses", action="store_true")
    ap.add_argument("--minimal-only", action="store_true")
    ap.add_argument("--no-brute-force", action="store_true")
    ap.add_argument("--solver", default=None)
    ap.add_argument("--timeout", type=int, default=None)
    a = ap.parse_args(argv)

    targets = [(from_string(p), a.k) for p in a.perm]
    if a.from_witnesses:
        wf = ROOT / "results" / "witnesses.jsonl"
        if wf.exists():
            seen = set()
            for line in wf.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if a.minimal_only and not row.get("minimal"):
                    continue
                key = (row["perm"], row["k"])
                if key not in seen:
                    seen.add(key)
                    targets.append((from_string(row["perm"]), row["k"]))
    if not targets:
        ap.error("nothing to certify: pass --perm or --from-witnesses")

    for perm, k in targets:
        e = certify(perm, k=k, brute_force=not a.no_brute_force,
                    solver=a.solver, timeout=a.timeout)
        bf = e.get("brute_force") or {}
        print(f"{e['id']}  n={e['n']} k={e['k']}  "
              f"{'SORTABLE' if e['sortable'] else 'UNSORTABLE'}  "
              f"{e['n_vars']} vars / {e['n_clauses']} clauses  {e['solve_seconds']}s  "
              f"2nd_solver={e.get('second_solver', {}).get('agrees')}  "
              f"brute_force={bf.get('agrees')}")
    print(f"\nwrote {CLAIMS.relative_to(ROOT)}")
    print("next: python proofcheck.py   and   python verify.py claims results/claims.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
