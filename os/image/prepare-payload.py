"""Stage the runtime allowlist with exact source/build identity; no user data."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=root):
    raise SystemExit('Commit source changes before image construction.')
result = subprocess.check_output([sys.executable, 'scripts/package-release.py'], cwd=root, text=True)
package = json.loads(result)
payload = root / 'os/image/payload'
payload.mkdir(exist_ok=True)
shutil.copyfile(package['archive'], payload / 'runtime.tar.gz')
shutil.copyfile(root / f"releases/{package['build']}.manifest.json", payload / 'manifest.json')
identity = {
    'source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'runtime_build': package['build'],
    'builder': '262d4df5a9f9d4133370465399a7958a7c22cdc7',
    'acceptance': 'EXPERIMENTAL, NOT FLASH-READY',
}
(payload / 'source.json').write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
print(json.dumps(identity))
