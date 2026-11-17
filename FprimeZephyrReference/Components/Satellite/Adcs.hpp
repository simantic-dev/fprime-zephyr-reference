#ifndef Components_Adcs_HPP
#define Components_Adcs_HPP

#include "FprimeZephyrReference/Components/Satellite/AdcsComponentAc.hpp"

namespace Components {

class Adcs final : public AdcsComponentBase {
  public:
    explicit Adcs(const char* compName);

  private:
    void run_handler(FwIndexType portNum, U32 context) override;
    bool m_adcReady = false;
};

}  // namespace Components

#endif
