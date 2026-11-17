#ifndef Components_Detumble_HPP
#define Components_Detumble_HPP

#include "FprimeZephyrReference/Components/Satellite/DetumbleComponentAc.hpp"

namespace Components {

class Detumble final : public DetumbleComponentBase {
  public:
    explicit Detumble(const char* compName);

  private:
    void run_handler(FwIndexType portNum, U32 context) override;
    void DETUMBLE_ENABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void DETUMBLE_DISABLE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void DETUMBLE_SET_GAIN_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, F32 gain) override;
    void setMode(DetumbleMode::T mode);

    DetumbleMode m_mode = DetumbleMode::OFF;
    F32 m_gain = 100.0f;
    F32 m_b[3] = {};
    F32 m_bdot[3] = {};
    I64 m_lastMs = 0;
    bool m_haveB = false;
};

}  // namespace Components

#endif
