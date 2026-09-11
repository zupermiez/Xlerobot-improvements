# CLAUDE.md

Context for Claude Code sessions opened in this repo.

## What this repo is

A companion to [XLeRobot](https://github.com/Vector-Wangel/XLeRobot) —
distilled setup for getting **Joy-Con and keyboard teleop** working on
an XLeRobot arm pair, built from real debugging on a first pair. This
repo exists to set up a **second arm pair fast**, reusing every fix and
gotcha already found, without re-deriving them.

## Situation when this repo was created

- A first XLeRobot pair (2 arms + head + omniwheel base) already works
  for Joy-Con and keyboard teleop, on an Ubuntu 22.04 x86_64 laptop —
  see `docs/environment.md` for the exact verified stack.
- Setting up a **second pair**, on either a Jetson Orin Nano or an
  **Ubuntu 20.04 laptop**. Decision: use the Ubuntu 20.04 laptop —
  same architecture as the reference setup, so this repo's recipe
  should apply close to verbatim. Full reasoning in
  `docs/environment.md` under "Jetson Orin Nano vs. Ubuntu 20.04
  laptop".
- The head motors (ids 7/8) on the first pair intermittently threw
  `ConnectionError` and crashed teleop — fixed by patching
  `payload/robots/xlerobot/xlerobot.py` to soft-fail on that specific
  bus instead of raising. That fix is already baked into the file
  shipped here — don't re-derive it, it's `git`-tracked in this repo.

## What to do when opened fresh in this repo on the new laptop

1. Check whether `./scripts/install.sh` has been run yet (look for a
   `lerobot/` checkout and a `lerobot` conda env next to this repo, at
   `$XLEROBOT_WORKDIR` — defaults to `~/codeprojects/LEROBOT`).
2. If not, walk the user through `./scripts/install.sh`, then the
   manual steps it prints (Bluetooth pairing, motor board power-up,
   `find_port.py`) — full detail in `docs/joycon_teleop_setup.md`.
3. If something breaks, run `./scripts/verify.sh` first — it checks
   every layer (conda env, python deps, DKMS driver, joycond, udev
   rules, Bluetooth pairing/connection, serial ports, calibration
   files) and will usually point straight at the broken layer.
4. Check `docs/known_issues.md` before treating a crash as new — the
   head-motor `ConnectionError` in particular is already fixed here,
   so if it recurs, check whether `payload/robots/xlerobot/xlerobot.py`
   actually got copied into the live `lerobot` checkout by
   `install.sh` (`lerobot/src/lerobot/robots/xlerobot/xlerobot.py`
   should match the version in this repo — diff them if unsure).
5. This repo's `payload/` is the source of truth for the robot
   class / IK model / joycon override / example scripts. If you fix
   something in the *live* installed copies (under the `lerobot` or
   `joycon-robotics` checkouts in `$XLEROBOT_WORKDIR`), copy the fix
   back into `payload/` here and commit it, so the next pair setup
   inherits it too. That's the whole point of this repo existing.

## Repo layout

```
scripts/install.sh   — automated setup (system deps, conda, lerobot,
                        joycon-robotics, drops in payload/)
scripts/verify.sh    — diagnostic health check
payload/robots/xlerobot/       — XLerobot robot class (patched)
payload/model/SO101Robot.py    — analytical IK solver dependency
payload/joyconrobotics_override/ — XLeRobot's modified joyconrobotics files
payload/examples/              — teleop entry-point scripts
docs/joycon_teleop_setup.md    — full Joy-Con recipe + manual steps
docs/keyboard_teleop_setup.md  — keyboard teleop recipe
docs/known_issues.md           — bugs found + fixes applied
docs/environment.md            — reference environment + Jetson-vs-laptop decision
```

## Conventions

- `payload/` files get copied verbatim into a `lerobot`/`joycon-robotics`
  checkout by `install.sh` — keep them drop-in compatible (no imports
  or paths specific to this repo's own layout).
- Don't hardcode Joy-Con Bluetooth MAC addresses anywhere in scripts or
  docs — each physical pair of controllers has its own, and they're
  gathered fresh via `bluetoothctl` during pairing.
- Default robot calibration id used across examples is `my_xlerobot`
  (see `XLerobotConfig(id="my_xlerobot")` in the example scripts) —
  keep that consistent unless there's a reason to run multiple pairs
  from the same machine with distinct ids.
