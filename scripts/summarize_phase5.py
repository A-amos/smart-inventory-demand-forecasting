"""Compile the exit gate from executed reports and immutable-file hashes, never assumed results."""
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'docs/test-results'


def main():
    suites = {}
    for name, expected in [('backend', 160), ('ml', 59), ('frontend', 29)]:
        tree = ET.parse(REPORTS / f'phase5-{name}.xml')
        cases = list(tree.iter('testcase'))
        failures = len(list(tree.iter('failure'))) + len(list(tree.iter('error')))
        assert len(cases) == expected and failures == 0, name
        suites[name] = {'executed': len(cases), 'failures': failures, 'junit': f'phase5-{name}.xml'}
    checks = {}
    for name, expected in [('live', 50), ('browser', 11), ('browser-persistence', 8)]:
        report = json.loads((REPORTS / f'phase5-{name}.json').read_text(encoding='utf-8'))
        assert len(report['checks']) == expected and all(row['passed'] for row in report['checks']), name
        checks[name] = {'passed': expected, 'executed_at_utc': report['executed_at_utc']}
    reference = json.loads((ROOT / 'backend/app/core/phase4-reference.json').read_text())
    frozen = json.loads((ROOT / 'docs/research/results/frozen-selection.json').read_text())
    hashes = {**reference, **frozen['source_fingerprints']}
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in hashes.items())
    proposal_sha = hashlib.sha256((ROOT / 'docs/Smart_Inventory_Consolidated_Five_Chapter_Proposal.docx').read_bytes()).hexdigest()
    assert proposal_sha == '9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2'
    build = (REPORTS / 'phase5-build.txt').read_text(encoding='utf-8')
    assert 'built in' in build and '621 modules transformed' in build
    migration = (REPORTS / 'phase5-migration-final.txt').read_text(encoding='utf-8')
    assert 'e52ad70491b2 (head)' in migration and 'No new upgrade operations detected.' in migration
    assert 'No broken requirements found.' in (REPORTS / 'phase5-container-dependencies.txt').read_text()
    containers = {row['Service']: row for row in [json.loads(line) for line in (REPORTS / 'phase5-compose-status.jsonl').read_text().splitlines()]}
    assert containers['db']['Health'] == 'healthy' and containers['migrate']['ExitCode'] == 0
    assert all(containers[name]['State'] == 'running' for name in ['db', 'backend', 'frontend'])
    rebuild = (REPORTS / 'phase5-compose-final.txt').read_text(encoding='utf-8')
    assert 'Built' in rebuild and 'frontend-1 Started' in rebuild
    output = {'verified_at_utc': datetime.now(UTC).isoformat(), 'phase5_exit_gate': 'passed', 'phase6_started': False,
              'suites': suites, 'actual_workflows': checks, 'migration_head': 'e52ad70491b2',
              'production_build': 'passed', 'compose_rebuild': 'passed', 'mysql_migration_check': 'passed',
              'protected_phase4_evidence_files_unchanged': len(reference), 'ML_source_files_unchanged': len(frozen['source_fingerprints']),
              'proposal_sha256': proposal_sha, 'selected_model': 'mean_28',
              'limitation': 'UK history ends 2011-11-10; current forecasts unavailable. Acknowledged 2011-11-11 scenario uses illustrative stock. No Kenyan validation.',
              'initial_failures': ['two new-test fixture/ORM failures corrected', 'esbuild filesystem sandbox restriction',
                                   'MySQL trigger binary-log privilege error 1419 corrected without resetting data', 'Docker subprocess sandbox restriction'],
              'remaining': ['Phase 6 full evaluation requires new instruction', 'fresh compatible operational history unavailable',
                            'participant/performance/cross-browser/deployment review not performed', 'upstream Starlette/AnyIO deprecation warning']}
    (REPORTS / 'phase5-summary.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print('Phase 5 exit gate verified from actual reports, running-stack evidence and preserved source/artifact hashes.')


if __name__ == '__main__': main()
