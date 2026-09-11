# Reference environment (first working pair)

Captured from the machine where the first arm pair's teleop was
verified working, for comparison if something behaves differently on
the second pair's machine.

| | |
|---|---|
| OS | Ubuntu 22.04.5 LTS, x86_64 |
| Kernel | 6.8.0-138-generic (dkms `hid-nintendo` module built for this exact kernel string — rebuild after kernel updates) |
| Conda | miniforge3, env name `lerobot`, python 3.10.19 |
| `lerobot` | v0.4.1, editable install from a git checkout, `xlerobot` robot class layered in manually (not upstream) |
| `joycon-robotics` (box2ai) | v0.0.2, editable install, `joyconrobotics/*.py` overridden with XLeRobot's modified versions |
| `hid` (pyhidapi) | v1.0.4 |
| DKMS | `nintendo/3.2` |
| `joycond` | built from the bundled source in `joycon-robotics`'s `make install` (not the apt package — `dpkg -S` found no matching package on this machine) |
| udev rules | `/usr/lib/udev/rules.d/{72,89}-joycond.rules` (from joycond build) + a `99-nitendo.rules` (note the upstream typo — matches `udev/99-nitendo.rules` in the `joycon-robotics` repo) |

## Jetson Orin Nano vs. Ubuntu 20.04 laptop for a second pair

Decision made: **use the Ubuntu 20.04 laptop** — same x86_64
architecture as the reference setup above, so this whole recipe applies
close to verbatim. Reasoning, for future reference:

| | x86_64 Ubuntu laptop | Jetson Orin Nano (aarch64) |
|---|---|---|
| Python wheels (torch, opencv, PyGLM, hid bindings, etc.) | Prebuilt on PyPI, "just work" | Frequently no aarch64 wheel — need NVIDIA JetPack-specific builds or compile from source |
| `hid-nintendo` DKMS build | Standard `linux-headers-$(uname -r)` via apt | Custom L4T kernel — generic headers package often unavailable; may need NVIDIA's kernel source for your exact JetPack version |
| Bluetooth | Laptop's built-in adapter, works out of the box | Devkit carrier usually has an M.2 WiFi/BT card, but custom carriers sometimes don't — check first |
| Reference to copy from | This repo, directly | None — first-timing every gotcha |

Jetson's advantage (onboard GPU for later policy inference) is
irrelevant to just getting teleop running, and the architecture
mismatch plus custom kernel is exactly the combination that turns a
quick setup into a half-day of wheel-hunting. Revisit Jetson once
teleop-only setups are boring and the goal shifts to onboard inference.
