# iSentek IST8310 3-axis magnetometer (7-bit 0x0C or 0x0E) as a scripted I2C peer.
#
# SOURCE CAVEAT: no IST8310 datasheet was retrievable, so the register behaviour is taken from what PX4
# (src/drivers/magnetometer/isentek/ist8310) and ArduPilot (AP_Compass_IST8310) read: WAI 0x00 = 0x10,
# STAT1 0x02 (DRDY bit 0), data 0x03..0x08 little-endian X/Y/Z, CNTL1 0x0A single-measurement (bit 0),
# CNTL2 0x0B soft reset (bit 0, self-clearing), CNTL3 0x0D resolution bits 4/5/6, plus 0x41/0x42 stored as
# written. The output scale follows CNTL3: with the three resolution bits set, 1320 LSB/gauss (PX4); clear,
# 100/0.3 LSB/gauss (ArduPilot). Axes are the chip's own (+z up); both drivers negate Z themselves.
# Not modelled: temperature (0x1C/0x1D), the cross-axis matrix at 0x9C..0xAD, self-test, data overrun.
#
# Stimulus. The field along the chip's axes, in nT. Defaults are the pyrite model's mid-latitude field.
# Set it at run time through the named property hook: `ctx.set_property(<board name>,
# "MagneticFluxDensityX" | "...Y" | "...Z", nT)`, applied at the next slice boundary. The initial field is
# set by an overlay before this file runs, e.g. `script: "FIELD_NT = [20000, 0, -45000]; exec(...)"`.
# Config (`config:` JSON in the overlay, ctx.config), ns of virtual time; it wins over a script-line value:
#   MEASUREMENT_NS   the single-measurement time. Default 6 ms.
#
# MODELED SIMPLIFICATION: no IST8310 datasheet value for the single-measurement conversion time was
# retrievable, so it is 6 ms, the figure the drivers poll for. STAT1 DRDY sets once that time has passed
# after CNTL1 is written.
# MODELED SIMPLIFICATION: a one-count alternating dither stands in for sensor noise, so a perfectly static
# field does not look like a stuck sensor to PX4's DataValidator (stale-data confidence drop).
import math

FIELD_NT = globals().get("FIELD_NT", [20000.0, 0.0, -45000.0])
MEASUREMENT_NS = globals().get("MEASUREMENT_NS", None)
DEFAULT_MEASUREMENT_NS = 6_000_000
FIELD_PROPS = ("MagneticFluxDensityX", "MagneticFluxDensityY", "MagneticFluxDensityZ")

WHO_AM_I, STAT1, DATA_XL, DATA_ZH, STAT2, CNTL1, CNTL2, CNTL3 = 0x00, 0x02, 0x03, 0x08, 0x09, 0x0A, 0x0B, 0x0D
WAI_VALUE = 0x10
RES_BITS = [1 << 4, 1 << 5, 1 << 6]
COUNTS_PER_GAUSS_HIGH = 1320.0
COUNTS_PER_GAUSS_DEFAULT = 100.0 / 0.3
NT_PER_GAUSS = 100_000.0


def _round(x):
    """Rust f64::round: half away from zero."""
    return math.floor(abs(x) + 0.5) * (1 if x >= 0 else -1)


class Slave:
    def __init__(self, ctx):
        self.ctx = ctx
        self.field_nt = list(FIELD_NT)
        self.measurement_ns = getattr(ctx, "config", {}).get("MEASUREMENT_NS", MEASUREMENT_NS)
        self.regs = bytearray(256)
        self.pointer = None
        self.data_ready = False
        self.raw = [0, 0, 0]
        self.dither = 0
        self.ready_at_ns = 0

    def _now_ns(self):
        return self.ctx.now_us * 1000

    def _convert(self):
        self.dither ^= 1
        for i in range(3):
            cpg = COUNTS_PER_GAUSS_HIGH if self.regs[CNTL3] & RES_BITS[i] else COUNTS_PER_GAUSS_DEFAULT
            q = max(-0x8000, min(0x7FFF, _round(self.field_nt[i] * cpg / NT_PER_GAUSS)))
            self.raw[i] = q - self.dither if q == 0x7FFF else q + self.dither
        self.data_ready = True
        t = self.measurement_ns if self.measurement_ns is not None else DEFAULT_MEASUREMENT_NS
        self.ready_at_ns = self._now_ns() + t
        self.regs[CNTL1] &= 0xF0   # a single measurement returns to standby

    def _read_register(self, r):
        if r == WHO_AM_I:
            return WAI_VALUE
        if r == STAT1:
            return 1 if self.data_ready and self._now_ns() >= self.ready_at_ns else 0
        if r == STAT2:
            return 0
        if DATA_XL <= r <= DATA_ZH:
            self.data_ready = False
            i = r - DATA_XL
            return (self.raw[i // 2] & 0xFFFF).to_bytes(2, "little")[i % 2]
        return self.regs[r]

    def _write_register(self, r, v):
        if r == CNTL1:
            self.regs[r] = v
            if v & 1:
                self._convert()
        elif r == CNTL2 and v & 1:
            # SRST self-clears: both drivers poll until it reads 0.
            self.regs = bytearray(256)
            self.data_ready = False
            self.raw = [0, 0, 0]
            self.dither = 0
        elif r in (WHO_AM_I, STAT1, STAT2) or DATA_XL <= r <= DATA_ZH:
            pass   # read-only
        else:
            self.regs[r] = v

    def set_property(self, name, value):
        if name not in FIELD_PROPS:
            raise ValueError("no scriptable property '%s' (%s: nT)" % (name, "/".join(FIELD_PROPS)))
        self.field_nt[FIELD_PROPS.index(name)] = float(value)

    def get_property(self, name):
        if name not in FIELD_PROPS:
            raise ValueError("no scriptable property '%s' (%s: nT)" % (name, "/".join(FIELD_PROPS)))
        return self.field_nt[FIELD_PROPS.index(name)]

    def on_write(self, data):
        if not data:
            return
        p = data[0]
        for b in data[1:]:
            self._write_register(p, b)
            p = (p + 1) & 0xFF
        self.pointer = p

    def on_read(self, count):
        if self.pointer is None:
            return bytes(count)
        p = self.pointer
        out = bytearray()
        for _ in range(count):
            out.append(self._read_register(p))
            p = (p + 1) & 0xFF
        self.pointer = p
        return bytes(out)
