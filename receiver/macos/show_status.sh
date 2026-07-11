#!/bin/sh
set -eu

DROP_DIR="${PIDROP_DIR:-$HOME/PiDrop}"
STATUS_FILE="$DROP_DIR/.pi_transfer_status.json"
HEARTBEAT_FILE="$DROP_DIR/.pi_heartbeat"

while true; do
  clear
  printf "\033[36mPiDrop Mac receiver - live status\033[0m\n"
  echo "Closing this window does NOT stop receiving files."
  echo

  python3 - "$STATUS_FILE" "$HEARTBEAT_FILE" <<'PY'
import json
import os
import sys
import time

status_file, heartbeat_file = sys.argv[1], sys.argv[2]
now = time.time()

def age_text(age):
    if age < 60:
        return f"{age:.0f} seconds ago"
    if age < 3600:
        return f"{age / 60:.1f} minutes ago"
    return f"{age / 3600:.1f} hours ago"

def fresh(path, seconds=30):
    try:
        return now - os.path.getmtime(path) <= seconds
    except OSError:
        return False

heartbeat_fresh = fresh(heartbeat_file)
status_fresh = fresh(status_file)
connected = heartbeat_fresh or status_fresh

if connected:
    print("\033[32mRaspberry Pi: CONNECTED\033[0m")
else:
    print("\033[31mRaspberry Pi: DISCONNECTED\033[0m")
print()

if not os.path.exists(status_file):
    print("Waiting for the Raspberry Pi to start a transfer...")
    sys.exit(0)

try:
    with open(status_file, encoding="utf-8") as handle:
        status = json.load(handle)
except Exception:
    print("Status is being updated. Retrying...")
    sys.exit(0)

state = status.get("state", "")
status_age = now - os.path.getmtime(status_file)
if status_fresh:
    print(f"Status:    {state}")
else:
    print(f"\033[33mStatus:    LAST KNOWN - {state}\033[0m")
    print("\033[33mNote:      Status is stale; Raspberry Pi is not updating right now.\033[0m")

gb = 1024 ** 3
print(f"Receiver:  {status.get('receiver', '')}")
print(f"File:      {status.get('filename', '')}")
print(f"Progress:  {status.get('percent', 0)}%")
print(f"Received:  {status.get('sent_bytes', 0) / gb:.2f} GB")
print(f"Remaining: {status.get('remaining_bytes', 0) / gb:.2f} GB")
print(f"Updated:   {status.get('updated', '')}")
print(f"Age:       {age_text(status_age)}")
PY

  echo
  echo "Press Ctrl+C to close status."
  sleep 2
done
