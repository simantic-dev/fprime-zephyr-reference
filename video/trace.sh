#!/bin/sh
# Records runs/trace.txt for the long video: 8 s of the nominal scenario with every write to the clock
# controller (RCC, 0x58024400) and every arrival at the boot functions and the four rate-group handlers,
# reduced to those lines (the raw log is about 70 MB). Batch run, no ground station. Then ./make.sh.
set -eu
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
LOG=$(mktemp)
( cd "$HERE/../sim" && sim run --scenario scenario.yaml --ascii --timeout 8 --trace-memory 0x58024400:256 \
    --trace-symbol sat:stm32_clock_control_init --trace-symbol sat:z_cstart --trace-symbol sat:main \
    --trace-symbol "sat:Components::EpsCan::run_handler" --trace-symbol "sat:Components::Detumble::run_handler" \
    --trace-symbol "sat:Components::Adcs::run_handler" --trace-symbol "sat:Components::FramParams::run_handler" ) > "$LOG" 2>&1
{ grep "(TRACE)" "$LOG" | sed -E 's/ r0=.*//'; grep "(MEM)" "$LOG" | grep " write " | sed -E 's/ 0x58024400:256//; s/ ctx=.*//'; } \
  | sort -t'[' -k2 -n > "$HERE/runs/trace.txt"
rm -f "$LOG"
wc -l "$HERE/runs/trace.txt"
