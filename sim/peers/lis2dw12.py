"""The demo's two LIS2DW12 accelerometers (acc0 @ i2c1 0x18, acc1 @ i2c1 0x19) as a
scripted I2C slave.

Why a script: the board only needs the register surface Zephyr and the
F' driver touch (WHO_AM_I, CTRL1..CTRL7, STATUS, OUT_X..Z). Samples come
straight from ACCEL, so the environment (sky.py) can drive
free fall without a FIFO path.

Why ACCEL is keyed by name: sky.py writes lis2dw12.ACCEL["acc0"/"acc1"];
the slave reads the same module, so both see one dict.
"""

import sys

sys.path.insert(0, "peers")  # sim runs from sim/ (../demo); one shared lis2dw12 module

# Peer name -> (x, y, z) in g. Board at rest, +Z up, unless a fixture says otherwise.
ACCEL = {}
DEFAULT_G = (0.0, 0.0, 1.0)

NAMES = {0x18: "acc0", 0x19: "acc1"}  # 7-bit address -> peer name

WHO_AM_I, CTRL1, CTRL2, CTRL6, OUT_T, CTRL7 = 0x0F, 0x20, 0x21, 0x25, 0x26, 0x3F
STATUS, OUT_X_L, OUT_Z_H = 0x27, 0x28, 0x2D
IF_ADD_INC = 0x04  # CTRL2 bit 2, default on
SOFT_RESET = 0x40  # CTRL2 bit 6, self-clearing
FS_RANGE_G = (2, 4, 8, 16)  # CTRL6 bits 5:4


class Slave:
    def __init__(self, ctx):
        import lis2dw12  # the module sky.py writes ACCEL into

        self.shared = lis2dw12
        self.ctx = ctx
        self.name = "acc0"
        self.ptr = 0
        self._reset()
        self.sample = b""

    def _reset(self):
        self.regs = bytearray(0x80)
        self.regs[CTRL2] = IF_ADD_INC

    def on_address(self, address, is_read):
        self.name = NAMES.get(address, self.name)
        return True

    def _advance(self):
        if self.regs[CTRL2] & IF_ADD_INC:
            self.ptr = (self.ptr + 1) & 0x7F

    def on_write(self, data):
        if not data:
            return len(data)
        self.ptr = data[0] & 0x7F
        for b in data[1:]:
            if self.ptr == CTRL2 and b & SOFT_RESET:
                self._reset()  # reset values, and the bit clears itself
            elif CTRL1 <= self.ptr <= CTRL6 or self.ptr == CTRL7:  # 0x26 OUT_T and the rest are read-only here
                self.regs[self.ptr] = b
            self._advance()
        return len(data)

    def _sample(self):
        # Left-justified in 16 bits at the CTRL6 full scale. CTRL1 MODE and
        # LP_MODE (bits 3:0) both 0 is low-power mode 1: 12-bit, four low bits zero.
        # Every other mode is 14-bit, two low bits zero.
        rng = FS_RANGE_G[(self.regs[CTRL6] >> 4) & 3]
        bits, shift = (12, 4) if self.regs[CTRL1] & 0x0F == 0 else (14, 2)
        half = 1 << (bits - 1)
        out = b""
        for g in self.shared.ACCEL.get(self.name, DEFAULT_G):
            counts = max(-half, min(half - 1, round(g * half / rng)))
            out += (counts << shift).to_bytes(2, "little", signed=True)
        return out

    def _reg(self, a):
        if a == WHO_AM_I:
            return 0x44
        if a == STATUS:
            return 0x01  # DRDY: a sample is always ready
        if OUT_X_L <= a <= OUT_Z_H:
            return self.sample[a - OUT_X_L]
        return self.regs[a]

    def on_read(self, count):
        self.sample = self._sample()  # one sample per burst, so X/Y/Z agree
        out = bytearray()
        for _ in range(count):
            out.append(self._reg(self.ptr))
            self._advance()
        return bytes(out)
