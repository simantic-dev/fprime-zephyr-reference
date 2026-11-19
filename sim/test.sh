#!/bin/sh
# Runs the prebuilt F' deployment (sim/fprime-demo.elf) on a simulated NUCLEO-H723ZG
# with the EPS fault schedule (HK requests 30/40/50 lose a frame, arrive corrupt, arrive late),
# 55 s of virtual time, no GDS and no network. Pass = the firmware boots, stores its boot
# count in FRAM, and retries and recovers each of the three damaged EPS housekeeping requests.
cd "$(dirname "$0")" || exit 1
OUT=$(mktemp) || exit 1
trap 'rm -f "$OUT"' EXIT
${SIM:-sim} run --scenario scenario-test.yaml --ascii usart2,epsnode --timeout 55 > "$OUT" 2>&1
rc=$?
fail=0
check() { if grep -qF -- "$2" "$OUT"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
[ $rc -eq 0 ] || { echo "FAIL sim exit $rc"; fail=1; }
check "Zephyr boots" "Booting Zephyr OS"
check "boot count kept in FRAM" "boot count 1 (stored in FRAM)"
check "lost HK frame retried" "FRAME_LOST (2), retrying"
check "bad-CRC HK retried" "CRC_ERROR (1), retrying"
check "late HK retried" "TIMEOUT (0), retrying"
[ "$(grep -cF 'HkRecovered : EPS HK ok on attempt 2' "$OUT")" -eq 3 ] && echo "ok   3 retries recovered" || { echo "FAIL 3 retries recovered"; fail=1; }
if grep -qiE 'HardFault|panic|FATAL|assert' "$OUT"; then echo "FAIL fault/panic lines"; fail=1; else echo "ok   no fault/panic"; fi
exit $fail
