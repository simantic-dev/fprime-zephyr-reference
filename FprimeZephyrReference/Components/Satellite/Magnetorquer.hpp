#ifndef Components_Magnetorquer_HPP
#define Components_Magnetorquer_HPP

#include "FprimeZephyrReference/Components/Satellite/MagnetorquerComponentAc.hpp"

namespace Components {

class Magnetorquer final : public MagnetorquerComponentBase {
  public:
    explicit Magnetorquer(const char* compName);

  private:
    void MTQ_SET_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, const MtqAxis& axis, I8 duty_pct) override;
    void MTQ_ENABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, bool enable) override;
    void driveIn_handler(FwIndexType portNum, bool enable, const MtqDuty& duty) override;

    bool gpioReady();
    bool setEnabled(bool enable);
    int setDuty(U8 axis, I8 duty, U32& pulse);

    MtqDuty m_duty;
    bool m_enabled = false;
    bool m_gpioReady = false;
};

}  // namespace Components

#endif
