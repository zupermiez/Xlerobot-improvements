# Joy-Con teleop setup — known-good recipe

This is the exact stack verified working on a first XLeRobot arm pair
(Ubuntu 22.04, x86_64 laptop, kernel 6.8). `scripts/install.sh` automates
everything below except the physical/interactive steps (Bluetooth pairing,
plugging in boards).

## What actually needs to be true

1. **`hid-nintendo` kernel driver** installed via DKMS for your *currently
   running* kernel. This is the #1 thing that silently breaks after a
   kernel update — `dkms status` must show `installed` for `uname -r`,
   not just some older kernel version.
2. **`joycond`** daemon running (`systemctl is-active joycond` → `active`).
   Without it, Bluetooth HID reports arrive but nothing exposes them as
   readable input devices reliably.
3. **udev rules** granting `0666` perms on the Joy-Con hidraw nodes
   (vendor `057e`, products `2006`/`2007`), otherwise you need root or a
   manual `chmod` every time.
4. **`joycon-robotics` python package** (from box2ai-robotics), with its
   `joyconrobotics/*.py` files **replaced** by XLeRobot's modified
   versions (`payload/joyconrobotics_override/` in this repo) — the
   upstream files alone don't have the XLeRobot-specific pose mapping.
5. **Joy-Cons paired AND currently connected.** Pairing survives reboots;
   the *connection* does not — Joy-Cons auto-disconnect when idle and
   need a reconnect (button press or `bluetoothctl connect <mac>`) every
   session.
6. **Motor control boards powered on and enumerated** as `/dev/ttyACM0`
   / `/dev/ttyACM1` (two CH340 USB-serial adapters in `lsusb`), and your
   user in the `dialout` group (avoids needing `sudo chmod 666` each
   time).
7. **A calibration file** for the robot id used in the example scripts
   (default: `my_xlerobot`), at
   `~/.cache/huggingface/lerobot/calibration/robots/xlerobot/`. If it's
   missing, the first `robot.connect()` walks you through calibration —
   expected on a fresh setup, not a bug.

## Install (automated)

```bash
git clone <this-repo-url> Xlerobot-improvements
cd Xlerobot-improvements
./scripts/install.sh
```

See `scripts/install.sh` for exactly what it does; short version:
apt system deps → conda env `lerobot` (python 3.10) → editable
`lerobot` install → drop in the patched `xlerobot` robot class +
`SO101Robot` IK model → clone+build `joycon-robotics` (DKMS +
joycond + udev via its own `make install`) → overlay the
XLeRobot-modified `joyconrobotics/*.py` files.

## Manual steps (can't be scripted)

### Pair the Joy-Cons

1. Hold the small sync button on the Joy-Con (between SR/SL) until the
   single light starts flashing.
2. `bluetoothctl`:
   ```
   scan on
   pair <MAC>
   trust <MAC>
   connect <MAC>
   ```
   or use the system Bluetooth settings UI — look for "Joy-Con (L)" /
   "Joy-Con (R)".
3. Press **L** (left Joy-Con) and **R** (right Joy-Con) together —
   only the first LED should stay lit on each, meaning the connection
   succeeded.

Do this for **both** Joy-Cons; note their MAC addresses somewhere handy
(e.g. `bluetoothctl paired-devices`) since you'll need to reconnect them
each session.

### Reconnect each session

Joy-Cons idle-disconnect. Before running teleop:
```bash
bluetoothctl connect <left-mac>
bluetoothctl connect <right-mac>
# or just press a button on each Joy-Con and wait for the vibration
```

### Sanity-check the Joy-Con pipeline alone

```bash
conda activate lerobot
python payload/examples/joycon_test_read_CN.py   # or wherever install.sh placed the examples
```
Only exercises the **left** Joy-Con by default (hardcoded `device="left"`
in that script) — a clean run confirms pairing → HID → gyro calibration
→ live pose streaming end to end.

### Motor boards

```bash
ls -la /dev/ttyACM0 /dev/ttyACM1     # both should exist once boards are powered
lsusb                                 # look for two CH340 (or FTDI) serial adapters
python lerobot/find_port.py           # confirms which port is which bus
```

Default config (`config_xlerobot.py`): `port1=/dev/ttyACM0` = left arm +
head, `port2=/dev/ttyACM1` = right arm + base. If you get
`need 9 motors, but 8 detected`, the ports are swapped for this
particular pair's wiring — edit `port1`/`port2` in
`lerobot/src/lerobot/robots/xlerobot/config_xlerobot.py` (or copy
`payload/robots/xlerobot/config_xlerobot.py`, edit, and re-drop it in).

### Run it

```bash
cd Xlerobot-improvements   # or wherever the example scripts landed
python payload/examples/7_xlerobot_teleop_joycon.py
```

First run with no existing calibration for the configured robot id
walks through a calibration routine (move each joint through its range,
follow the Feetech-bus prompts) before teleop starts, then saves the
calibration so future runs skip straight to teleop.

## Known issues / fixes already applied here

See `docs/known_issues.md` for the flaky head-motor (ids 7/8)
`ConnectionError` crash and the soft-fail patch applied in
`payload/robots/xlerobot/xlerobot.py`.
