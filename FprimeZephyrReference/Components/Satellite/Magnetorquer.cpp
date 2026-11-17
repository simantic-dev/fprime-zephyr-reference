#include "FprimeZephyrReference/Components/Satellite/Magnetorquer.hpp"

#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>

namespace {
const struct device* const pwm_dev = DEVICE_DT_GET(DT_ALIAS(mtq_pwm));
constexpr U32 PERIOD_NS = PWM_USEC(50);  // 20 kHz, above audible coil whine
const struct gpio_dt_spec en = GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), mtq_en_gpios);
const struct gpio_dt_spec dir[3] = {GPIO_DT_SPEC_GET_BY_IDX(DT_PATH(zephyr_user), mtq_dir_gpios, 0),
                                    GPIO_DT_SPEC_GET_BY_IDX(DT_PATH(zephyr_user), mtq_dir_gpios, 1),
                                    GPIO_DT_SPEC_GET_BY_IDX(DT_PATH(zephyr_user), mtq_dir_gpios, 2)};
}  // namespace

namespace Components {

Magnetorquer::Magnetorquer(const char* compName) : MagnetorquerComponentBase(compName) {}

// shortcut: pins configured on first use, so the bridge enable is left at its reset state (input)
// until the first MTQ command; move to a topology init hook if the bridge must be held off at boot.
bool Magnetorquer::gpioReady() {
    if (!m_gpioReady) {
        int err = gpio_pin_configure_dt(&en, GPIO_OUTPUT_INACTIVE);
        for (U8 i = 0; i < 3 && !err; i++) {
            err = gpio_pin_configure_dt(&dir[i], GPIO_OUTPUT_ACTIVE);
        }
        if (err) {
            this->log_WARNING_HI_GpioError(err);
            return false;
        }
        m_gpioReady = true;
    }
    return true;
}

bool Magnetorquer::setEnabled(bool enable) {
    if (!gpioReady() || gpio_pin_set_dt(&en, enable) != 0) {
        return false;
    }
    if (enable != m_enabled) {
        m_enabled = enable;
        this->log_ACTIVITY_HI_BridgeEnabled(enable);
    }
    this->tlmWrite_enabled(m_enabled);
    return true;
}

int Magnetorquer::setDuty(U8 axis, I8 duty, U32& pulse) {
    pulse = PERIOD_NS / 100 * U32(duty < 0 ? -duty : duty);
    if (!gpioReady()) {
        return -EIO;
    }
    int err = gpio_pin_set_dt(&dir[axis], duty >= 0);
    if (!err) {
        err = pwm_set(pwm_dev, axis + 1, PERIOD_NS, pulse, PWM_POLARITY_NORMAL);  // CH1..CH3
    }
    if (err) {
        this->log_WARNING_HI_PwmError(MtqAxis(MtqAxis::T(axis)), err);
        return err;
    }
    m_duty[axis] = duty;
    return 0;
}

void Magnetorquer::MTQ_SET_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, const MtqAxis& axis, I8 duty_pct) {
    if (duty_pct > 100 || duty_pct < -100) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::VALIDATION_ERROR);
        return;
    }
    U32 pulse = 0;
    if (setDuty(U8(axis.e), duty_pct, pulse)) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }
    this->tlmWrite_duty_pct(m_duty);
    this->log_ACTIVITY_HI_DutySet(axis, duty_pct, pulse);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void Magnetorquer::MTQ_ENABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, bool enable) {
    this->cmdResponse_out(opCode, cmdSeq, setEnabled(enable) ? Fw::CmdResponse::OK : Fw::CmdResponse::EXECUTION_ERROR);
}

void Magnetorquer::driveIn_handler(FwIndexType portNum, bool enable, const MtqDuty& duty) {
    U32 pulse;
    for (U8 i = 0; i < 3; i++) {
        setDuty(i, enable ? duty[i] : I8(0), pulse);
    }
    setEnabled(enable);
    this->tlmWrite_duty_pct(m_duty);
}

}  // namespace Components
