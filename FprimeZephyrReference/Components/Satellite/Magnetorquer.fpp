module Components {

  enum MtqAxis : U8 {
    X
    Y
    Z
  }

  @ Signed duty cycle per axis, percent: + drives DIR high (positive dipole), - low
  array MtqDuty = [3] I8

  @ Drive all three coils at once (the detumble controller's output)
  port MtqDrive(enable: bool, duty: MtqDuty)

  @ Three magnetorquer coils, body X/Y/Z, each on an H-bridge. One enable GPIO for all
  @ bridges (mtq-en-gpios, active high), magnitude = PWM duty on mtq-pwm CH1..CH3,
  @ sign = DIR GPIO (mtq-dir-gpios). Pins: boards/nucleo_h723zg.overlay.
  passive component Magnetorquer {

    @ Set one coil's signed duty cycle, -100..100 %
    guarded command MTQ_SET(axis: MtqAxis, duty_pct: I8)

    @ Enable or disable the H-bridges (mtq-en-gpios)
    guarded command MTQ_ENABLE(enable: bool)

    guarded input port driveIn: MtqDrive

    telemetry duty_pct: MtqDuty
    telemetry enabled: bool

    event DutySet(axis: MtqAxis, duty_pct: I8, pulse_ns: U32) \
      severity activity high \
      format "MTQ {} duty {}% (pulse {} ns)"

    event BridgeEnabled(enable: bool) \
      severity activity high \
      format "MTQ H-bridges enabled: {}"

    event PwmError(axis: MtqAxis, err: I32) \
      severity warning high \
      format "MTQ {} pwm_set failed: {}" \
      throttle 4

    event GpioError(err: I32) \
      severity warning high \
      format "MTQ GPIO setup failed: {}"

    time get port timeCaller
    command reg port cmdRegOut
    command recv port cmdIn
    command resp port cmdResponseOut
    text event port logTextOut
    event port logOut
    telemetry port tlmOut
  }

}
