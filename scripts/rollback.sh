#!/usr/bin/env bash
set -euo pipefail
runtime_root="$HOME/pi-smart-hub"
test -L "$runtime_root/previous" || { echo 'No earlier application release. Use systemctl --user stop pi-smart-hub.service to return to desktop.'; exit 1; }
previous="$(readlink -f "$runtime_root/previous")"
case "$previous" in "$runtime_root/releases/"*) ;; *) echo 'Unexpected rollback target'; exit 1;; esac
test -f "$previous/dist/index.html"
ln -sfn "$previous" "$runtime_root/current.next"
mv -Tf "$runtime_root/current.next" "$runtime_root/current"
systemctl --user restart pi-smart-hub.service
systemctl --user is-active pi-smart-hub.service
