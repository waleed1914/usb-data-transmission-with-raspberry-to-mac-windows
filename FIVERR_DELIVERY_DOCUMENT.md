# Fiverr Delivery Document

## Project Name

PiDrop: Raspberry Pi USB Data Transfer to Mac

## Delivery Summary

This delivery includes a Raspberry Pi based USB transfer system that automatically copies files from a USB drive to a Mac over the local Wi-Fi network using SMB file sharing.

The system was tested with both Windows and Mac during development. The final client setup is focused on Mac, because the client will use a Mac receiver.

## Main Features Delivered

- Automatic USB detection on Raspberry Pi
- Automatic transfer from Raspberry Pi to Mac over local Wi-Fi
- SMB based file transfer
- Mac receive folder support
- OLED display status support
- Live Mac status viewer script
- Automatic startup on Raspberry Pi boot
- Date/time folder creation for each USB batch
- Skip already copied files
- Verify files after transfer using checksum
- Re-send missing or corrupted files
- Safe resume behavior after reboot or interruption
- Raspberry Pi service logs for troubleshooting

## GitHub Repository

Repository:

```text
https://github.com/waleed1914/usb-data-transmission-with-raspberry-to-mac-windows
```

Client setup guide:

```text
https://github.com/waleed1914/usb-data-transmission-with-raspberry-to-mac-windows/blob/main/CLIENT_SETUP_GUIDE.md
```

## Delivered Files

Important files included in the repository:

```text
pi_usb_transfer.py
install_pi.sh
pi-usb-transfer.service
config.example.json
CLIENT_SETUP_GUIDE.md
receiver/macos/install_receiver.sh
receiver/macos/show_status.sh
receiver/windows/install_receiver.cmd
receiver/windows/install_receiver.ps1
receiver/windows/show_status.cmd
receiver/windows/show_status.ps1
```

## Mac Receiver Setup

The Mac receives files in:

```text
~/PiDrop
```

The Mac must have File Sharing enabled:

```text
System Settings → General → Sharing → File Sharing
```

The `PiDrop` folder must be shared with Read & Write permission.

Windows File Sharing / SMB must be enabled in the Mac File Sharing options.

## Raspberry Pi Setup

The Raspberry Pi runs the transfer service automatically on startup:

```bash
sudo systemctl enable pi-usb-transfer.service
sudo systemctl restart pi-usb-transfer.service
```

The main configuration file is:

```text
/etc/pi-usb-transfer/config.json
```

The Mac IP address, username, and password must be entered in this config file.

## OLED Setup

OLED wiring:

```text
OLED VCC  -> Raspberry Pi 5V
OLED GND  -> Raspberry Pi GND
OLED SCL  -> Raspberry Pi GPIO 3 / physical pin 5
OLED SDA  -> Raspberry Pi GPIO 2 / physical pin 3
```

The OLED uses I2C address:

```text
0x3C
```

The tested OLED driver is:

```text
sh1106
```

## How to View Live Status on Mac

After running the Mac installer, open Terminal and run:

```bash
~/PiDrop/show_status.sh
```

This shows:

```text
Raspberry Pi: CONNECTED / DISCONNECTED
Status: TRANSFERRING / VERIFYING / SKIPPING
File:
Progress:
Received:
Remaining:
Updated:
```

Closing this Terminal window does not stop the transfer.

## Important Notes for Client

- Keep the Mac and Raspberry Pi on the same Wi-Fi network.
- Keep the Mac awake while receiving files.
- Do not remove the USB drive while files are transferring.
- If the same USB is connected again, already copied files are checked and skipped.
- If a file is deleted from the Mac receive folder, the Raspberry Pi will copy it again the next time the USB is checked.
- If transfer is interrupted, the system verifies files and continues safely.

## Testing Completed

The following items were tested:

- Raspberry Pi service startup
- USB file detection
- SMB connection to receiver
- File transfer
- Existing file verification
- Skipping already verified files
- OLED SH1106 display test
- Mac SMB login
- Mac file transfer
- Mac live status script

## Final Client Instructions

Please follow the setup guide:

```text
CLIENT_SETUP_GUIDE.md
```

The guide is written step by step for a non-technical user.

## Support / Troubleshooting

Useful Raspberry Pi commands:

```bash
sudo systemctl status pi-usb-transfer.service
journalctl -u pi-usb-transfer.service -f
```

Test Mac SMB connection from Raspberry Pi:

```bash
smbclient //MAC_IP/PiDrop -U MAC_USERNAME
```

Check OLED detection:

```bash
i2cdetect -y 1
```

Expected OLED address:

```text
3c
```
