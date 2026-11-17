module Components {

  enum DetumbleMode : U8 {
    OFF
    ON
  }

  @ B-dot detumble controller. Every 10 Hz tick it reads magnetometer 0 (body-mounted),
  @ low-passes the finite difference dB/dt, and when ON commands a dipole
  @ m = -gain * dB/dt per axis, saturated to +/-100 % duty, through Magnetorquer.
  @ Units: B in uT, dB/dt in uT/s, gain in % duty per uT/s.
  passive component Detumble {

    @ 10 Hz tick
    guarded input port run: Svc.Sched

    @ Coil drive (to Magnetorquer.driveIn)
    output port mtqOut: MtqDrive

    @ Start the B-dot loop: enables the H-bridges and drives the coils every tick
    guarded command DETUMBLE_ENABLE

    @ Stop the loop: zero duty, H-bridges off
    guarded command DETUMBLE_DISABLE

    @ Controller gain, % duty per uT/s (>= 0)
    guarded command DETUMBLE_SET_GAIN(gain: F32)

    telemetry mode: DetumbleMode
    @ % duty per uT/s
    telemetry gain: F32
    @ Filtered dB/dt per body axis, uT/s
    telemetry bdot_uT_s: Vec3
    @ |dB/dt|, uT/s: the tumble-rate proxy the controller damps
    telemetry bdot_norm_uT_s: F32
    @ Crude body-rate estimate |dB/dt| / |B|, deg/s. It sees only the rate component
    @ perpendicular to B (rotation about B is invisible) plus the orbital field change
    @ (~0.1 deg/s in LEO). A proxy, not a gyro.
    telemetry rate_est_deg_s: F32
    @ Duty the controller commands, % per axis (0 when OFF)
    telemetry duty_cmd: MtqDuty

    event ModeChanged(mode: DetumbleMode, gain: F32) \
      severity activity high \
      format "Detumble {} (gain {} %/(uT/s))"

    event GainSet(gain: F32) \
      severity activity high \
      format "Detumble gain {} %/(uT/s)"

    event MagError(err: I32) \
      severity warning high \
      format "Detumble magnetometer read failed: {}" \
      throttle 4

    time get port timeCaller
    command reg port cmdRegOut
    command recv port cmdIn
    command resp port cmdResponseOut
    text event port logTextOut
    event port logOut
    telemetry port tlmOut
  }

}
