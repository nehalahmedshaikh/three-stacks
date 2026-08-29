#!/usr/bin/env python3
"""Run drat-trim over every UNSAT claim in results/claims.json.

Like verify.py this is deliberately standalone: it imports nothing from the
``unsortable`` package.  All it does is hand the DIMACS file and the DRAT
certificate to drat-trim -- a checker written by someone else -- and report
the verdict.

drat-trim is not bundled.  Point this script at a binary with either

    set THREE_STACKS_DRAT_TRIM=C:\\path\\to\\drat-trim.exe
    python proofcheck.py --drat-trim C:\\path\\to\\drat-trim.exe

or put ``drat-trim`` on PATH.  To build it::

    git clone https://github.com/marijnheule/drat-trim
    cd drat-trim && gcc -O2 -o drat-trim drat-trim.c

Exit status is 0 only if every UNSAT claim verified.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CLAIMS = ROOT / "results" / "claims.json"


def find_drat_trim(explicit: str | None) -> str | None:
    for cand in (explicit, os.environ.get("THREE_STACKS_DRAT_TRIM")):
        if cand and Path(cand).exists():
            return cand
    for name in ("drat-trim", "drat-trim.exe", "drattrim"):
        found = shutil.which(name)
        if found:
            return found
    for name in ("drat-trim.exe", "drat-trim"):
        local = ROOT / "tools" / name
        if local.exists():
            return str(local)
    return None


def check_one(binary: str, cnf: Path, drat: Path, timeout: int) -> tuple[str, str]:
    """Return (verdict, detail).  verdict in {VERIFIED, FAILED, ERROR}."""
    try:
        r = subprocess.run([binary, str(cnf), str(drat)], capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "ERROR", f"drat-trim timed out after {timeout}s"
    except OSError as e:
        return "ERROR", str(e)
    out = (r.stdout or "") + (r.stderr or "")
    if "s VERIFIED" in out:
        return "VERIFIED", f"exit {r.returncode}"
    if "s NOT VERIFIED" in out or "NOT VERIFIED" in out:
        return "FAILED", out.strip().splitlines()[-1] if out.strip() else "no output"
    if "TRIVIAL UNSAT" in out:
        return "VERIFIED", "trivially unsat (falsified original clause)"
    tail = out.strip().splitlines()[-3:] if out.strip() else ["no output"]
    return "ERROR", " | ".join(tail)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    ap.add_argument("--drat-trim", default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args(argv)

    if not a.claims.exists():
        print(f"no claims file at {a.claims}; run scripts/certify.py first")
        return 1
    claims = json.loads(a.claims.read_text())
    unsat = [c for c in claims if not c.get("sortable")]
    if not unsat:
        print("no UNSAT claims to check")
        return 0

    binary = find_drat_trim(a.drat_trim)
    if binary is None:
        print("drat-trim not found.\n")
        print("The following claims have certificates ready but UNCHECKED:")
        for c in unsat:
            print(f"  {c['id']}  n={c['n']} k={c['k']}  {c['perm']}")
            print(f"      cnf  {c.get('cnf')}")
            print(f"      drat {c.get('drat')}")
        print("\nBuild drat-trim and re-run:")
        print("  git clone https://github.com/marijnheule/drat-trim")
        print("  cd drat-trim && gcc -O2 -o drat-trim drat-trim.c")
        print("  set THREE_STACKS_DRAT_TRIM=...\\drat-trim.exe")
        return 2

    print(f"drat-trim: {binary}\n")
    bad = skipped = checked = 0
    for c in unsat:
        cnf, drat = ROOT / c["cnf"], ROOT / c["drat"]
        if not cnf.exists() or not drat.exists():
            # Only the shortest witnesses ship their (large) certificate pair;
            # the rest regenerate deterministically.  Absent is not wrong.
            print(f"{c['id']:>24}  SKIPPED   n={c['n']} k={c['k']}  "
                  f"artifact not in repo")
            skipped += 1
            continue
        verdict, detail = check_one(binary, cnf, drat, a.timeout)
        print(f"{c['id']:>24}  {verdict:<9} n={c['n']} k={c['k']}  {c['perm']}")
        checked += 1
        if verdict != "VERIFIED":
            print(f"{'':>24}  {detail}")
            bad += 1
    print(f"\n{checked - bad}/{checked} certificates verified"
          + (f", {skipped} skipped (regenerate with scripts/certify.py "
             f"--perm <perm>)" if skipped else ""))
    if skipped and checked == 0:
        print("nothing to check -- regenerate the certificates first")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
