#!/usr/bin/env bash
# Sweep self-dual permutations at increasing lengths, one after another.
#
# The lengths must run in order.  Atkinson's theorem constrains the *shortest*
# unsortable permutation, so pinning the last entry to 1 is only legitimate at
# length L once every shorter length has come back empty.  Running them
# concurrently would also just split the cores.
#
#   bash scripts/dual_ladder.sh 18 19 20
set -u
cd "$(dirname "$0")/.."
WORKERS="${WORKERS:-12}"
PYTHON="${PYTHON:-.venv/bin/python}"
mkdir -p logs

if [[ ! -x "$PYTHON" ]]; then
  echo "Python not found at $PYTHON; create .venv or set PYTHON=/path/to/python" >&2
  exit 2
fi

for n in "$@"; do
  log="logs/dual${n}.log"
  echo "=== length $n -> $log ==="
  "$PYTHON" -u scripts/dual.py sweep --n "$n" --k 3 \
      --workers "$WORKERS" > "$log" 2> "logs/dual${n}.err"
  if grep -q "UNSORTABLE" "$log"; then
    echo "HIT at length $n -- stopping the ladder"
    grep "UNSORTABLE" "$log"
    exit 0
  fi
  echo "length $n: empty"
done
echo "ladder finished with no hit"
