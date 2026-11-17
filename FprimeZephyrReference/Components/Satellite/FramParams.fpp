module Components {

  @ Persistent parameters in the FRAM (fram0): boot counter at address 0
  passive component FramParams {

    @ 1 Hz tick: counts this boot on the first call
    sync input port run: Svc.Sched

    @ Write a 32-bit word at a byte address
    sync command FRAM_WRITE(addr: U32, value: U32)

    @ Read a 32-bit word at a byte address; the value is reported as an event
    sync command FRAM_READ(addr: U32)

    telemetry boot_count: U32

    event BootCount(count: U32) \
      severity activity high \
      format "boot count {} (stored in FRAM)"

    event FramWritten(addr: U32, value: U32) \
      severity activity high \
      format "FRAM[0x{x}] <- 0x{x}"

    event FramValue(addr: U32, value: U32) \
      severity activity high \
      format "FRAM[0x{x}] = 0x{x}"

    event FramError(addr: U32, err: I32) \
      severity warning high \
      format "FRAM access at 0x{x} failed: {}"

    time get port timeCaller
    command reg port cmdRegOut
    command recv port cmdIn
    command resp port cmdResponseOut
    text event port logTextOut
    event port logOut
    telemetry port tlmOut
  }

}
