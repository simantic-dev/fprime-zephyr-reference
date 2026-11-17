#ifndef Components_FramParams_HPP
#define Components_FramParams_HPP

#include "FprimeZephyrReference/Components/Satellite/FramParamsComponentAc.hpp"

namespace Components {

class FramParams final : public FramParamsComponentBase {
  public:
    explicit FramParams(const char* compName);

  private:
    void run_handler(FwIndexType portNum, U32 context) override;
    void FRAM_WRITE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 addr, U32 value) override;
    void FRAM_READ_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 addr) override;
    bool m_counted = false;
};

}  // namespace Components

#endif
