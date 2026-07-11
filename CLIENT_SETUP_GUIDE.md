# PiDrop Client Setup Guide

Raspberry Pi USB transfer to Mac with OLED status

This guide is for a non-technical user. Follow each setup step in order.

## What this system does

When a USB drive is plugged into the Raspberry Pi, the Raspberry Pi automatically copies the USB files to the Mac over Wi-Fi.

The system will:

- copy USB files to the Mac;
- create a date/time folder for each USB drive;
- skip files that were already copied;
- verify copied files using checksum;
- send missing or damaged files again;
- show status on the OLED screen;
- show live status on the Mac Terminal;
- start automatically when the Raspberry Pi powers on.

## What you need

- Raspberry Pi with Wi-Fi
- Mac computer
- 1.3 inch I2C OLED display
- USB drive
- Same Wi-Fi network for Raspberry Pi and Mac

---

## Setup 1: Connect the OLED to Raspberry Pi

Connect the OLED wires like this:

```text
OLED VCC  -> Raspberry Pi 5V
OLED GND  -> Raspberry Pi GND
OLED SCL  -> Raspberry Pi GPIO 3 / physical pin 5
OLED SDA  -> Raspberry Pi GPIO 2 / physical pin 3
```

On the Raspberry Pi, open Terminal and run:

```bash
sudo raspi-config
```

Go to:

```text
Interface Options
I2C
Enable
```

Reboot the Raspberry Pi:

```bash
sudo reboot
```

After reboot, check the OLED:

```bash
sudo apt update
sudo apt install -y i2c-tools
i2cdetect -y 1
```

You should see `3c` in the result.

---

## Setup 2: Install PiDrop on Raspberry Pi

On the Raspberry Pi, open Terminal and run:

```bash
cd ~
git clone https://github.com/waleed1914/usb-data-transmission-with-raspberry-to-mac-windows.git
cd usb-data-transmission-with-raspberry-to-mac-windows
chmod +x install_pi.sh
sudo ./install_pi.sh
```

---

## Setup 3: Create the Mac receive folder

On the Mac, open Terminal and run:

```bash
mkdir -p ~/PiDrop
```

Files will be saved here:

```text
Macintosh HD → Users → your-user-name → PiDrop
```

---

## Setup 4: Turn on File Sharing on Mac

On the Mac, open:

```text
System Settings → General → Sharing
```

Turn on:

```text
File Sharing
```

Click the info/details button beside File Sharing.

Add this folder:

```text
/Users/YOUR_MAC_USERNAME/PiDrop
```

Give your Mac user:

```text
Read & Write
```

Click:

```text
Options
```

Turn on:

```text
Windows File Sharing
```

Check your Mac user account in the list.

If macOS asks for your password, enter your Mac login password.

Click:

```text
OK
Done
```

---

## Setup 5: Find the Mac username and IP address

On the Mac Terminal, run:

```bash
whoami
```

Write down the username.

Example:

```text
aliashraf169
```

Then run:

```bash
ipconfig getifaddr en0
```

Write down the IP address.

Example:

```text
192.168.1.16
```

Keep these details:

```text
Mac username: ______________________
Mac IP:       ______________________
Mac password: your Mac login password
```

---

## Setup 6: Test Mac connection from Raspberry Pi

On Raspberry Pi Terminal, run:

```bash
smbclient //MAC_IP/PiDrop -U MAC_USERNAME
```

Example:

```bash
smbclient //192.168.1.16/PiDrop -U aliashraf169
```

Enter the Mac login password.

If it works, you will see:

```text
smb: \>
```

Then type:

```bash
ls
exit
```

If this step works, the Mac is ready.

---

## Setup 7: Configure Raspberry Pi for the Mac

On Raspberry Pi, open the config file:

```bash
sudo nano /etc/pi-usb-transfer/config.json
```

Replace everything with this:

```json
{
  "destinations": [
    {
      "name": "MAC",
      "share": "//MAC_IP/PiDrop",
      "username": "MAC_USERNAME",
      "password": "MAC_PASSWORD",
      "domain": "",
      "mount_point": "/mnt/pi-receiver-mac"
    }
  ],
  "usb_roots": ["/media/pi", "/run/media/pi"],
  "poll_seconds": 3,
  "oled": {
    "enabled": true,
    "driver": "sh1106",
    "i2c_address": "0x3C",
    "width": 128,
    "height": 64,
    "rotate": 0
  }
}
```

Replace these values:

```text
MAC_IP
MAC_USERNAME
MAC_PASSWORD
```

Example:

```json
{
  "destinations": [
    {
      "name": "MAC",
      "share": "//192.168.1.16/PiDrop",
      "username": "aliashraf169",
      "password": "your-mac-password",
      "domain": "",
      "mount_point": "/mnt/pi-receiver-mac"
    }
  ],
  "usb_roots": ["/media/pi", "/run/media/pi"],
  "poll_seconds": 3,
  "oled": {
    "enabled": true,
    "driver": "sh1106",
    "i2c_address": "0x3C",
    "width": 128,
    "height": 64,
    "rotate": 0
  }
}
```

Save the file:

```text
CTRL + O
Enter
CTRL + X
```

---

## Setup 8: Start the Raspberry Pi transfer service

On Raspberry Pi, run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-usb-transfer.service
sudo systemctl restart pi-usb-transfer.service
```

Check status:

```bash
sudo systemctl status pi-usb-transfer.service
```

It should say:

```text
active (running)
```

---

## Setup 9: Install the Mac live status viewer

On the Mac Terminal, run:

```bash
cd ~
git clone https://github.com/waleed1914/usb-data-transmission-with-raspberry-to-mac-windows.git
cd usb-data-transmission-with-raspberry-to-mac-windows
chmod +x receiver/macos/install_receiver.sh
./receiver/macos/install_receiver.sh
```

Open the live status viewer anytime with:

```bash
~/PiDrop/show_status.sh
```

The status viewer shows:

```text
Raspberry Pi: CONNECTED / DISCONNECTED
Status: TRANSFERRING / VERIFYING / SKIPPING
File:
Progress:
Received:
Remaining:
Updated:
```

Closing the Terminal does not stop receiving files.

---

## Setup 10: Use the system

1. Turn on the Mac.
2. Turn on the Raspberry Pi.
3. Make sure both are connected to the same Wi-Fi.
4. Plug the USB drive into the Raspberry Pi.
5. The Raspberry Pi starts copying automatically.
6. Watch progress on the OLED screen or Mac status viewer.
7. Files appear in:

```text
~/PiDrop
```

The Raspberry Pi creates a folder like:

```text
2026-07-11_15-30-22_USBNAME
```

---

## Troubleshooting

### Mac login fails

Test from Raspberry Pi:

```bash
smbclient //MAC_IP/PiDrop -U MAC_USERNAME
```

Check:

- Mac File Sharing is on.
- Windows File Sharing is on.
- Correct username from `whoami`.
- Correct Mac login password.
- Raspberry Pi and Mac are on the same Wi-Fi.

### OLED is blank

Check OLED address:

```bash
i2cdetect -y 1
```

You should see:

```text
3c
```

Run OLED test:

```bash
/opt/pi-usb-transfer/venv/bin/python - <<'PY'
import time
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

device = sh1106(i2c(port=1, address=0x3C), width=128, height=64)
device.contrast(255)

with canvas(device) as draw:
    draw.text((0, 0), "OLED TEST", fill="white")
    draw.text((0, 16), "SH1106 0x3C", fill="white")
    draw.rectangle((0, 40, 127, 63), outline="white", fill="white")

time.sleep(30)
PY
```

### Service restart hangs

Run:

```bash
sudo systemctl kill pi-usb-transfer.service
sudo systemctl start pi-usb-transfer.service
```

### Check Raspberry Pi logs

Run:

```bash
journalctl -u pi-usb-transfer.service -f
```

Stop logs with:

```text
CTRL + C
```

---

## Notes for the client

- Do not remove the USB while files are transferring.
- Do not turn off the Mac while receiving files.
- If the same USB is connected again, already copied files are checked and skipped.
- If a file is deleted from the Mac receive folder, the Raspberry Pi will copy it again next time.
- The Mac Terminal status window is only for viewing progress. Closing it does not stop the transfer.
