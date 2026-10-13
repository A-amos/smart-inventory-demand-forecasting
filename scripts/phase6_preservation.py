"""Verify frozen evidence without invoking any training or historical report writer."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    reference = json.loads((ROOT / 'backend/app/core/phase4-reference.json').read_text())
    frozen = json.loads((ROOT / 'docs/research/results/frozen-selection.json').read_text())
    expected = reference | frozen['source_fingerprints']
    results = [{'path': name, 'expected': value, 'actual': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()} for name, value in expected.items()]
    assert all(row['actual'] == row['expected'] for row in results)
    report = {'checked_at_utc': datetime.now(UTC).isoformat(), 'unchanged': True, 'protected_results': len(reference), 'sources': len(frozen['source_fingerprints']), 'files': results}
    (ROOT / 'docs/test-results/phase6-preservation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Preserved {len(reference)} frozen result/artifact files and {len(frozen['source_fingerprints'])} ML sources.")


if __name__ == '__main__': main()
