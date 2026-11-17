#ifndef Components_EpsCan_HPP
#define Components_EpsCan_HPP

#include "FprimeZephyrReference/Components/Satellite/EpsCanComponentAc.hpp"

namespace Components {

class EpsCan final : public EpsCanComponentBase {
  public:
    explicit EpsCan(const char* compName);

  private:
    void run_handler(FwIndexType portNum, U32 context) override;
    void EPS_PING_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;

    void send(U8 dport, U8 sport, U8 flags, const U8* payload, U8 len);
    void sendHk();
    void onFrame(U32 id, const U8* data, U8 dlc);
    void onPacket(U32 header, const U8* data, U16 len);
    void fault(EpsFault reason);

    bool m_started = false;
    U32 m_tick = 0;
    U16 m_ident = 0;
    // HK request in flight: attempt number (0 = idle), our CSP source port, deadline tick
    U8 m_attempt = 0;
    U8 m_sport = 32;
    U32 m_deadline = 0;
    U32 m_ok = 0;
    U32 m_retries = 0;
    // ping in flight: start time in ms (0 = none)
    U32 m_pingStart = 0;
    U32 m_pingDeadline = 0;
    // CFP reassembly of one packet from the EPS node
    bool m_rxActive = false;
    U16 m_rxIdent = 0;
    U8 m_rxRemain = 0;
    U32 m_rxHeader = 0;
    U16 m_rxLen = 0;
    U16 m_rxGot = 0;
    U8 m_rxBuf[64];
};

}  // namespace Components

#endif
