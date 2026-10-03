"""Package an explicit runtime allowlist; never include audit backups or secrets."""
import hashlib
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent.parent
files = []
for name in ("services/backend", "app/browser-extension", "dist"):
    files.extend(p for p in (root / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
for name in ("requirements.lock", "scripts/run-hub.py", "scripts/install-session.sh", "scripts/activate-release.sh", "scripts/rollback.sh", "scripts/probe-application.py", "scripts/service-keyboard-host.py"):
    files.append(root / name)
files.sort()
manifest = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
build = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:12]
destination = root / "releases"
destination.mkdir(exist_ok=True)
archive = destination / f"pi-smart-hub-{build}.tar.gz"
with tarfile.open(archive, "w:gz") as bundle:
    for p in files:
        def mode(info):
            if info.name == "scripts/service-keyboard-host.py":
                info.mode = 0o755
            return info
        bundle.add(p, arcname=str(p.relative_to(root)).replace("\\", "/"), filter=mode)
(destination / f"{build}.manifest.json").write_text(json.dumps({"build":build,"sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"files":manifest},indent=2),encoding="utf-8")
print(json.dumps({"build":build,"archive":str(archive),"files":len(files)}))
