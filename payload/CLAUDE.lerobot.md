# CLAUDE.md

Context for Claude Code sessions opened in this `lerobot` checkout.

## What this checkout is

Upstream [huggingface/lerobot](https://github.com/huggingface/lerobot)
(v0.4.1 on the reference machine), `pip install -e .`'d into the conda
env `lerobot` (python 3.10), with **XLeRobot** files layered on top that
are *not* upstream:

- `src/lerobot/robots/xlerobot/` — 3-omniwheel XLeRobot (head-motor soft-fail patch)
- `src/lerobot/robots/xlerobot_2wheels/` — 2-wheel differential-drive variant
- `src/lerobot/robots/xlerobot_mecanum/` — mecanum variant (stock XLeRobot, unused)
- `src/lerobot/model/SO101Robot.py` — analytical IK used by the teleop examples
- `examples/[0-8]_*.py`, `examples/joycon_*.py` — XLeRobot teleop scripts
- `src/lerobot/utils/robot_utils.py` — one-line `precise_sleep = busy_wait` shim
  (XLeRobot code imports `precise_sleep`, which 0.4.1 doesn't have)

These show up as untracked/modified in `git status` — that's expected.

**Source of truth is the sibling repo
[Xlerobot-improvements](https://github.com/zupermiez/Xlerobot-improvements)**
(`../Xlerobot-improvements/payload/`). Its `scripts/install.sh` clones this
checkout, drops the payload in, and installs `joycon-robotics` + the Joy-Con
kernel driver. If you fix something here, copy it back into that repo's
`payload/` and commit/push there — otherwise the next machine loses the fix.

## Getting started on a new machine

```bash
git clone https://github.com/zupermiez/Xlerobot-improvements ~/codeprojects/LEROBOT/Xlerobot-improvements
cd ~/codeprojects/LEROBOT/Xlerobot-improvements
./scripts/install.sh      # system deps, conda env, lerobot, joycon-robotics, payload
./scripts/verify.sh       # checks every layer; run this first when something breaks
```

Then the manual steps it prints: pair Joy-Cons via `bluetoothctl`, power the
motor boards, confirm ports. Details in `../Xlerobot-improvements/docs/`.

Always `conda activate lerobot` before running anything.

## Hardware layout (reference robot — 2-wheel base)

Feetech STS3215 servos, two USB buses at 1 Mbps:

| Port | Bus | Motors |
|---|---|---|
| `/dev/ttyACM0` | bus1 (`port1`) | left arm IDs 1–6, head IDs 7–8 |
| `/dev/ttyACM1` | bus2 (`port2`) | right arm IDs 1–6, left wheel ID 9, right wheel ID 10 |

If the ports enumerate swapped, fix `port1`/`port2` in the robot's config file
(`config_xlerobot_2wheels.py` / `config_xlerobot.py`) rather than replugging.
`lerobot-find-port` identifies which board is which.

Calibration files live in `~/.cache/huggingface/lerobot/calibration/robots/<robot_type>/<id>.json`
and are **not** in git — copy them over or recalibrate on a new machine
(the first run of a teleop script walks through calibration).

## Running teleop

```bash
conda activate lerobot
python examples/7_xlerobot_2wheels_teleop_joycon.py        # 2-wheel, Joy-Con (id my_xlerobot_2wheels_lab)
python examples/7_xlerobot_2wheels_teleop_joycon_smooth.py # same, with smoothed base accel
python examples/4_xlerobot_2wheels_teleop_keyboard.py      # 2-wheel, keyboard
python examples/7_xlerobot_teleop_joycon.py                # 3-omniwheel, Joy-Con (id my_xlerobot)
python examples/joycon_test_read_CN.py                     # Joy-Con connectivity check only
```

Pick the `xlerobot_2wheels` scripts for a robot with 2 base wheels — the
3-omniwheel `xlerobot` class expects a third wheel motor and fails on connect.

## Gotchas

- **Joy-Cons drop off Bluetooth when idle.** Pairing persists; the connection
  doesn't. `bluetoothctl connect <mac>` or press a button. Check
  `/sys/class/hidraw/*/device/uevent` (`HID_NAME`) to see which are live.
  Don't hardcode Joy-Con MACs in code — each controller pair differs.
- **Joy-Con hidraw permissions** come from `/etc/udev/rules.d/99-nitendo.rules`
  (upstream typo in the name) installed by `joycon-robotics`' `make install`.
- **`hid-nintendo` is a DKMS module** — rebuild after a kernel update
  (`sudo dkms autoinstall`) or Joy-Cons won't show up.
- **Serial permissions:** user must be in the `dialout` group.
- **Head motors 7/8 flaky** → already soft-failed in `xlerobot/xlerobot.py`;
  see `docs/known_issues.md` in Xlerobot-improvements before debugging a crash.
- **2-wheel base:** wheel motors are in velocity mode and don't support the
  Lock register, so `configure()` enables torque on the right-arm motors only
  on bus2; upstream XLeRobot also configured bus2 twice and never bus1 — both
  fixed in this checkout's `xlerobot_2wheels.py`.
- `joyconrobotics` is an editable install from `../joycon-robotics/joycon-robotics`
  with XLeRobot's modified `*.py` overlaid — reinstalling it from PyPI loses that.

## Upstream lerobot conventions

For non-XLeRobot work, upstream rules apply: code in `src/lerobot/`, tests in
`tests/` (`pytest tests/...`), lint with `pre-commit run --all-files` (ruff).
Robots register via `RobotConfig.register_subclass("<name>")` in their config
file and subclass `lerobot.robots.Robot`.
