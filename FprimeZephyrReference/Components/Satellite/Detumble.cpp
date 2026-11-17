#include "FprimeZephyrReference/Components/Satellite/Detumble.hpp"

#include <cmath>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>

extern struct k_mutex magn_lock;  // Adcs.cpp

namespace {
const struct device* const magn = DEVICE_DT_GET(DT_ALIAS(magn0));
// First-order low-pass on dB/dt: time constant dt/ALPHA = 0.5 s at 10 Hz. Smooths the
// magnetometer's LSB steps, which at a few deg/s are larger than one tick's field change.
constexpr F32 ALPHA = 0.2f;
constexpr F32 RAD_TO_DEG = 57.29578f;

F32 norm(const F32 v[3]) {
    return std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
}
}  // namespace

namespace Components {

Detumble::Detumble(const char* compName) : DetumbleComponentBase(compName) {}

void Detumble::run_handler(FwIndexType portNum, U32 context) {
    struct sensor_value xyz[3];
    int err = 0;
    for (U8 attempt = 0; attempt < 2; attempt++) {
        if (attempt) {
            // IST8310 takes 6 ms per single conversion; a fetch before data-ready returns -EIO.
            k_msleep(6);
        }
        k_mutex_lock(&magn_lock, K_FOREVER);
        err = sensor_sample_fetch(magn);
        if (!err) {
            err = sensor_channel_get(magn, SENSOR_CHAN_MAGN_XYZ, xyz);
        }
        k_mutex_unlock(&magn_lock);
        if (!err) {
            break;
        }
    }
    if (err) {
        this->log_WARNING_HI_MagError(err);
        return;
    }
    const I64 now = k_uptime_get();  // measured dt, so a late tick does not inflate dB/dt
    F32 b[3];
    for (U8 i = 0; i < 3; i++) {
        b[i] = sensor_value_to_float(&xyz[i]) * 100.0f;  // gauss -> uT
        if (m_haveB && now > m_lastMs) {
            const F32 raw = (b[i] - m_b[i]) / (F32(now - m_lastMs) * 1e-3f);
            m_bdot[i] += ALPHA * (raw - m_bdot[i]);
        }
        m_b[i] = b[i];
    }
    m_lastMs = now;
    m_haveB = true;

    MtqDuty duty;
    for (U8 i = 0; i < 3; i++) {
        F32 d = m_mode == DetumbleMode::ON ? -m_gain * m_bdot[i] : 0.0f;
        d = d > 100.0f ? 100.0f : (d < -100.0f ? -100.0f : d);
        duty[i] = I8(std::lround(d));
    }
    if (m_mode == DetumbleMode::ON) {
        this->mtqOut_out(0, true, duty);
    }

    const F32 bn = norm(b);
    const F32 bdotn = norm(m_bdot);
    this->tlmWrite_bdot_uT_s(Vec3({m_bdot[0], m_bdot[1], m_bdot[2]}));
    this->tlmWrite_bdot_norm_uT_s(bdotn);
    this->tlmWrite_rate_est_deg_s(bn > 0.0f ? bdotn / bn * RAD_TO_DEG : 0.0f);
    this->tlmWrite_duty_cmd(duty);
    this->tlmWrite_mode(m_mode);
    this->tlmWrite_gain(m_gain);
}

void Detumble::setMode(DetumbleMode::T mode) {
    if (mode == DetumbleMode::OFF) {
        this->mtqOut_out(0, false, MtqDuty(I8(0)));
    }
    if (m_mode != mode) {
        m_mode = mode;
        this->log_ACTIVITY_HI_ModeChanged(m_mode, m_gain);
    }
}

void Detumble::DETUMBLE_ENABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    setMode(DetumbleMode::ON);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void Detumble::DETUMBLE_DISABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    setMode(DetumbleMode::OFF);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void Detumble::DETUMBLE_SET_GAIN_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, F32 gain) {
    if (!(gain >= 0.0f && gain <= 1e4f)) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::VALIDATION_ERROR);
        return;
    }
    m_gain = gain;
    this->log_ACTIVITY_HI_GainSet(gain);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

}  // namespace Components
