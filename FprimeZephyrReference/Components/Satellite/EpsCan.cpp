// The demo EPS protocol (sim/EPS-PROTOCOL.md): CSP v1 over CAN, framed as libcsp 1.x
// csp_if_can.c (CFP) frames it, which is what sim/peers/eps_node.py speaks:
//   CAN id (29-bit) = src5 dst5 type1 remain8 ident10; type 0 = BEGIN, 1 = MORE
//   BEGIN data = 4-byte CSP header (BE) + 2-byte length (BE) + first 2 payload bytes
//   MORE data  = next 8 payload bytes
//   CSP header = prio2 src5 dst5 dport6 sport6 flags8; flag 0x01 = CRC32C (BE) appended to payload
#include "FprimeZephyrReference/Components/Satellite/EpsCan.hpp"

#include <zephyr/drivers/can.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/crc.h>

namespace {
const struct device* const can_dev = DEVICE_DT_GET(DT_CHOSEN(zephyr_canbus));
CAN_MSGQ_DEFINE(eps_rxq, 32);

constexpr U8 FC_ADDR = 1, EPS_ADDR = 2;
constexpr U8 PING_PORT = 1, HK_PORT = 12, PING_SPORT = 17;
constexpr U8 HK_GET = 0x10, HK_VERSION = 1;
constexpr U8 FLAG_CRC32 = 0x01, PRIO_NORM = 2;
constexpr U8 TRIES = 3;
constexpr U32 PERIOD_TICKS = 10, TIMEOUT_TICKS = 3;  // at 10 Hz: HK every 1 s, 300 ms per attempt
constexpr U16 HK_LEN = 15;  // version u8, uptime_s u32, vbat_mV u16, ibat_mA i16, v3v3_mV u16, v5_mV u16, temp_cC i16

U32 be32(const U8* p) {
    return (U32(p[0]) << 24) | (U32(p[1]) << 16) | (U32(p[2]) << 8) | p[3];
}
U16 be16(const U8* p) {
    return U16((p[0] << 8) | p[1]);
}
void put_be32(U8* p, U32 v) {
    p[0] = U8(v >> 24); p[1] = U8(v >> 16); p[2] = U8(v >> 8); p[3] = U8(v);
}
}  // namespace

namespace Components {

EpsCan::EpsCan(const char* compName) : EpsCanComponentBase(compName) {}

void EpsCan::send(U8 dport, U8 sport, U8 flags, const U8* payload, U8 len) {
    const U32 header = (U32(PRIO_NORM) << 30) | (U32(FC_ADDR) << 25) | (U32(EPS_ADDR) << 20) |
                       (U32(dport) << 14) | (U32(sport) << 8) | flags;
    const U8 frames = U8(1 + (len > 2 ? (len - 2 + 7) / 8 : 0));
    const U16 ident = m_ident;
    m_ident = (m_ident + 1) & 0x3FF;
    U8 off = 0;
    for (U8 i = 0; i < frames; i++) {
        struct can_frame f = {};
        f.flags = CAN_FRAME_IDE;
        f.id = (U32(FC_ADDR) << 24) | (U32(EPS_ADDR) << 19) | (U32(i ? 1 : 0) << 18) |
               (U32(frames - 1 - i) << 10) | ident;
        U8 n = 0;
        if (i == 0) {
            put_be32(f.data, header);
            f.data[4] = 0;
            f.data[5] = len;
            n = 6;
        }
        while (n < 8 && off < len) {
            f.data[n++] = payload[off++];
        }
        f.dlc = n;
        const int err = can_send(can_dev, &f, K_MSEC(10), nullptr, nullptr);
        if (err) {
            this->log_WARNING_HI_CanError(1, err);
            return;
        }
    }
}

void EpsCan::sendHk() {
    m_sport = U8(m_sport >= 63 ? 32 : m_sport + 1);  // fresh port per attempt: late replies to an old one are ignored
    U8 req[5] = {HK_GET};
    put_be32(&req[1], crc32_c(0, req, 1, true, true));
    m_deadline = m_tick + TIMEOUT_TICKS;
    this->send(HK_PORT, m_sport, FLAG_CRC32, req, sizeof(req));
}

void EpsCan::fault(EpsFault reason) {
    if (m_attempt < TRIES) {
        this->log_WARNING_LO_HkRetry(m_attempt, TRIES, reason);
        this->tlmWrite_hk_retries(++m_retries);
        m_attempt++;
        this->sendHk();
    } else {
        this->log_WARNING_HI_HkFailed(TRIES);
        m_attempt = 0;
    }
}

void EpsCan::onFrame(U32 id, const U8* data, U8 dlc) {
    const bool more = (id >> 18) & 1;
    const U8 remain = U8((id >> 10) & 0xFF);
    const U16 ident = U16(id & 0x3FF);
    if (((id >> 24) & 0x1F) != EPS_ADDR) {
        return;
    }
    if (!more) {
        if (dlc < 6) {
            return;
        }
        m_rxActive = true;
        m_rxIdent = ident;
        m_rxRemain = remain;
        m_rxHeader = be32(data);
        m_rxLen = be16(&data[4]);
        m_rxGot = 0;
        if (m_rxLen > sizeof(m_rxBuf)) {
            m_rxActive = false;
            return;
        }
        data += 6;
        dlc = U8(dlc - 6);
    } else if (!m_rxActive || ident != m_rxIdent) {
        return;
    } else if (remain + 1 != m_rxRemain) {
        // a frame of this packet never arrived: abort reassembly, as csp_if_can does
        m_rxActive = false;
        if (m_attempt && ((m_rxHeader >> 14) & 0x3F) == m_sport) {
            this->fault(EpsFault::FRAME_LOST);
        }
        return;
    } else {
        m_rxRemain = remain;
    }
    for (U8 i = 0; i < dlc && m_rxGot < m_rxLen; i++) {
        m_rxBuf[m_rxGot++] = data[i];
    }
    if (m_rxGot >= m_rxLen) {
        m_rxActive = false;
        this->onPacket(m_rxHeader, m_rxBuf, m_rxLen);
    }
}

void EpsCan::onPacket(U32 header, const U8* data, U16 len) {
    const U8 dport = U8((header >> 14) & 0x3F), sport = U8((header >> 8) & 0x3F);
    if (sport == PING_PORT && dport == PING_SPORT && m_pingStart) {
        this->log_ACTIVITY_HI_PingReply(k_uptime_get_32() - m_pingStart);
        m_pingStart = 0;
        return;
    }
    if (sport != HK_PORT || dport != m_sport || !m_attempt) {
        return;  // stale (e.g. a late reply to an attempt we already retried)
    }
    if (!(header & FLAG_CRC32) || len != HK_LEN + 4 || crc32_c(0, data, HK_LEN, true, true) != be32(&data[HK_LEN]) ||
        data[0] != HK_VERSION) {
        this->fault(EpsFault::CRC_ERROR);
        return;
    }
    this->tlmWrite_uptime_s(be32(&data[1]));
    this->tlmWrite_vbat_mV(be16(&data[5]));
    this->tlmWrite_ibat_mA(I16(be16(&data[7])));
    this->tlmWrite_v3v3_mV(be16(&data[9]));
    this->tlmWrite_v5_mV(be16(&data[11]));
    this->tlmWrite_temp_C(F32(I16(be16(&data[13]))) / 100.0f);  // centi-degrees C on the wire
    this->tlmWrite_hk_ok(++m_ok);
    if (m_attempt > 1) {
        this->log_ACTIVITY_HI_HkRecovered(m_attempt);
    }
    m_attempt = 0;
}

void EpsCan::run_handler(FwIndexType portNum, U32 context) {
    if (!m_started) {
        m_started = true;
        const struct can_filter filter = {.id = U32(FC_ADDR) << 19, .mask = 0x1FU << 19, .flags = CAN_FILTER_IDE};
        int err = can_add_rx_filter_msgq(can_dev, &eps_rxq, &filter);
        if (err >= 0) {
            err = can_start(can_dev);
        }
        if (err < 0) {
            this->log_WARNING_HI_CanError(0, err);
        }
    }
    m_tick++;
    struct can_frame f;
    while (k_msgq_get(&eps_rxq, &f, K_NO_WAIT) == 0) {
        this->onFrame(f.id, f.data, f.dlc);
    }
    if (m_attempt && m_tick >= m_deadline) {
        this->fault(EpsFault::TIMEOUT);
    }
    if (m_pingStart && m_tick >= m_pingDeadline) {
        this->log_WARNING_LO_PingTimeout();
        m_pingStart = 0;
    }
    if (!m_attempt && m_tick % PERIOD_TICKS == 0) {
        m_attempt = 1;
        this->sendHk();
    }
}

void EpsCan::EPS_PING_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    static const U8 payload[8] = {0, 1, 2, 3, 4, 5, 6, 7};
    m_pingStart = k_uptime_get_32() | 1;  // never 0 while in flight
    m_pingDeadline = m_tick + PERIOD_TICKS;
    this->send(PING_PORT, PING_SPORT, 0, payload, sizeof(payload));
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

}  // namespace Components
