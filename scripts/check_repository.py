"""Check source layout and complete acceptance inventory, not hardware success."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
required = ['README.md', 'AGENTS.md', 'STATUS.md', 'docs/PRODUCT.md',
            'docs/ARCHITECTURE.md', 'docs/HARDWARE.md', 'docs/ROADMAP.md',
            'docs/DEVELOPMENT.md', 'docs/OPERATIONS.md', 'docs/SECURITY.md',
            'docs/adr/README.md', 'app/ui/src/main.tsx',
            'services/backend/app.py', 'os/README.md',
            'hardware/raspberry-pi-4/README.md', '.github/workflows/verify.yml']
errors = [f'Missing: {p}' for p in required if not (root / p).is_file()]
ledger = json.loads((root / 'docs/acceptance.json').read_text(encoding='utf-8'))
expected = set(re.findall(r'^\| ([A-Z][A-Z0-9]*-\d+) \|', (root / 'docs/DEFINITION_OF_DONE.md').read_text(encoding='utf-8'), re.M))
items = ledger['product']
if len(items) != len(expected) or {i['id'] for i in items} != expected:
    errors.append('Product acceptance inventory differs from DoD')
for item in ledger['preparation'] + items:
    if item['status'] not in {'OPEN', 'FAIL', 'PASS'}:
        errors.append(f"Invalid status: {item['id']}")
    if item['status'] == 'PASS':
        if not item.get('candidate') or not item.get('evidence'):
            errors.append(f"Unsubstantiated PASS: {item['id']}")
        for evidence in item.get('evidence', []):
            p = (root / evidence).resolve()
            if not p.is_relative_to(root) or not p.is_file():
                errors.append(f"Missing evidence: {item['id']}")
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Repository structure and {len(items)} product criteria: PASS (not product acceptance)')
