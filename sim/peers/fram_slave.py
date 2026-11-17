"""Serial SPI FRAM (FM25/CY15-style opcodes, 2 Mbit, 3 address bytes) as a scripted SPI slave.

A pure byte-stream state machine: no erase, no page wrap, no busy time, so a
write is committed as each byte arrives. Firmware drives it through Zephyr's
atmel,at25 EEPROM driver (boards/nucleo_h723zg.overlay). Starts blank: every
run is a first boot.
"""

WREN, WRDI, RDSR, WRSR, READ, WRITE, RDID, FSTRD = 0x06, 0x04, 0x05, 0x01, 0x03, 0x02, 0x9F, 0x0B
SR_WEL = 0x02            # write-enable latch
SIZE = 2 * 1024 * 1024 // 8
ADDR_BYTES = 3
DEVICE_ID = b"\xc2\x22\x00"


class Slave:
    def __init__(self, ctx):
        self.ctx = ctx
        self.mem = bytearray(SIZE)
        self.status = 0
        self._reset_frame()

    def _reset_frame(self):
        self.phase = "opcode"
        self.op = None
        self.addr = 0
        self.addr_seen = 0
        self.id_index = 0

    def on_finish(self):
        """Chip select released: the next byte is an opcode."""
        self._reset_frame()

    def on_transmit(self, b):
        """One MOSI byte in, the MISO byte for this same beat out."""
        if self.phase == "opcode":
            return self._opcode(b)
        if self.phase == "addr":
            self.addr = (self.addr << 8) | b
            self.addr_seen += 1
            if self.addr_seen == ADDR_BYTES:
                self.addr &= SIZE - 1
                self.phase = "dummy" if self.op == FSTRD else "data"
            return 0
        if self.phase == "dummy":  # fast read burns one byte
            self.phase = "data"
            return 0
        if self.phase == "data":
            v = 0
            if self.op in (READ, FSTRD):
                v = self.mem[self.addr]
            elif self.status & SR_WEL:  # a write without WREN is dropped, as on a real part
                self.mem[self.addr] = b
            self.addr = (self.addr + 1) & (SIZE - 1)  # linear, never page-wraps
            return v
        if self.phase == "status":
            return self.status
        if self.phase == "id":
            v = DEVICE_ID[self.id_index % len(DEVICE_ID)]
            self.id_index += 1
            return v
        return 0

    def _opcode(self, b):
        self.op = b
        if b == WREN:
            self.status |= SR_WEL
            self._reset_frame()
        elif b == WRDI:
            self.status &= ~SR_WEL
            self._reset_frame()
        elif b == RDSR:
            self.phase = "status"
        elif b == WRSR:
            self.phase = "wrsr"
        elif b == RDID:
            self.phase = "id"
        elif b in (READ, WRITE, FSTRD):
            self.phase = "addr"
        else:
            self._reset_frame()
        return 0
