#!/bin/sh
# Scripted walkthrough against a running demo (../demo starts it). Telemetry comes
# from the GDS's own recording ($LOGS), so the eclipse at t=90 s shows however late
# this starts; commands go up the ground link through fprime-cli and the events they
# produce are printed as they land. Times are the firmware's own (virtual) clock.
#
# Usage: walkthrough.sh [nominal|faults]
# env:   LOGS (GDS log dir), VENV (venv with fprime-gds), DETUMBLE_S (default 90, virtual s of B-dot)
set -eu

MODE=${1:-nominal}
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
DICT=$HERE/dictionary.json
LOGS=${LOGS:-$HERE/../.demo/gds-logs}
VENV=${VENV:-$HERE/../.demo/venv}
D=ReferenceDeployment
[ -f "$LOGS/channel.log" ] || { echo "no GDS recording at $LOGS; start ../demo $MODE first" >&2; exit 1; }

gds() {  # queries over the GDS recording: wait-t S | table S... | latest CH | nlines | wait-event RE FROM | events RE
         #   | now | detumble S... | mean CH T0 T1
  python3 - "$LOGS" "$@" <<'PY'
import re, sys, time
logs, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]

def rows(name):  # "TB_NONE: 26.059600s, context, raw time, name, id, [severity,] value"
    out = []
    for ln in open(f"{logs}/{name}.log"):
        f = [x.strip() for x in ln.split(",", 6 if name == "event" else 5)]
        if len(f) >= 6:
            out.append((float(f[0].split()[1].rstrip("s")), f[3].split(".")[-1], f[-1]))
    return out

def at(sec):  # first telemetry packet stamped in virtual second `sec` (a packet's stamp is its
    c = {}   # newest channel write, so one delayed by an EPS retry can share a second with the next)
    for t, n, v in rows("channel"):
        if int(t) == sec:
            c.setdefault(n, v)
    return c

def nums(v):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", v)]

def poll(cond, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if r := cond():
            return r
        time.sleep(0.5)
    sys.exit(f"timed out after {timeout} s ({cmd} {' '.join(args)})")

def show(ev):
    t, n, v = ev
    print(f"  t={t:9.3f}s  {n:18} {v}")

if cmd == "wait-t":
    poll(lambda: any(t >= float(args[0]) for t, _, _ in rows("channel")), 600)
elif cmd == "table":
    print("   t_s  vbat_mV ibat_mA  sun_mV PAN1..PAN6                    bright  magn0_uT x/y/z")
    for s in map(int, args):
        c = at(s)
        if "vbat_mV" not in c:
            print(f"  {s:4d}  (no telemetry recorded: GDS not connected yet)")
            continue
        sun = " ".join(f"{int(x):5d}" for x in nums(c["sun_mV"]))
        mag = " ".join(f"{x * 100:6.1f}" for x in nums(c["magn0"]))  # channel is gauss
        print(f"  {s:4d}  {c['vbat_mV']:>7} {c['ibat_mA']:>7}  {sun}    {c['brightest_panel']:>4}   {mag}")
elif cmd == "latest":
    print(f"  {args[0]} = {[v for _, n, v in rows('channel') if n == args[0]][-1]}")
elif cmd == "nlines":
    print(len(rows("event")))
elif cmd == "wait-event":
    new = poll(lambda: (r := rows("event")[int(args[1]):]) and any(re.search(args[0], n) for _, n, _ in r) and r, 60)
    for ev in new:
        show(ev)
elif cmd == "now":
    print(int(rows("channel")[-1][0]))
elif cmd == "detumble":
    print("   t_s  mode  rate_est_deg_s  |dB/dt|_uT_s  magn0_uT x/y/z          duty_cmd % x/y/z  bridges")
    for s in map(int, args):
        c = at(s)
        if "rate_est_deg_s" not in c:
            print(f"  {s:4d}  (no detumble telemetry recorded)")
            continue
        mag = " ".join(f"{x * 100:6.1f}" for x in nums(c["magn0"]))
        duty = " ".join(f"{int(x):4d}" for x in nums(c["duty_cmd"]))
        print(f"  {s:4d}  {c['mode']:>4}  {float(c['rate_est_deg_s']):14.3f}  {float(c['bdot_norm_uT_s']):12.3f}"
              f"  {mag}   {duty}      {c.get('enabled', '?')}")
elif cmd == "mean":
    v = [float(x) for t, n, x in rows("channel") if n == args[0] and float(args[1]) <= t < float(args[2])]
    print(f"{sum(v) / len(v):.4f}" if v else "nan")
elif cmd == "events":
    for ev in rows("event"):
        if re.search(args[0], ev[1]):
            show(ev)
PY
}

cli() {
  "$VENV/bin/fprime-cli" command-send "$@" --dictionary "$DICT" --no-zmq \
    --tts-addr 127.0.0.1 --tts-port 50050 -l "$LOGS/../cli-logs" --log-directly >/dev/null
}

send() {  # send <event regex that ends the wait> <command> [--arguments ...]
  pat=$1; shift
  from=$(gds nlines)
  echo "> $*"
  cli "$@"
  gds wait-event "$pat" "$from"
}

echo "== 1. Orbit: EPS housekeeping, sun sensors and magnetometer through the eclipse (umbra from t=90 s)"
gds wait-t 121
gds table 10 20 30 40 50 60 70 80 88 89 90 91 92 100 110 120

echo; echo "== 2. Boot count kept in FRAM"
gds latest boot_count

echo; echo "== 3. Commands up the ground link, and their events"
send 'PingReply|PingTimeout' $D.eps.EPS_PING
send 'DutySet|PwmError' $D.mtq.MTQ_SET --arguments Y 40
send 'FramWritten|FramError' $D.fram.FRAM_WRITE --arguments 0x100 0xCAFEF00D
send 'FramValue|FramError' $D.fram.FRAM_READ --arguments 0x100

echo; echo "== 4. Detumble: ground enables the onboard B-dot loop (magnetometer -> dB/dt -> bridge enable + DIR + TIM1 PWM)"
DETUMBLE_S=${DETUMBLE_S:-90}
t0=$(( $(gds now) + 20 ))
gds wait-t $t0
echo "   tumbling, controller OFF:"
gds detumble $((t0 - 20)) $((t0 - 10)) $((t0 - 1))
before=$(gds mean rate_est_deg_s $((t0 - 20)) $t0)
send 'ModeChanged' $D.detumble.DETUMBLE_ENABLE
t1=$(gds now)
gds wait-t $((t1 + DETUMBLE_S))
echo "   controller ON:"
gds detumble $(seq $((t1 + 2)) 10 $((t1 + DETUMBLE_S)))
after=$(gds mean rate_est_deg_s $((t1 + DETUMBLE_S - 20)) $((t1 + DETUMBLE_S)))
send 'ModeChanged' $D.detumble.DETUMBLE_DISABLE
python3 - "$before" "$after" "$DETUMBLE_S" <<'PY'
import sys
b, a, n = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
print(f"   rate estimate (20 s mean): {b:.3f} deg/s before, {a:.3f} deg/s after {n} s of B-dot")
if b > 0 and a < 0.5 * b:
    print(f"   DETUMBLED: rate estimate down {b / a if a else float('inf'):.1f}x")
else:
    print("   open-loop physics: the coils were driven but the rate did not drop; this sky spins the")
    print("   satellite kinematically and ignores magnetorquer torque (closed loop needs an attitude dynamics plant).")
PY

if [ "$MODE" = faults ]; then
  echo; echo "== 5. EPS faults injected on the CAN bus (HK requests 30/40/50) and the firmware's retries"
  gds events 'HkRetry|HkRecovered|HkFailed'
  gds latest hk_retries
fi
