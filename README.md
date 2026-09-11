# Xlerobot-improvements

Distilled, known-working setup for getting **Joy-Con and keyboard
teleop** running on an [XLeRobot](https://github.com/Vector-Wangel/XLeRobot)
arm pair — plus the fixes and gotchas discovered getting the first pair
working, so a second (or third) pair can be set up fast instead of
re-discovering the same issues.

This is a companion to the main XLeRobot project, not a replacement —
see that repo for hardware assembly, full docs, simulation, and every
other teleop mode. This repo exists purely to make **"clone this, run
one script, plug in the hardware, teleop works"** true.

## Quick start

```bash
git clone <this-repo-url> Xlerobot-improvements
cd Xlerobot-improvements
./scripts/install.sh
```

Then follow the printed next steps (Bluetooth pairing, plugging in
motor boards — these are physical steps that can't be scripted). Full
detail in `docs/joycon_teleop_setup.md` and `docs/keyboard_teleop_setup.md`.

Check your setup at any point with:
```bash
./scripts/verify.sh
```

## What's in here

- `scripts/install.sh` — end-to-end setup: system deps, conda env,
  `lerobot` editable install, `joycon-robotics` build (DKMS driver +
  joycond + udev rules), and drops in everything below.
- `scripts/verify.sh` — diagnostic script checking every layer of the
  stack (conda env, python deps, DKMS, joycond, udev rules, Bluetooth,
  serial ports, calibration).
- `payload/robots/xlerobot/` — the `XLerobot` robot class, **already
  patched** to soft-fail on flaky head-motor (ids 7/8) connections
  instead of crashing teleop (see `docs/known_issues.md`).
- `payload/model/SO101Robot.py` — the analytical IK solver the arm
  control depends on.
- `payload/joyconrobotics_override/` — XLeRobot's modified
  `joyconrobotics` package files, layered on top of the upstream
  box2ai `joycon-robotics` install.
- `payload/examples/` — the teleop entry-point scripts
  (`7_xlerobot_teleop_joycon.py`, `4_xlerobot_teleop_keyboard.py`,
  `joycon_test_read_CN.py`).
- `docs/` — the actual knowledge: setup recipes, known issues and
  their fixes, and the reference environment this was all verified
  against.
- `CLAUDE.md` — context for Claude Code so a fresh session in this repo
  can pick up immediately without re-deriving any of this.

## Known issues already fixed here

- **Head motors (ids 7/8) crashing teleop on a flaky connection** —
  now soft-fails with a warning instead of raising. See
  `docs/known_issues.md`.

## License

MIT — see `LICENSE`.
