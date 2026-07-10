#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo ./install_pi.sh"
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
apt-get update
apt-get install -y python3-venv python3-dev python3-pip cifs-utils i2c-tools libjpeg-dev zlib1g-dev
install -d /opt/pi-usb-transfer /etc/pi-usb-transfer /var/lib/pi-usb-transfer /mnt/pi-receiver-pc /mnt/pi-receiver-mac
install -m 755 "$SCRIPT_DIR/pi_usb_transfer.py" /opt/pi-usb-transfer/pi_usb_transfer.py
install -m 644 "$SCRIPT_DIR/pi-usb-transfer.service" /etc/systemd/system/pi-usb-transfer.service
if [ ! -f /etc/pi-usb-transfer/config.json ]; then
  install -m 600 "$SCRIPT_DIR/config.example.json" /etc/pi-usb-transfer/config.json
fi
python3 -m venv /opt/pi-usb-transfer/venv
/opt/pi-usb-transfer/venv/bin/pip install --upgrade pip
/opt/pi-usb-transfer/venv/bin/pip install luma.oled
systemctl daemon-reload
systemctl enable pi-usb-transfer.service
echo "Edit /etc/pi-usb-transfer/config.json, then run:"
echo "  sudo systemctl start pi-usb-transfer"
