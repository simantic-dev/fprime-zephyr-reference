# The demo EPS (CSP address 2) as a scripted CAN node, speaking the demo EPS
# protocol (../EPS-PROTOCOL.md): CSP v1 over CAN with libcsp 1.x CFP framing
# (29-bit id = src5 dst5 type1 remain8 ident10; BEGIN frame = 4-byte CSP header +
# 2-byte length + 2 payload bytes, MORE frames = 8 payload bytes). It answers CSP
# ping (port 1) and the housekeeping request on port 12. Battery voltage and
# current come from the orbit model (orbit.LIVE, written by sky.py); the fault
# schedule comes from sky.py's config. A CAN node has no ctx.config of its own.
#
# Faults, by HK request number as this node counts them (deterministic):
#   "drop":    the second CAN frame of the reply is never sent -> FRAME_LOST
#   "corrupt": one payload bit is flipped, so the CRC32C fails  -> CRC_ERROR
#   "late":    the reply is sent 500 ms late, after the requester gave up -> TIMEOUT
import orbit

ADDR = 2
PING_PORT, HK_PORT = 1, 12
HK_GET, HK_VERSION = 0x10, 1
FLAG_CRC32 = 0x01
RAIL_3V3_MV, RAIL_5V_MV, BOARD_TEMP_CC = 3300, 5000, 2150  # declared demo values
LATE_US = 500_000


def crc32c(data):
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 & -(crc & 1))
    return crc ^ 0xFFFFFFFF


def cfp_id(src, dst, begin, remain, ident):
    return (src << 24) | (dst << 19) | ((0 if begin else 1) << 18) | (remain << 10) | ident


def cfp_frames(header, payload):
    """Split one CSP v1 packet into CAN frame payloads the way csp_if_can does."""
    first = header.to_bytes(4, "big") + len(payload).to_bytes(2, "big") + payload[:2]
    return [first] + [payload[i:i + 8] for i in range(2, len(payload), 8)]


class Node:
    def __init__(self, ctx):
        self.ctx = ctx
        self.rx = {}      # (src, ident) -> [header, length, bytearray]
        self.ident = 0
        self.hk_count = 0
        self.late = []

    def on_frame(self, f):
        cid, data = f["id"], bytes(f["data"])
        if not f["extended"] or (cid >> 19) & 0x1F != ADDR:
            return
        src, begin, ident = (cid >> 24) & 0x1F, not (cid >> 18) & 1, cid & 0x3FF
        if begin:
            if len(data) < 6:
                return
            self.rx[(src, ident)] = [int.from_bytes(data[:4], "big"), int.from_bytes(data[4:6], "big"),
                                     bytearray(data[6:])]
        elif (src, ident) in self.rx:
            self.rx[(src, ident)][2] += data
        else:
            return
        header, length, buf = self.rx[(src, ident)]
        if len(buf) >= length:
            del self.rx[(src, ident)]
            self.on_packet(header, bytes(buf[:length]))

    def on_packet(self, header, payload):
        prio, src = header >> 30, (header >> 25) & 0x1F
        dport, sport, flags = (header >> 14) & 0x3F, (header >> 8) & 0x3F, header & 0xFF
        if flags & FLAG_CRC32:
            if len(payload) < 4 or crc32c(payload[:-4]) != int.from_bytes(payload[-4:], "big"):
                self.ctx.warning("request with bad CRC32C dropped")
                return
            payload = payload[:-4]
        if dport == PING_PORT:
            reply = payload
        elif dport == HK_PORT and payload[:1] == bytes([HK_GET]):
            self.hk_count += 1
            reply = self.housekeeping()
        else:
            return
        if flags & FLAG_CRC32:
            reply += crc32c(reply).to_bytes(4, "big")
        rheader = (prio << 30) | (ADDR << 25) | (src << 20) | (sport << 14) | (dport << 8) | (flags & FLAG_CRC32)
        frames = cfp_frames(rheader, reply)
        fault = orbit.LIVE.get("faults", {}).get(self.hk_count) if dport == HK_PORT else None
        if fault == "corrupt":
            frames[1] = bytes([frames[1][0] ^ 0x04]) + frames[1][1:]
        if fault == "late":
            self.late.append((src, frames))
            self.ctx.schedule_oneshot(LATE_US)
        else:
            self.transmit(src, frames, drop=1 if fault == "drop" else None)
        if dport == PING_PORT:
            self.ctx.info(f"ping reply to node {src}")

    def transmit(self, dst, frames, drop=None):
        ident = self.ident
        self.ident = (self.ident + 1) & 0x3FF
        for i, chunk in enumerate(frames):
            if i != drop:
                self.ctx.send(cfp_id(ADDR, dst, i == 0, len(frames) - 1 - i, ident), chunk, extended=True)

    def on_timer(self):
        for dst, frames in self.late:
            self.transmit(dst, frames)
        self.late = []

    def housekeeping(self):
        s = orbit.LIVE["state"]
        vbat, ibat = int(round(s["vbat_v"] * 1000)), int(round(s["ibat_a"] * 1000))
        fault = orbit.LIVE.get("faults", {}).get(self.hk_count)
        self.ctx.info("HK #%d t=%.1f s %s vbat=%.3f V ibat=%+.3f A soc=%.5f%s"
                      % (self.hk_count, s["t"], "eclipse" if s["eclipse"] else "sun", s["vbat_v"],
                         s["ibat_a"], s["soc"], " [fault: %s]" % fault if fault else ""))
        return (bytes([HK_VERSION]) + (self.ctx.now_us // 1_000_000).to_bytes(4, "big")
                + vbat.to_bytes(2, "big") + ibat.to_bytes(2, "big", signed=True)
                + RAIL_3V3_MV.to_bytes(2, "big") + RAIL_5V_MV.to_bytes(2, "big")
                + BOARD_TEMP_CC.to_bytes(2, "big", signed=True))
