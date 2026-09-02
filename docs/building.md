# Building the external checkers

Nothing in `tools/` is committed. Both programs are third party, the binaries
are platform-specific, and prebuilt executables in a repository that asks to
be trusted are worth less than instructions. This file records what the build
actually takes, including the parts that cost hours the first time.

The tests skip rather than fail when these are absent, so a clone is usable
without them — you just cannot re-verify the DRAT certificates.

## What is needed, and why

| tool | used by | why not a library |
|---|---|---|
| [drat-trim](https://github.com/marijnheule/drat-trim) | `proofcheck.py` | third-party proof checking is the whole point; a checker sharing code with the solver cannot catch a shared bug |
| [CaDiCaL](https://github.com/arminbiere/cadical) | `scripts/certify.py` | PySAT's in-memory DRAT capture **truncates** — see below |

PySAT is still used everywhere else, and `pip install python-sat` covers the
search and the tests. The binaries are only for producing and checking
certificates.

## drat-trim

```bash
git clone https://github.com/marijnheule/drat-trim
gcc -O2 -Dgetc_unlocked=getc -o tools/drat-trim.exe drat-trim/drat-trim.c
```

The `-Dgetc_unlocked=getc` shim is required on Windows/MinGW, where
`getc_unlocked` does not exist. It is a performance hint only, so replacing it
with `getc` changes nothing about what gets checked.

## CaDiCaL

```bash
git clone https://github.com/arminbiere/cadical
cd cadical && ./configure && make
# then link statically, see below
```

**Link it statically.** A default MinGW build produces an executable that
fails at startup with a missing-DLL error as soon as it is run from anywhere
other than the build shell:

```bash
g++ -O2 -static -static-libgcc -static-libstdc++ -o tools/cadical.exe <objects>
```

**Do not build under a path containing a space.** If the toolchain lives
somewhere like `C:\Users\Nehal Ahmed\...`, the link step fails. Short (8.3)
paths, a directory junction, and `subst` all fail too, because `gcc` resolves
its own real path and rediscovers the space. The fix that works is copying the
toolchain somewhere clean:

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
check without a solver. Everything else regenerates:

```bash
python scripts/certify.py --perm <permutation> --k 3
python proofcheck.py
```
