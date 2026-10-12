#!/usr/bin/env python3
"""Capture read-only Android screen evidence through an existing ADB connection."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def adb_base():
    executable = shutil.which("adb")
    if not executable:
        raise RuntimeError("adb is not installed or is not on PATH")
    return [executable]


def devices():
    completed = subprocess.run(adb_base() + ["devices", "-l"], capture_output=True, text=True, timeout=15, check=True)
    rows = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append({"serial": parts[0], "state": parts[1]})
    return rows


def choose_serial(requested):
    connected = [row["serial"] for row in devices() if row["state"] == "device"]
    if requested:
        if requested not in connected:
            raise RuntimeError("requested device is not connected and authorized")
        return requested
    if len(connected) != 1:
        raise RuntimeError("use --serial when zero or multiple authorized devices are connected")
    return connected[0]


def capture(serial, output):
    completed = subprocess.run(adb_base() + ["-s", serial, "exec-out", "screencap", "-p"], capture_output=True, timeout=30, check=True)
    if not completed.stdout.startswith(PNG_HEADER):
        raise RuntimeError("ADB did not return a PNG screenshot")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(completed.stdout)
    output.chmod(0o600)
    return {"serial": serial, "path": str(output.resolve()), "bytes": len(completed.stdout)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("devices")
    screenshot = commands.add_parser("screenshot")
    screenshot.add_argument("--serial")
    screenshot.add_argument("--out", type=Path, default=Path("private/current-screen.png"))
    args = parser.parse_args()
    try:
        result = devices() if args.command == "devices" else capture(choose_serial(args.serial), args.out)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
