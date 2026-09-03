# Building the external checkers

Nothing in `tools/` is committed. Both programs are third party, the binaries
are platform-specific, and prebuilt executables in a repository that asks to
be trusted are worth less than instructions. This file records what the build
actually takes, including the parts that cost hours the first time.

The Python test suite does not require them, so a clone is usable without
either binary. They are needed only to generate or independently check DRAT
certificates.

## What is needed, and why

| tool | used by | why not a library |
|---|---|---|
| [drat-trim](https://github.com/marijnheule/drat-trim) | `proofcheck.py` | third-party proof checking is the whole point; a checker sharing code with the solver cannot catch a shared bug |
| [CaDiCaL](https://github.com/arminbiere/cadical) | `scripts/certify.py` | writes the DRAT proof directly to disk; see below |

PySAT is used everywhere else. These binaries are only for producing and
checking certificates.

## Ubuntu/Debian build

First complete the Python setup in the [README](../README.md#verify-it-yourself).
Then, from the repository root:

```bash
sudo apt install build-essential git
mkdir -p tools
```

The virtual environment and everything under `tools/` are ignored. Recreate
them on each platform rather than copying them from another machine.

## What survives a fresh clone

The repository deliberately separates durable results from working state:

* `results/claims.json`, the plain `results/basis_k*_n*.json` reports,
  `results/basis_found.json`, and `proofs/*.json` are tracked result data.
* The hash-suffixed `results/basis_k*_n*_*.json` files are reports for
  arbitrary candidates. They are ignored because they can be reproduced by
  rerunning `scripts/verify_basis.py` with the candidate permutation.
* `results/witnesses.jsonl` is an append-only search log written automatically
  by the hunting, mining, harvesting, gradient, and construction scripts.
  `scripts/promote_witnesses.py` distilled its minimal discoveries into the
  tracked `results/basis_found.json`. The log is useful for resuming or
  re-analysing old searches, but is not needed to retain the published set.
* `logs/` is detached console output. Keep it only when investigating an old
  run. Python caches, `.venv/`, third-party source trees, and binaries are all
  disposable and platform-specific.
* Uncommitted `proofs/*.cnf` and `proofs/*.drat` are large generated evidence.
  For claims in `results/claims.json`, the permutations remain in tracked
  metadata and the artifacts can be regenerated.

## drat-trim

```bash
git clone https://github.com/marijnheule/drat-trim
gcc -O2 -o tools/drat-trim drat-trim/drat-trim.c
```

On Windows/MinGW, name the output `tools/drat-trim.exe` and add
`-Dgetc_unlocked=getc`: MinGW does not provide `getc_unlocked`. It is a
performance hint only, so replacing it with `getc` changes nothing about what
gets checked.

## CaDiCaL

```bash
git clone https://github.com/arminbiere/cadical
cd cadical
./configure
make -j
cp build/cadical ../tools/cadical
```

The commands above produce the normal Linux binary. On Windows, **link it
statically**. A default MinGW build produces an executable that
fails at startup with a missing-DLL error as soon as it is run from anywhere
other than the build shell:

```bash
g++ -O2 -static -static-libgcc -static-libstdc++ -o tools/cadical.exe <objects>
```

On Windows, **do not build under a path containing a space.** If the
toolchain lives somewhere like `C:\Users\Nehal Ahmed\...`, the link step
fails. Short (8.3) paths, a directory junction, and `subst` all fail too,
because `gcc` resolves its own real path and rediscovers the space. The fix
that works is copying the toolchain somewhere clean:

```powershell
robocopy "C:\path with spaces\mingw64" C:\mingw64 /E
```

Then build with `C:\mingw64\bin` on `PATH`. The project directory may contain
spaces; it is the *compiler's* location that matters.

## Why not capture the proof in memory

`scripts/certify.py` shells out to a solver binary that writes DRAT straight
to a file, rather than using PySAT's proof capture. On the length-33 witness,
capture returned 15 MB of a proof the solver reported writing as 6.1 MB, and
drat-trim rejected it — "conflict claimed, but not detected" — on an instance
that is genuinely unsatisfiable. Different solvers failed on different
instances, which is the signature of lossy capture rather than of a wrong
answer.

A truncated proof that still verifies would be sound, since drat-trim checks
every step. One that fails is indistinguishable from a real refutation
failure, which is worse than useless.

## Regenerating certificates

The four shortest pairs (lengths 21–24) are committed, so the headline claims
check without a solver. Everything else regenerates from the permutation
recorded in `results/claims.json` or the corresponding `proofs/*.json` file:

```bash
python scripts/certify.py --claim-id k3_n25_b6356c09 --no-brute-force
python proofcheck.py
```

The JSON is metadata, not an input snapshot: `certify.py` deterministically
rebuilds the CNF from the permutation and asks CaDiCaL to emit a fresh DRAT
proof. Solver timings and the exact proof byte stream may differ.
