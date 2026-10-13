"""Read-only final documentation/evidence integrity checks; no model fitting."""
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
paths=['README.md','DEVELOPMENT_LOG.md','docs/API.md','docs/ARCHITECTURE.md','docs/DATABASE.md','docs/TESTING.md','docs/DECISION_SUPPORT.md','docs/INSTALLATION_GUIDE.md','docs/USER_MANUAL.md','docs/SYSTEM_LIMITATIONS.md','docs/OBJECTIVE_TRACEABILITY.md','docs/USABILITY_EVALUATION.md','docs/research/PHASE6_REVIEW.md','docs/academic/CHAPTER_4_EVIDENCE.md','docs/academic/CHAPTER_5_EVIDENCE.md','docs/test-results/final-24-test-cases.md','docs/test-results/PERFORMANCE.md','docs/test-results/SECURITY_REVIEW.md','docs/test-results/COMPATIBILITY.md','docs/screenshots/final/README.md']
checks=[]
if os.environ.get('INVENTORY_TEST_REPORT_PREFIX')=='publication':
    paths+=['docs/DEMO_GUIDE.md','docs/HOW_THE_SYSTEM_WORKS.md','docs/PROJECT_DEFENSE_GUIDE.md','docs/PUBLICATION_REVIEW.md','NOTICE.md']
def check(label,valid,actual):
    checks.append({'check':label,'passed':bool(valid),'actual':actual})
    assert valid,label
try:
    missing=[];links=0
    for name in paths:
        file=ROOT/name
        check('Document exists: '+name,file.is_file() and file.stat().st_size>0,file.stat().st_size if file.exists() else None)
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if target.startswith(('https://','http://','#','app://')):continue
            path=unquote(target.split('#')[0]).strip('<>')
            if not path:continue
            links+=1
            if not (file.parent/path).exists():missing.append({'document':name,'target':target})
    check('All local Markdown links resolve',not missing,{'links_checked':links,'missing':missing})
    cases=json.loads((ROOT/'docs/test-results/final-24-test-cases.json').read_text(encoding='utf-8'))
    check('Exactly original TC01 through TC24 recorded',[c['id'] for c in cases['cases']]==[f'TC{i:02}' for i in range(1,25)],len(cases['cases']))
    check('No representative-user result invented',cases['cases'][-1]['status']=='PENDING EXTERNAL ACTION' and cases['passed']==23 and cases['pending']==1,{'pass':cases['passed'],'pending':cases['pending']})
    for case in cases['cases']:
        for ref in case['evidence']:
            if '#/checks/' in ref:
                file,label=ref.split('#/checks/')
                index=int(label.split()[0])
                row=json.loads((ROOT/'docs/test-results'/file).read_text(encoding='utf-8'))['checks'][index]
                check(case['id']+' actual referenced check',row['passed'],row['check'])
    proposal=ROOT/'docs/Smart_Inventory_Consolidated_Five_Chapter_Proposal.docx'
    check('Original proposal preserved',hashlib.sha256(proposal.read_bytes()).hexdigest()==cases['proposal_sha256'],cases['proposal_sha256'])
    manifest=json.loads((ROOT/'docs/test-results/phase6-screenshots.json').read_text(encoding='utf-8'))
    required=['login','dashboard','categories','products','inventory','inventory-history','sales-entry','sales-history','csv-import-preview','forecast','recommendation','model-comparison']
    check('All requested actual views recorded',all((ROOT/f'docs/screenshots/final/{x}.jpg').is_file() for x in required),required)
    for item in manifest['screenshots']:
        check('Screenshot hash: '+item['path'],hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['bytes'])
    summary=json.loads((ROOT/'docs/test-results/phase6-summary.json').read_text(encoding='utf-8'))
    check('Summary matches executed suites',summary['automated_total']==251 and sum(s['failed'] for s in summary['automated_suites'])==0 and summary['participants']==0,summary['automated_total'])
    check('Historical date/UK limitation in conclusions','current 2026 or Kenyan accuracy' in (ROOT/'docs/academic/CHAPTER_5_EVIDENCE.md').read_text(encoding='utf-8'), 'Current inference not claimed')
    print(f'{len(checks)} read-only documentation/evidence checks passed; no missing local links or invented participant result.')
finally:
    prefix=os.environ.get('INVENTORY_TEST_REPORT_PREFIX','phase6')
    assert prefix in {'phase6','publication'}
    (ROOT/f'docs/test-results/{prefix}-documentation.json').write_text(json.dumps({'executed_at_utc':datetime.now(UTC).isoformat(),'checks':checks},indent=2),encoding='utf-8')
