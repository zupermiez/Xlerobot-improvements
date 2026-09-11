# Keyboard teleop setup

Much simpler than Joy-Con — no Bluetooth, no DKMS driver, no daemon.

## Requirements

- Same `lerobot` conda env + editable install as Joy-Con setup
  (see `docs/joycon_teleop_setup.md`), including the patched
  `xlerobot` robot class in `payload/robots/xlerobot/` and the
  `SO101Robot` IK model in `payload/model/`.
- `lerobot`'s `pynput`-based `KeyboardTeleop` (pulled in automatically
  by the editable `lerobot` install).
- Motor control boards powered on, `/dev/ttyACM0`/`/dev/ttyACM1`
  present, ports confirmed with `python lerobot/find_port.py` (see
  the Joy-Con doc for the full port-mapping gotcha).
- **Both arms of the pair physically connected** before running —
  the script expects the full two-arm + head + base config; running
  with only one arm connected will fail or behave oddly (this bit us
  once — don't try to test with just one arm plugged in).

## Run it

```bash
conda activate lerobot
cd Xlerobot-improvements
python payload/examples/4_xlerobot_teleop_keyboard.py
```

First run with no calibration for the configured robot id
(`my_xlerobot` by default) walks through calibration before teleop
starts.

## Key mappings

Separate key groups for left arm, right arm, base movement, and head —
see the script header comments in
`payload/examples/4_xlerobot_teleop_keyboard.py` for the exact keys;
they're defined in `KeyboardTeleopConfig`/the script's local key maps
rather than duplicated here to avoid drift.
