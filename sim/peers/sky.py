# Environment controller: every tick of virtual time, evaluates orbit.py and
# publishes the result. acc0/acc1 (LIS2DW12) are fed through lis2dw12.ACCEL,
# which the lis2dw12 peer reads on I2C. Battery state and the fault schedule go
# to eps_node.py through orbit.LIVE.
#
# ctx.config (JSON in the board file): any orbit.PARAMS key overrides the default;
# "faults": {"<hk request #>": "drop" | "corrupt" | "late"}; "tick_ms" (100).
#
# The six sun sensors are ADC1 inputs (boards/nucleo_h723zg.overlay), driven with
# ctx.set_property(adc, "ch<N>", volts); the IST8310s take the field through their
# MagneticFluxDensityX/Y/Z properties (nT).
import sys

sys.path.insert(0, "peers")  # sim runs from sim/ (../demo)
import lis2dw12  # noqa: E402

import orbit  # noqa: E402

SUN_ADC = "adcM1S2"                  # ADC1
SUN_INPUTS = (15, 10, 5, 16, 2, 6)   # panels 1..6: PA3, PC0, PB1, PA0, PF11, PF12
MAGNETOMETERS = ("mag0", "mag1")     # both mounted on body axes


class Peripheral:
    def __init__(self, ctx):
        self.ctx = ctx
        cfg = dict(ctx.config)
        orbit.LIVE["faults"] = {int(k): v for k, v in cfg.pop("faults", {}).items()}
        self.tick_us = int(cfg.pop("tick_ms", 100)) * 1000
        self.orbit = orbit.Orbit(**cfg)
        self.ticks = 0

    def on_access(self, req):
        # Arm the tick on the init access (reset clears timers before it).
        if req.is_init:
            self.update()
            self.ctx.schedule_periodic(self.tick_us)

    def on_timer(self):
        self.ticks += 1
        self.update()

    def update(self):
        s = self.orbit.step(self.ticks * self.tick_us / 1e6)
        orbit.LIVE["state"] = s
        for ch, v in zip(SUN_INPUTS, s["sun_v"]):
            self.ctx.set_property(SUN_ADC, "ch%d" % ch, v)
        for m in MAGNETOMETERS:
            for axis, nt in zip("XYZ", s["mag_nt"]):
                self.ctx.set_property(m, "MagneticFluxDensity" + axis, nt)
        lis2dw12.ACCEL["acc0"] = self.orbit.accel_g()
        lis2dw12.ACCEL["acc1"] = self.orbit.accel_g()
