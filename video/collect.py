#!/usr/bin/env python3
"""Writes data.js for the F´ demo video from two recorded walkthroughs (Simantic video kit: every number
on screen comes from a run's output, never typed into a scene).

  collect.py <nominal walkthrough.txt> <faults walkthrough.txt> [data.js] [sim version]

The walkthroughs are ./demo's walkthrough output (runs/<mode>/walkthrough.txt, recorded by record.sh).
Asserts what the video claims; a failed assert means re-record or change the video, not this script.
"""
import json, pathlib, re, sys

nom_txt, flt_txt = (pathlib.Path(p).read_text() for p in sys.argv[1:3])
out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path(__file__).with_name("data.js")

ROW = re.compile(r"^\s+(\d+)\s+(\d+)\s+(-?\d+)\s+" + r"\s+".join([r"(\d+)"] * 6) + r"\s+(\d)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$")
EV = re.compile(r"^\s+t=\s*([\d.]+)s\s+(\w+)\s+(.*)$")

def orbit(txt):
    rows = []
    for ln in txt.split("== 2.")[0].splitlines():
        if m := ROW.match(ln):
            g = m.groups()
            rows.append({"t": int(g[0]), "vbat": int(g[1]), "ibat": int(g[2]), "sun": [int(x) for x in g[3:9]],
                         "bright": int(g[9]), "mag": [float(x) for x in g[10:13]]})
    return rows

def events(txt, section):
    part = txt.split(f"== {section}.")[1].split("\n== ")[0]
    cmds, cur = [], None
    for ln in part.splitlines():
        if ln.startswith("> "):
            cur = {"cmd": ln[2:].replace("ReferenceDeployment.", "").replace(" --arguments", ""), "events": []}
            cmds.append(cur)
        elif (m := EV.match(ln)):
            if cur is None:  # events listed without a command (the faults section)
                cur = {"cmd": None, "events": []}
                cmds.append(cur)
            cur["events"].append({"t": float(m[1]), "name": m[2], "text": m[3].strip()})
    return cmds

nom = orbit(nom_txt)
cmds = events(nom_txt, 3)
boot = int(re.search(r"boot_count = (\d+)", nom_txt)[1])
flt = [e for c in events(flt_txt, 5) for e in c["events"]]
retries = int(re.search(r"hk_retries = (\d+)", flt_txt)[1])

# What the video says, checked against the runs.
assert len(nom) >= 12, "orbit table incomplete"
lit = [r for r in nom if r["t"] <= 90]
dark = [r for r in nom if r["t"] >= 92]
assert all(max(r["sun"]) > 0 for r in lit), "some panel lit on every row up to the umbra"
assert all(r["ibat"] > 0 for r in lit[:-1]), "charging in sun (the last lit row may already carry the umbra HK reply)"
assert all(max(r["sun"]) == 0 and r["ibat"] < 0 for r in dark), "eclipse: all sun sensors 0 and battery discharging"
names = [e["name"] for c in cmds for e in c["events"]]
for n in ("PingReply", "DutySet", "FramWritten", "FramValue"):
    assert n in names, f"missing {n}"
assert "0xcafef00d" in next(e["text"] for c in cmds for e in c["events"] if e["name"] == "FramValue")
assert [e["name"] for e in flt] == ["HkRetry", "HkRecovered"] * 3, f"faults: {[e['name'] for e in flt]}"
assert retries == 3 and "HkFailed" not in flt_txt
for kind in ("FRAME_LOST", "CRC_ERROR", "TIMEOUT"):
    assert any(kind in e["text"] for e in flt), f"missing {kind}"

DATA = {
    "mcu": "STM32H723", "board": "NUCLEO-H723ZG", "sim": sys.argv[4] if len(sys.argv) > 4 else None,   # `sim --version` of the runs
    "orbit": nom, "boot_count": boot,
    "commands": [c for c in cmds if c["cmd"]],
    "faults": flt, "hk_retries": retries,
    "walk": [l.rstrip() for l in nom_txt.splitlines()[:19]],   # what ./demo prints first, for the "run it" scene
}
out.write_text("// Written by collect.py from runs/*/walkthrough.txt. Do not edit by hand.\nwindow.DATA = "
               + json.dumps(DATA, indent=1) + ";\n")
print(out, f"{len(nom)} orbit rows, {len(DATA['commands'])} commands, {len(flt)} fault events")
