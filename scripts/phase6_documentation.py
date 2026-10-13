"""Finalize current documentation while retaining previous phase log evidence."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
def write(path,text):(ROOT/path).write_text(text.rstrip()+'\n',encoding='utf-8')
def prefix(path,heading,text):
    original=read(path)
    if heading in original:
        start=original.index(heading)
        next_section=original.find('\n## ',start+len(heading))
        original=original[:start]+original[next_section:] if next_section>=0 else original[:start]
    first,rest=original.split('\n',1)
    write(path,first+'\n\n'+text.strip()+'\n'+rest)

readme=read('README.md')
old=next(p for p in readme.split('\n\n') if p.startswith('Phases 1–5'))
readme=readme.replace(old,'''Phases 1–5 are implemented. Phase 6 software evaluation and academic evidence are prepared: **163 backend, 59 ML and 29 frontend tests passed**, production build and live Docker/MySQL/API verification passed, and a full browser workflow was executed. The original proposal cases have **23 passes and TC24 pending real participants**. Performance, bounded security and compatibility observations are recorded. Edge smoke testing passed; Chrome is partial and Firefox was blocked by browser-tool policy. Dependency advisories remain unresolved. The project is not claimed fully evaluated.

The application provides authorized sessions, catalog/current inventory/audit, atomic operational sales, previewed historical imports, genuine baseline/RF/XGBoost research, frozen mean_28 inference, immutable explainable decisions and Recharts views. Managers explicitly map supported UK series and acknowledge the dated research scenario. Compatible history ends 2011-11-10: current 2026 forecasts are unavailable and current inventory remains UNASSESSED. Historical UK results do not validate Kenyan accuracy. No automatic purchases occur; all 31 protected research/model/source hashes remain unchanged.

Start with [installation](docs/INSTALLATION_GUIDE.md) and the [user manual](docs/USER_MANUAL.md). Final evidence: [24 cases](docs/test-results/final-24-test-cases.md), [objective traceability](docs/OBJECTIVE_TRACEABILITY.md), [Chapter 4](docs/academic/CHAPTER_4_EVIDENCE.md), [Chapter 5](docs/academic/CHAPTER_5_EVIDENCE.md), [limitations](docs/SYSTEM_LIMITATIONS.md) and [development log](DEVELOPMENT_LOG.md).''')
readme=readme.replace("Backend pytest isolates data in SQLite. Separate scripts exercise actual local API/MySQL: scripts/verify_phase1.py, verify_phase2.py and verify_phase3.py retain their original revision gates; scripts/verify_phase5.py targets the current Phase 5 stack.","Backend pytest isolates data in SQLite. Phase 6 scripts verify_phase6_sales.py, verify_phase6_decisions.py and verify_phase6_security.py target the current API/MySQL schema; older scripts retain their original historical revision gates. Run forecasting failure checks sequentially because they temporarily hide and restore only the container artifact.")
readme=readme.replace("The browser test's catalog records are archived and can be viewed by checking Show archived records.","The Phase 6 fixture P6-BROWSER-20261001 remains active and labelled for demonstration: stock17, incoming3, allocated2, two sales and one historical forecast/recommendation. Earlier fixtures are archived and viewable. Trusted ignored model/development-data files must accompany the academic bundle; a source-only checkout lacks them.")
readme=readme.replace('This increment stops at Phase 5.','This increment stops at Phase 6; participant evaluation and complete Chrome/Firefox checks remain pending. Actual screens: [final screenshots](docs/screenshots/final/README.md). Use `python scripts/phase6_infer.py` for read-only historical inference; the original CLI writes a preserved report.')
write('README.md',readme)

api=read('docs/API.md').replace('Forecasting and analytical report endpoints remain outside this increment.','Forecasting and comparison endpoints are implemented as documented above; this sentence supersedes the historical foundation scope.')
api=api.replace('The inventory_version may be stale on an identical committed retry because replay does not adjust stock again.','The inventory_version may be stale on an identical committed retry because replay does not adjust stock again. Phase 6 fixes a verified gap-lock deadlock: only MySQL1213 retries after complete rollback, up to three total attempts, with10/20ms backoff, same request key and fresh stock/version checks. Other errors/exhaustion return503; stale/insufficient stock remains409. See test-results/PERFORMANCE.md.')
api=api.replace('## Phase 4 forecast contract','## Historical Phase 4 contract (superseded by implemented Phase 5 HTTP integration)')
api+='\n\nFinal review: current routes are documented above and verified in phase6-decisions-live.json. Original Phase 4 CLI inference writes last-inference.json; use scripts/phase6_infer.py to preserve frozen results. Current2026inference remains unavailable. See OBJECTIVE_TRACEABILITY.md.\n'
write('docs/API.md',api)

architecture=read('docs/ARCHITECTURE.md')+'''

## Phase 6 verified refinement and evaluation

Architecture remains unchanged. Four measured concurrent-sale503responses were caused by unique-request-key gap-lock deadlocks. The existing sales service retries only MySQL1213 after complete rollback, up to three total attempts, with the same UUID and fresh stock/version checks. Stale/insufficient-stock conflicts and ambiguous connection failures are not retried. Three regression cases and a repeat440-request run verify the fix. See test-results/PERFORMANCE.md and backend/tests/test_sales.py. All31protected research/source hashes remain unchanged. Objective/evaluation boundaries are in OBJECTIVE_TRACEABILITY.md and SYSTEM_LIMITATIONS.md.
'''
write('docs/ARCHITECTURE.md',architecture)
database=read('docs/DATABASE.md').replace('## Phase 4 model boundary','## Historical Phase 4 model boundary (current schema is in Phase 5 below)')+'''

## Final Phase 6 verification

No new schema/migration. Actual MySQL8.4.11 is at e52ad70491b2; alembiccheck finds no differences. Eight immutable triggers and direct browser-created sale/stock/audit/forecast/decision persistence are verified. Same-stock sales serialize safely; audit failure rolls back all writes. Cross-product load exposed a gap-lock deadlock; bounded1213retries fix the measured defect without weakening stock/version rules. Reproduction uses a new project-scoped volume and retains both volumes. No reset, drop or downgrade was run. See test-results/phase6-stack.json, phase6-sales-live.json, phase6-browser-persistence.json and phase6-reproduction.json.
'''
write('docs/DATABASE.md',database)
decision=read('docs/DECISION_SUPPORT.md').replace('Phase 6 full evaluation, participant research and live Kenyan validity remain outside this increment.','Phase 6 software/evidence evaluation is now recorded; participant research and current Kenyan validity remain unestablished.')+'''

Final browser/MySQL scenario: position18, lead demand83.571428571, target87.571428571, suggested reorder69.571428571, immutable inventory version3. Historical quantity50 leaves current stock17 unchanged. Separate overstock/zero-order and all identity/date/version/failure boundaries passed live verification. Current2026inference remains intentionally unavailable. See OBJECTIVE_TRACEABILITY.md, SYSTEM_LIMITATIONS.md and test-results/final-24-test-cases.md.
'''
write('docs/DECISION_SUPPORT.md',decision)
roadmap=read('docs/IMPLEMENTATION_ROADMAP.md')
intro=roadmap.split('\n\n')[1]
roadmap=roadmap.replace(intro,'Every phase ends with tests, actual evidence and a DEVELOPMENT_LOG.md update. The proposal remains authoritative. Phases0–5are implemented; Phase6software/evidence evaluation has executed. Participant evaluation is pending, Chrome compatibility is partial, Firefox was policy-blocked and dependency advisories remain unresolved. The project is not claimed fully evaluated. No further phase was started.')
final=next(line for line in roadmap.splitlines() if line.startswith('Phase 5 verification:'))
roadmap=roadmap.replace(final,'Final status: backend163,ML59,frontend29 tests passed; build/Compose/MySQL/API and isolated reproduction passed. Phase6executed43sales,50decision,21security,11browserand7browser-persistence checks. The first load deadlock was fixed;440repeat requests succeeded. All31protected research/source hashes remain unchanged. Current inventory stays UNASSESSED without fresh compatible forecasts. Participant usefulness, completeChrome/Firefox checks and dependency remediation remain pending; see DEVELOPMENT_LOG.md and OBJECTIVE_TRACEABILITY.md.')
write('docs/IMPLEMENTATION_ROADMAP.md',roadmap)

testing=read('docs/TESTING.md')
start=testing.index('## Proposal cases and execution status')
end=testing.index('## Foundation checks',start)
testing=testing[:start]+'''## Final proposal cases

The authoritative final table is [final-24-test-cases.md](test-results/final-24-test-cases.md), with conditions, input/actions, expectations, actual results, status and exact evidence references. All24outcomes recorded:23PASS,0finalFAIL,TC24PENDING EXTERNAL ACTION. Previous phase sections below preserve historical results/pending statuses; they do not represent current unimplemented functionality.

'''+testing[end:]
testing=testing.replace('## Phase 5 coverage and verification','## Historical Phase 5 coverage and verification')
intro='''## Phase 6 final verification

Executed full suites: backend163passed/0failed/0skipped (JUnit85.320s; console85.36s), ML59/0/0 (14.164s), frontend29/0/0 (JUnit7.094s). Backend has one upstream Starlette/AnyIO BlockingPortal deprecation; no ML/frontend warnings were reported. Frontend tests mock API calls; ML unit tests use synthetic fixtures. Neither substitutes for actual research/realMySQL.

Production build passed:621modules,9.35s, main216.81kB/dashboard392.53kB, no chunk-size advisory. FinalCompose rebuild/start passed. ActualMySQL8.4.11 head e52ad70491b2, alembiccheck and host/containerpipcheck pass; health/readiness/frontend200. Live reports:43sales/import checks,50forecast/decision checks,21security checks,11fullbrowser checks and7read-only browser-persistence checks. Actual same-stock sales201/409 and injected audit rollback establish transaction safety. Historical imports, repeated/overlapping files and stale/archived/unauthorized writes were verified. Eight immutability triggers protect stored evidence.

440performance requests at1/4workers passed after fixing a measured MySQL1213deadlock. First failure retained. Concurrent inferencep95~16.824s is a limitation; no invented SLA. Actual browser covered full login/product/stock/sale/import/historicalforecast/recommendation/dashboard/history/logout. Screenshots in screenshots/final. All6validation/fourfinal metrics recalculated from saved predictions match within1e-10;31protected research/model/source hashes unchanged. No retraining or final-result overwrite.

Final24proposal cases:23PASS,TC24pending representative participants. No responses or supervisor approval invented. Edge boundedsmoke verified; Chrome partial and Firefox unexecuted due toolpolicy. Boundedsecurity verified, but audits report unresolved26Pythonrecords/14distinctadvisoryIDpairs and10frontendentries. Raw reports and findings are preserved. Do not call this penetration testing or full compatibility.

Isolated startup reproduction generated localenvironment, applied migrations to a new project-scopedvolume, created authorized user and verifiedlogin/logout/frontend/readiness/pipcheck/frozeninference. Temporaryservices stopped; existingdevelopmentvolume and isolatedvolume retained. Maincheckout suites executed separately from startup. Researchhistory ends2011-11-10: valid historicalUKtest metrics do not establishcurrent2026orKenyanaccuracy. Unsupportedcurrent/staleforecasts are intentionally rejected and currentstock UNASSESSED.

Evidence: [summary](test-results/phase6-summary.json), [cases](test-results/final-24-test-cases.md), [performance](test-results/PERFORMANCE.md), [security](test-results/SECURITY_REVIEW.md), [compatibility](test-results/COMPATIBILITY.md), [usability instrument](USABILITY_EVALUATION.md), [reproduction](test-results/phase6-reproduction.json). Exact commands, failures and fixes are in DEVELOPMENT_LOG.md. The following dated sections retain earlier phase evidence; their earlier “remaining/pending” notes are superseded by this section.
'''
write('docs/TESTING.md',testing.split('\n',1)[0]+'\n\n'+intro+'\n'+testing.split('\n',1)[1])

log='''## 2026-10-01 — Phase 6 final software evaluation and academic evidence

**COMPLETED:** evaluation reports, all 24 proposal outcomes, objective traceability, usability instrument, setup/user/limitations guides, technical-document review, Chapter 4/5 drafts and screenshots. **VERIFIED:** 251 automated tests, production build, rebuilt Compose/MySQL/API, full browser workflow, rollback/concurrency/import integrity, frozen hashes/metrics, normal/modest concurrent load and isolated startup. **PENDING EXTERNAL ACTION:** approved consenting usability participants and field requirements research; complete Chrome/Firefox testing through supported tools or supervised manual work. **UNRESOLVED:** dependency advisories, one upstream deprecation and current forecasting validity. **OUT OF SCOPE:** retraining/reselection, automatic procurement, supplier-network optimization, enterprise certification and remote deployment. No full-evaluation or commercial-effectiveness claim is made.

The user confirmed no participants are available; only the instrument was prepared. No identities, approvals, responses or satisfaction findings were invented. Proposal Table 4.1 and the four objectives remain authoritative. Proposal SHA256: 9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2. The proposal, diagrams, roadmap and documentation were reviewed. Phase 4 selection, results, artifact and 13 source fingerprints were preserved; all 31 protected hashes were verified unchanged at the end. No retraining, tuning, winner replacement or sealed-result rewrite occurred.

### Actual commands and final results

Commands ran from project root except frontend commands. `Python` below denotes `.venv/Scripts/python.exe` (3.12.14); `Docker` denotes `C:/Users/user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe`. Frontend used cached Node24.19.0 and pnpm11.19.0 (`C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd`), with Node directory on PATH and pnpm_config_verify_deps_before_run=false. Docker/socket, esbuild ancestor-access and audit-network reruns used approved escalation after real sandbox failures. Outputs redirected to named docs/test-results files, without credentials.

| Executed command / operation | Actual final result | Artifact |
|---|---|---|
| `Python -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase6-backend.xml` |163passed,0failed/skipped,1warning; console85.36s/JUnit85.320s |phase6-backend.xml/txt; before-fix160passed retained |
| `Python -m pytest ml/tests --junitxml=docs/test-results/phase6-ml.xml` |59passed,0failed/skipped,0reportedwarnings;14.164s |phase6-ml.xml/txt |
| Frontend `pnpm test --reporter=junit --outputFile=../docs/test-results/phase6-frontend.xml` |29passed,0failed/skipped,0reportedwarnings; JUnit7.094s |phase6-frontend.xml/txt |
| Frontend `pnpm build` |621modules,9.35s;216.81kBmain/392.53kBdashboard; no chunk-size advisory |phase6-build.txt |
| `Docker compose up --build -d` (initial and after defect fix) |Rebuilt main services successfully |phase6-compose-final.txt; initial tool output |
| `Python scripts/phase6_stack_checks.py` |Records Dockerps, alembiccurrent/check, host/containerpipcheck; DBhealthy, API/UIrunning, migrateExit0, head e52ad70491b2, no pending differences; HTTP200live/ready/frontend |phase6-stack.json/txt; exact nested command strings and stdout/stderr |
| `Python scripts/verify_phase6_sales.py` (again after final rebuild) |43actualAPI/MySQLchecks passed |phase6-sales-live.json/txt |
| `Python scripts/verify_phase6_decisions.py` (sequentially after sales, final rebuild) |50actualAPI/MySQLchecks passed |phase6-decisions-live.json/txt |
| `Python scripts/verify_phase6_security.py` |21boundedlivechecks passed |phase6-security.json/txt |
| `Python scripts/phase6_performance.py` (first failure then after fix) |Final440requests/0errors;246.120s including setup/cleanup |phase6-performance.json/txt; first-failure.json/txt preserved |
| Actual CUA/native browser UI operations |Full IABworkflow11checks; real sale/import/forecast/recommendation/charts/history/logout; Edge boundedsmoke; Chrome partial; Firefox blocked byURLpolicy |phase6-browser.json/state.txt; phase6-compatibility.json; screenshots/final |
| `Python scripts/verify_phase6_browser_persistence.py` |7read-only actualMySQLchecks passed; no fixture mutation |phase6-browser-persistence.json/txt |
| `Python scripts/phase6_verify_metrics.py` |10read-only saved-prediction MAE/RMSE checks match within1e-10 |phase6-metrics.json/txt |
| `Python scripts/phase6_preservation.py` (before and final) |18evidence/artifact+13sourcehashesunchanged |phase6-preservation.json/txt |
| `Python scripts/phase6_infer.py` |Genuine20728/2011-11-10/28dayforecast-v1, new report only |phase6-inference.json |
| `Python -m venv .local/audit-venv`; isolated auditvenv pipinstallpip-audit |Audittool2.10.1 installed after approved network rerun; appMLenvunchanged |phase6-audit-install.txt; sandbox-failure.txt |
| AuditPython `-m pip_audit -r .local/phase6-installed.txt --no-deps --disable-pip --format json --output docs/test-results/phase6-python-audit.json` |Exit1:26returnedrecords/14distinct(package,ID)pairs across3packages; fully-hashed-requirements warning |phase6-python-audit.json/txt |
| Frontend `pnpm audit --json` |Exit1:10entries,2low/5moderate/2high/1critical |phase6-frontend-audit.json; networkfailure in tool output |
| `Python scripts/phase6_reproduce.py` (three runs, isolated ports/volume) |Finalsuccess: environment creation, startup/migrations/account/login/logout/revocation/frontend/readiness/pipcheck/frozeninference; stopped onlyisolatedservices; volumesretained |phase6-reproduction.json/txt; first/secondfailurecopies |
| `Python scripts/finalize_phase6.py` |Asserts successful recorded evidence, publishes24outcomes/summary/reviews/guides/academic drafts; no frozen outputs touched |phase6-summary.json/txt; new documentation |
| `Python scripts/phase6_documentation.py` |Finalizes README/API/architecture/database/testing/decision/roadmap/log, preserving previous phase evidence |This entry and linked docs |

### Verified defect, failures and corrective actions

1. First concurrent load produced four sale HTTP503 responses and failed the corresponding integrity assertions. Other operations succeeded. The application DB user lacked PROCESS permission for SHOW ENGINE INNODB STATUS; existing local container root was used only to read diagnostics. InnoDB identified unique request-key gap-lock deadlocks across different products. Sales now retry only MySQL1213 after complete rollback, up to three attempts with10/20ms backoff, the same UUID and fresh stock/version checks. Exhaustion/other errors remain503; stale/insufficient stock remains409. Three tests verify rollback-and-one-sale success, exhaustion and no retry on connection error2006. All163 backend tests and the repeated440-request load then passed. Original failure JSON/TXT and diagnostic remain.
2. Isolated startup first created a user but login returned401. Windows text-pipe newline translation was suspected; bootstrap input was changed to UTF-8 bytes to avoid CRLF translation. A new unique account then passed login/logout. The second run reached genuine inference but asserted nonexistent ForecastOutput.horizon; the harness was corrected to horizon_days. The third complete run passed. Both failure reports remain. No database reset, fallback model or ML-source change occurred.
3. Initial frontend tests/build and Docker sandbox execution failed due to esbuild ancestor permissions and command encoding/socket limits. Approved reruns passed. Audit installation and pnpm audit initially failed with restricted-network WinError10013/fetch errors; approved reruns completed and reported actual advisories. Two attempts to copy failure logs under frontend/docs failed because that path did not exist. Initial frontend/audit failure outputs were subsequently overwritten; they are documented from actual tool traces, not claimed as saved files. Python audit installation failure remains retained.
4. Browser faults included a Chrome screenshot timeout at5000ms, CUA kernel timeouts and request-header-policy failure. The existing in-app tab was recovered. An exact category-success locator had no match; the saved category list established persistence. Chrome final chart/logout are unverified. Edge indexed controls sometimes had stale/offscreen geometry; refreshed state and observed coordinates were used. Immediate AX text lagged after logout, while the screenshot showed sign-in. Selecting Firefox stopped Computer Use because URL-policy enforcement was unsupported; **browser automation ended there**, with no alternative-control workaround. Partial/unexecuted checks are explicit.
5. A documentation patch failed because its expected roadmap line differed; files were verified unchanged and the update was corrected against actual text. Reads of nonexistent app/models subfiles and a wrong skill API path also failed; rg located models.py and the actual docs/api.md. These are tooling failures, not successful application tests. No error was silently relabelled passed.

### Actual system/research results and remaining risks

All24proposal outcomes are recorded:23PASS,0finalFAIL,TC24pending. Original failures remain visible; this does not imply every broader quality condition passed. Automated total251(163+59+29), zero failures/skips, one unresolved Starlette/AnyIO deprecation. Live43sales,50decision,21security,11browser and7persistence checks passed. Same-stock requests returned201/409 with one decrement/audit; an injected MySQL audit failure rolled back. CSV live2accepted/4rejected and browser1accepted/2rejected retained every rejection. Imports do not adjust stock; repeats are idempotent and conflicting overlapping confirmations roll back.

Browser demo P6-BROWSER-20261001 remains active and labelled: on-hand17, incoming3, allocated2, version3. Operational sale100 records quantity3/KES120.50; historical sale101 records quantity50. Exactly three movements persist: opening, adjustment, sale. Explicit20728mapping led to forecast4a1f9161-32f8-4559-b724-62f80907e944 and recommendationaf82e6f7-3339-4455-bc8b-45d51b85c509. Position18, lead demand83.571428571, safety4, target87.571428571, multiplier2, threshold175.142857142 and suggested69.571428571 produce REPLENISH. A separate overstock/zero-order check preserves earlier history. Actual screenshots cover all11requested views without credentials. These are synthetic test transactions, not genuine customer trade or measured retail effectiveness.

Four-worker performance uses one shared manager identity and separate products; it is not a participant study or same-stock stress test. Normal88/concurrent352requests have actual round-trip means, percentiles and statuses. Concurrent inference p95 is16.824s and login3.869s, material delays. Eight normal samples per operation, a shared machine and a small workload limit tail estimates. No numerical SLA or enterprise capacity is claimed. Same-row integrity is separately verified with actual MySQL. Machine: Windows11build26300, eight logical processors, about15.85GiB RAM, HP EliteBook840G5, DockerWSL2/MySQL8.4.11.

Dependency advisories remain: cryptography44.0.3(10raw/6distinct IDs), pytest8.3.5(2raw/1ID), Starlette0.46.2(14raw/7IDs), and10frontend entries including critical Vitest/high Vite advisories. Audits can duplicate aliases. Consistency and functional tests do not establish security. No forced framework upgrade or frozen ML dependency change occurred. Reviewed compatible hardening is recommended before remote exposure; this is not penetration testing. Git exclusions cover local secrets, but no source files/commits are tracked, so no committed-history audit is claimed.

Mean_28 remains the validation winner: MAE4.753635204/RMSE36.360015732. Final MAE5.335034014/RMSE17.944563987 uses1680targets. Seasonal naive has lower final MAE4.939880952/RMSE17.008523773; final results did not change selection. MAPE is omitted for1169zero actuals. All six validation/four final score sets match read-only recalculation. Compatible history ends2011-11-10; raw UK data ends2011. No current2026or Kenyan accuracy is asserted. Current/stale rejections remain. Genuine current forecasting needs recent compatible history and separately approved evaluation. There is no automatic procurement or commercial-effectiveness claim.

The usability instrument has eight tasks, five-point Likert/comments, consent/privacy and task timing/analysis instructions: **zero responses**, no claimed supervisor approval. Objectives1–3are supported within the bounded UK study/synthetic rules; Objective4remains partial pending human evaluation and broader compatibility. Chapter4/5drafts state these limits. Isolated startup used a new project mysql_data volume and ports3307/8001/5174; both volumes were retained and temporary services stopped. Model/development data are ignored trusted-bundle files, so no source-only cold-clone success is claimed. The main stack remains running; no later phase was started.

Final artifacts: docs/test-results/phase6-summary.json, final-24-test-cases.md/json, PERFORMANCE.md, SECURITY_REVIEW.md and COMPATIBILITY.md; objective/usability/setup/user/limitations guides; Chapter4/5drafts; research/PHASE6_REVIEW.md; screenshots/final/README.md. Research documents were reviewed without changing frozen results. Earlier dated sections below preserve historical evidence and do not supersede this status.
'''
original=read('DEVELOPMENT_LOG.md')
write('DEVELOPMENT_LOG.md',original.split('\n',1)[0]+'\n\n'+log+'\n'+original.split('\n',1)[1])
print('Current technical documents and final development log updated; prior phase evidence retained.')
