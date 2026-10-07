"""
Get one left + one right Joy-Con connected and holding. Several Joy-Cons share
the same name, so it tries every paired one, keeps reconnecting when they drop,
and the first of each side that streams input for HOLD_S seconds wins; the
other same-side ones are then ignored (unless the winner drops). Sets player LEDs so you can tell them apart:
  L#1 -> LED 1, R#1 -> LED 2, L#2 -> LED 3, R#2 -> LED 4

Run: conda activate lerobot && python examples/joycon_connect_test.py
"""

import re
import subprocess
import sys
import time

import hid

HOLD_S = 5.0
REPORT_TIMEOUT_S = 1.0  # no input report for this long => considered dropped
CONNECT_RETRY_S = 6.0
EXTRA_MONITOR_S = 30.0  # keep watching this long after all succeeded
TOTAL_TIMEOUT_S = 600.0
NINTENDO_VID = 0x057E
RUMBLE_NEUTRAL = bytes([0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40])


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def norm_mac(s):
    return re.sub(r"[^0-9a-f]", "", (s or "").lower())


def paired_joycons():
    out = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True).stdout
    devs = []
    for line in out.splitlines():
        m = re.match(r"Device ([0-9A-F:]{17}) (Joy-Con \((L|R)\))", line.strip())
        if m:
            devs.append((m.group(1), m.group(3)))
    return devs


def bt_connected(mac):
    out = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True).stdout
    return "Connected: yes" in out


class JoyCon:
    def __init__(self, mac, side, label, led):
        self.mac, self.side, self.label, self.led = mac, side, label, led
        self.dev = None
        self.connect_proc = None
        self.last_connect_try = 0.0
        self.stream_start = None
        self.last_report = None
        self.counter = 0
        self.succeeded = False
        self.drops = 0
        self.open_time = 0.0
        self.last_check = 0.0

    def name(self):
        return f"{self.label} ({self.mac})"

    def subcmd(self, cmd, args=b""):
        pkt = bytes([0x01, self.counter & 0xF]) + RUMBLE_NEUTRAL + bytes([cmd]) + args
        self.counter += 1
        self.dev.write(pkt)

    def close(self, reason):
        if self.dev is not None:
            try:
                self.dev.close()
            except Exception:
                pass
            self.dev = None
            if self.stream_start is not None:
                held = time.time() - self.stream_start
                self.drops += 1
                log(f"DROP    {self.name()}: {reason} (held {held:.1f}s, drops={self.drops})")
        self.stream_start = None
        self.last_report = None

    def try_bt_connect(self):
        if self.connect_proc is not None and self.connect_proc.poll() is None:
            return
        if time.time() - self.last_connect_try < CONNECT_RETRY_S:
            return
        self.last_connect_try = time.time()
        self.connect_proc = subprocess.Popen(
            ["timeout", "10", "bluetoothctl", "connect", self.mac],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def try_open(self):
        target = norm_mac(self.mac)
        for d in hid.enumerate(NINTENDO_VID):
            if norm_mac(d.get("serial_number")) == target:
                try:
                    dev = hid.device()
                    dev.open_path(d["path"])
                    dev.set_nonblocking(True)
                except Exception as e:
                    log(f"open failed {self.name()} {d['path']}: {e}")
                    return
                self.dev = dev
                self.open_time = time.time()
                try:
                    self.subcmd(0x03, b"\x30")  # full input report mode (60Hz stream)
                    time.sleep(0.03)
                    self.subcmd(0x30, bytes([1 << (self.led - 1)]))  # player LED
                except Exception as e:
                    self.close(f"write failed: {e}")
                    return
                log(f"OPENED  {self.name()} on {d['path'].decode()}")
                return

    def poll(self):
        now = time.time()
        if self.dev is None:
            if now - self.last_check < 0.5:
                return
            self.last_check = now
            if bt_connected(self.mac):
                self.try_open()
            else:
                self.try_bt_connect()
            return
        try:
            got = False
            while True:
                data = self.dev.read(64)
                if not data:
                    break
                got = True
        except Exception as e:
            self.close(f"read error: {e}")
            return
        if got:
            self.last_report = now
            if self.stream_start is None:
                self.stream_start = now
        elif self.last_report is None:
            if now - self.open_time > 3:
                self.close("opened but no input reports within 3s")
            return
        if self.last_report and now - self.last_report > REPORT_TIMEOUT_S:
            self.close(f"no input for {REPORT_TIMEOUT_S}s")
            return
        if not self.succeeded and self.stream_start and now - self.stream_start >= HOLD_S:
            self.succeeded = True
            log(f"SUCCESS {self.name()} held {HOLD_S:.0f}s (LED {self.led})")


def main():
    devs = paired_joycons()
    if not devs:
        log("No paired Joy-Cons found in bluetoothctl.")
        sys.exit(1)
    counts = {"L": 0, "R": 0}
    order = {("L", 1): 1, ("R", 1): 2, ("L", 2): 3, ("R", 2): 4}
    jcs = []
    for mac, side in devs:
        counts[side] += 1
        n = counts[side]
        jcs.append(JoyCon(mac, side, f"{side}#{n}", order.get((side, n), 4)))
    log("Watching: " + ", ".join(j.name() for j in jcs))
    log("READY - power on the Joy-Cons (press a button / sync).")

    t0 = time.time()
    all_done_at = None
    last_status = 0.0
    winner = {"L": None, "R": None}
    while True:
        for side in winner:
            w = winner[side]
            if w is not None and w.dev is None:
                log(f"LOST    {side} winner {w.name()}, retrying all {side} Joy-Cons")
                w.succeeded = False
                winner[side] = None
        for j in jcs:
            w = winner[j.side]
            if w is not None and w is not j:
                if j.dev is not None:
                    j.close(f"{j.side} side already held by {w.label}")
                continue
            j.poll()
            if j.succeeded and winner[j.side] is None:
                winner[j.side] = j
                log(f"WINNER  {j.side}: {j.name()}")
        now = time.time()
        if now - last_status > 10:
            last_status = now
            parts = []
            for j in jcs:
                st = "streaming %.0fs" % (now - j.stream_start) if j.stream_start else ("open" if j.dev else "waiting")
                parts.append(f"{j.label}:{st}{' OK' if j.succeeded else ''} d{j.drops}")
            log("status  " + " | ".join(parts))
        if all_done_at is None and winner["L"] and winner["R"]:
            all_done_at = now
            log(f"PAIR READY: L={winner['L'].name()} R={winner['R'].name()}. "
                f"Monitoring {EXTRA_MONITOR_S:.0f}s more for drops...")
        elif all_done_at and not (winner["L"] and winner["R"]):
            all_done_at = None
        if all_done_at and now - all_done_at > EXTRA_MONITOR_S:
            break
        if now - t0 > TOTAL_TIMEOUT_S:
            log("Timeout.")
            break
        time.sleep(0.01)

    log("FINAL: " + " | ".join(f"{j.name()} success={j.succeeded} drops={j.drops}" for j in jcs))
    for side, w in winner.items():
        log(f"FINAL {side}: {w.name() if w else 'none held'}")
    for j in jcs:
        j.close("exit")


if __name__ == "__main__":
    main()
