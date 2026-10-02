#!/usr/bin/env bash
# Activate only an explicitly packaged, already extracted release.
set -euo pipefail
build="${1:?build required}"
[[ "$build" =~ ^[0-9a-f]{12}$ ]] || { echo 'Invalid build'; exit 1; }
runtime_root="$HOME/pi-smart-hub"
release="$runtime_root/releases/$build"
test "$(realpath -- "$release")" = "$release"
test -f "$release/dist/index.html"
test -f "$release/services/backend/app.py"
test -x "$runtime_root/.venv/bin/python"
"$runtime_root/.venv/bin/python" -m compileall -q "$release/services/backend"
if test -L "$runtime_root/current"; then
  previous="$(readlink -f "$runtime_root/current")"
  case "$previous" in "$runtime_root/releases/"*) ;; *) echo 'Unexpected current target'; exit 1;; esac
  ln -sfn "$previous" "$runtime_root/previous"
fi
ln -sfn "$release" "$runtime_root/current.next"
mv -Tf "$runtime_root/current.next" "$runtime_root/current"
bash "$release/scripts/install-session.sh"
systemctl --user restart pi-smart-hub.service
systemctl --user is-active pi-smart-hub.service
