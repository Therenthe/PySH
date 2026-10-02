#!/usr/bin/env bash
# Run as the graphical-session user, from an already verified release.
set -euo pipefail
release_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="$HOME/pi-smart-hub"
test -f "$release_root/dist/index.html"
test -x "$runtime_root/.venv/bin/python"
mkdir -p "$HOME/.config/systemd/user" "$HOME/.config/autostart" "$HOME/.local/share/applications"
cat > "$HOME/.config/systemd/user/pi-smart-hub.service" <<EOF
[Unit]
Description=Pi Smart Hub
After=graphical-session.target pipewire.service

[Service]
Type=simple
WorkingDirectory=$runtime_root/current
ExecStart=$runtime_root/.venv/bin/python $runtime_root/current/scripts/run-hub.py
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1
UMask=0077

[Install]
WantedBy=default.target
EOF
cat > "$HOME/.local/share/applications/pi-smart-hub.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Pi Smart Hub
Comment=Clock, weather, radio and media
Exec=systemctl --user start pi-smart-hub.service
Icon=multimedia-player
Terminal=false
Categories=AudioVideo;
EOF
cat > "$HOME/.config/autostart/pi-smart-hub.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Pi Smart Hub
Exec=sh -c 'systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XDG_SESSION_TYPE; systemctl --user start pi-smart-hub.service'
Terminal=false
EOF
systemctl --user daemon-reload
echo 'Session launcher installed; explicit start required for this session.'
