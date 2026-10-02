"""Fail closed unless the selected milestone has complete, readable evidence."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['preparation', 'product'], required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
ledger = json.loads((root / 'docs/acceptance.json').read_text(encoding='utf-8'))
items = ledger[args.phase]
failed = []
if not items:
    failed.append('Empty milestone')
ids = [item['id'] for item in items]
if len(ids) != len(set(ids)):
    failed.append('Duplicate criterion IDs')
if args.phase == 'product':
    required = set(re.findall(r'^\| ([A-Z][A-Z0-9]*-\d+) \|', (root / 'docs/DEFINITION_OF_DONE.md').read_text(encoding='utf-8'), re.M))
else:
    required = {'PREP-01', 'PREP-02', 'PREP-03', 'PREP-04', 'PREP-05', 'PREP-06', 'PREP-07'}
if set(ids) != required:
    failed.append(f'Criteria mismatch: missing={sorted(required-set(ids))}, extra={sorted(set(ids)-required)}')
if len({item.get('candidate') for item in items if item['status'] == 'PASS'}) > 1:
    failed.append('PASS evidence belongs to different candidates')
for item in items:
    if item['status'] != 'PASS' or not item.get('evidence') or not item.get('candidate'):
        failed.append(f"{item['id']}: {item['status']}")
        continue
    for evidence in item['evidence']:
        path = (root / evidence).resolve()
        if not path.is_relative_to(root) or not path.is_file() or not path.stat().st_size:
            failed.append(f"{item['id']}: invalid/missing evidence {evidence}")
if failed:
    print('\n'.join(failed))
    raise SystemExit(1)
print(f'{args.phase}: PASS ({len(items)} criteria with evidence; review content separately)')
