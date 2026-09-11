#!/usr/bin/env bash
# Xlerobot-improvements install script
#
# Sets up a second XLeRobot arm pair for Joy-Con / keyboard teleop on a fresh
# Ubuntu 20.04/22.04 x86_64 machine, reproducing the exact working setup
# documented in docs/. Safe to re-run (mostly idempotent).
#
# Usage:
#   ./scripts/install.sh                 # full install
#   SKIP_SYSTEM_DEPS=1 ./scripts/install.sh   # skip apt steps (e.g. re-run after reboot)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="${XLEROBOT_WORKDIR:-$HOME/codeprojects/LEROBOT}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-lerobot}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
LEROBOT_GIT_URL="${LEROBOT_GIT_URL:-https://github.com/huggingface/lerobot.git}"
JOYCON_GIT_URL="https://github.com/box2ai-robotics/joycon-robotics.git"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "==> 1/7 System packages (dkms build deps, hid libs, bluetooth)"
if [ -z "${SKIP_SYSTEM_DEPS:-}" ]; then
    sudo apt-get update
    sudo apt-get install -y \
        dkms libevdev-dev libudev-dev cmake git build-essential \
        libhidapi-dev libhidapi-hidraw0 libhidapi-libusb0 \
        bluetooth bluez linux-headers-"$(uname -r)"
else
    echo "    (skipped, SKIP_SYSTEM_DEPS set)"
fi

echo "==> 2/7 Conda env ($CONDA_ENV_NAME, python $PYTHON_VERSION)"
if ! command -v conda >/dev/null 2>&1; then
    echo "    conda not found. Install miniforge first:"
    echo "    curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
    echo "    bash Miniforge3-Linux-x86_64.sh"
    exit 1
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
if ! conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    conda create -y -n "$CONDA_ENV_NAME" "python=$PYTHON_VERSION"
fi
conda activate "$CONDA_ENV_NAME"

echo "==> 3/7 lerobot (editable install)"
if [ ! -d lerobot ]; then
    git clone "$LEROBOT_GIT_URL" lerobot
fi
cd lerobot
pip install -e .
cd "$WORKDIR"

echo "==> 4/7 Drop in XLeRobot's xlerobot robot class + IK model (with the flaky-head-motor soft-fail patch already applied)"
mkdir -p lerobot/src/lerobot/robots/xlerobot
cp "$REPO_ROOT"/payload/robots/xlerobot/*.py lerobot/src/lerobot/robots/xlerobot/
mkdir -p lerobot/src/lerobot/model
cp "$REPO_ROOT"/payload/model/SO101Robot.py lerobot/src/lerobot/model/

echo "==> 5/7 joycon-robotics (kernel driver + joycond + udev rules)"
if [ ! -d joycon-robotics ]; then
    git clone "$JOYCON_GIT_URL" joycon-robotics
fi
cd joycon-robotics
pip install -e .
sudo make install   # builds+installs hid-nintendo DKMS module, joycond daemon+service, udev rules
cd "$WORKDIR"

echo "==> 6/7 Overlay XLeRobot's modified joyconrobotics/*.py on top of the pip-installed package"
cp "$REPO_ROOT"/payload/joyconrobotics_override/*.py joycon-robotics/joyconrobotics/

echo "==> 7/7 Copy example scripts into place for quick access"
mkdir -p Xlerobot-improvements-examples
cp "$REPO_ROOT"/payload/examples/*.py Xlerobot-improvements-examples/

cat <<'EOF'

==================================================================
Install steps done. Remaining steps are physical / interactive and
can't be scripted -- see docs/joycon_teleop_setup.md for details:

  1. Pair each Joy-Con over Bluetooth (sync button -> bluetoothctl
     pair -> press L+R together to confirm).
  2. Run the connectivity check:
       conda activate lerobot
       python Xlerobot-improvements-examples/joycon_test_read_CN.py
  3. Plug in / power on the motor control boards, then:
       ls /dev/ttyACM0 /dev/ttyACM1
       python lerobot/find_port.py     # confirm port -> arm mapping
     (defaults: port1=/dev/ttyACM0=left arm+head, port2=/dev/ttyACM1=right arm+base;
      edit lerobot/src/lerobot/robots/xlerobot/config_xlerobot.py if swapped)
  4. Run teleop (first run walks through calibration for robot id my_xlerobot):
       python Xlerobot-improvements-examples/7_xlerobot_teleop_joycon.py
==================================================================
EOF
