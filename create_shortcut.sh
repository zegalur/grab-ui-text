#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/GrabUIText.sh"
ICON_PATH="$SCRIPT_DIR/other/icon.svg"
APP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$APP_DIR/GrabUIText.desktop"

mkdir -p "$APP_DIR"

# Create .desktop file content
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=GrabUIText
Comment=Grab, read aloud and transtale UI text
Exec=$TARGET_SCRIPT
Icon=$ICON_PATH
Terminal=true
Path=$SCRIPT_DIR
Categories=Utility;
EOF

# Make the target script and shortcut executable
chmod +x "$TARGET_SCRIPT"
chmod +x "$DESKTOP_FILE"

# Try to put a copy on the Desktop
DESKTOP_SHORTCUT="$HOME/Desktop/GrabUIText.desktop"
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$DESKTOP_SHORTCUT"
    chmod +x "$DESKTOP_SHORTCUT"
    gio set "$DESKTOP_SHORTCUT" metadata::trusted true 2>/dev/null
fi

echo "Shortcut created: $DESKTOP_FILE"
echo "If you have a Desktop folder, a shortcut was also placed there."
