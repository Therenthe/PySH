#!/usr/bin/env bash
# Prepare the runtime only. Does not launch an app or alter desktop autostart.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
test "$(uname -m)" = aarch64 || { echo 'Expected the arm64 target'; exit 1; }
test -f "$project_root/requirements.lock"
if ! command -v mpv >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends mpv python3-venv
fi
python3 -m venv "$project_root/.venv"
"$project_root/.venv/bin/python" -m pip install --no-cache-dir -r "$project_root/requirements.lock"
"$project_root/.venv/bin/python" -m pip check
"$project_root/.venv/bin/python" "$project_root/scripts/backend_smoke.py"
"$project_root/.venv/bin/python" "$project_root/scripts/pi_preflight.py"
