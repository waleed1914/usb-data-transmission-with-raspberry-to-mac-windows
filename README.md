# Raspberry Pi USB to SMB transfer

The Raspberry Pi watches for mounted USB drives and copies their contents to
`PiDrop` SMB shares on both a Windows PC and a Mac. A 1.3-inch 128x64 SH1106
I2C OLED shows separate PC/Mac connection states, filename, percentage, errors,
and completion.

## Behavior

- Starts automatically at Pi boot using systemd.
- Connects to the PC and Mac independently and retries either one while offline.
- Creates a dated folder such as
  `PiDrop/2026-07-09_14-35-22_MY_USB/` on both receivers.
- Remembers the USB filesystem UUID and reuses its dated folder when the same
  drive returns, allowing verified files to be skipped and only missing,
  changed, or damaged files to be sent again.
- Skips a destination file only when its relative path, byte size, and SHA-256
  checksum match the source.
- Writes to `<filename>.part` and renames only after a complete copy. Interrupted
  copies are therefore safely retried.
- Shows total data sent and remaining on the OLED during each receiver transfer.
- Reads every copied file back over SMB and verifies its SHA-256 checksum.
  A mismatch is removed and resent up to three times immediately, then retried
  again by the service loop.
- Processes a USB drive once per insertion. Remove/reinsert it to rescan after
  adding files while it remains connected.

## 1. Prepare the receiver

### Windows

Open PowerShell **as Administrator**, then:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\receiver\windows\install_receiver.ps1
```

The SMB share survives reboots; the startup helper ensures its directory exists.
Use the Windows account password, not a PIN. A blank-password account cannot
normally authenticate over SMB.

### macOS

Run:

```sh
chmod +x receiver/macos/install_receiver.sh
./receiver/macos/install_receiver.sh
```

Then perform the one-time File Sharing steps printed by the script. macOS keeps
the share enabled across reboots; the LaunchAgent ensures the folder exists at
login.

Give the receiver a DHCP reservation/static IP so the Pi can always find it.

## 2. Wire the OLED

For the usual Raspberry Pi 40-pin header:

| OLED | Raspberry Pi |
|---|---|
| VCC | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SDA | GPIO2/SDA (pin 3) |
| SCL | GPIO3/SCL (pin 5) |

Enable I2C with `sudo raspi-config`, then verify address `3c` using
`i2cdetect -y 1`.

## 3. Install on Raspberry Pi

Copy this directory to the Pi and run:

```sh
chmod +x install_pi.sh
sudo ./install_pi.sh
sudo nano /etc/pi-usb-transfer/config.json
sudo systemctl start pi-usb-transfer
```

Set the two `destinations` entries to `//PC_IP/PiDrop` and
`//MAC_IP/PiDrop`, with the correct credentials for each. Then inspect operation
with:

```sh
sudo systemctl status pi-usb-transfer
sudo journalctl -u pi-usb-transfer -f
```

The configuration is mode `0600`, but it contains an SMB password. Use a
dedicated, non-administrator receiver account where possible.
