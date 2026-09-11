#!/usr/bin/env bash
# Quick health check for the joycon + arm teleop stack.
# Mirrors the diagnostic commands that found real issues during setup.
set -uo pipefail

echo "--- conda env ---"
conda info --envs 2>/dev/null | grep '*' || echo "no active conda env"
which python

echo "--- python deps ---"
python -c "import hid; print('hid OK')" 2>&1
python -c "import glm; print('glm OK')" 2>&1
python -c "import scipy; print('scipy OK')" 2>&1
python -c "import joyconrobotics; print('joyconrobotics OK', joyconrobotics.__file__)" 2>&1
python -c "import lerobot.robots.xlerobot as x; print('lerobot.robots.xlerobot OK', x.__file__)" 2>&1

echo "--- dkms (hid-nintendo kernel driver) ---"
dkms status 2>&1 | grep -i nintendo || echo "NOT installed for current kernel: $(uname -r)"

echo "--- joycond service ---"
systemctl is-enabled joycond 2>&1
systemctl is-active joycond 2>&1

echo "--- udev rules ---"
ls /usr/lib/udev/rules.d/ /etc/udev/rules.d/ 2>/dev/null | grep -i -E "joycond|nintendo|nitendo"

echo "--- bluetooth paired/connected ---"
bluetoothctl paired-devices 2>&1 | grep -i "joy-con" || echo "no Joy-Con paired yet"
for mac in $(bluetoothctl paired-devices 2>/dev/null | awk '/Joy-Con/{print $2}'); do
    bluetoothctl info "$mac" | grep -E "Name|Connected|Paired"
done

echo "--- serial ports (motor control boards) ---"
ls -la /dev/ttyACM* /dev/ttyUSB* 2>&1
lsusb 2>&1 | grep -iE "ch340|ftdi|serial" || echo "no USB serial adapter detected"

echo "--- dialout group (needed for serial port access without chmod) ---"
id -nG | grep -qw dialout && echo "IN dialout group" || echo "NOT in dialout group -- run: sudo usermod -aG dialout \$USER, then log out/in"

echo "--- calibration files ---"
ls -la "$HOME/.cache/huggingface/lerobot/calibration/robots/xlerobot/" 2>&1 || echo "none yet -- first teleop run will calibrate"
