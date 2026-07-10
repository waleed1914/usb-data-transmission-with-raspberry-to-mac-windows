#!/usr/bin/env python3
"""Copy new files from removable USB volumes to a mounted SMB destination."""

import json
import hashlib
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("PI_TRANSFER_CONFIG", "/etc/pi-usb-transfer/config.json"))
STATE_PATH = Path("/var/lib/pi-usb-transfer/batches.json")
LOG = logging.getLogger("pi-usb-transfer")
running = True


class StatusDisplay:
    def __init__(self, config):
        self.device = None
        self.canvas = None
        if not config.get("enabled", True):
            return
        try:
            from luma.core.interface.serial import i2c
            from luma.core.render import canvas
            from luma.oled.device import sh1106

            address = int(str(config.get("i2c_address", "0x3C")), 0)
            self.device = sh1106(
                i2c(port=1, address=address),
                width=int(config.get("width", 128)),
                height=int(config.get("height", 64)),
                rotate=int(config.get("rotate", 0)),
            )
            self.canvas = canvas
        except Exception as exc:
            LOG.warning("OLED unavailable: %s", exc)

    def show(self, title, line1="", line2="", progress=None):
        LOG.info("%s | %s | %s", title, line1, line2)
        if not self.device:
            return
        with self.canvas(self.device) as draw:
            draw.text((0, 0), str(title)[:21], fill="white")
            draw.text((0, 16), str(line1)[:21], fill="white")
            draw.text((0, 30), str(line2)[:21], fill="white")
            if progress is not None:
                value = max(0.0, min(1.0, progress))
                draw.rectangle((0, 51, 127, 62), outline="white")
                draw.rectangle((2, 53, 2 + int(123 * value), 60), fill="white")


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def mounted(path):
    return os.path.ismount(path)


def mount_share(destination):
    point = Path(destination["mount_point"])
    point.mkdir(parents=True, exist_ok=True)
    if mounted(point):
        return True
    options = [
        f"username={destination['username']}",
        f"password={destination['password']}",
        "vers=3.0",
        "iocharset=utf8",
        "rw",
        "noserverino",
        f"uid={os.getuid()}",
        f"gid={os.getgid()}",
    ]
    if destination.get("domain"):
        options.append(f"domain={destination['domain']}")
    try:
        subprocess.run(
            ["mount", "-t", "cifs", destination["share"], str(point), "-o", ",".join(options)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        LOG.warning("SMB mount failed: %s", exc.stderr.strip())
        return False


def usb_volumes(config):
    volumes = []
    destinations = {
        Path(item["mount_point"]).resolve() for item in config["destinations"]
    }
    for root_text in config["usb_roots"]:
        root = Path(root_text)
        if not root.is_dir():
            continue
        for candidate in root.iterdir():
            try:
                if candidate.is_dir() and candidate.resolve() not in destinations and mounted(candidate):
                    volumes.append(candidate)
            except OSError:
                pass
    return volumes


def same_file(source, destination, progress_callback=None):
    try:
        source_stat = source.stat()
        dest_stat = destination.stat()
        if source_stat.st_size != dest_stat.st_size:
            return False
        source_hash = file_hash(source, progress_callback)
        dest_hash = file_hash(destination, progress_callback)
        return source_hash == dest_hash
    except OSError:
        return False


def file_hash(path, progress_callback=None):
    digest = hashlib.sha256()
    done = 0
    last_update = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            done += len(block)
            if progress_callback:
                now = time.monotonic()
                if now - last_update >= 1:
                    progress_callback(path, done)
                    last_update = now
    if progress_callback:
        progress_callback(path, done)
    return digest.digest()


def data_size(value):
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f}{unit}" if unit != "B" else f"{int(amount)}B"
        amount /= 1024


def write_status(mount_point, receiver, state, filename="", sent=0, remaining=0, percent=0):
    status_path = Path(mount_point) / ".pi_transfer_status.json"
    temporary = status_path.with_suffix(".tmp")
    payload = {
        "receiver": receiver,
        "state": state,
        "filename": filename,
        "sent_bytes": sent,
        "remaining_bytes": remaining,
        "percent": round(percent, 1),
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        temporary.replace(status_path)
    except OSError as exc:
        LOG.debug("Could not update receiver status: %s", exc)


def write_heartbeat(destination):
    heartbeat = Path(destination["mount_point"]) / ".pi_heartbeat"
    temporary = heartbeat.with_suffix(".tmp")
    try:
        temporary.write_text(
            json.dumps(
                {
                    "receiver": destination["name"],
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            ),
            encoding="utf-8",
        )
        temporary.replace(heartbeat)
    except OSError as exc:
        LOG.debug("Could not update heartbeat: %s", exc)


def source_files(volume):
    for root, dirs, files in os.walk(volume):
        dirs[:] = [name for name in dirs if not name.startswith(".")]
        for name in files:
            if not name.startswith("."):
                yield Path(root) / name


def volume_id(volume):
    try:
        result = subprocess.run(
            ["findmnt", "-no", "UUID", "--target", str(volume)],
            check=True,
            capture_output=True,
            text=True,
        )
        uuid = result.stdout.strip()
        if uuid:
            return uuid
    except (OSError, subprocess.CalledProcessError):
        pass
    return f"name-{volume.name}"


def safe_name(value):
    cleaned = "".join(char if char.isalnum() or char in "-_" else "_" for char in value)
    return cleaned.strip("_") or "USB"


def load_batches():
    try:
        with STATE_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save_batches(batches):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(batches, handle, indent=2)
    temporary.replace(STATE_PATH)


def batch_for(volume, batches):
    identifier = volume_id(volume)
    if identifier not in batches:
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        batches[identifier] = f"{timestamp}_{safe_name(volume.name)}"
        save_batches(batches)
    return batches[identifier]


def copy_one(source, destination, destination_config, display, sent_before, total_bytes):
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    size = source.stat().st_size
    copied = 0
    try:
        with source.open("rb") as src, partial.open("wb") as dst:
            while True:
                block = src.read(1024 * 1024)
                if not block:
                    break
                dst.write(block)
                copied += len(block)
                sent = sent_before + copied
                remaining = max(0, total_bytes - sent)
                percent = sent * 100 / max(total_bytes, 1)
                display.show(
                    f"Sent {data_size(sent)}",
                    source.name,
                    f"Left {data_size(remaining)}",
                    sent / max(total_bytes, 1),
                )
                write_status(
                    destination_config["mount_point"],
                    destination_config["name"],
                    "TRANSFERRING",
                    source.name,
                    sent,
                    remaining,
                    percent,
                )
            dst.flush()
            os.fsync(dst.fileno())
        shutil.copystat(source, partial)
        partial.replace(destination)
        # Read the file back through SMB. Success means source and receiver
        # contain exactly the same bytes, not merely the same filename/size.
        sent = sent_before + size
        remaining = max(0, total_bytes - sent)
        percent = sent * 100 / max(total_bytes, 1)

        def verifying_status(_path, _done):
            display.show(
                "VERIFYING",
                source.name,
                f"Left {data_size(remaining)}",
                sent / max(total_bytes, 1),
            )
            write_status(
                destination_config["mount_point"],
                destination_config["name"],
                "VERIFYING",
                source.name,
                sent,
                remaining,
                percent,
            )

        verifying_status(source, 0)
        if file_hash(source, verifying_status) != file_hash(destination, verifying_status):
            destination.unlink(missing_ok=True)
            raise IOError(f"SHA-256 verification failed for {source.name}")
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def transfer_volume(volume, destination_config, batch_name, display):
    destination_root = Path(destination_config["mount_point"]) / batch_name
    files = list(source_files(volume))
    pending = []
    skipped = 0
    skipped_bytes = 0
    for source in files:
        destination = destination_root / source.relative_to(volume)
        if destination.exists():
            display.show(
                "VERIFY EXISTING",
                source.name,
                "Checking receiver",
            )
            write_status(
                destination_config["mount_point"],
                destination_config["name"],
                "VERIFYING EXISTING FILE",
                source.name,
                sent=skipped_bytes,
                remaining=0,
                percent=0,
            )

        def existing_status(_path, _done):
            write_status(
                destination_config["mount_point"],
                destination_config["name"],
                "VERIFYING EXISTING FILE",
                source.name,
                sent=skipped_bytes,
                remaining=0,
                percent=0,
            )

        if same_file(source, destination, existing_status):
            skipped += 1
            skipped_bytes += source.stat().st_size
            display.show(
                "SKIPPING",
                source.name,
                "Already verified",
            )
            write_status(
                destination_config["mount_point"],
                destination_config["name"],
                "SKIPPING - ALREADY EXISTS",
                source.name,
                sent=skipped_bytes,
                remaining=0,
                percent=100,
            )
        else:
            pending.append((source, destination))

    if not pending:
        write_status(
            destination_config["mount_point"],
            destination_config["name"],
            "COMPLETE - ALREADY VERIFIED",
            sent=0,
            remaining=0,
            percent=100,
        )
        display.show(
            f"{destination_config['name']}: copied",
            volume.name,
            f"{skipped} files skipped",
            1,
        )
        return

    total_bytes = sum(source.stat().st_size for source, _ in pending)
    sent_bytes = 0
    write_status(
        destination_config["mount_point"],
        destination_config["name"],
        "STARTING",
        sent=0,
        remaining=total_bytes,
        percent=0,
    )
    for source, destination in pending:
        if not running:
            return
        last_error = None
        for attempt in range(1, 4):
            try:
                copy_one(
                    source,
                    destination,
                    destination_config,
                    display,
                    sent_bytes,
                    total_bytes,
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                LOG.warning(
                    "Copy/verify attempt %d failed for %s: %s", attempt, source, exc
                )
                display.show(
                    f"VERIFY RETRY {attempt}/3",
                    source.name,
                    "Resending file",
                    sent_bytes / max(total_bytes, 1),
                )
                write_status(
                    destination_config["mount_point"],
                    destination_config["name"],
                    f"VERIFY RETRY {attempt}/3",
                    source.name,
                    sent_bytes,
                    max(0, total_bytes - sent_bytes),
                    sent_bytes * 100 / max(total_bytes, 1),
                )
        if last_error:
            raise last_error
        sent_bytes += source.stat().st_size
    display.show(
        f"{destination_config['name']}: complete",
        f"Sent {data_size(sent_bytes)}",
        f"Verified; {skipped} skip",
        1,
    )
    write_status(
        destination_config["mount_point"],
        destination_config["name"],
        "COMPLETE AND VERIFIED",
        sent=sent_bytes,
        remaining=0,
        percent=100,
    )


def connection_screen(display, states, usb_waiting=False):
    names = list(states)
    first = f"{names[0]}: {'CONNECTED' if states[names[0]] else 'DISCONNECTED'}"
    second = ""
    if len(names) > 1:
        second = f"{names[1]}: {'CONNECTED' if states[names[1]] else 'DISCONNECTED'}"
    display.show("Insert USB" if usb_waiting else "Receiver status", first, second)


def stop(_signum, _frame):
    global running
    running = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    config = load_config()
    display = StatusDisplay(config.get("oled", {}))
    batches = load_batches()
    # A (USB path, receiver name) pair is tracked separately, so an offline
    # computer receives the same drive when it later reconnects.
    seen = set()
    display.show("Pi USB Transfer", "Waiting for network", "")

    while running:
        states = {}
        for destination in config["destinations"]:
            states[destination["name"]] = mount_share(destination)
            if states[destination["name"]]:
                write_heartbeat(destination)
        volumes = usb_volumes(config)
        current = {str(item.resolve()) for item in volumes}
        seen = {pair for pair in seen if pair[0] in current}
        if not volumes:
            connection_screen(display, states, usb_waiting=True)
        for volume in volumes:
            batch_name = batch_for(volume, batches)
            for destination in config["destinations"]:
                key = (str(volume.resolve()), destination["name"])
                if key in seen or not states[destination["name"]]:
                    continue
                try:
                    transfer_volume(volume, destination, batch_name, display)
                    seen.add(key)
                except Exception:
                    LOG.exception("Transfer failed for %s to %s", volume, destination["name"])
                    display.show(
                        f"{destination['name']}: ERROR", volume.name, "Will retry"
                    )
        if volumes and not any(states.values()):
            connection_screen(display, states)
        time.sleep(config.get("poll_seconds", 3))
    display.show("Service stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        LOG.exception("Fatal error: %s", exc)
        sys.exit(1)
