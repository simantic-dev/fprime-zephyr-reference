# Satellite demo on a simulated NUCLEO-H723ZG

`../demo [nominal|faults]` runs this directory's prebuilt F' deployment
(`fprime-demo.elf`, dictionary `dictionary.json`) on `sim`, Simantic's
simulator (proprietary; install with `curl -fsSL https://simantic.com/install | sh`),
inside an orbit and power environment, with the stock F' ground station attached.

Upstream base: fprime-community/fprime-zephyr-reference `23aade5`, the commit this
branch is known to build from, with `lib/fprime` at nasa/fprime `744d3e3`.

## Files

| File | What |
|---|---|
| `scenario.yaml`, `scenario-faults.yaml` | the machine, a CAN bus to the EPS, USART3 bridged to `tcp:5761` for the GDS |
| `nucleo-h723zg.board` | the parts around the chip; `faults.board` adds the EPS fault schedule |
| `peers/orbit.py`, `peers/sky.py` | orbit, attitude, sun, field and battery model, pushed into the parts every 100 ms |
| `peers/eps_node.py` | the EPS, speaking `EPS-PROTOCOL.md` |
| `peers/fram_slave.py`, `peers/lis2dw12.py`, `peers/ist8310.py` | FRAM, accelerometers, magnetometers |
| `walkthrough.sh` | the scripted walkthrough `../demo` runs against the GDS |
| `build.sh` | rebuilds `fprime-demo.elf` and `dictionary.json` (Zephyr SDK 0.17.0) |

## NUCLEO-H723ZG pins

Our choice of free header pins (UM2407); the Zephyr side is
`../boards/nucleo_h723zg.overlay`.

| Function | Peripheral | Pins (header) |
|---|---|---|
| F' ground link | USART3 | PD8 TX / PD9 RX (ST-LINK VCP) |
| Console | USART2 | PD5 TX / PD6 RX (CN9) |
| EPS bus | FDCAN1 | PD0 RX / PD1 TX (CN9) |
| FRAM | SPI1 | PA5 SCK D13, PA6 MISO D12, PB5 MOSI D11, CS PD14 D10 |
| 2x LIS2DW12 (0x18, 0x19), 2x IST8310 (0x0C, 0x0E) | I2C1 | PB8 SCL D15, PB9 SDA D14 |
| Sun sensors, panels 1..6 | ADC1 INP15/10/5/16/2/6 | PA3 A0, PC0 A1, PB1 A3, PA0 (CN10), PF11 (CN10), PF12 (CN10) |
| Magnetorquer PWM X/Y/Z | TIM1 CH1/CH2/CH3 | PE9 D6, PE11 D5, PE13 D3 |
| Magnetorquer DIR X/Y/Z | GPIO | PG14 D2, PE14 D4, PG12 D7 |
| Magnetorquer bridge enable | GPIO | PF3 D8 |

## What is real and what is simulated

The F' deployment is the real binary, built for the upstream `nucleo_h723zg`
Zephyr board. The STM32H723ZG and its peripherals are simulated, and so is everything
past the pins: the parts above are Python peers, and their values come from
`orbit.py` (a 1U CubeSat in a 500 km polar orbit, tumbling at 3 deg/s, umbra from
t = 90 s). Panel geometry, photodiode output, cell resistance and the EPS rails are
declared demo parameters, marked `MODELED SIMPLIFICATION` in the code. The
environment spins the satellite kinematically: coil torque is ignored, so detumble
drives the coils but the rate does not drop.

In `faults` mode the EPS damages HK requests 30, 40 and 50 (lost CAN frame, bad
CRC32C, 500 ms late); the firmware retries each one.
