// Written by collect.py from runs/*/walkthrough.txt. Do not edit by hand.
window.DATA = {
 "mcu": "STM32H723",
 "board": "NUCLEO-H723ZG",
 "sim": "sim 0.10.2 (build 83eb7a66)",
 "orbit": [
  {
   "t": 10,
   "vbat": 7754,
   "ibat": 333,
   "sun": [
    2302,
    0,
    0,
    1203,
    0,
    1499
   ],
   "bright": 1,
   "mag": [
    -3.1,
    1.7,
    -45.2
   ]
  },
  {
   "t": 20,
   "vbat": 7755,
   "ibat": 332,
   "sun": [
    1392,
    0,
    0,
    2193,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    -1.4,
    2.4,
    -45.1
   ]
  },
  {
   "t": 30,
   "vbat": 7746,
   "ibat": 235,
   "sun": [
    108,
    0,
    0,
    2595,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    0.0,
    2.1,
    -45.0
   ]
  },
  {
   "t": 40,
   "vbat": 7757,
   "ibat": 333,
   "sun": [
    0,
    0,
    1203,
    2302,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    0.7,
    1.2,
    -44.9
   ]
  },
  {
   "t": 50,
   "vbat": 7758,
   "ibat": 332,
   "sun": [
    0,
    0,
    2193,
    1392,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    0.5,
    0.3,
    -44.8
   ]
  },
  {
   "t": 60,
   "vbat": 7749,
   "ibat": 235,
   "sun": [
    0,
    0,
    2595,
    108,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    -0.2,
    0.1,
    -44.7
   ]
  },
  {
   "t": 70,
   "vbat": 7759,
   "ibat": 333,
   "sun": [
    0,
    1203,
    2302,
    0,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    -0.8,
    0.5,
    -44.5
   ]
  },
  {
   "t": 80,
   "vbat": 7760,
   "ibat": 332,
   "sun": [
    0,
    2193,
    1392,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -0.9,
    1.6,
    -44.4
   ]
  },
  {
   "t": 88,
   "vbat": 7754,
   "ibat": 259,
   "sun": [
    0,
    2570,
    379,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -0.3,
    2.5,
    -44.2
   ]
  },
  {
   "t": 89,
   "vbat": 7752,
   "ibat": 246,
   "sun": [
    0,
    2586,
    244,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -0.2,
    2.6,
    -44.2
   ]
  },
  {
   "t": 90,
   "vbat": 7708,
   "ibat": -195,
   "sun": [
    0,
    2595,
    108,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    0.0,
    2.7,
    -44.2
   ]
  },
  {
   "t": 91,
   "vbat": 7708,
   "ibat": -195,
   "sun": [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "bright": 1,
   "mag": [
    0.1,
    2.7,
    -44.2
   ]
  },
  {
   "t": 92,
   "vbat": 7708,
   "ibat": -195,
   "sun": [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "bright": 1,
   "mag": [
    0.2,
    2.8,
    -44.2
   ]
  },
  {
   "t": 100,
   "vbat": 7708,
   "ibat": -195,
   "sun": [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "bright": 1,
   "mag": [
    1.6,
    3.0,
    -44.0
   ]
  },
  {
   "t": 110,
   "vbat": 7707,
   "ibat": -195,
   "sun": [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "bright": 1,
   "mag": [
    3.5,
    2.3,
    -43.8
   ]
  },
  {
   "t": 120,
   "vbat": 7707,
   "ibat": -195,
   "sun": [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   "bright": 1,
   "mag": [
    4.9,
    0.3,
    -43.6
   ]
  }
 ],
 "boot_count": 1,
 "commands": [
  {
   "cmd": "eps.EPS_PING",
   "events": [
    {
     "t": 123.239,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10017000 dispatched to port 8"
    },
    {
     "t": 123.248,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10017000 completed"
    },
    {
     "t": 123.337,
     "name": "PingReply",
     "text": "EPS ping reply in 99 ms"
    }
   ]
  },
  {
   "cmd": "mtq.MTQ_SET Y 40",
   "events": [
    {
     "t": 124.737,
     "name": "DutySet",
     "text": "MTQ Y duty 40% (pulse 20000 ns)"
    },
    {
     "t": 124.746,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10019000 dispatched to port 10"
    },
    {
     "t": 124.756,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10019000 completed"
    }
   ]
  },
  {
   "cmd": "fram.FRAM_WRITE 0x100 0xCAFEF00D",
   "events": [
    {
     "t": 126.137,
     "name": "FramWritten",
     "text": "FRAM[0x100] <- 0xcafef00d"
    },
    {
     "t": 126.146,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x1001a000 dispatched to port 9"
    },
    {
     "t": 126.156,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x1001a000 completed"
    }
   ]
  },
  {
   "cmd": "fram.FRAM_READ 0x100",
   "events": [
    {
     "t": 127.937,
     "name": "FramValue",
     "text": "FRAM[0x100] = 0xcafef00d"
    },
    {
     "t": 127.945,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x1001a001 dispatched to port 9"
    },
    {
     "t": 127.955,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x1001a001 completed"
    }
   ]
  }
 ],
 "faults": [
  {
   "t": 33.136,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: FRAME_LOST, retrying"
  },
  {
   "t": 33.237,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  },
  {
   "t": 42.136,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: CRC_ERROR, retrying"
  },
  {
   "t": 42.236,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  },
  {
   "t": 51.337,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: TIMEOUT, retrying"
  },
  {
   "t": 51.437,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  }
 ],
 "hk_retries": 3,
 "walk": [
  "== 1. Orbit: EPS housekeeping, sun sensors and magnetometer through the eclipse (umbra from t=90 s)",
  "   t_s  vbat_mV ibat_mA  sun_mV PAN1..PAN6                    bright  magn0_uT x/y/z",
  "    10     7754     333   2302     0     0  1203     0  1499       1     -3.1    1.7  -45.2",
  "    20     7755     332   1392     0     0  2193     0  1499       4     -1.4    2.4  -45.1",
  "    30     7746     235    108     0     0  2595     0  1499       4      0.0    2.1  -45.0",
  "    40     7757     333      0     0  1203  2302     0  1499       4      0.7    1.2  -44.9",
  "    50     7758     332      0     0  2193  1392     0  1499       3      0.5    0.3  -44.8",
  "    60     7749     235      0     0  2595   108     0  1499       3     -0.2    0.1  -44.7",
  "    70     7759     333      0  1203  2302     0     0  1499       3     -0.8    0.5  -44.5",
  "    80     7760     332      0  2193  1392     0     0  1499       2     -0.9    1.6  -44.4",
  "    88     7754     259      0  2570   379     0     0  1499       2     -0.3    2.5  -44.2",
  "    89     7752     246      0  2586   244     0     0  1499       2     -0.2    2.6  -44.2",
  "    90     7708    -195      0  2595   108     0     0  1499       2      0.0    2.7  -44.2",
  "    91     7708    -195      0     0     0     0     0     0       1      0.1    2.7  -44.2",
  "    92     7708    -195      0     0     0     0     0     0       1      0.2    2.8  -44.2",
  "   100     7708    -195      0     0     0     0     0     0       1      1.6    3.0  -44.0",
  "   110     7707    -195      0     0     0     0     0     0       1      3.5    2.3  -43.8",
  "   120     7707    -195      0     0     0     0     0     0       1      4.9    0.3  -43.6",
  ""
 ]
};
