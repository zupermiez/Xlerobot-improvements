# Known issues and fixes

## Head motors (ids 7/8) crash teleop on a flaky bus

**Symptom:**
```
ConnectionError: Failed to sync read 'Present_Position' on ids=[7, 8] after 1 tries.
[TxRxResult] Incorrect status packet!
```
raised from `xlerobot.py`'s `get_observation()` (or `send_action()`),
killing the whole teleop script over the head pan/tilt motors — the
least critical joints (last in the daisy-chain on `bus1`, sharing the
bus with the left arm).

**Fix applied** in `payload/robots/xlerobot/xlerobot.py`: reads/writes
to the head motors go through `_read_head_pos_soft()` / a try/except
around the head `sync_write`, which catch `ConnectionError`, log a
warning, and fall back to the last known-good head position (or hold
still) instead of crashing. Left/right arms and base are untouched —
those still hard-fail on a dropped connection, which is what you want
for anything safety/motion-critical.

This masks symptoms of a genuinely flaky connection on that bus segment
(daisy-chain wiring, baud rate, termination) — worth checking the
physical connection to motors 7/8 if the warning fires a lot, since the
patch avoids the crash but doesn't fix marginal hardware.

If it needs tightening further (e.g. retry a couple of times before
falling back rather than giving up after one try), bump `num_retry` on
the head-motor `sync_read`/`sync_write` calls specifically.

## Missing/renumbered base wheels (or head) crash `connect()` outright

**Symptom:**
```
FeetechMotorsBus motor check failed on port '/dev/ttyACM1':

Missing motor IDs:
  - 7 (expected model: 777)
  - 8 (expected model: 777)
```
This is a *different* failure from the runtime one above — it happens
during `robot.connect()`'s initial handshake, before teleop even
starts, and aborts the whole connection (both buses), not just the
head. Easy to misdiagnose: ids `7`/`8` exist on **both** buses with
different meanings — `bus1`/port1 (left arm) uses them for
`head_motor_1`/`head_motor_2`, `bus2`/port2 (right arm) uses them for
`base_left_wheel`/`base_back_wheel` (`base_right_wheel` is `9`). Check
*which port* the error names before assuming it's the head.

Root cause on a second arm pair: the base wheel motors were physically
configured with different IDs than the software expects (e.g. found
`9,10` instead of the expected `7,8,9`) — not simply absent hardware.
Confirm with a live scan (no need to unplug anything):
```python
from lerobot.motors.feetech import FeetechMotorsBus
for port in ["/dev/ttyACM0", "/dev/ttyACM1"]:
    print(port, FeetechMotorsBus.scan_port(port))
```

**Fix applied:** `XLerobotConfig.skip_missing_motors` (default `False`).
When `True`, a motor-check failure during `connect()` drops just the
unresponsive motor IDs (logged loudly per motor) instead of aborting —
the rest of the robot still connects. `get_observation`/`send_action`/
`stop_base` degrade gracefully: a fully/partially missing head returns
no head observation and skips head writes; a base with fewer than all
three wheels reports zero velocity and skips base writes entirely
(partial wheel kinematics isn't meaningful). Left/right arms are never
droppable this way — a missing arm motor still hard-fails, since that's
safety/motion-critical.

Enable it via env var in the shipped example scripts without editing
code:
```bash
XLEROBOT_SKIP_MISSING_MOTORS=1 python payload/examples/7_xlerobot_teleop_joycon.py
```
or directly: `XLerobotConfig(id="my_xlerobot", skip_missing_motors=True)`.

This masks a real mismatch rather than fixing it — if you actually want
the base working, the wheel motors need re-numbering to match the
config (7/8/9) via the motor setup routine, not just skipping.

## `software/src/robots/xlerobot*` showing as deleted in the main Xlerobot repo

The main `Xlerobot` repo's working tree can show
`software/src/robots/xlerobot/`, `xlerobot_2wheels/`, `xlerobot_mecanum/`
as deleted (uncommitted) while teleop still works fine — because Python
actually imports `lerobot.robots.xlerobot` from wherever `lerobot` was
`pip install -e .`'d from (a separate checkout), not from the Xlerobot
repo itself. Harmless as long as that separate `lerobot` checkout still
has the robot class files (this repo's `payload/robots/xlerobot/` is
exactly that — drop it into `<lerobot_checkout>/src/lerobot/robots/xlerobot/`).
If the deletion in the Xlerobot repo was unintentional, `git checkout --
software/src/robots/` there restores it.

## Joy-Con "not connected" even though paired

Joy-Cons disconnect from Bluetooth when idle — pairing is persistent,
the live connection is not. Reconnect each session with
`bluetoothctl connect <mac>` or by pressing a button on the controller.
This is expected behavior, not a bug.

## Docs reference `joycon_test_read.py`, actual file is `joycon_test_read_CN.py`

The upstream XLeRobot docs mention `joycon_test_read.py` for the
connectivity sanity check; the file that actually exists (Chinese
comments, English output) is `joycon_test_read_CN.py`. Use that one.
