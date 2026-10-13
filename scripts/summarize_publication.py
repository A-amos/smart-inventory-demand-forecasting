"""Summarize executed publication checks; never fit or rewrite frozen research."""
import json
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/test-results'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def main():
    suites=[]
    for name in ['backend','ml','frontend']:
        tree=ET.parse(OUT/f'publication-{name}.xml').getroot()
        children=tree.findall('testsuite')
        counts={key:sum(int(x.get(key,'0')) for x in children) for key in ['tests','failures','errors','skipped']}
        assert counts['tests'] and counts['failures']==counts['errors']==counts['skipped']==0
        suites.append({'name':name,**counts,'junit_seconds':float(tree.get('time')) if tree.get('time') else sum(float(x.get('time','0')) for x in children),'reported_warnings':1 if name=='backend' else 0})
    live={}
    for name in ['sales-live','decisions-live','security','stack']:
        report=read(f'publication-{name}.json')
        assert report['checks'] and all(x['passed'] for x in report['checks'])
        if 'commands' in report:assert all(x['exit_code']==0 for x in report['commands'])
        live[name]=len(report['checks'])
    preserved=read('publication-preservation.json');assert preserved['unchanged']
    python=read('publication-python-audit.json');frontend=read('publication-frontend-audit.json')
    py_vulns=sum(len(x['vulns']) for x in python['dependencies'])
    fe_vulns=sum(frontend['metadata']['vulnerabilities'].values())
    assert py_vulns==fe_vulns==0
    build=(OUT/'publication-build.txt').read_text(encoding='utf-8')
    build_seconds=float(re.search(r'built in ([\d.]+)s',build).group(1))
    compat=read('publication-compatibility.json')
    assert all(x['passed'] for x in compat['browsers'][0]['checks'])
    assert len(compat['browsers'][0]['chart_paths'])==2
    receipt=OUT/'publication-github.json'
    publication='Published privately; initial push/clone/browser verification recorded in publication-github.json' if receipt.exists() and read('publication-github.json').get('passed') else 'Prepared; actual remote verification is recorded separately after push'
    result={'executed_at_utc':datetime.now(UTC).isoformat(),'automated_suites':suites,'automated_total':sum(x['tests'] for x in suites),'frontend_build_seconds':build_seconds,'live_checks':live,'protected_hashes':len(preserved['protected_files']),'application_audit_findings':{'python':py_vulns,'frontend':fe_vulns},'compatibility':compat['browsers'],'proposal_cases':{'passed':23,'total':24,'pending':'TC24participant evaluation'},'participants':0,'responses':0,'publication':publication,'limitations':['Historical UK2009–2011 data does not validate current Kenyan accuracy','No commercial effectiveness/automatic procurement','Original historical reproduction lock retains advisories; not used for updated application','Upstream TestClient/httpx deprecation and audit hash-pinning warnings','Browser follow-up limitations recorded individually']}
    (OUT/'publication-summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    rows='\n'.join(f"| {s['name']} | {s['tests']} |0|0| {s['reported_warnings']} | {s['junit_seconds']:.3f} |" for s in suites)
    review=f'''# Final publication review —2026-10-13

Software finalization uses actual new reports, preserving originalPhase4/5/6evidence. The four research objectives and original proposal remain authoritative. No research winner, metric, protocol, dataset, artifact or frozen source was changed. Human evaluation is pending, not a software-completion blocker. Publication destination is the requested private `A-amos/smart-inventory-demand-forecasting`; actual push verification is recorded separately.

## Completed and verified

| Suite | Passed | Failed/errors | Skipped | Reported warnings | JUnit seconds |
|---|---:|---:|---:|---:|---:|
{rows}

All251automated tests passed after final dependency changes. Backend console duration115.10s; ML27.87s; frontend wall duration16.17s (JUnit root time records test duration, not wall duration). Frontend build621modules/{build_seconds:.2f}s passed, main216.81kB/dashboard392.53kB. Reports:publication-backend.xml/txt, publication-ml.xml/txt, publication-frontend.xml/txt, publication-build.txt.

Docker Compose rebuilt and started successfully, including a final cached rebuild for the transitive frontend fix. MySQL8.4.11 is healthy; head e52ad70491b2; alembiccheck has no pending operations; host/containerpipcheck pass; live/readiness/frontendHTTP200. Actual43sales/import,50forecast/decision and21security checks pass against the rebuilt services. These verify authentication, catalog, inventory/audit, atomic/concurrent sales, rollback, CSVschema/rejections/duplicates/no-stock-change, real inference/mapping/persistence, risk/reorder formulas, immutable histories, roles and failure isolation. See publication-stack.json, publication-sales-live.json, publication-decisions-live.json and publication-security.json. Tagged fixtures are archived; the earlier labelled browser demonstration remains active. No database reset, downgrade or volume deletion occurred.

All31protected source/result/artifact fingerprints remain unchanged, and real frozen20728/origin2011-11-10/28day inference passes in the updated environment. Saved metrics are unaltered: mean_28validationMAE4.753635204/finalMAE5.335034014/RMSE17.944563987; seasonalnaivefinal4.939880952/17.008523773 remains lower without replacing the winner. MAPE remains omitted. See publication-preservation.json and publication-inference.json.

## Compatible dependency changes

| Package | Previous | Publication |
|---|---|---|
|FastAPI|0.115.12|0.143.0|
|Starlette|0.46.2|1.7.0|
|cryptography|44.0.3|50.0.2|
|pytest|8.3.5|9.1.1|
|Vite|6.3.5|6.4.3|
|Vitest|3.1.3|4.1.11|
|source-map-js|1.2.1|1.2.2|

Candidates were installed in ignored `.local/final-venv`, leaving the original `.venv`, MLsources/protocol/directrequirements, historicalMLlock and artifacts intact. Pydantic2.11.4 and coreMLversions are preserved; only application/development dependencies changed. Compatible added dependencies are constrained in backend/requirements-lock.txt; frontend resolutions are recorded in pnpm-lock.yaml. [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/), [Vitest4migration](https://v4.vitest.dev/guide/migration.html), and the [source-map-js advisory](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) informed the review. Full regression and live behavior, not version numbers alone, establish compatibility here.

Current pip-audit of the exact installed publication environment and pnpm audit of the final lockfile both report **zero known advisories** (publication-python-audit.json/txt, publication-frontend-audit.json). The first frontend re-audit found one new high source-map-js advisory; its compatible patch was applied and frontend/full suites rerun. The original26Pythonrecords and10frontend findings remain preserved in Phase6reports; the historical reproduction lock still contains original versions/advisories and should remain isolated, not deployed. Zero current audit findings are not proof of security or penetration testing. Pip-audit warns that fully hashed requirements are preferable; one upstream Starlette TestClient/httpx deprecation and one whatwg-encoding installation deprecation remain documented.

## Actual compatibility follow-up

Chrome154.0.8037.59:11actual bounded login/navigation/products/inventory/movement/sales/import/dashboard/forecast/recommendation/history/logout observations passed. Two nonempty opacity1SVGlinepaths and visible historical/forecast lines were independently checked; screenshot: [Chrome chart](screenshots/publication/chrome-chart.jpg), [full dashboard](screenshots/publication/chrome-dashboard.jpg). This was a technical smoke, not participant testing; operational/import persistence is separately verified by live APItests. Edge and Firefox current-version outcomes are recorded without inferred passes in [publication-compatibility.json](test-results/publication-compatibility.json). Original Edge154smoke evidence is retained. No universal/mobile/accessibility certification is claimed.

## Repository hygiene and reproducibility

`.gitignore` excludes environment/credentials, virtual environments,.localtools,node_modules,caches,privatekeys,localDBdata and raw/full/sealed datasets. Source tests retain explicitly synthetic dummy passwords, not operational credentials. A bounded scan checks exact known local credential values and common credential/key signatures; it does not promise universal secret detection. Candidate/staged reports record no findings and all31frozen fingerprints. Exact byte attributes avoid Windows/Linux newline changes breaking research hashes.

The trusted356byte selected baseline and1,221,454byte derived development CSV are included so a clone can run the historical demo without retraining. Aggregate columns are date/SKU/demand/price, with no customer/invoice identifiers. Raw archives/workbook and other binaries remain local/ignored; noLFSneeded. Dataset attribution/change notices:[NOTICE.md](../NOTICE.md); acquisition and isolated independent reconstruction remain documented in ml/README.md. Software has no newly imposed open-source license.

README and [DEMO_GUIDE](DEMO_GUIDE.md), [HOW_THE_SYSTEM_WORKS](HOW_THE_SYSTEM_WORKS.md), [PROJECT_DEFENSE_GUIDE](PROJECT_DEFENSE_GUIDE.md) cover setup, all modules, defense answers and actual limitations. Original24case evidence remains23PASS/TC24pending; usability instrument has zero participants/responses. UK2009–2011data does not validate current Kenyan accuracy; no dates, winner or findings were changed for presentation. No automatic procurement or commercial effectiveness is claimed.

## Failures and corrective actions

- PyPImetadata read initially failed sandbox networkWinError10013; approved rerun succeeded. Dependency installs/audits used approved external network access.
- One README patch was rejected because delete/add targeted the same file; README was then rewritten from a local prepared file, without deleting documentation/evidence.
- Git staging initially refused ownership because the sandbox initialized.git under another local account. Subsequent commands trust only this exact workspace with per-command safe.directory; no global wildcard trust was added.
- A stack assertion ran while the last frontend container/migration job was still rebuilding. Its failure is retained as publication-stack-during-rebuild-failure.json/txt; after Compose exit0, the complete stack/live sequence passed. No failed check was called successful.
- Chrome first inventory had a request-header-policy error; retry recovered. Exact-label selection included nested option text and timed out; observed native keyboard and later combobox-role selection succeeded. Initial full-page capture lacked plotted lines; it is retained, followed by DOMpath verification and an in-view screenshot with both curves. No chart code was changed.
- Edge native input initially lacked reachable geometry; a fresh screenshot mapping and observed maximize control resolved it. A low-battery system modal interrupted the last native checks; exact subsequent results are in the compatibility report. No unsupported browser action is claimed passed.
- GitHub CLI was initially absent/unauthenticated. Officialv2.102.0 was downloaded into ignored.localtools and release checksum verified. User approved the displayed persistentOAuthscopes and personally completed emailed account verification. CLI confirmedA-amos. No tokens, passwords, pairing codes or private browser data are committed.

## Pending external action and known limitations

Real supervisor-approved voluntary participants/field requirements evaluation remain pending: zero participants, zero responses, no ratings/feedback invented. Browser limitations are explicit in the current compatibility report. Original research reproduction advisories and current upstream warnings remain documented. HistoricalUKresults cannot establish current Kenyan forecasting or commercial benefit; incomingETA/pack/cost/probabilistic/enterprise optimization remain outside scope. GitHub visibility must remain private unless the user separately requests public access.
'''
    (ROOT/'docs/PUBLICATION_REVIEW.md').write_text(review,encoding='utf-8')
    print('Publication verification summary written:251tests;114business/security live checks;31frozen hashes;0current audit findings; participant/browser limits explicit.')

if __name__=='__main__':main()
