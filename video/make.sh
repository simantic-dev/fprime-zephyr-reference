#!/usr/bin/env bash
# Builds the F´ demo video: fetches the Simantic video kit into .kit/ (needs access to the simulator's
# repository), writes data.js from the recorded runs, renders video.mp4 (or stills). Runs: ./record.sh.
#
# Usage: make.sh [--stills 3 10 ...]     env: PYRITE (pyrite checkout, default ~/dev/simantic/pyrite),
#                                              PY (python with playwright + imageio-ffmpeg, default python3)
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
PYRITE=${PYRITE:-$HOME/dev/simantic/pyrite} PY=${PY:-python3}
rm -rf "$HERE/.kit" && mkdir -p "$HERE/.kit"
git -C "$PYRITE" archive origin/main docs/video/assets docs/video/render.py | tar -x -C "$HERE/.kit" --strip-components=2
"$PY" "$HERE/collect.py" "$HERE/runs/nominal/walkthrough.txt" "$HERE/runs/faults/walkthrough.txt" "$HERE/data.js" \
  "$(head -1 "$HERE/runs/sim-version.txt")"
"$PY" "$HERE/.kit/render.py" "$HERE/video.html" "$@"
