#include "FprimeZephyrReference/Components/Satellite/FramParams.hpp"

#include <zephyr/drivers/eeprom.h>

namespace {
const struct device* const fram = DEVICE_DT_GET(DT_ALIAS(fram0));
constexpr U32 BOOT_COUNT_ADDR = 0;
}  // namespace

namespace Components {

FramParams::FramParams(const char* compName) : FramParamsComponentBase(compName) {}

void FramParams::run_handler(FwIndexType portNum, U32 context) {
    if (m_counted) {
        return;
    }
    m_counted = true;
    U32 count = 0;
    int err = eeprom_read(fram, BOOT_COUNT_ADDR, &count, sizeof(count));
    if (!err) {
        count++;
        err = eeprom_write(fram, BOOT_COUNT_ADDR, &count, sizeof(count));
    }
    if (err) {
        this->log_WARNING_HI_FramError(BOOT_COUNT_ADDR, err);
        return;
    }
    this->tlmWrite_boot_count(count);
    this->log_ACTIVITY_HI_BootCount(count);
}

void FramParams::FRAM_WRITE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 addr, U32 value) {
    const int err = eeprom_write(fram, addr, &value, sizeof(value));
    if (err) {
        this->log_WARNING_HI_FramError(addr, err);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }
    this->log_ACTIVITY_HI_FramWritten(addr, value);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void FramParams::FRAM_READ_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 addr) {
    U32 value = 0;
    const int err = eeprom_read(fram, addr, &value, sizeof(value));
    if (err) {
        this->log_WARNING_HI_FramError(addr, err);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }
    this->log_ACTIVITY_HI_FramValue(addr, value);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

}  // namespace Components
