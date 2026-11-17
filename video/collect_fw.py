#!/usr/bin/env python3
"""Writes fw.js for the long video: what is inside the ELF, how it loads, how it boots and how its loops run.
Sources: sim/fprime-demo.elf (through binutils), the build's devicetree, and runs/trace.txt, which is
`sim run --trace-memory <RCC> --trace-symbol ...` output reduced to register writes and function arrivals
(trace.sh). Every number in the firmware scenes comes from here.

  collect_fw.py <binutils prefix, e.g. .../arm-zephyr-eabi-> <zephyr.dts> [fw.js]
"""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
tool, dts = sys.argv[1], pathlib.Path(sys.argv[2]).read_text()
out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "fw.js"
ELF = HERE.parent / "sim/fprime-demo.elf"
run = lambda *a: subprocess.run([tool + a[0], *a[1:]], capture_output=True, text=True, check=True).stdout

# --- sections
sizes = run("size", "-A", str(ELF))
sec = {m[1]: int(m[2]) for m in re.finditer(r"^(\S+)\s+(\d+)\s+\d+$", sizes, re.M)}
text0 = int(re.search(r"^text\s+\d+\s+(\d+)$", sizes, re.M)[1])
flash_used = sum(sec[k] for k in ("rom_start", "text", "device_area", "sw_isr_table", "rodata", "datas"))
ram_used = sec["datas"] + sec["bss"] + sec["noinit"]
flash_size = int(re.search(r"flash0: flash@8000000 \{.*?reg = < 0x8000000 (0x[0-9a-f]+) >", dts, re.S)[1], 16)
ram_base, ram_size = (int(x, 16) for x in re.search(r"sram0: memory@24000000 \{\s*reg = < (0x[0-9a-f]+) (0x[0-9a-f]+) >", dts).groups())
hse = int(re.search(r"clk_hse: clk-hse \{.*?clock-frequency = < (0x[0-9a-f]+|\d+) >", dts, re.S)[1], 0)

# --- code by origin, from the symbol table (functions only)
code, end = {"satellite": 0, "fprime": 0, "zephyr": 0}, text0
for ln in sorted(run("nm", "-S", "-C", str(ELF)).splitlines()):   # by address; skip aliases and symbols nested in the last one
    f = ln.split(None, 3)
    if len(f) == 4 and f[2] in "TtWw" and end <= int(f[0], 16) < text0 + sec["text"]:
        end = int(f[0], 16) + int(f[1], 16)
        n = f[3]
        k = "satellite" if n.startswith("Components::") else "fprime" if re.match(
            r"(Svc|Fw|Os|Drv|Zephyr|ComCcsds|CdhCore|Utils|Types|ReferenceDeployment|Baremetal)::|vtable|typeinfo|non-virtual", n) else "zephyr"
        code[k] += int(f[1], 16)
assert all(v > 4000 for v in code.values()) and sum(code.values()) <= sec["text"], (code, sec["text"])

# --- vector table: first two words of flash
w = bytes.fromhex("".join(run("objdump", "-s", "-j", "rom_start", str(ELF)).splitlines()[4].split()[1:3]))
sp, reset = int.from_bytes(w[:4], "little"), int.from_bytes(w[4:], "little")
assert ram_base < sp <= ram_base + ram_size and reset & 1 and 0x08000000 < reset < 0x08000000 + flash_size

# --- trace: clock registers and function arrivals
writes, arrivals = [], {}
for ln in open(HERE / "runs/trace.txt"):
    if m := re.match(r"\[([\d.]+)s\] \(MEM\) write addr=(0x[0-9a-f]+) width=4 value=(0x[0-9a-f]+)", ln):
        writes.append((float(m[1]), int(m[2], 16) & 0xFFF, int(m[3], 16)))
    elif m := re.match(r"\[([\d.]+)s\] \(TRACE\) (\S+?)(\(.*\))? pc=", ln):
        arrivals.setdefault(m[2].split("::")[-2] if "::" in m[2] else m[2], []).append(float(m[1]))
final = {}
for t, a, v in writes:
    final[a] = (t, v)
OFF = {"RCC_CR": 0x400, "RCC_CFGR": 0x410, "RCC_D1CFGR": 0x418, "RCC_PLLCKSELR": 0x428, "RCC_PLL1DIVR": 0x430}
r = {k: final[a][1] for k, a in OFF.items()}
divm, n, p = r["RCC_PLLCKSELR"] >> 4 & 0x3F, (r["RCC_PLL1DIVR"] & 0x1FF) + 1, (r["RCC_PLL1DIVR"] >> 9 & 0x7F) + 1
assert r["RCC_PLLCKSELR"] & 3 == 2, "PLL source is HSE"
assert r["RCC_CFGR"] & 7 == 3, "system clock switched to PLL1"
sysclk = hse // divm * n // p
assert sysclk == 550_000_000, sysclk   # what the board's devicetree asks for; change the video if this changes
REGS = [["RCC_CR", "HSEON | HSEBYP", f"use the board's {hse // 10**6} MHz clock"],
        ["RCC_PLLCKSELR", f"source HSE, M = {divm}", f"{hse // 10**6} MHz ÷ {divm}"],
        ["RCC_PLL1DIVR", f"N = {n}, P = {p}", f"× {n} ÷ {p}"],
        ["RCC_CR", "PLL1ON", "start the PLL, wait for lock"],
        ["RCC_CFGR", "SW = PLL1", "switch the core over"]]
assert r["RCC_CR"] & (1 << 16 | 1 << 18 | 1 << 24) == (1 << 16 | 1 << 18 | 1 << 24), "HSEON, HSEBYP and PLL1ON set"

per = lambda k: [round((b - a) * 1000) for a, b in zip(arrivals[k][1:], arrivals[k][2:])]   # the first cycle after start-up is short (91 ms)
for k, want in (("EpsCan", 100), ("Detumble", 100), ("Adcs", 1000), ("FramParams", 1000)):
    assert len(per(k)) >= 3 and all(abs(x - want) <= 3 for x in per(k)), (k, per(k))

# --- the B-dot filter loop of Detumble::run_handler, as built
dis = run("objdump", "-d", "-C", "--no-show-raw-insn", "--disassemble=Components::Detumble::run_handler(short, unsigned int)", str(ELF))
ins = [(m[1], m[2].split("\t@")[0].replace("\t", " ").strip()) for m in re.finditer(r"^\s+([0-9a-f]+):\t(.+)$", dis, re.M)]
tgt = lambda t: int(t.split()[1], 16)
back = next(i for i, (a, t) in enumerate(ins) if t.startswith("bne") and tgt(t) < int(a, 16)
            and any("fdiv" in s for _, s in ins[i - 45:i]))
start = next(i for i, (a, _) in enumerate(ins) if int(a, 16) == tgt(ins[back][1]))
loop = [{"addr": a, "text": re.sub(r" <.*>$", lambda m: " " + re.sub(r"__aeabi_|__", "", m[0].strip(" <>")) if "Detumble" not in m[0] else "", t)}
        for a, t in ins[start:back + 1]]
calls = [l for l in loop if l["text"].startswith("bl ")]
assert sum("fsub" in l["text"] for l in calls) == 2 and sum("fdiv" in l["text"] for l in calls) == 2, [l["text"] for l in calls]

DATA = {
    "sections": {k: sec[k] for k in ("text", "rodata", "datas", "bss", "noinit")}, "code": code,
    "flash": {"base": 0x08000000, "size": flash_size, "used": flash_used}, "ram": {"base": ram_base, "size": ram_size, "used": ram_used},
    "vectors": {"sp": sp, "reset": reset},
    "boot": {"z_cstart": arrivals["z_cstart"][0], "clock_init": arrivals["stm32_clock_control_init"][0], "pll_on": final[0x430][0],
             "main": arrivals["main"][0], "first_cycle": arrivals["EpsCan"][0], "rcc_writes": len(writes)},
    "clock": {"hse": hse, "divm": divm, "n": n, "p": p, "sysclk": sysclk, "regs": REGS},
    "loops": {k: [round(t, 4) for t in arrivals[k]] for k in ("EpsCan", "Detumble", "Adcs", "FramParams")},
    "loop_asm": [l for l in loop if l["text"].startswith(("bl ", "bne", "cmp"))],
}
out.write_text("// Written by collect_fw.py from sim/fprime-demo.elf and runs/trace.txt. Do not edit by hand.\nwindow.FW = " + json.dumps(DATA) + ";\n")
print(out, f"flash {flash_used}/{flash_size}, ram {ram_used}/{ram_size}, sysclk {sysclk // 10**6} MHz, code {code}")
for l in DATA["loop_asm"]: print("  ", l["addr"], l["text"])
