# What the demo satellite's sensors see, as a function of virtual time: a 1U
# CubeSat in a circular polar orbit, spinning slowly with no attitude control.
# Pure Python and deterministic; sky.py pushes these values into the board's
# models every tick and eps_node.py reads the battery state for EPS HK.
#
# Frames. Inertial: Z = Earth's spin axis, the orbit lies in the X-Z plane
# (inclination 90 deg), position r(u) = r (cos u, 0, sin u), orbit normal -Y.
# Body: the satellite spins about body +Z at SPIN; at t=0 the body frame is the
# inertial frame turned by TILT about Y, so the spin axis is not the sun line
# and every panel's illumination changes over a revolution.
import math
import random

# --- Physical constants
MU_EARTH = 398600.4418      # km^3/s^2, WGS-84 gravitational parameter
R_EARTH = 6371.0            # km, IUGG mean Earth radius
SOLAR_CONSTANT = 1361.0     # W/m^2, total solar irradiance at 1 AU (Kopp & Lean 2011)
B0_NT = 29404.8             # nT, |g10| of IGRF-13 (epoch 2020): axial dipole equatorial surface field

# --- Scenario parameters (declared, not fitted; override via sky config)
PARAMS = {
    "altitude_km": 500.0,       # typical CubeSat LEO
    "beta_deg": 0.0,            # sun angle to the orbit plane; 0 = longest eclipse
    "eclipse_entry_s": 15.0,    # orbit phase chosen so the umbra starts this long after t=0
    "spin_deg_s": 0.5,          # tumble rate about body +Z
    "tilt_deg": 30.0,           # spin axis tilt (initial attitude)
    # Sun-sensor photodiode amplifier output at normal incidence.
    # MODELED SIMPLIFICATION: a demo parameter, not derived from a photodiode and
    # gain resistor. Stays below VDDA 3.3 V.
    "sun_full_v": 3.0,
    # Solar panel per face: 2 x Azur Space 3G30C-Advanced (30.18 cm^2 each,
    # 29.5 % BOL AM0 efficiency, datasheet), a common 1U CubeSat panel cell.
    "cells_per_face": 2,
    "cell_area_m2": 30.18e-4,
    "cell_efficiency": 0.295,
    "load_w": 1.5,              # platform load, declared by the scenario
    # Battery: 2S1P of Panasonic NCR18650B (datasheet: 3.35 Ah typ., 4.2 V
    # charge, 2.5 V discharge cut-off).
    "cells_series": 2,
    "cells_parallel": 1,
    "cell_capacity_ah": 3.35,
    "cell_v_full": 4.2,
    "cell_v_empty": 2.5,
    # MODELED SIMPLIFICATION: DC resistance is not on the NCR18650B datasheet;
    # this stands in for it until a measured value replaces it.
    "cell_r_ohm": 0.05,
    "soc0": 0.8,
    # LIS2DW12 high-performance noise density 90 ug/sqrt(Hz) (datasheet),
    # over an ODR/2 bandwidth at the declared ODR.
    "acc_noise_ug_rthz": 90.0,
    "acc_odr_hz": 100.0,
    "seed": 1,
}

# Panel normals in the body frame, PAN1..PAN6 (ADC channels in sky.py). MODELED
# SIMPLIFICATION: a declared demo geometry, not taken from a real structure.
PANELS = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]

# Shared state between scripts (all scopes live in one interpreter): sky.py
# writes, eps_node.py reads.
LIVE = {}


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Orbit:
    def __init__(self, **overrides):
        p = self.p = dict(PARAMS, **overrides)
        self.r = R_EARTH + p["altitude_km"]
        self.n = math.sqrt(MU_EARTH / self.r ** 3)           # rad/s mean motion
        beta = math.radians(p["beta_deg"])
        self.sun = (math.cos(beta), -math.sin(beta), 0.0)     # inertial, unit
        # Umbra (cylindrical shadow): r.s < 0 and |r x s| < R_E, i.e.
        # cos u < -k with k = sqrt(1 - (R_E/r)^2) / cos(beta). Entry at u = acos(-k).
        k = math.sqrt(1 - (R_EARTH / self.r) ** 2) / math.cos(beta)
        u_entry = math.acos(-k) if k < 1 else math.pi
        self.u0 = u_entry - self.n * p["eclipse_entry_s"]
        self.w = math.radians(p["spin_deg_s"])
        self.tilt = math.radians(p["tilt_deg"])
        self.panel_w = SOLAR_CONSTANT * p["cells_per_face"] * p["cell_area_m2"] * p["cell_efficiency"]
        self.soc = p["soc0"]
        self.t = 0.0
        self.rng = random.Random(p["seed"])
        self.acc_sigma_g = p["acc_noise_ug_rthz"] * 1e-6 * math.sqrt(p["acc_odr_hz"] / 2)

    def to_body(self, v, t):
        c, s = math.cos(self.tilt), math.sin(self.tilt)
        x, y, z = c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2]  # Ry(tilt)
        a = -self.w * t                                            # Rz(-w t)
        return (math.cos(a) * x - math.sin(a) * y, math.sin(a) * x + math.cos(a) * y, z)

    def position(self, t):
        u = self.u0 + self.n * t
        return (self.r * math.cos(u), 0.0, self.r * math.sin(u))

    def eclipsed(self, t):
        rv = self.position(t)
        along = dot(rv, self.sun)
        perp2 = dot(rv, rv) - along * along
        return along < 0 and perp2 < R_EARTH ** 2

    def sun_cosines(self, t):
        """cos(angle to each panel normal), clamped at 0; all 0 in umbra."""
        if self.eclipsed(t):
            return [0.0] * 6
        sb = self.to_body(self.sun, t)
        return [max(0.0, dot(sb, n)) for n in PANELS]

    def field_nt(self, t):
        """Axial dipole B = -B0 (R_E/r)^3 [3 (z.r^) r^ - z], in body axes.
        MODELED SIMPLIFICATION: no dipole tilt, no higher IGRF harmonics."""
        rv = self.position(t)
        rh = tuple(c / self.r for c in rv)
        k = -B0_NT * (R_EARTH / self.r) ** 3
        b = (k * 3 * rh[2] * rh[0], k * 3 * rh[2] * rh[1], k * (3 * rh[2] * rh[2] - 1))
        return self.to_body(b, t)

    def accel_g(self):
        """Free fall: 0 g plus white noise. Centripetal spin acceleration
        (w^2 r ~ 1e-7 g at 1 cm) is below the noise and left out."""
        return tuple(self.rng.gauss(0.0, self.acc_sigma_g) for _ in range(3))

    def battery(self, cos):
        """Terminal voltage (V) and current (A, + = charging) of the pack for the
        current SoC and net power. V = Voc + I R and I = P / V give
        V = (Voc + sqrt(Voc^2 + 4 P R)) / 2.
        MODELED SIMPLIFICATION: OCV linear in SoC between the datasheet end
        voltages; ideal (lossless) MPPT and charger."""
        p = self.p
        ocv = p["cells_series"] * (p["cell_v_empty"] + self.soc * (p["cell_v_full"] - p["cell_v_empty"]))
        r = p["cells_series"] * p["cell_r_ohm"] / p["cells_parallel"]
        net_w = self.panel_w * sum(cos) - p["load_w"]
        v = (ocv + math.sqrt(ocv * ocv + 4 * net_w * r)) / 2
        return v, net_w / v

    def step(self, t):
        """Advance to virtual time t (s); returns everything the sensors report."""
        cos = self.sun_cosines(t)
        v, i = self.battery(cos)
        p = self.p
        self.soc += i * (t - self.t) / 3600 / (p["cells_parallel"] * p["cell_capacity_ah"])
        self.t = t
        return {"t": t, "eclipse": self.eclipsed(t), "sun_cos": cos,
                "sun_v": [c * p["sun_full_v"] for c in cos], "mag_nt": self.field_nt(t),
                "vbat_v": v, "ibat_a": i, "soc": self.soc}


if __name__ == "__main__":
    o = Orbit()
    s0 = o.step(0.0)
    assert not s0["eclipse"] and o.eclipsed(15.01) and not o.eclipsed(14.99)
    assert abs(s0["sun_cos"][0] - math.cos(math.radians(30))) < 1e-9       # PAN1 = cos(tilt)
    assert abs(s0["sun_cos"][5] - 0.5) < 1e-9 and s0["sun_cos"][4] == 0     # -Z lit, +Z dark
    B = [math.sqrt(dot(o.field_nt(t), o.field_nt(t))) for t in range(0, 5700, 60)]
    assert 23000 < min(B) and max(B) < 47000                                # 23-47 uT at 500 km
    s20 = [o.step(t / 10) for t in range(1, 201)][-1]
    assert s20["eclipse"] and s20["sun_v"] == [0.0] * 6 and s20["ibat_a"] < 0 < s0["ibat_a"]
    assert s20["vbat_v"] < s0["vbat_v"]
    print("orbit self-check ok: t=0 PAN1 %.3f V vbat %.3f V ibat %+.3f A | t=20 vbat %.3f V ibat %+.3f A"
          % (s0["sun_v"][0], s0["vbat_v"], s0["ibat_a"], s20["vbat_v"], s20["ibat_a"]))
