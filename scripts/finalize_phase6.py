"""Publish Phase 6 evidence from executed reports, without altering frozen research."""
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/test-results'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(path,text):
    destination=ROOT/path
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(text.strip()+'\n',encoding='utf-8')
def dump(path,data):write(path,json.dumps(data,indent=2,ensure_ascii=False))
def checked(name):
    data=read(name)
    assert data['checks'] and all(c['passed'] for c in data['checks']),name
    return data
def evidence(name,label):
    data=checked(name)
    index=next(i for i,c in enumerate(data['checks']) if c['check']==label)
    return f'{name}#/checks/{index} ({label})'

sales=checked('phase6-sales-live.json')
decisions=checked('phase6-decisions-live.json')
security=checked('phase6-security.json')
browser=checked('phase6-browser.json')
persistence=checked('phase6-browser-persistence.json')
metrics=read('phase6-metrics.json');assert all(c['passed'] for c in metrics['checks'])
reproduction=read('phase6-reproduction.json');assert reproduction['passed']
stack=checked('phase6-stack.json');assert all(c['exit_code']==0 for c in stack['commands'])
preservation=read('phase6-preservation.json');assert preservation['unchanged']
performance=read('phase6-performance.json');assert sum(r['errors'] for r in performance['results'])==0

suites=[]
for kind in ['backend','ml','frontend']:
    root=ET.parse(OUT/f'phase6-{kind}.xml').getroot()
    nodes=root.findall('testsuite')
    tests=sum(int(s.attrib['tests']) for s in nodes)
    failed=sum(int(s.attrib.get('failures','0'))+int(s.attrib.get('errors','0')) for s in nodes)
    skipped=sum(int(s.attrib.get('skipped','0')) for s in nodes)
    assert tests and failed==0 and skipped==0
    suites.append({'suite':kind,'tests':tests,'passed':tests,'failed':failed,'skipped':skipped,'reported_warnings':1 if kind=='backend' else 0,'seconds':float(root.attrib['time']) if 'time' in root.attrib else sum(float(s.attrib['time']) for s in nodes),'evidence':f'phase6-{kind}.xml'})
assert 'built in 9.35s' in (OUT/'phase6-build.txt').read_text()

# Tool observations are recorded individually. No partial browser is promoted to PASS.
compat=read('phase6-compatibility.json')
edge=compat['browsers'][0]
edge['checks'][-1]['actual']='Actual post-click screenshot displayed Sign in to your workspace; immediate AX text was stale'
edge['checks'][-1]['evidence']='Native Computer Use post-click screenshot observed on 2026-10-01; no saved logout image'
edge['status']='PASS (bounded navigation/render/logout smoke)'
compat['browsers']=[edge,{
    'browser':'Google Chrome','version':'154.0.8037.59','status':'PARTIAL',
    'checks':[{'area':'login','actual':'Actual authorized manager login succeeded'}, {'area':'navigation','actual':'Products, Categories, Inventory, Sales entry, CSV import and Dashboard visited'}, {'area':'product/inventory','actual':'Pages opened; initial catalog request was still loading; final quantities not independently verified'}, {'area':'sales form','actual':'Form opened'}, {'area':'import page','actual':'Page opened'}, {'area':'dashboard/charts','actual':'Initial dashboard loading observed; final chart rendering NOT VERIFIED'}, {'area':'logout','actual':'NOT EXECUTED'}],
    'limitation':'CDP screenshot timeout, CUA kernel timeouts and request-header policy load failure; browser automation subsequently stopped by Windows browser URL-policy enforcement. No browser fallback after stop.'},
    {'browser':'Mozilla Firefox','version':'156.0.1','status':'NOT EXECUTED',
     'checks':[{'area':area,'actual':'NOT EXECUTED'} for area in ['login','navigation','product/inventory','sales form','import page','dashboard/charts','logout']],
     'limitation':'Installed browser launched; selecting its window stopped Computer Use because URL-policy enforcement is unsupported. No application behavior asserted.'}]
compat['version_source']='Installed executable ProductVersion file properties; not guessed from another browser.'
compat['scope']='Localhost desktop smoke; no mobile, accessibility certification or universal cross-browser guarantee.'
dump('docs/test-results/phase6-compatibility.json',compat)

S=lambda label:evidence('phase6-sales-live.json',label)
D=lambda label:evidence('phase6-decisions-live.json',label)
Q=lambda label:evidence('phase6-security.json',label)
B=lambda label:evidence('phase6-browser.json',label)
cases=[]
def case(number,module,objective,preconditions,action,expected,actual,refs,status='PASS'):
    cases.append({'id':f'TC{number:02d}','module':module,'objective':objective,'preconditions':preconditions,'input_action':action,'expected_result':expected,'actual_result':actual,'status':status,'evidence':refs})
case(1,'Authentication','Valid account and password','Authorized local manager; running API/UI','Sign in; navigate Dashboard','User reaches authorized dashboard','Manager welcome and authenticated dashboard displayed; live session HTTP200',[Q('Login returns a non-cacheable authorized manager session'),B('Login, category and product creation'),B('TC21 updated dashboard after sale')])
case(2,'Authentication','Incorrect password','Active isolated researcher test account','Submit five incorrect passwords','Access denied with safe message','Incorrect passwords returned generic401; persistent lockout followed',[Q('Five failed logins trigger persistent lockout')])
case(3,'Authentication','Unauthenticated request to protected page','No bearer session','GET dashboard; POST protected sales','Request rejected or redirected','Anonymous dashboard and sale writes HTTP401',[Q('Anonymous dashboard denied'),S('Anonymous cannot record sales')])
case(4,'Authentication','Sign out of active session','Authenticated session','Sign out; reuse same bearer','Protected session ends','HTTP204 logout; protected access401; actual browser sign-in screen restored',[Q('Manager logout revokes protected access'),B('Browser logout')])
case(5,'Products','Add valid product','Manager; active category','Create P6-BROWSER-20261001 with stock20','Product saved and visible','Saved product visible in browser and independently read from MySQL',[B('Login, category and product creation'),'phase6-browser-persistence.json#/checks/0'])
case(6,'Products','Submit product with missing required field','Manager session','POST product lacking required field','Validation prevents save','HTTP422',[Q('Missing required product field rejected')])
case(7,'Products','Update existing product','Existing manager-owned demonstration fixture','Update product name; read/list; restore normal label','Updated values displayed','Manager update persisted; actual browser displayed edited literal name and restored label',[Q('Manager product update persisted'),B('TC23 script-like text safely rendered')])
case(8,'Products','Attempt duplicate disallowed product identifier','Existing SKU','POST product with same SKU','Duplicate rejected','HTTP409',[Q('Duplicate SKU rejected')])
case(9,'Sales/Inventory','Record valid product sale','Stock20; allocated2; current version2','Record quantity3 at KES120.50','Sale stored and stock adjusted according to defined rules','Browser sale100 persisted; stock17/version3; one linked movement',[B('Operational sale recorded'),'phase6-browser-persistence.json#/checks/1','phase6-browser-persistence.json#/checks/2','phase6-browser-persistence.json#/checks/3',S('Two concurrent sales serialized safely')])
case(10,'Sales/Inventory','Record sale for nonexistent product','Manager; baseline ledger captured','POST nonexistent product','Invalid product reference rejected','HTTP404 and unchanged ledger',[S('Invalid product rejected without ledger changes')])
case(11,'Sales/Inventory','Enter invalid negative sale quantity','Manager; baseline ledger','POST negative quantity','Input rejected','HTTP422 and unchanged ledger; CSV reports negative row',[S('Invalid quantity rejected without ledger changes'),S('Preview reports duplicate/invalid quantity/date/SKU rows')])
case(12,'Sales/Inventory','Import correctly formatted sales file','Manager; active known SKU','Preview UTF-8 CSV; explicitly confirm valid rows','Valid records imported and counted','Live2 accepted/4 rejected retained; browser1 accepted/2 rejected, sale101 quantity50; current stock17 unchanged',[S('Historical confirmation persists valid rows only'),S('Historical quantity exceeding current stock still leaves inventory/audit unchanged'),B('Historical import preview and confirmation'),'phase6-browser-persistence.json#/checks/3'])
case(13,'Forecasting','Forecast product with sufficient valid history','Explicit20728 mapping; compatible365+days; acknowledged UK demo','Origin2011-11-10 horizon28','Forecast returned with product and horizon','Real frozen mean_28 inference matched independent last28day mean;28 points persisted',[D('Actual frozen inference matches independently calculated last-28-day mean'),B('Frozen historical inference'),'phase6-browser-persistence.json#/checks/5'])
case(14,'Forecasting','Forecast product with inadequate history','Unmapped/unsupported product; isolated shortened-history ML fixture','Request forecast; exercise insufficient/gapped-history contract','Useful error or fallback shown','API422 unsupported/unmapped; UI explicit unavailable message; executed ML test rejects insufficient history, never fabricates fallback',[D('Unsupported/unmapped product rejected safely'),'phase6-ml.xml: test_unknown_sku_insufficient_history_and_early_origin; test_invalid_daily_data_rejected'])
case(15,'Forecasting','Malformed forecasting request','Manager; supported product','Request horizon beyond28','Validation error returned','HTTP422',[D('Horizon above contract')])
case(16,'Forecasting','Compare predictions with held-out observed sales','Frozen predictions and evaluation records','Read-only recalculate MAE/RMSE for identical targets','Error metrics calculated and documented','All6 validation and4 final candidates matched saved metrics within1e-10; selected final MAE5.335034014 RMSE17.944563987; MAPE omitted',[ 'phase6-metrics.json','../research/results/final-test.json','../research/results/frozen-selection.json'])
case(17,'Risks/Replenishment','Projected demand exceeds available stock','Historical research context; on-hand17/incoming3/allocated2','Generate decision with lead3/safety4','Stockout risk indicated','Position18 < target87.571428571 -> REPLENISH; deterministic indicator',[B('Explainable historical recommendation'),'phase6-browser-persistence.json#/checks/6'])
case(18,'Risks/Replenishment','Stock exceeds defined excess-stock threshold','Same valid forecast; illustrative stock999','Generate new decision','Overstock condition indicated','Actual OVERSTOCK when position > target×multiplier',[D('Overstock uses strict configured threshold and zero reorder')])
case(19,'Risks/Replenishment','Demand and inventory imply a positive order','Valid lead-time coverage and snapshot','Compute max(0,target-position)','Nonnegative reorder quantity displayed','Browser suggested69.571428571 with every formula component',[B('Explainable historical recommendation'),'phase6-browser-persistence.json#/checks/6'])
case(20,'Risks/Replenishment','Inputs imply no additional stock required','High stock; valid historic forecast','Generate/read overstock snapshot','Zero order displayed with explanation','Suggested0; original formula, stock/configuration/forecast and assumptions preserved',[D('Overstock uses strict configured threshold and zero reorder'),D('Recommendation history remains immutable and chronologically ordered')])
case(21,'Dashboard/Integration','Request dashboard after recording a sale','Active supported fixture and current stock version','Sale then refresh dashboard','Updated stock and visual summaries displayed','Actual browser on-hand17 position18; chart renders; API sale invalidates old snapshot -> UNASSESSED without rewriting',[B('TC21 updated dashboard after sale'),B('Actual charts and comparison'),D('Existing operational sale updates dashboard stock and invalidates old decision')])
case(22,'Dashboard/Integration','Prediction service is temporarily unavailable','Container artifact copied from trusted host; ledger digest baseline','Temporarily hide container artifact; request generation; restore finally','System handles failure without corrupting records','HTTP503; inventory/readiness200; entire operational ledger digests unchanged; artifact restored',[D('Actual missing artifact returns clear 503 without ledger corruption'),D('Inventory API remains usable during real artifact failure'),D('Artifact restored and verified after failure test')])
case(23,'Security','User attempts SQL/script injection in input','Bound ORM queries; actual React browser','SQL-like login; store/render script-like product label','Input safely handled without unauthorized execution','Generic401 SQL-like login; literal script text displayed; zero injected script nodes; no unauthorized access observed',[Q('SQL-like login denied with generic error'),Q('Script/SQL-like product text round-trips as data'),B('TC23 script-like text safely rendered')])
case(24,'Usability/Performance','Representative user completes key workflow','Supervisor approval and consenting representative participants required','Conduct instrument tasks; time completion; collect actual Likert responses','Task completion and response time documented','No participants available (user confirmed). Technical workflow11checks and440request performance run executed, but representative-user task completion/feedback not measured',['../USABILITY_EVALUATION.md','phase6-browser.json','phase6-performance.json'],'PENDING EXTERNAL ACTION')
dump('docs/test-results/final-24-test-cases.json',{'proposal_source':'Table4.1, docs/Smart_Inventory_Consolidated_Five_Chapter_Proposal.docx','proposal_sha256':'9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2','executed_at_utc':datetime.now(UTC).isoformat(),'passed':23,'failed':0,'pending':1,'cases':cases})
table=['# Final proposal-wide test cases','Source: original proposal Table 4.1 (TC01–TC24), independently mapped to actual executed evidence. **23 PASS; 0 final FAIL; 1 PENDING EXTERNAL ACTION.** Earlier failures remain in separate reports and DEVELOPMENT_LOG.md. PASS means this bounded condition was observed, not broad commercial effectiveness. Historical forecasting uses UK2011 research; no valid2026 inference claim.','| ID | Module / objective | Preconditions | Input / action | Expected | Actual | Status | Evidence |','|---|---|---|---|---|---|---|---|']
table+=['| '+' | '.join(str(v).replace('|','/') for v in [c['id'],c['module']+': '+c['objective'],c['preconditions'],c['input_action'],c['expected_result'],c['actual_result'],c['status'],'<br>'.join(c['evidence'])])+' |' for c in cases]
write('docs/test-results/final-24-test-cases.md','\n\n'.join(table[:2])+'\n\n'+'\n'.join(table[2:]))

perf_table='| Mode | Operation | Workers | Requests | Mean ms | p50 ms | p95 ms | Max ms | Errors |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n'
for r in performance['results']:
    perf_table+=f"| {r['mode']} | {r['operation']} | {r['concurrent_workers']} | {r['requests']} | {r['mean_ms']:.2f} | {r['p50_ms']:.2f} | {r['p95_ms']:.2f} | {r['max_ms']:.2f} | {r['errors']} |\n"
write('docs/test-results/PERFORMANCE.md',f'''
# Actual prototype performance measurements

Executed 2026-10-01 against local Docker Desktop/WSL2, MySQL8.4.11, FastAPI and frozen historical inference. Windows11 build26300, HP EliteBook840G5, eight logical processors, approximately15.85GiB installed RAM; native Python3.12.14/httpx client. Measurement uses `perf_counter`, `ThreadPoolExecutor` and NumPy percentiles. Raw statuses and per-request timings: [phase6-performance.json](phase6-performance.json); executable [script](../../scripts/phase6_performance.py).

Normal: one worker × eight requests ×11 operations =88. Modest concurrent: four workers × eight ×11 =352. Total **440 measured requests, zero errors** after the verified fix. Four simulated concurrent workers share one authorized manager identity; each has its own product for writes. This is not four recruited users. Requests are closed-loop per operation, not a sustained mixed retail arrival model. Setup, one actual28-day inference warmup per worker, prerequisite stock GETs and cleanup are outside individual request samples. Total run including setup/cleanup: **{performance['duration_seconds']:.3f}s**. Each result duration is the operation group's wall time. Round trips include HTTP/server/database work; no browser rendering time is inferred.

{perf_table}

Inventory integrity was checked after both workload modes: worker0 stock1000→984 after eight normal sales plus eight concurrent sales; workers1–3 stock1000→992 after eight concurrent sales each. Inventory-update measurements preserve on-hand and increment the audit/version; they do not consume stock. Raw report contains stock and sale-count assertions. Actual same-stock competing-sale verification is separately [43 live checks](phase6-sales-live.json): one201 and one409, one decrement/audit. Worker-specific stress stock alone would not prove same-row integrity.

First run had **four sale HTTP503 responses** under four workers. [Original failure](phase6-performance-first-failure.json) and [InnoDB diagnostic](phase6-innodb-diagnostic.txt) are preserved. InnoDB identified unique-request-key gap-lock deadlocks across different products. A bounded transaction retry now retries only MySQL1213, up to three total attempts, after rollback, with10/20ms backoff. It rechecks stock/version and uses the same UUID. Exhaustion and other database errors remain explicit503; stale/insufficient stock remain409. Three regression cases prove rollback/one-sale success, exhaustion and no retry on connection errors. [Official MySQL deadlock handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html) supports retrying victim transactions. The second full440-request run passed.

Concurrent inference p95 was approximately16.824s and login p95 approximately3.869s: these are material prototype delays, not hidden failures. CPU-heavy hashing/inference and shared-machine contention contribute; this test does not isolate their causal shares. Eight samples per normal operation and32 concurrent samples make tail estimates unstable. The proposal supplies no numerical SLA, so no invented latency threshold is marked passed. No commercial-scale capacity, throughput maximum, long-duration reliability or enterprise SLA is established. Research inference is the acknowledged2011 UK scenario; current2026 forecasts remain unavailable.
''')

python_audit=read('phase6-python-audit.json')
vulnerable=[x for x in python_audit['dependencies'] if x['vulns']]
audit_table='| Package | Installed | Returned records | Distinct advisory IDs | Audit-reported fixes |\n|---|---|---:|---:|---|\n'
for x in vulnerable:
    fixes=sorted({v for a in x['vulns'] for v in a['fix_versions']})
    audit_table+=f"| {x['name']} | {x['version']} | {len(x['vulns'])} | {len({a['id'] for a in x['vulns']})} | {', '.join(fixes)} |\n"
write('docs/test-results/SECURITY_REVIEW.md',f'''
# Bounded academic security verification

Executed 2026-10-01 on localhost. This is neither a penetration test nor a claim that the system is secure. [21 live checks](phase6-security.json), [43 sales/import checks](phase6-sales-live.json), [50 decision checks](phase6-decisions-live.json), [actual browser](phase6-browser.json) and163 backend tests supply the observed evidence. Scripts: `verify_phase6_security.py`, `verify_phase6_sales.py`, `verify_phase6_decisions.py`.

| Control | Actual observation | Evidence |
|---|---|---|
| Password/session storage | Argon2id password hash differs from plaintext; only SHA256 bearer digest stored | security checks1–3 |
| Anonymous/role enforcement |401 anonymous;403 researcher catalog, stock, sale, import, mapping, forecast and recommendation writes; manager writes persist | security/sales/decisions reports |
| Expiry/revocation/lockout | Persisted session expiry set into past ->401; logout revokes; five wrong passwords lock15minutes; correct password still denied while locked; simulated elapsed expiry permits login | security report; test did not wait480minutes |
| Query/text handling | ORM bound-query implementation reviewed; SQL-like login generic401; script-like name round-trips as literal; actual browser zero injected script nodes | security and browser TC23 |
| CSV bounds/identity | Strict columns/dates/positive quantities; >1MiB413; duplicate rows reported; repeat file/confirmation idempotent; overlapping import rolls back | sales/security reports |
| Archives/version/atomicity | Archived sale/import denied; stale inventory version409; audit failure rolls back; competing same-stock sales201/409 | sales report |
| Immutable evidence | Eight MySQL triggers reject direct UPDATE/DELETE on four tables; old snapshots unchanged | decisions report |
| Git exclusions | `.env`, backend/.env, ignored `.local` account and audit environment match ignore rules | security report |

The repository currently has no tracked source files/commit. Ignore checks establish local exclusions, not an audited committed history or proof that no secret exists anywhere. Test reports never publish bearer tokens or passwords. Local authorized account credentials remain in ignored `.local/verification-account.json`; raw retail customer IDs are excluded from inference exports/images. Joblib is loaded only from trusted frozen files, never from uploads. Digest checks do not make attacker-controlled artifacts safe.

Host and container `pip check` pass ([stack report](phase6-stack.json)); this checks dependency consistency, not vulnerabilities. `pip-audit` was safely installed in isolated `.local/audit-venv`, leaving application/frozen ML dependencies unchanged. Scanned actual installed versions using frozen installed-package list, `--no-deps --disable-pip`; tool warns that fully hashed requirements are preferable. Audit exited1 with **26 returned records across three packages,14 distinct(package, advisoryID) pairs**; duplicate IDs/aliases mean26 is not26 independent vulnerabilities. [Raw Python audit](phase6-python-audit.json), [warnings/output](phase6-python-audit.txt).

{audit_table}

Frontend `pnpm audit --json` also exited1: **10 advisory entries:2low,5moderate,2high,1critical**. Seven concern Vite6.3.5 (reported patch levels6.3.6–6.4.3); two Vitest3.1.3 (critical fixed3.2.6, another4.1.11); one @vitest/mocker (4.1.11). [Raw frontend audit](phase6-frontend-audit.json) includes advisory URLs and affected paths. Vitest/pytest are development tools; no Vitest UI was launched. Vite is the local Compose development server, so its advisories cannot be dismissed solely as dev dependencies. Exploit reachability was not established for every advisory. Dependency consistency and passing functional tests do not negate audit findings.

**Unresolved:** dependency advisories, upstream Starlette/AnyIO warning, TLS and deployment hardening, shared-edge rate limiting, broader input/authorization attack coverage and security assessment. A reviewed dependency-upgrade increment is recommended before any remote deployment. FastAPI0.115.12 constrains Starlette; replacing it blindly with1.x would require compatible framework upgrades and regression. No forced major upgrades or frozen ML dependency changes occurred in Phase6. Local services bind127.0.0.1; localhost HTTP is unsuitable as an assumed remote-production configuration.
''')

compat_rows='| Browser / version | Login | Navigation | Product/inventory | Sales form | Import | Dashboard/chart | Logout | Result |\n|---|---|---|---|---|---|---|---|---|\n'
compat_rows+='| Edge154.0.4258.48 | Observed | Observed |17/3/2 observed | Observed | Observed | Real curves and tooltip; current UNASSESSED | Sign-in screen observed | Bounded PASS |\n'
compat_rows+='| Chrome154.0.8037.59 | Observed | Pages opened | Opened; final values unverified | Opened | Opened | Loading only; chart unverified | Not executed | PARTIAL |\n'
compat_rows+='| Firefox156.0.1 | Not executed | Not executed | Not executed | Not executed | Not executed | Not executed | Not executed | BLOCKED BY TOOL POLICY |\n'
write('docs/test-results/COMPATIBILITY.md',f'''
# Actual browser compatibility observations

{compat_rows}

Versions come from installed executable ProductVersion properties. Chrome and Edge are installed under Program Files; Firefox is installed under Program Files/Mozilla Firefox. The full transaction workflow was separately executed in the Codex in-app Chromium browser ([11 checks](phase6-browser.json)); its engine version was not read and is not substituted for a Chrome/Edge/Firefox result.

Edge used native Windows UI after the browser connector was unavailable. The actual UI showed the product, stock17/incoming3/allocated2, sales fields, CSV preview controls, dashboard position18/UNASSESSED, historical20728 chart lines and hover value27.857142857, immutable recommendation69.571428571, and sign-in after logout. Immediate AX text after clicks could lag the screenshot; the logout result uses the observed sign-in screenshot. [Edge dashboard AX evidence](phase6-edge-dashboard.txt), [real chart screenshot](../screenshots/final/compatibility-edge-chart.jpg), [structured observations](phase6-compatibility.json). Native window was resized/maximized during navigation and later restored by the UI; no responsive/mobile guarantee follows.

Chrome initially accepted login/navigation but CDP screenshot timed out, CUA kernel timed out, and request-header policy could not load. Final chart/logout checks are unexecuted, not successful. Firefox launched; selecting its native window **stopped Computer Use because URL-policy enforcement is unsupported for that Windows browser**. Browser automation stopped at that boundary; no alternate browser-control workaround was used. No Firefox application result is asserted. These are tooling limits, not evidence of application defects.

**Pending:** complete Chrome chart/logout and Firefox checklist using a supported approved automation surface or supervised manual testing. Edge's bounded result does not establish universal cross-browser compatibility. No mobile, assistive-technology or accessibility certification was performed.
''')

write('docs/USABILITY_EVALUATION.md','''
# Usability evaluation instrument — pending external participation

**Status: PENDING EXTERNAL ACTION.** The user confirmed no participants are available. This instrument is prepared for supervisor review; no supervisor approval, recruitment, consent, task responses or Likert findings are claimed. Technical automated browser checks are not human usability evidence. TC24 remains pending.

Before recruitment, obtain the supervisor's approval of protocol/participants and any applicable university/outlet permission. Invite a small feasible group of relevant retail stock/sales managers and researchers, recording the actual number and role categories when conducted. The proposal discusses approximately20–30personnel for requirements elicitation; that planned figure is not an achieved sample or mandatory fabricated final response count. No outlet interviews or requirements questionnaires have been conducted in this implementation; requirements derive from the proposal and user instructions.

Consent script: this is a voluntary undergraduate prototype study, not an employee assessment. Participants may skip a question or stop without disadvantage. Explain tasks, approximate session duration, data collected (coded task success/time, role category, ratings and comments), who sees anonymized results, and agreed retention/deletion date. Use participant codes only; do not publish names, emails, passwords or identifying employer details. Obtain actual consent before timing/recording. No automated purchasing occurs. Demonstrate only synthetic stock and clearly labelled historical UK forecasts; these do not validate Kenyan performance.

| Task | Starting condition / action | Observable success |
|---|---|---|
| U1 | Authorized study account; sign in and locate Products/Inventory | Identifies correct page without credential disclosure |
| U2 | Manager uses a dedicated synthetic study category/SKU; add/edit product | Correct SKU/category/lead time/safety recorded |
| U3 | Review/adjust dedicated test stock using a reason | Correct on-hand/incoming/allocated and new version understood |
| U4 | Record a small operational sale; view chronological history | Recognizes sale decreases usable stock and sees stored transaction |
| U5 | Preview prepared CSV with valid, duplicate and invalid rows; confirm valid-only | Identifies rejected rows and explains historical import does not change current stock |
| U6 | Inspect stored acknowledged2011 UK forecast and accessible daily table | Identifies product/origin/horizon/units and says it is not a current Kenyan forecast |
| U7 | Inspect stored risk/reorder snapshot | Explains position, lead time, safety, target, reorder and human-review boundary |
| U8 | Review current dashboard/history and sign out | Distinguishes UNASSESSED from adequate; protected session ends |

Record start/end with a monotonic timer, task duration seconds, completion(success/partial/fail), assistance/attempt count and observed errors. Fix allowable assistance prompts before sessions; label assisted completion. Do not use API latency as a substitute for human task time. The facilitator should provide identical instructions and avoid leading prompts. Researcher role can review U1/U3/U5–U8 but must not be asked to bypass server write restrictions.

5-point scale:1strongly disagree,2disagree,3neutral,4agree,5strongly agree. After tasks ask: (1) login/navigation was easy; (2) product/stock views were clear; (3) sale/import feedback was clear; (4) forecast period/units were understandable; (5) risk labels were understandable; (6) reorder quantity and assumptions were understandable; (7) dashboard information was useful for reviewing stock; (8) overall application was easy to use. Add open comments: confusing point, helpful part, suggested improvement. Allow N/A separately and never convert it to3.

Blank response record fields: participant code; role category; consent yes/no; instrument version; actual date; taskID; start/end/duration; completion; help/errors; Q1–Q8(each1–5orN/A); comments. There are **zero collected responses**. After real sessions, report actual n, distributions/median per item, missing/N/A counts, task success and median/range time, assistance, anonymized themes and recruitment limitations. Small convenience samples do not prove commercial acceptance, improved stockout rates or Kenyan forecasting accuracy. Do not manufacture aggregate percentages or apply an unvalidated pass cutoff. Update TC24 only from actual participant evidence.
''')

write('docs/OBJECTIVE_TRACEABILITY.md','''
# Research objective traceability

Requirements authority: original proposal, section1.3.2 and Table4.1. Evidence distinguishes actual retail research from synthetic software scenarios and human evaluation still pending.

| Specific objective (verbatim) | Implemented/evaluated work | Actual evidence | Conclusion and limit |
|---|---|---|---|
|1. Analyze historical retail sales data and identify patterns and factors associated with product demand. | UCI provenance/quality audit; training-only60-SKU EDA; daily/weekday/monthly/price/intermittency tables | [Dataset](research/DATASET.md), [EDA](research/EDA.md), [training trend](research/eda/training-trend.png), [weekday/zeros](research/eda/weekday-and-zeros.png), [monthly](research/eda/monthly-seasonality.png), [SKU table](research/eda/sku-summary.csv) | VERIFIED bounded UK case study:71.23%zero days, weak median lag7association. Associations are not causal effects; missing inventory/promotions/store data; no Kenyan inference. |
|2. Evaluate selected machine-learning models for forecasting future retail product demand. | mean/seasonal baselines, two RF/two XGBoost configurations; chronological expanding validation; selection frozen before final labels;60×28final targets | [Protocol](research/EXPERIMENT_PROTOCOL.md), [Comparison](research/MODEL_COMPARISON.md), [Final model](research/FINAL_MODEL.md), [selection](research/results/frozen-selection.json), [actual metrics verification](test-results/phase6-metrics.json), [31 hashes](test-results/phase6-preservation.json) | VERIFIED mean_28selected on validation MAE4.753635; final MAE5.335034/RMSE17.944564. Seasonal naive has lower final error; winner not changed. MAPE omitted for1169/1680zeros. No retraining/replacement inPhase6. |
|3. Develop an inventory decision approach that uses forecast demand to identify stockout and overstock risks and recommend replenishment quantities. | Position=on-hand+incoming−allocated; lead-demand+safety target; target×multiplier excess threshold; max(0,target−position); immutable reasoned snapshots | [Rules](DECISION_SUPPORT.md), [50 live checks](test-results/phase6-decisions-live.json), [actual browser persistence](test-results/phase6-browser-persistence.json), [recommendation screen](screenshots/final/recommendation.jpg) | VERIFIED deterministic synthetic scenario:position18,target87.571428571,reorder69.571428571; overstock/zero alternative separately verified. No purchase execution, service-level probability or measured stockout reduction. |
|4. Evaluate the forecasting accuracy and decision-support effectiveness of the proposed system. | Held-out metrics,251automated tests,23executed proposal cases,liveMySQL/API,browser,performance,security,compatibility observations; prepared usability instrument | [24-case table](test-results/final-24-test-cases.md), [Testing](TESTING.md), [Performance](test-results/PERFORMANCE.md), [Security](test-results/SECURITY_REVIEW.md), [Compatibility](test-results/COMPATIBILITY.md), [Usability](USABILITY_EVALUATION.md), [Chapters4/5](academic/CHAPTER_4_EVIDENCE.md) | PARTIALLY VERIFIED: historical forecasting accuracy and software rule behavior supported. Representative-user effectiveness pending; Chromepartial/Firefoxunexecuted due tooling; dependency advisories unresolved. No demonstrated Kenyan/commercial effectiveness. |

FR1–FR9 are traced in [requirements](REQUIREMENTS.md) and final cases: authentication01–04; catalog05–08; sales/inventory/import09–12; forecasting/evaluation13–16; risk/replenishment17–20; dashboard/failure21–22; injection23; representative-user24pending. Category, audit, concurrent-sale, version and role supplements are in full backend/live suites. NFR usability is pending participants; performance has measured results without numerical SLA; security has bounded checks plus advisories; reliability has MySQL rollback/concurrency; maintainability has tiers/migrations/reproduction; compatibility remains bounded/partial; explainability is shown by actual snapshots.

Compatible UCI development history ends2011-11-10; raw dataset ends2011. Stored historical model evaluation is valid only for its held-out2011window. Current2026requests are intentionally rejected/unassessed. Recent compatible product history and a separately approved validation/research increment are needed for genuine current forecasts; no dates, winner or frozen results were changed for presentation.
''')

write('docs/SYSTEM_LIMITATIONS.md','''
# System and research limitations

This is an undergraduate local prototype with genuine historical forecasting experiments and verified deterministic software behavior. It has not established commercial effectiveness or current Kenyan forecasting accuracy.

- Data: one UK online gift/wholesale retailer,2009–2011, pricesGBP;60training-selectedSKUs and fixed28-dayhorizon. Application operational pricesKES do not convert research prices or transfer UK accuracy to Kenya. No store/category/promotion, supplier ETA, availability or unmet-demand labels exist.
- Historical validity: compatible application history ends2011-11-10. The frozen historical artifact is not a valid current2026source. Unsupported/stale/current requests fail intentionally; current dashboard UNASSESSED is not adequate/safe. Recent compatible history, source agreement and approved evaluation are required for current deployment; supplying arbitrary application CSV alone does not make it a compatible forecasting dataset.
- Research design: one final28-daywindow, two validation origins, no significance intervals or causal feature effects. Pooling conceals poor individual series; wholesale extremes and intermittent demand remain. Seasonal naive beat selectedmean_28on final error; selection remains validation-based. MAPE omitted for zero/intermittent targets. Demand is recorded gross purchased units, not uncensored latent demand.
- Decisions: fixed safety stock and configurable supplier lead time; all confirmed incoming assumed within lead time without ETA; deterministic target/risk rather than calibrated stockout probability; fractional raw shortage without pack/cost rounding. No global inventory optimum, measured financial benefit, achieved service level or reduced-stockout experiment.
- Operational scope: no automatic procurement, supplier-network optimization, ERP, returns/correction workflow, production hosting or external integration. Sales cannot consume allocated stock or incoming stock. Histories preserve archived identities; frontend uses bounded pagination rather than enterprise reporting.
- Evaluation:251automated tests and23proposal conditions passed; TC24requires representative participants. No supervisor-approved field requirements interviews or participant usability responses exist. Instrument prepared only. Full browser workflow is technical automation, not human feedback.
- Performance:440localhost requests at1/4workers; inference p95~16.824s concurrent, login~3.869s. No SLA existed, enterprise capacity or sustained-load certification. Shared development machine and small sample limit inference.
- Compatibility: Edge bounded smoke verified; Chromepartial; Firefox policy-blocked before application testing. No universal browser, mobile or accessibility claim.
- Security: bounded verification, not penetration testing. Python audit26records/14distinct advisoryIDpairs across3packages, frontend10entries includingcriticaldevtool advisory remain. Framework/dependency upgrades and deployment hardening need review before remote exposure. One Starlette/AnyIO deprecation remains.
- Reproduction: startup verified safely on an isolated newComposevolume with packaged trusted frozen model and development history. Ignored raw/processed/binary files must be supplied by the trusted academic bundle; a source-only checkout lacks them. No repository commit exists, so SHA fingerprints serve as research identity. No cold-cache build or arbitrary-hardware certification is claimed.

No Phase4results/model/MLsources were altered. Recommendations require human review and never execute purchases. See [test results](TESTING.md), [objective traceability](OBJECTIVE_TRACEABILITY.md) and [Chapter5](academic/CHAPTER_5_EVIDENCE.md) for claim boundaries.
''')

write('docs/INSTALLATION_GUIDE.md','''
# Installation and safe reproduction

Tested environment: Windows11, Python3.12.14, nativeNode24.19.0/pnpm11.19.0, DockerDesktopWSL2 with Compose; containerPython3.12/Node22/MySQL8.4.11. No external account required. Install Docker/these runtimes by approved normal methods if absent. Commands below start from project root in PowerShell. Keep secrets local.

## Trusted academic bundle

Source, pinned requirements and frontend lockfile are required, together with `docs/research/results/`, `backend/app/core/phase4-reference.json`, `ml/artifacts/uci-retail-v1-0cc2a83c3e40/selected.joblib` and `data/processed/phase4/development.csv`. Binary/data are ignored by Git. Preserve the original trusted Phase4bundle; do not run training/final-evaluation/export commands over the frozen directory. If files are absent, stop forecasting setup and obtain the trusted bundle or use the separately documented isolated research reproduction process in ml/README.md after appropriate authorization. Never deserialize user-supplied joblib.

## Local Compose startup

```powershell
python scripts/create_local_env.py
docker compose up --build -d
docker compose ps --all
docker compose exec -T backend alembic current
docker compose exec -T backend alembic check
docker compose exec backend python -m app.bootstrap --email manager@example.com --name "Inventory Manager"
```

Environment generator preserves existing.env and generates URL-safe local MySQL passwords. Bootstrap prompts privately for a new strong password; no default/public administrator or self-registration. It must run in a usable terminal (not log passwords). Open http://localhost:5173; APIreadiness http://localhost:8000/api/v1/health/ready; OpenAPI http://localhost:8000/docs. Current head e52ad70491b2; no pending upgrade operations. Compose waits for healthy DB, runs migrations, then starts API. MySQL3306/API8000/UI5173bindlocalhost. MySQLdata stays in named volume; **never run down-v, reset, drop or migration downgrade without approval**. `docker compose stop` retains data. This is a devserver prototype launcher, not production hosting.

If Docker is absent from PATH on the evaluated machine, CLI is `C:/Users/user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe`. The local-development trigger configuration is documented in DATABASE.md; do not grant globalSUPER or change deployment replication settings casually.

## Native test environment

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
.venv/Scripts/python.exe -m pip install -r ml/requirements.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/local-backend.xml
.venv/Scripts/python.exe -m pytest ml/tests --junitxml=docs/test-results/local-ml.xml
Push-Location frontend
pnpm install --frozen-lockfile
pnpm test --reporter=junit --outputFile=../docs/test-results/local-frontend.xml
pnpm build
Pop-Location
.venv/Scripts/python.exe scripts/phase6_preservation.py
.venv/Scripts/python.exe scripts/phase6_infer.py
```

Backend unit/integration tests use temporary SQLite; actual MySQL is tested separately. ML tests fit synthetic tiny models only, never retrain selected research artifact. NativeMLrequirements include NumPy/Pandas/sklearn/XGBoostversions matching frozen metadata. `phase6_infer.py` performs real historical20728/2011-11-10/28inference and writes only a new test-results report. Original `ml.cli infer` writes `last-inference.json`, so do not use it in-place on preserved Phase4evidence. No current2026forecast is available. Frontend tests mock network; actual API/browser checks establish deployed behavior. Dependency audits have unresolved advisories; passing pipcheck alone is not a security guarantee.

## Isolated reproduction actually executed

`.venv/Scripts/python.exe scripts/phase6_reproduce.py` uses ignored `.local/phase6-repro/.env`, project `smartinventory-phase6-repro`, new project-scoped mysql_data, ports3307/8001/5174and explicit Compose overrides. First invocation created the environment/new volume and applied all migrations; later reruns safely reused that isolated volume. CLI account/login/read/logout/revocation/frontend/readiness/pipcheck/frozeninference pass in final report. Account credentials remain ignored. The script stops only its temporary services after success and deletes no volume. [Final report](test-results/phase6-reproduction.json), first/second harness failures retained alongside it. Existing development DB/volume were not reset.

The backend/ML/frontend full suites and build were executed on the main evaluated checkout, not inside the fresh isolated volume; that distinction matters. Fresh container dependency consistency and startup were verified, but no cold-cache/source-only missing-artifact success is claimed. Live fixture scripts use the ignored verification account and tagged records; read their scope before running. The decision verifier temporarily hides/restores the container artifact to test503failure and should run sequentially with other forecasting checks. See DEVELOPMENT_LOG.md for exact executed commands.
''')

write('docs/USER_MANUAL.md','''
# User manual

Local prototype: http://localhost:5173. Only use an authorized account created by the administrator CLI; no public registration or default credentials. Managers modify operational records and generate evidence; researchers read. The server enforces roles. Original stock/research snapshots remain auditable after archive.

## Login and navigation

Enter authorized email/password, select Sign in. Wrong/locked/disabled credentials produce a safe generic message; five wrong attempts lock15minutes. Session expires after480minutes; reload requires sign-in because the token is held in memory. Do not share credentials. Choose workspace page buttons. [Actual login](screenshots/final/login.jpg).

## Categories and products

Create an active category, then a unique SKU/name/category/unit product. Set initial on-hand once, positive lead-time days, nonnegative safety stock and overstock multiplier>1. SKU is normalized uppercase; archived SKUs remain reserved. Edit metadata/settings separately from stock. Archive preserves history; categories with active products cannot be archived. Show archived records permits historical viewing/restoration where supported. [Categories](screenshots/final/categories.jpg), [Products](screenshots/final/products.jpg).

## Inventory and audit

Select product; review on-hand, confirmed incoming, allocated, version and timestamp. Enter all stock components and a meaningful adjustment reason. Nonnegative quantities and allocated≤on-hand are enforced. A stale edit409means reload and review before resubmission. View movements to see opening/adjustment/sale actor and before/after stock. [Inventory](screenshots/final/inventory.jpg), [after-sale audit](screenshots/final/inventory-history.jpg). Browser demonstration20→17is an actual test sale, not genuine customer trade.

## Sales and history

Manager selects active product, positive quantity, actual sale date/time and optional nonnegative KESunitprice. The sale consumes unallocated on-hand immediately, even if backdated. Incoming does not authorize sale. Submit once; an unchanged UUID retry is idempotent. Insufficient/stale stock returns409; archived/invalid product is rejected. Reload before a new attempt when stock changed. History supports product/date/user/source filtering with pagination and newest-first sale time. [Entry](screenshots/final/sales-entry.jpg), [history](screenshots/final/sales-history.jpg).

## Historical CSV import

Use historical import only when stock impact is already accounted for. UTF-8CSV required columns `sku,sale_date,quantity`; optional `unit_price,external_id`. Use ISOtimestamp with timezone, positive finite quantity, optional KESprice. Limit1MiB/5000rows. Choose file, Preview CSV, review accepted/rejected rows, tick explicit valid-only acceptance and Confirm historical import within30minutes. **Historical import never changes current inventory or adds stock movements.** Rejected rows are retained. Duplicate identity uses product+externalID or normalized content; provide different externalIDs for distinct identical sales. Exact repeated file/confirmation does not duplicate history. Re-preview expired/stale/conflicting preview. [Actual1valid/2rejected preview](screenshots/final/csv-import-preview.jpg).

## Forecasts and recommendations

Dashboard shows actual current inventory; with this2011UKartifact, current forecasts are unavailable and risk is UNASSESSED, which does not mean adequate. No arbitrary mapping or date shift is performed. For an authorized historical research demonstration only, acknowledge UK/notKenyan limitation, explicitly map a supported SKU such as20728 with reason and individual-countunit, and select research context. Generate origin2011-11-10/horizon≤28; old snapshots remain visible and immutable. The chart/table contains verified UKhistorical demand and stored predictions, not current Kenyan demand. [Forecast](screenshots/final/forecast.jpg), [comparison](screenshots/final/model-comparison.jpg). Mean_28won validation; seasonal naive had lower final error, which does not change selection.

Choose a stored forecast and generate a dated research decision2011-11-11only when lead-time coverage is sufficient. Read position=on-hand+incoming−allocated; target=lead-time demand+safety; raw/suggested reorder=max(0,target−position); excess threshold=target×multiplier. All assumptions, version, model/digest and origin are displayed. Incoming is assumed within lead time; no ETA/pack rounding. Stock/config changes make earlier snapshot nonapplicable but never rewrite it. Research stock examples are synthetic, not measured2011inventory. **Human review is required; no purchase executes.** [Recommendation](screenshots/final/recommendation.jpg).

## Dashboard, errors and logout

Overview shows current stock components, positions and applicable status counts. Refresh after transactions; compare current versus historical context carefully. Unsupported products lack a forecast; missing/corrupt artifact gives503while operational inventory remains usable. Expired sessions return to sign-in. Inspect persistent histories for explanations rather than treating UNASSESSED as safe. [Dashboard](screenshots/final/dashboard.jpg). Select Sign out; protected session is revoked on the server and sign-in returns. Browser automation is technical evidence only; no participant usefulness rating has been collected.
''')

write('docs/research/PHASE6_REVIEW.md','''
# Phase 6 review of preserved research documentation

Reviewed DATASET.md, EDA.md, EXPERIMENT_PROTOCOL.md, MODEL_COMPARISON.md and FINAL_MODEL.md against original proposal, actual result JSON/CSV, registered digest and source fingerprints. These documents record Phase4chronology; phrases such as “integration is Phase5work” are historical scope statements, superseded for application status by DECISION_SUPPORT.md/API.md. Their recorded research results and selection remain unchanged. No retraining, replacing, test-driven tuning or rewriting final predictions occurred.

New read-only verification [phase6-metrics.json](../test-results/phase6-metrics.json) recalculates all six validation/four final scores from saved predictions within1e-10. [phase6-preservation.json](../test-results/phase6-preservation.json) verifies18protected evidence/artifact files and13source/protocol/dependency fingerprints. Updated runtime application/academic documentation references these originals rather than manufacturing a new experiment.

Valid conclusions:60-SKUbounded UKhistorical observed-sales case study; training-only analysis; validation selection before final labels; final2011window; zero/intermittentMAPEomission; meanbaselinewonvalidation; seasonal naive lower final error; weak/variable per-series results retained. Invalid conclusions: current2026forecast validity, Kenyan accuracy, causal price/calendar effects, commercial stockout/cost reductions or participant satisfaction. Recent compatible history and separately approved evaluation are needed for current use. Original CLI infer writes a preserved report; use the new read-only Phase6inference script for demonstration.
''')

ml_table='| Candidate | Validation MAE | Validation RMSE | Final MAE | Final RMSE |\n|---|---:|---:|---:|---:|\n'
val=json.loads((ROOT/'docs/research/results/validation.json').read_text())['scores']
final=json.loads((ROOT/'docs/research/results/final-test.json').read_text())['scores']
for model in ['mean_28','seasonal_naive','rf_leaf5','rf_leaf15','xgb_depth5','xgb_depth3']:
    f=final.get(model)
    ml_table+=f"| {model} | {val[model]['mae']:.6f} | {val[model]['rmse']:.6f} | {f['mae'] if f else 'Not final-tested'} | {f['rmse'] if f else 'Not final-tested'} |\n"

write('docs/academic/CHAPTER_4_EVIDENCE.md',f'''
# Chapter 4 — actual implementation and evaluation evidence

This is an evidence draft for the Maseno University BSc project. The original proposal remains the requirements authority. Evaluation was executed on 2026-10-01. Sources distinguish frozen historical research from synthetic application verification; no field findings are invented.

## 4.1 System Code Generation

Implemented React/Vite/Tailwind/Recharts presentation, FastAPI/Pydantic HTTP validation, SQLAlchemy operational and decision services, MySQL InnoDB persistence, and an independent Python/Pandas/NumPy/scikit-learn/XGBoost research module. Source directories are `frontend/src`, `backend/app`, `backend/alembic` and `ml`. Pinned dependencies and Compose configuration support setup. Managers modify records; researchers read. Archives, stock versions, audit history, atomic sales and previewed historical imports are implemented. Phase 6 added evaluation scripts/documentation and a verified MySQL deadlock retry fix with three tests. No new architecture, forecasting model or procurement execution was added.

## 4.2 System Integration

The modular N-tier application uses a localhost frontend proxy and versioned API. MySQL is at migration head e52ad70491b2. Database health, migration consistency, host/container dependency consistency, API/frontend HTTP 200 and persistence were checked. See [architecture](../ARCHITECTURE.md), [database](../DATABASE.md), [API](../API.md) and [stack evidence](../test-results/phase6-stack.json). Sales lock stock, reject overselling/stale writes and commit sale, stock and audit together. Historical imports never adjust current stock. The forecast adapter verifies the trusted frozen model and history; generation appends immutable evidence without changing the operational ledger. Isolated startup, authorized account creation, login/logout and read-only inference passed while preserving the existing database ([reproduction](../test-results/phase6-reproduction.json)).

## 4.3 Machine Learning Implementation

UCI Online Retail II contains 1,067,371 actual transactions from a UK retailer during 2009–2011. The study uses 60 eligible SKUs selected using training data. Initial training ends 2011-09-15; expanding validation origins are 2011-09-15 and 2011-10-13. Final origin 2011-11-10 forecasts 2011-11-11 through 2011-12-08. RF/XGBoost use prior-only lags, shifted rolling statistics, known calendar values and lagged prices. Future demand/prices are excluded. Two baselines and two configurations per tree family were compared. Selection used validation MAE, then RMSE/name, and was frozen before final labels. Selected **mean_28** uses the last 28 observed quantities: the experiment legitimately selected a baseline. See [protocol](../research/EXPERIMENT_PROTOCOL.md), [EDA](../research/EDA.md) and [final model](../research/FINAL_MODEL.md). No Phase 6 retraining or result rewriting occurred; 31 protected hashes remain unchanged.

## 4.4 Testing

Final full suites: **163 backend + 59 ML + 29 frontend = 251 tests**, with zero failures/skips. Backend reports one upstream Starlette/AnyIO deprecation; ML/frontend report no warnings. JUnit times are 85.320, 14.164 and 7.094 seconds respectively; backend console time is 85.36 seconds. Frontend duration is the report's root time. Production build passed: 621 modules in 9.35 seconds. See [testing](../TESTING.md), [backend JUnit](../test-results/phase6-backend.xml), [ML](../test-results/phase6-ml.xml), [frontend](../test-results/phase6-frontend.xml) and [build](../test-results/phase6-build.txt).

### 4.4.1 Unit Testing

Pytest covers authentication, catalog, constraints, CSV parsing, decision contracts and failure paths. Synthetic ML fixtures test chronological alignment, leakage, zeros, gaps, schema, serialization, versions and determinism. Vitest/Testing Library uses mocked API responses with genuine comparison records. Full suites include unit and integration cases; the 251 total is not a count of pure unit tests. Three new backend cases exercise transient deadlock rollback/retry, retry exhaustion and a connection error that must not retry. These tests never fit the selected research artifact.

### 4.4.2 Integration Testing

Actual MySQL/API verification executed 43 sales/import checks, 50 forecast/decision checks, 21 security checks and seven read-only browser persistence checks, plus startup/migration checks. SQLite alone does not establish locking semantics. Simultaneous sales against the same stock returned 201/409; an injected audit failure rolled back sale/stock writes. Repeated files/rows were handled explicitly. Eight database triggers reject immutable UPDATE/DELETE. A temporarily missing container artifact returned 503 with operational table digests unchanged and inventory/readiness returning 200; the artifact was restored in finally. Reports are in `docs/test-results/phase6-*-live.json`, `phase6-security.json` and `phase6-browser-persistence.json`.

### 4.4.3 Functional Testing

All 24 original conditions have a recorded outcome: **23 PASS; TC24 PENDING EXTERNAL ACTION**. See [conditions/actions/expectations/results](../test-results/final-24-test-cases.md). The actual in-app browser traversed login, category/product, inventory, operational sale, historical import preview/confirmation, explicit UK mapping, valid historical forecast, recommendation, dashboard/history and logout. Eleven checks and 13 core screenshots were recorded. Independent MySQL reads establish sales 100/101 and stock 17/version 3. See [workflow](../test-results/phase6-browser.json) and [screenshots](../screenshots/final/README.md). This is technical automation, not a representative-user study.

### 4.4.4 Performance Testing

Real httpx timing measured 88 normal requests with one worker and 352 requests with four workers: 440 total. The final run had zero errors and took 246.120 seconds including setup/cleanup. The first run had four sale 503 deadlock victims; the diagnostic and bounded transaction retry fix are recorded. The repeat run passed. Concurrent inference p95 was about 16.824 seconds; login p95 was about 3.869 seconds. These are material delays. See [latencies/method/machine](../test-results/PERFORMANCE.md) and [raw samples](../test-results/phase6-performance.json). No SLA or enterprise capacity is claimed.

### 4.4.5 Usability Testing

**Pending: zero participants and zero responses.** The user confirmed no participants are available. The task, consent, Likert and comment instrument is prepared for supervisor review. No approval, recruitment or favorable ratings are invented. See [instrument](../USABILITY_EVALUATION.md). Human task timing, usefulness and outlet requirements elicitation remain external work.

### 4.4.6 Security Testing

Bounded verification observed password/session hashing, server authorization, expiry/revocation/lockout, query/text handling, CSV limits/duplicates, archive/version rules and Git exclusions. Script-like input rendered literally with zero injected nodes. Dependency consistency passes, but audits returned 26 Python records/14 distinct advisory-ID pairs across three packages and 10 frontend entries, including a critical development-tool advisory. Findings remain unresolved; no penetration-test or overall security claim is made. See [review](../test-results/SECURITY_REVIEW.md).

### 4.4.7 Compatibility Testing

Edge 154.0.4258.48 rendered login, navigation, stock, forms, import, dashboard chart and logout. Chrome 154.0.8037.59 testing is partial due to CDP/kernel/header-policy failures; final chart/logout remain unverified. Firefox 156.0.1 was installed and launched, but selecting its window stopped Computer Use because Windows browser URL-policy enforcement is unsupported. No Firefox application result is asserted. See [matrix](../test-results/COMPATIBILITY.md). Universal compatibility is not claimed.

## 4.5 Machine Learning Results

{ml_table}

All six validation candidates use 3,360 identical targets; all four finalists use 1,680 targets. MAPE is omitted because 1,169 final actuals are zero; no epsilon or hidden positive-only subset is used. Selected mean_28 final MAE is 5.335034 and RMSE is 17.944564. Seasonal naive has lower final error; selection remains validation-based. Weak individual series are retained, including SKU 22595 with MAE 80. No significance or universal accuracy claim follows. Read-only recalculation matched all ten score sets within 1e-10: [metrics](../test-results/phase6-metrics.json), [comparison figure](../research/results/model-comparison.png), [per-SKU errors](../research/results/final-test-by-sku.csv) and [representatives](../research/results/representative-final-forecasts.png).

## 4.6 Inventory Decision-Support Results

The browser's synthetic SKU P6-BROWSER-20261001 was explicitly linked to UK series 20728. Forecast origin is 2011-11-10 for 28 days; recommendation date is 2011-11-11. Stock 17 + incoming 3 − allocated 2 gives position 18. Three daily predictions total 83.571428571; safety stock 4 gives target 87.571428571. Multiplier 2 gives threshold 175.142857142. Suggested reorder 69.571428571 yields REPLENISH. Immutable forecast 4a1f9161-32f8-4559-b724-62f80907e944 and recommendation af82e6f7-3339-4455-bc8b-45d51b85c509 were independently read from MySQL. Historical quantity 50 did not change stock 17. A separate API stock-999 scenario produced OVERSTOCK/zero reorder while preserving the earlier decision. See [persisted formulas](../test-results/phase6-browser-persistence.json), [screen](../screenshots/final/recommendation.jpg) and [rules](../DECISION_SUPPORT.md).

All confirmed incoming is assumed to arrive within lead time; there is no ETA, pack/cost or probabilistic optimization. Synthetic 2026 test stock paired with a UK 2011 forecast is a demonstration, not measured 2011 inventory or economic effectiveness. Current inventory remains UNASSESSED and unsupported/current forecast requests are rejected. Recommendations require human review and execute no purchase.

## 4.7 Summary

Software integration, bounded transaction/decision behavior and genuine historical forecasting evidence are verified. Participant usefulness, complete Chrome/Firefox compatibility and dependency remediation remain outstanding. UK data ending in 2011 cannot validate current 2026 or Kenyan accuracy. See [objective traceability](../OBJECTIVE_TRACEABILITY.md) and [limitations](../SYSTEM_LIMITATIONS.md).
''')

write('docs/academic/CHAPTER_5_EVIDENCE.md','''
# Chapter 5 — evidence-based findings and conclusions

## 5.1 Introduction

This draft relates actual historical research and prototype evaluation to the four specific proposal objectives. No field respondents, current Kenyan forecasts, commercial benefits or security/compatibility certification are inferred from technical tests. See [objective matrix](../OBJECTIVE_TRACEABILITY.md) and [Chapter 4 evidence](CHAPTER_4_EVIDENCE.md).

## 5.2 Summary of Findings

Objective 1: analyzed a training-only sample of 60 SKUs from actual UCI Online Retail II UK sales. Training contains 37,753 SKU-days and 26,891 zero days (71.23%). Median lag-7 correlation is 0.046; median price-demand association is −0.069. Tables/plots show intermittency, weekday differences and extreme purchases. These descriptive associations do not establish causal demand factors. No inventory, promotion, store or Kenyan observations exist.

Objective 2: compared two baselines and selected RF/XGBoost configurations chronologically. Validation MAE selected mean_28 (4.753635), frozen before final labels were opened. On 1,680 final targets its MAE is 5.335034 and RMSE is 17.944564. Seasonal naive performed better on the final window: MAE 4.939881 and RMSE 17.008524. The selected model was not changed using test results. MAPE is omitted for zero/intermittent data; weak series remain in the results. Phase 6 read-only verification matches frozen metrics and 31 protected hashes; no retraining or rewriting occurred.

Objective 3: implemented deterministic stock-risk/reorder rules using current stock, confirmed incoming, allocations, lead time, safety stock and an excess multiplier. The actual synthetic browser scenario has position 18, target 87.571428571 and suggested reorder 69.571428571, classified REPLENISH. A separate high-stock scenario produces OVERSTOCK and zero reorder. Immutable history preserves original conditions. Operational sales commit stock, sale and audit atomically; historical imports never change current stock. Human review is retained. No procurement execution, global optimality or measured stockout reduction is claimed.

Objective 4: executed 251 automated tests (163 backend, 59 ML, 29 frontend), with zero failures/skips and one upstream warning. Build, Compose, MySQL, live API and a full browser workflow passed. Twenty-three proposal conditions passed; TC24 is pending real participants. The final 440-request localhost performance run had zero errors after a measured deadlock defect was fixed; concurrent inference p95 is about 16.824 seconds. Bounded security checks worked, but dependency advisories remain unresolved. Edge smoke testing passed; Chrome is partial and Firefox was policy-blocked. Representative-user effectiveness and field requirements validation remain unmeasured.

## 5.3 Conclusion

The prototype combines genuine historical forecasting comparison with a working web inventory application and auditable, explainable decisions. Tests support the observed contracts, transaction integrity and scenario arithmetic; they do not establish commercial effectiveness. A simple mean baseline won validation, showing that greater model complexity did not guarantee better accuracy in this study. The historical UK held-out window provides valid historical metrics, not current 2026 or Kenyan accuracy. Unsupported/stale current requests are intentionally rejected, and UNASSESSED does not mean safe. Recent compatible history and approved evaluation are required for genuine current forecasts. Participant usability remains pending; the project is not claimed fully evaluated.

## 5.4 Recommendations

Use the local acknowledged historical demonstration until recent compatible data and retailer validation are available. Obtain supervisor/outlet permissions and voluntary participants for the usability instrument and requirements elicitation. Complete Chrome/Firefox checks through a supported automation surface or supervised manual protocol. Review dependency advisories and compatible framework upgrades before remote exposure; rerun functional/security/build checks while preserving research fingerprints. Retain human review of assumptions, quantity and date/model/stock versions.

## 5.5 Limitations

The UK online gift/wholesale dataset covers 2009–2011, with 60 selected SKUs, two validation origins and one final 28-day horizon. It cannot establish current Kenyan accuracy, causal features or unmet demand. Model quality varies across series; extremes and zeros affect errors. This undergraduate prototype uses synthetic decision stock, fixed safety stock and deterministic incoming assumptions, with fractional raw reorder quantities. It excludes automatic procurement and supplier-network optimization. No commercial capacity, cost improvement or stockout reduction is certified. There are no participant responses; compatibility is partial; dependency advisories and one warning remain. Trusted ignored model/data files are required for reproduction; a source-only checkout cannot assume their presence. See [full limitations](../SYSTEM_LIMITATIONS.md).

## 5.6 Areas for Future Work

After separate approval, future work may collect recent consenting retailer data and inventory availability, evaluate Kenyan transferability, add rolling origins/horizons and uncertainty analysis, and compare intermittent-demand methods without tuning against this sealed final window. Other opportunities include ETA-aware incoming, service-level safety/cost/pack rules, returns/corrections, realistic mixed-load testing, performance profiling, participant usability, accessibility evaluation and deployment/dependency hardening. None is implemented or claimed achieved in Phase 6. Automatic purchase execution remains out of scope.
''')

screenshots=[]
for file in sorted((ROOT/'docs/screenshots/final').glob('*.jpg')):
    screenshots.append({'path':file.relative_to(ROOT).as_posix(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
dump('docs/test-results/phase6-screenshots.json',{'source':'Actual localhost application screenshots; no generated mockups or credentials','screenshots':screenshots})
write('docs/screenshots/final/README.md','# Actual final application screens\n\nCaptured from the working local application; no passwords/tokens shown. Historical forecasts and synthetic stock are clearly demo evidence, not current Kenyan results. Login/CSV/recommendation views visually inspected; original full pages retain their real layout.\n\n'+'\n'.join(f"- [{Path(x['path']).stem}]({Path(x['path']).name})" for x in screenshots)+'\n\nThe Edge chart is separate compatibility evidence. The small viewport recommendation-detail is an additional cropped view; recommendation.jpg contains the complete original page. Hash manifest: ../../test-results/phase6-screenshots.json.\n')

summary={'generated_at_utc':datetime.now(UTC).isoformat(),'status':'Software/evidence activities completed; external evaluation and partial compatibility remain pending','automated_suites':suites,'automated_total':sum(s['tests'] for s in suites),'proposal_cases':{'total':24,'pass':23,'fail':0,'pending':1},'live_checks':{'sales':len(sales['checks']),'decisions':len(decisions['checks']),'security':len(security['checks']),'browser':len(browser['checks']),'browser_mysql_persistence':len(persistence['checks'])},'performance_requests':sum(r['requests'] for r in performance['results']),'performance_errors':0,'production_build':'PASS','compose_mysql_api':'PASS','isolated_reproduction':'PASS','protected_hashes':31,'participants':0,'compatibility':{'Edge':'bounded PASS','Chrome':'PARTIAL','Firefox':'NOT EXECUTED: tool URL policy'},'unresolved':['Participant usability and field requirements evaluation','Complete Chrome/Firefox compatibility','Python/frontend dependency advisories','Starlette/AnyIO deprecation','2011 UK data cannot provide valid2026/Kenyan forecasts'],'no_retraining':True}
dump('docs/test-results/phase6-summary.json',summary)
print('Evidence published:251 executed tests;23 proposal cases PASS,TC24 pending; actual performance/security/compatibility and academic documents. No full-evaluation claim.')
