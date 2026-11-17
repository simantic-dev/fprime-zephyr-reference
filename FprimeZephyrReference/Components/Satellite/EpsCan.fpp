module Components {

  @ Why an EPS housekeeping attempt failed
  enum EpsFault {
    TIMEOUT     @< no complete reply within the attempt window
    CRC_ERROR   @< reply reassembled but its CRC32C (or version byte) does not match
    FRAME_LOST  @< a CAN frame of the reply is missing (remain count skipped)
  }

  @ EPS node over CSP v1 on CAN (sim/EPS-PROTOCOL.md): housekeeping request on each 1 s slot, with retries
  passive component EpsCan {

    @ 10 Hz tick: drains received CAN frames, runs the request/retry state machine
    guarded input port run: Svc.Sched

    @ CSP ping (port 1) to the EPS node; the reply is reported as an event
    guarded command EPS_PING

    telemetry vbat_mV: U16
    telemetry ibat_mA: I16
    telemetry v3v3_mV: U16
    telemetry v5_mV: U16
    telemetry temp_C: F32
    telemetry uptime_s: U32
    telemetry hk_ok: U32
    telemetry hk_retries: U32

    event HkRetry(attempt: U8, tries: U8, reason: EpsFault) \
      severity warning low \
      format "EPS HK attempt {}/{} failed: {}, retrying"

    event HkRecovered(attempt: U8) \
      severity activity high \
      format "EPS HK ok on attempt {}"

    event HkFailed(tries: U8) \
      severity warning high \
      format "EPS HK failed after {} attempts"

    event PingReply(ms: U32) \
      severity activity high \
      format "EPS ping reply in {} ms"

    event PingTimeout() \
      severity warning low \
      format "EPS ping: no reply"

    event CanError(op: U8, err: I32) \
      severity warning high \
      format "CAN error: op {} returned {}"

    time get port timeCaller
    command reg port cmdRegOut
    command recv port cmdIn
    command resp port cmdResponseOut
    text event port logTextOut
    event port logOut
    telemetry port tlmOut
  }

}
