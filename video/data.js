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
    2296,
    0,
    0,
    1215,
    0,
    1499
   ],
   "bright": 1,
   "mag": [
    -3.2,
    1.7,
    -45.2
   ]
  },
  {
   "t": 20,
   "vbat": 7755,
   "ibat": 332,
   "sun": [
    1380,
    0,
    0,
    2200,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    -1.5,
    2.3,
    -45.2
   ]
  },
  {
   "t": 30,
   "vbat": 7746,
   "ibat": 235,
   "sun": [
    95,
    0,
    0,
    2596,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    -0.1,
    2.0,
    -45.1
   ]
  },
  {
   "t": 40,
   "vbat": 7757,
   "ibat": 333,
   "sun": [
    0,
    0,
    1215,
    2296,
    0,
    1499
   ],
   "bright": 4,
   "mag": [
    0.6,
    1.1,
    -45.0
   ]
  },
  {
   "t": 50,
   "vbat": 7758,
   "ibat": 332,
   "sun": [
    0,
    0,
    2200,
    1380,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    0.4,
    0.2,
    -44.9
   ]
  },
  {
   "t": 60,
   "vbat": 7749,
   "ibat": 235,
   "sun": [
    0,
    0,
    2596,
    95,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    -0.3,
    0.0,
    -44.8
   ]
  },
  {
   "t": 70,
   "vbat": 7759,
   "ibat": 333,
   "sun": [
    0,
    1215,
    2296,
    0,
    0,
    1499
   ],
   "bright": 3,
   "mag": [
    -0.9,
    0.5,
    -44.6
   ]
  },
  {
   "t": 80,
   "vbat": 7760,
   "ibat": 332,
   "sun": [
    0,
    2200,
    1380,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -1.0,
    1.5,
    -44.5
   ]
  },
  {
   "t": 88,
   "vbat": 7754,
   "ibat": 259,
   "sun": [
    0,
    2572,
    366,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -0.4,
    2.4,
    -44.3
   ]
  },
  {
   "t": 89,
   "vbat": 7752,
   "ibat": 246,
   "sun": [
    0,
    2587,
    230,
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
    2596,
    95,
    0,
    0,
    1499
   ],
   "bright": 2,
   "mag": [
    -0.1,
    2.6,
    -44.3
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
    2.7,
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
    1.5,
    3.0,
    -44.1
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
    3.4,
    2.2,
    -43.9
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
    4.8,
    0.2,
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
     "t": 124.22,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10016000 dispatched to port 8"
    },
    {
     "t": 124.229,
     "name": "PingReply",
     "text": "EPS ping reply in 11 ms"
    },
    {
     "t": 124.238,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10016000 completed"
    }
   ]
  },
  {
   "cmd": "mtq.MTQ_SET Y 40",
   "events": [
    {
     "t": 126.218,
     "name": "DutySet",
     "text": "MTQ Y duty 40% (pulse 20000 ns)"
    },
    {
     "t": 126.227,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10018000 dispatched to port 10"
    },
    {
     "t": 126.237,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10018000 completed"
    }
   ]
  },
  {
   "cmd": "fram.FRAM_WRITE 0x100 0xCAFEF00D",
   "events": [
    {
     "t": 128.229,
     "name": "FramWritten",
     "text": "FRAM[0x100] <- 0xcafef00d"
    },
    {
     "t": 128.237,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10019000 dispatched to port 9"
    },
    {
     "t": 128.247,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10019000 completed"
    }
   ]
  },
  {
   "cmd": "fram.FRAM_READ 0x100",
   "events": [
    {
     "t": 130.029,
     "name": "FramValue",
     "text": "FRAM[0x100] = 0xcafef00d"
    },
    {
     "t": 130.037,
     "name": "OpCodeDispatched",
     "text": "Opcode 0x10019001 dispatched to port 9"
    },
    {
     "t": 130.047,
     "name": "OpCodeCompleted",
     "text": "Opcode 0x10019001 completed"
    }
   ]
  }
 ],
 "faults": [
  {
   "t": 33.129,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: FRAME_LOST, retrying"
  },
  {
   "t": 33.229,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  },
  {
   "t": 42.129,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: CRC_ERROR, retrying"
  },
  {
   "t": 42.229,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  },
  {
   "t": 51.329,
   "name": "HkRetry",
   "text": "EPS HK attempt 1/3 failed: TIMEOUT, retrying"
  },
  {
   "t": 51.429,
   "name": "HkRecovered",
   "text": "EPS HK ok on attempt 2"
  }
 ],
 "hk_retries": 3
};
