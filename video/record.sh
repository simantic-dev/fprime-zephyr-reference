#!/bin/sh
# Records the two runs the video is built from (./demo nominal, then ./demo faults; about 10 min each at
# 1x wall clock) and keeps what collect.py reads: the walkthrough output and the GDS event log. Then ./make.sh.
set -eu
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$HERE/..
mkdir -p "$HERE/runs" && sim --version > "$HERE/runs/sim-version.txt"
for MODE in nominal faults; do
  "$ROOT/demo" "$MODE"
  mkdir -p "$HERE/runs/$MODE"
  cp "$ROOT/.demo/walkthrough.txt" "$ROOT/.demo/gds-logs/event.log" "$HERE/runs/$MODE/"
done
