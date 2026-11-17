module Components {

  @ X, Y, Z
  array Vec3 = [3] F32

  @ Sun-sensor photodiode voltage per panel, panel 1..6
  array SunMv = [6] U16

  @ Attitude sensors: 2x accelerometer, 2x magnetometer, 6 sun sensors
  passive component Adcs {

    @ 1 Hz tick: read every sensor once
    sync input port run: Svc.Sched

    @ m/s^2
    telemetry accel0: Vec3
    telemetry accel1: Vec3
    @ gauss
    telemetry magn0: Vec3
    telemetry magn1: Vec3
    telemetry sun_mV: SunMv
    @ 1..6, the panel with the highest sun-sensor voltage
    telemetry brightest_panel: U8

    event SensorError(sensor: U8, err: I32) \
      severity warning high \
      format "attitude sensor {} read failed: {}" \
      throttle 4

    time get port timeCaller
    text event port logTextOut
    event port logOut
    telemetry port tlmOut
  }

}
