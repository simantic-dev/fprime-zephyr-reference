# Demo EPS protocol

A small protocol made up for this demo, between the flight software's `eps`
component (`FprimeZephyrReference/Components/Satellite/EpsCan.cpp`) and the
simulated power system (`sim/peers/eps_node.py`). It is not any real EPS's
interface.

## Transport

CSP v1 over CAN 2.0B (29-bit ids), framed as libcsp 1.x `csp_if_can.c` (CFP) frames it:

| CAN id bits | Field |
|---|---|
| 28..24 | source address |
| 23..19 | destination address |
| 18 | type: 0 = BEGIN, 1 = MORE |
| 17..10 | remain: frames still to come in this packet |
| 9..0 | ident: same for every frame of one packet |

The BEGIN frame carries the 4-byte CSP header (big-endian: prio 2 bits, src 5,
dst 5, dport 6, sport 6, flags 8), a 2-byte big-endian payload length and the
first 2 payload bytes. Each MORE frame carries the next 8 bytes. A receiver
that sees a gap in `remain` drops the packet. Flag `0x01` means a CRC32C of the
payload is appended, big-endian (libcsp's CRC32).

| Node | CSP address |
|---|---|
| flight computer (NUCLEO-H723ZG) | 1 |
| EPS | 2 |

## Services

| EPS port | Request | Reply |
|---|---|---|
| 1 (CSP ping) | any payload, no CRC | the same payload, back to the requester's source port |
| 12 (housekeeping) | `0x10` (HK_GET), CRC32C flag set | 15-byte HK record below, CRC32C flag set |

The flight software uses a fresh source port (32..63) for each HK attempt, so a
late reply to an attempt it already gave up on is ignored.

### HK record, version 1 (all big-endian)

| Offset | Type | Field | Unit |
|---|---|---|---|
| 0 | u8 | version (= 1) | |
| 1 | u32 | EPS uptime | s |
| 5 | u16 | battery voltage `vbat_mV` | mV |
| 7 | i16 | battery current `ibat_mA`, + = charging | mA |
| 9 | u16 | 3.3 V rail | mV |
| 11 | u16 | 5 V rail | mV |
| 13 | i16 | board temperature | 0.01 degC |

Followed by the 4-byte CRC32C. A reply with a bad CRC, a wrong length or an
unknown version counts as `CRC_ERROR`.

## Timing (flight software side)

HK is requested once per second (every 10th 10 Hz tick). Each attempt waits
300 ms; up to 3 attempts. Each failed attempt emits `HkRetry` with the reason
(`TIMEOUT`, `CRC_ERROR`, `FRAME_LOST`); a success after a retry emits
`HkRecovered`; three failures emit `HkFailed`.
