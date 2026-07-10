#!/bin/sh
set -eu

DEST="$HOME/PiDrop"
mkdir -p "$DEST"
chmod 700 "$DEST"

PLIST="$HOME/Library/LaunchAgents/com.pazhong.pidrop-ready.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.pazhong.pidrop-ready</string>
  <key>ProgramArguments</key><array>
    <string>/bin/mkdir</string><string>-p</string><string>$DEST</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)/com.pazhong.pidrop-ready" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Folder ready: $DEST"
echo "Now open System Settings > General > Sharing > File Sharing."
echo "Add $DEST, enable SMB for this user under Options, and grant Read & Write."
echo "Pi share path will be //MAC_IP/PiDrop (use your Mac username/password)."
