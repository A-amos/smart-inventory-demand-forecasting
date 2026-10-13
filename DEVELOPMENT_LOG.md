# Development log

## 2026-10-13 — Private GitHub publication receipt

Created https://github.com/A-amos/smart-inventory-demand-forecasting as PRIVATE using the authenticated official CLI, then pushed main successfully. Initial commit: `33b2fbc33a234de20698214ee8e5fe1042ab6a3a` (`feat: complete smart inventory forecasting system`). Scoped author identity is A-amos with GitHub's verified-account noreply address; no global Git identity or wildcard trust was changed. Commands: `gh repo create A-amos/smart-inventory-demand-forecasting --private --description ...`; `git -c safe.directory=C:/Users/user/Projects/SmartInventory remote add origin https://github.com/A-amos/smart-inventory-demand-forecasting.git`; `git -c safe.directory=C:/Users/user/Projects/SmartInventory push -u origin main`. All returned exit0. Repository metadata/API confirmed private ownership and default main. Recursive remote blob paths/hashes matched all395committed files. Remote README bytes matched the initial commit, and actual Chrome displayed Private/main/source folders, rendered README and Mermaid architecture. Screenshots: docs/screenshots/publication/github-repository.jpg and github-readme.jpg.

Executed `git clone --branch main --single-branch https://github.com/A-amos/smart-inventory-demand-forecasting.git .local/publication-clone` into a new ignored folder, exit0. From that clone, the isolated publication Python ran `scripts/verify_publication_preservation.py`:31protected hashes and genuine20728/origin2011-11-10/28day inference passed without fitting. Saved actual clone report as publication-clone-preservation.json. The verifier generates two publication reports; after saving its actual result, those two clone reports were restored from original committed bytes. All395clone file Git blob identities then matched the initial remote commit. This is clone/hash/inference verification, not a claimed cold-cache Docker startup. Original Docker/live checks remain separately recorded.

Harness/tool failures were corrected without altering application or frozen research: the GitHub recursive tree endpoint returned the resolved commit SHA in its top-level response; an initial assertion wrongly expected the local tree SHA. Verification now compares every remote blob and separately records both identities. The first clone comparison wrongly included the two intentionally regenerated publication reports; saving the new result and restoring those two clone reports enabled a valid whole-tree comparison. One README update patch failed because the actual cases link differed; no partial change was made, and a verified substring update succeeded. One GitHub indexed scroll hit a detached node; screenshot-backed refreshed scrolling verified the README. Firefox157.0.1 launched and one target window was found, but selection stopped Computer Use because Windows Firefox URL-policy enforcement is unsupported. No subsequent UI input was attempted; no Firefox application pass is claimed. A JS variable declaration error before selection was corrected. Chrome11/Edge8bounded checks remain passed; participant counts remain0/0.

Evidence: docs/test-results/publication-github.json/txt, publication-clone-preservation.json, publication-compatibility.json and publication-summary.json. Repeated publication-prefixed documentation checks passed93conditions after receipt/README/limitations updates. The receipt verifies the first push; a subsequent documentation-only commit records this evidence. Final local/remote SHA and private/main status are checked after that push and returned separately, avoiding an impossible self-referential commit SHA. No public visibility, force push, credential exposure or database deletion occurred.

## 2026-10-13 — Final academic preparation and private GitHub publication

Reviewed the project tree, proposal requirements, architecture, routes/services/schema/migrations, research contract, dependency records, prior tests and Git state. All requested modules are present. Main was active; there were no commits or remotes initially. Prepared a professional README, dataset/academic NOTICE, and DEMO_GUIDE.md, HOW_THE_SYSTEM_WORKS.md (A–Y processes with files/tables/endpoints) and PROJECT_DEFENSE_GUIDE.md. Updated installation/limitations notes to distinguish historical evaluation from current publication packaging. Original proposal, diagrams, migrations, research results and earlier test evidence were retained. Chapter5numbered objectives and the usability instrument remain intact.

Compatible updates: FastAPI0.115.12→0.143.0, Starlette0.46.2→1.7.0, cryptography44.0.3→50.0.2, pytest8.3.5→9.1.1, Vite6.3.5→6.4.3, Vitest3.1.3→4.1.11 and source-map-js1.2.1→1.2.2. Isolated `.local/final-venv` kept the original Python environment intact. Pydantic2.11.4/coreMLversions and all originalMLsources/protocol/directrequirements/lock/artifact/results remain unchanged. Backend constraints and frontend lock record the new application resolutions. No training, retuning, winner replacement or frozen-result writing occurred.

Actual commands (Python denotes `.local/final-venv/Scripts/python.exe`; Docker is the verified per-user CLI; pnpm used nativeNode24.19.0/pnpm11.25.0 with verify_deps_before_run=false):

| Command / action | Actual result | Evidence under docs/test-results |
|---|---|---|
| Python -m pip install -r backend/requirements-dev.txt -r ml/requirements.txt |Isolated install passed; originalMLenvironment preserved |publication-python-install.txt |
| Frontend pnpm add -DE vite@6.4.3 vitest@4.1.11; pnpm update source-map-js --depth10 |Pinned compatible updates installed; transitive patch fixed re-audit finding |publication-frontend-exact-install.txt,publication-source-map-update.txt |
| Python -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/publication-backend.xml |163passed,0failed/skipped; one upstream Starlette TestClient/httpx deprecation; console115.10s |publication-backend.xml/txt |
| Python -m pytest ml/tests --junitxml=docs/test-results/publication-ml.xml |59passed,0failed/skipped/reportedwarnings;27.87s |publication-ml.xml/txt |
| Frontend pnpm test --reporter=default --reporter=junit --outputFile.junit=../docs/test-results/publication-frontend.xml |29passed,0failed/skipped/reportedwarnings; wall16.17s |publication-frontend.xml/txt |
| Frontend pnpm build |Passed621modules/16.35s; main216.81kB/dashboard392.53kB |publication-build.txt |
| Docker compose up --build -d (then cached rebuild for final frontend patch) |Both builds/startups passed; originalMySQLvolume retained. Linuxscientific/NCCLdownloads were large/slow; no model change |publication-compose-first.txt,publication-compose.txt |
| INVENTORY_TEST_REPORT_PREFIX=publication; Python scripts/phase6_stack_checks.py |DBhealthy,API/frontendrunning,migrateExit0; MySQL8.4.11/head e52ad70491b2; alembiccheck/host+containerpipcheck pass; live/ready/frontend200 |publication-stack.json/txt, exact nested commands/stdout |
| Same report prefix; Python scripts/verify_phase6_sales.py |43actualMySQL/APIchecks pass,including concurrent same-stock201/409, audit rollback, historical no-stock-change and duplicates |publication-sales-live.json/txt |
| Same prefix; Python scripts/verify_phase6_decisions.py |50actualMySQL/APIchecks pass, real frozen inference/mapping/persistence/formulas/immutability/roles/failure isolation |publication-decisions-live.json/txt |
| Same prefix; Python scripts/verify_phase6_security.py |21boundedlivechecks pass; local credentials excluded from staged Git |publication-security.json/txt |
| Python scripts/verify_publication_preservation.py |31protected hashes unchanged; real20728/2011-11-10/28dayinference passed without fitting |publication-preservation.json/txt,publication-inference.json |
| Isolated pip-audit exact installed-package list; frontend pnpm audit --json |Final0known advisories in updated publication Pythonenvironment/frontendlock. First FEre-audit found source-map-js high; patched and rerun |publication-python-audit.json/txt,publication-frontend-audit.json |
| Actual Chrome/nativeEdge follow-up |Recorded real login/navigation/stock/forms/import/dashboard/storedforecast/decision/logout outcomes; screenshots/limitations individual, no fabricated compatibility |publication-compatibility.json,Chrome/EdgeAXfiles,screenshots/publication |
| Python scripts/review_repository.py; --staged |No denied paths, known local credential values or common token/key signatures;31staged frozen byte hashes match |publication-repository-candidate.json/txt,publication-repository-staged.json/txt |
| Python scripts/summarize_publication.py |251testpasses,114business/securitylivechecks,31protectedhashes,0currentauditfindings summarized |publication-summary.json/txt,PUBLICATION_REVIEW.md |
| INVENTORY_TEST_REPORT_PREFIX=publication; Python scripts/verify_phase6_documents.py |93 read-only documentation/evidence checks passed |publication-documentation.json/txt |

Browser follow-up completed: Chrome154.0.8037.59 passed11bounded checks; Edge155.0.4283.45 passed8bounded checks, including both plotted curves and logout after the battery interruption cleared. These are technical checks, not participant evaluation. Current Firefox status remains individually recorded. A documentation-verifier invocation initially overwrote its original Phase6 report because only stdout was redirected; the original JSON was restored byte-for-byte from the staged Git blob, the new report was saved under publication, and the verifier now supports the explicit publication prefix. The corrected invocation passed93checks. No original research result was overwritten.

Failure/correction records: initial PyPImetadata request hit sandboxWinError10013; approved network rerun succeeded. First READMEpatch used duplicate delete/add targets and was rejected; content was then safely rewritten without deleting evidence. Initial gitadd hit sandbox-owner mismatch; only this exact verified workspace is trusted per command, with no global wildcard safe.directory. A stack check ran while the final rebuild/migration was still completing and failed; retained publication-stack-during-rebuild-failure.json/txt, then reran the entire stack/live sequence after Compose exit0. Chrome header policy first failed then recovered; exact-label dropdown included nested option labels and timed out, resolved with observed native keyboard/combobox-role selection. First screenshot captured axes without plotted curves; retained initial capture, verified two nonempty opacity1paths and captured visible curves. No chart/application code was changed. NativeEdge required screenshot-backed geometry/maximization; low-battery system modal interrupted later native input, with precise outcomes in the compatibility report. These are accurately recorded failures/tooling limits, not successful tests.

Repository policy: strengthened ignores for environments, credentials, local tools, caches, privatekeys and DBfiles. Raw/customer/full/sealed datasets remain ignored. Included only originalverified356byte baseline and1,221,454byte aggregate development history (date/SKU/demand/price, no customer/invoice identifiers), making a clone runnable without retraining. `.gitattributes *-text` prevents line-ending conversion invalidating research fingerprints. NoGitLFSneeded. Preserved raw-data acquisition/isolated reconstruction instructions and UCI/CCBY4attribution/change notices. No new open-source software license was imposed. Synthetic test passwords remain intentionally identifiable test fixtures, not real credentials. The bounded scan is not a universal secret-detection guarantee.

GitHub authentication: connected account and officialCLIconfirmedA-amos. CLIv2.102.0 was installed only in ignored.localtools with official release checksum verification. The user explicitly approved displayed persistentOAuthaccess and personally completed emailed verification. No pairing codes, tokens, passwords, cookies or private browser data are committed. Preferred repository did not exist at initial check. Private creation, initial commit/push and actual remote verification follow the completed gates and are recorded in a subsequent receipt; no public repository or force push is authorized.

COMPLETED: software finalization, student demonstration/study/defense guides, repository preparation and actual regression/security review. VERIFIED:251tests/build/Compose/MySQL/API/frozeninference+hashes and individually recorded browser checks. PENDING EXTERNAL ACTION:real approved usability/field participants; zero participants/responses, TC24pending(23of24cases passed). KNOWN LIMITATIONS:UK2009–2011history does not validate current Kenyan forecasting, deterministic rules/synthetic decision scenarios, original research-reproduction-lock advisories, upstreamTestClient/audit-hash/deprecatedtransitive warnings, bounded browser/load/security scope. No automaticprocurement, commercial effectiveness or full participant evaluation is claimed. OriginalPhase6performance evidence is retained and not relabelled a new load run.

## 2026-10-13 — Chapter 5 and usability document verification

Verified that docs/academic/CHAPTER_5_EVIDENCE.md and docs/USABILITY_EVALUATION.md both exist. Added the requested Chapter 5 subsections 5.2.1–5.2.4 without changing recorded model results or findings. Made the 23-of-24 result and pending TC24 participant evaluation explicit. The existing UK2009–2011/current-Kenyan limitation, incomplete Chrome/Firefox checks, unresolved dependency advisories and absence of commercial-effectiveness claims remain intact. The prepared usability instrument is retained, with explicit current recorded counts of zero participants and zero responses; no ratings or feedback were invented.

Verification: read both UTF-8 files and the recorded Phase 6 log; checked file existence, the ordered Chapter 5 headings and required evidence/limitation statements. This was a documentation-only change; no application tests, model training or participant evaluation were rerun, and no Phase 4 result/artifact was modified.

## 2026-10-01 — Phase 6 final software evaluation and academic evidence

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
| `Python scripts/verify_phase6_documents.py` |88 read-only documentation/evidence checks passed, including local links, case references, proposal hash and screenshot manifest |phase6-documentation.json/txt |

### Verified defect, failures and corrective actions

1. First concurrent load produced four sale HTTP503 responses and failed the corresponding integrity assertions. Other operations succeeded. The application DB user lacked PROCESS permission for SHOW ENGINE INNODB STATUS; existing local container root was used only to read diagnostics. InnoDB identified unique request-key gap-lock deadlocks across different products. Sales now retry only MySQL1213 after complete rollback, up to three attempts with10/20ms backoff, the same UUID and fresh stock/version checks. Exhaustion/other errors remain503; stale/insufficient stock remains409. Three tests verify rollback-and-one-sale success, exhaustion and no retry on connection error2006. All163 backend tests and the repeated440-request load then passed. Original failure JSON/TXT and diagnostic remain.
2. Isolated startup first created a user but login returned401. Windows text-pipe newline translation was suspected; bootstrap input was changed to UTF-8 bytes to avoid CRLF translation. A new unique account then passed login/logout. The second run reached genuine inference but asserted nonexistent ForecastOutput.horizon; the harness was corrected to horizon_days. The third complete run passed. Both failure reports remain. No database reset, fallback model or ML-source change occurred.
3. Initial frontend tests/build and Docker sandbox execution failed due to esbuild ancestor permissions and command encoding/socket limits. Approved reruns passed. Audit installation and pnpm audit initially failed with restricted-network WinError10013/fetch errors; approved reruns completed and reported actual advisories. Two attempts to copy failure logs under frontend/docs failed because that path did not exist. Initial frontend/audit failure outputs were subsequently overwritten; they are documented from actual tool traces, not claimed as saved files. Python audit installation failure remains retained.
4. Browser faults included a Chrome screenshot timeout at5000ms, CUA kernel timeouts and request-header-policy failure. The existing in-app tab was recovered. An exact category-success locator had no match; the saved category list established persistence. Chrome final chart/logout are unverified. Edge indexed controls sometimes had stale/offscreen geometry; refreshed state and observed coordinates were used. Immediate AX text lagged after logout, while the screenshot showed sign-in. Selecting Firefox stopped Computer Use because URL-policy enforcement was unsupported; **browser automation ended there**, with no alternative-control workaround. Partial/unexecuted checks are explicit.
5. A documentation patch failed because its expected roadmap line differed; files were verified unchanged and the update was corrected against actual text. Reads of nonexistent app/models subfiles and a wrong skill API path also failed; rg located models.py and the actual docs/api.md. These are tooling failures, not successful application tests. No error was silently relabelled passed.
6. The log-polishing helper initially used Windows' default cp1252 to read UTF-8 source and raised UnicodeDecodeError. It was rerun with explicit UTF-8 and preserved all previous phase log sections. Final documentation verification also uses explicit UTF-8. Performance wording was corrected after reviewing raw integrity assertions: worker0's sixteen sales comprise eight normal plus eight concurrent sales; stock adjustments preserve quantity and do not reduce stock.

### Actual system/research results and remaining risks

All24proposal outcomes are recorded:23PASS,0finalFAIL,TC24pending. Original failures remain visible; this does not imply every broader quality condition passed. Automated total251(163+59+29), zero failures/skips, one unresolved Starlette/AnyIO deprecation. Live43sales,50decision,21security,11browser and7persistence checks passed. Same-stock requests returned201/409 with one decrement/audit; an injected MySQL audit failure rolled back. CSV live2accepted/4rejected and browser1accepted/2rejected retained every rejection. Imports do not adjust stock; repeats are idempotent and conflicting overlapping confirmations roll back.

Browser demo P6-BROWSER-20261001 remains active and labelled: on-hand17, incoming3, allocated2, version3. Operational sale100 records quantity3/KES120.50; historical sale101 records quantity50. Exactly three movements persist: opening, adjustment, sale. Explicit20728mapping led to forecast4a1f9161-32f8-4559-b724-62f80907e944 and recommendationaf82e6f7-3339-4455-bc8b-45d51b85c509. Position18, lead demand83.571428571, safety4, target87.571428571, multiplier2, threshold175.142857142 and suggested69.571428571 produce REPLENISH. A separate overstock/zero-order check preserves earlier history. Actual screenshots cover all11requested views without credentials. These are synthetic test transactions, not genuine customer trade or measured retail effectiveness.

Four-worker performance uses one shared manager identity and separate products; it is not a participant study or same-stock stress test. Normal88/concurrent352requests have actual round-trip means, percentiles and statuses. Concurrent inference p95 is16.824s and login3.869s, material delays. Eight normal samples per operation, a shared machine and a small workload limit tail estimates. No numerical SLA or enterprise capacity is claimed. Same-row integrity is separately verified with actual MySQL. Machine: Windows11build26300, eight logical processors, about15.85GiB RAM, HP EliteBook840G5, DockerWSL2/MySQL8.4.11.

Dependency advisories remain: cryptography44.0.3(10raw/6distinct IDs), pytest8.3.5(2raw/1ID), Starlette0.46.2(14raw/7IDs), and10frontend entries including critical Vitest/high Vite advisories. Audits can duplicate aliases. Consistency and functional tests do not establish security. No forced framework upgrade or frozen ML dependency change occurred. Reviewed compatible hardening is recommended before remote exposure; this is not penetration testing. Git exclusions cover local secrets, but no source files/commits are tracked, so no committed-history audit is claimed.

Mean_28 remains the validation winner: MAE4.753635204/RMSE36.360015732. Final MAE5.335034014/RMSE17.944563987 uses1680targets. Seasonal naive has lower final MAE4.939880952/RMSE17.008523773; final results did not change selection. MAPE is omitted for1169zero actuals. All six validation/four final score sets match read-only recalculation. Compatible history ends2011-11-10; raw UK data ends2011. No current2026or Kenyan accuracy is asserted. Current/stale rejections remain. Genuine current forecasting needs recent compatible history and separately approved evaluation. There is no automatic procurement or commercial-effectiveness claim.

The usability instrument has eight tasks, five-point Likert/comments, consent/privacy and task timing/analysis instructions: **zero responses**, no claimed supervisor approval. Objectives1–3are supported within the bounded UK study/synthetic rules; Objective4remains partial pending human evaluation and broader compatibility. Chapter4/5drafts state these limits. Isolated startup used a new project mysql_data volume and ports3307/8001/5174; both volumes were retained and temporary services stopped. Model/development data are ignored trusted-bundle files, so no source-only cold-clone success is claimed. The main stack remains running; no later phase was started.

Final artifacts: docs/test-results/phase6-summary.json, final-24-test-cases.md/json, PERFORMANCE.md, SECURITY_REVIEW.md and COMPATIBILITY.md; objective/usability/setup/user/limitations guides; Chapter4/5drafts; research/PHASE6_REVIEW.md; screenshots/final/README.md. Research documents were reviewed without changing frozen results. Earlier dated sections below preserve historical evidence and do not supersede this status.

## 2026-10-01 — Phase 5 exit gate passed on actual evidence

Objective 3 is implemented in the existing modular N-tier application: explicit supported UK-series mappings; inference from the frozen validation-selected mean_28 artifact; append-only versioned forecasts/daily points; immutable inventory-position/target/reorder/risk recommendation snapshots; manager-only mutations/researcher reads; paginated evidence histories; Recharts 3.10.1 dashboard with actual historical/stored demand and genuine separate validation/final comparisons. Ordinary requests never fit/retrain/retune a model. Phase 4 winner and final-test evidence remain unchanged. No purchase execution or Phase 6 work.

### Final commands and results

Commands ran from the project root unless frontend/backend context is specified. Local Python executable is `.venv\Scripts\python.exe`; pnpm 11.19.0 is the cached runtime `dependencies\bin\fallback\pnpm.cmd` with Node 24.19.0 prepended to PATH and `pnpm_config_verify_deps_before_run=false`. Docker CLI is `C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`. Output redirections saved the named evidence files; approved reruns resolved sandbox restrictions.

| Actual command | Final result | Evidence under docs/test-results |
|---|---|---|
| `Python -m pytest backend/tests -c backend/pytest.ini -q --junitxml=docs/test-results/phase5-backend.xml` | **160 passed**, one upstream Starlette/AnyIO deprecation, 45.33 s | phase5-backend.xml/txt |
| `Python -m pytest ml/tests -q --junitxml=docs/test-results/phase5-ml.xml` | **59 passed**, 8.82 s; synthetic regression fixtures, no research-artifact retraining | phase5-ml.xml/txt |
| Frontend: `pnpm test --reporter=default --reporter=junit --outputFile.junit=../docs/test-results/phase5-frontend.xml` | **29 passed**, four files, 5.27 s after final applicability/form-state changes | phase5-frontend.xml/txt |
| Frontend: `pnpm build` | **Passed**, 621 modules, 3.88 s; main 216.81 kB/gzip66.90, dashboard 392.53 kB/gzip114.76; no >500 kB advisory | phase5-build.txt |
| `docker compose up --build -d` | Final rebuild/start **passed**; MySQL healthy, migration exited 0, API/frontend running | phase5-compose-rebuild.txt and phase5-compose-final.txt; phase5-compose-status.jsonl |
| `docker compose exec -T backend alembic current` and `alembic check` | **e52ad70491b2 (head)**, **No new upgrade operations detected** | phase5-migration-final.txt |
| `docker compose exec -T backend python -m pip check` | **No broken requirements found** | phase5-container-dependencies.txt |
| `Python scripts/verify_phase5.py` | Final **50 actual live MySQL/API checks passed** (first complete run 48; added explicit sale→dashboard verification) | phase5-live.json/txt |
| Actual local in-app browser workflow via CUA | **11 workflow checks passed**, including rebuilt UI, real rendered curves, snapshot history, archives and logout | phase5-browser.json; four phase5-browser-*.png screenshots |
| `Python scripts/verify_phase5_browser_persistence.py` | **8 checks passed** for exact browser-created MySQL evidence, reversible fixture cleanup and frozen hashes | phase5-browser-persistence.json/txt |
| `Python scripts/summarize_phase5.py` | Gate verified from executed JUnit/workflow/build/migration/stack reports and unchanged hashes | phase5-summary.json/txt |

### Actual decision and integrity evidence

Live MySQL: version 8.4.11; eight append-only triggers installed; mapping sequences unique and positive; evidence creation timestamps DATETIME(6). Supported API inference exactly matches the independent last-28-day observed mean for UK StockCode 20728. Two concurrent identical forecast requests persist one UUID/record. Invalid current origin, stale decision date, missing forecast and short horizon fail clearly. Unit cases additionally exercise model/artifact/feature/mapping/product/SKU/unit mismatch, date/day gaps, count mismatch, invalid quantities and missing parameters.

The actual API scenarios verify `position=on_hand+incoming−allocated`, sum of all lead-time daily quantities + safety, raw `max(0,target−position)`, configured target×multiplier and strict overstock boundary. Snapshot generation changes no operational tables. SQL UPDATE and DELETE against all four evidence tables fail with append-only SQLSTATE45000. Exact recommendation retry after stock changes returns its original JSON, new request UUID appends different stock evidence, histories remain ordered and unchanged. Researcher reads/403 writes, anonymous401, proxy and logout were verified against the running stack.

A real missing-artifact test temporarily renamed only the container copy of selected.joblib, restored it in finally and verified support again. Generation returned clear 503; products and readiness remained200; SHA-256 digests and counts of every products/sales/inventory/stock_movements/sales_imports row remained identical. The host frozen binary was never moved or edited. An actual existing operational sale then reduced synthetic on-hand5→4 and position6→5; the dashboard invalidated the old decision as UNASSESSED and retained the original recommendation unchanged. This is verification of existing Phase 3 behavior, not new sales implementation.

Browser: created clearly labelled synthetic unit stock with lead3/safety4/multiplier2, on-hand5/incoming3/allocated2. Initially unavailable without mapping. After explicit UK acknowledgement and reasoned20728 mapping, actual stored forecasts produced lead demand **83.571428571**, position **6**, target **87.571428571**, reorder **81.571428571**, threshold **175.142857142** → REPLENISH. Changed illustrative stock to999, generated separate OVERSTOCK/zero-reorder snapshot, inspected the unchanged original decision and verified rebuilt UI's nonapplicable historical notice. Recharts rendered both historical and forecast curves; genuine validation/final numbers showed mean_28 selected on validation. Browser logout returned to sign-in. Fixture products/categories were archived with all forecasts/recommendations/audit retained; the partial-run fixture was separately archived. Direct MySQL verification confirms one browser forecast, two decisions, original/current versions2/3, zero sales and only opening+two explicit adjustment movements for this browser fixture. These synthetic stock examples are **not research findings**.

### Failures and fixes

Initial Phase 5/backend, dependency/sandbox and first migration failures are preserved in the progress record below. Final fixes include: passive immutable relationship deletion; corrected category fixture reuse; approved esbuild/Docker execution after actual restrictions; resumable nontransactional MySQL migration after error1419; documented local-development trigger setting without global SUPER grant; microsecond timestamps and sequence constraints; lazy chart loading to remove the first609kB bundle advisory; cleared overview while changing context; explicit historical applicability notices; mapping forms reset when product/mapping changes. Browser's exact-label Category locator included nested option text and failed; switched to its observed combobox role/name, then the workflow passed. A documentation patch initially expected the wrong TESTING heading; corrected using the actual file heading. No reset/drop/downgrade, volume deletion, external account or credential disclosure occurred.

### Preservation, documentation and remaining boundaries

All **18 protected Phase 4 evidence/artifact files** and **13 frozen ML source fingerprints** match their original SHA-256 values. Proposal DOCX SHA remains `9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2`. No research CLI command that rewrites final results/schema/examples was run. API/ARCHITECTURE/DATABASE/TESTING, README and roadmap now describe Phase 5; DECISION_SUPPORT.md documents every formula, identity/freshness/version rule, source assumption and human-review boundary. Phase5-summary.json records the actual gate.

The frozen compatible history ends **2011-11-10**. Current operational forecasts remain unavailable; current inventory is **UNASSESSED**, not declared safe. Acknowledged UK demonstrations retain origin2011-11-10/as-of2011-11-11 and use present illustrative inventory, not measured2011 stock or Kenyan validation. No unseen-SKU or stale-date fallback, new fitting, ETA inference, calibrated probabilities, pack/procurement rounding or automatic purchases. Fresh compatible operational history and any later research changes require separate scope approval. Phase 6 full system/performance/cross-browser/participant/deployment evaluation has **not begun**. Upstream deprecation and production privilege/security reviews remain documented limits. This increment stops here.

## 2026-10-01 — Phase 5 implementation and verification in progress

Scope: Objective 3 only. Reviewed the complete Phase 5 request, proposal decision formulas (3.12–3.13), roadmap and frozen Phase 4 artifact/contract. Added explicit manager-controlled research-series mapping, inference-only HTTP integration, versioned append-only forecasts/points, immutable recommendation snapshots, Decimal inventory/target/reorder/overstock rules, server authorization and Recharts dashboard. No research model, experiment configuration or final-test evidence was retrained/replaced/rewritten. No Phase 6 work.

Key limitation: compatible history ends 2011-11-10. Current stock decisions remain UNASSESSED; historical UK research generation requires explicit acknowledgement, origin 2011-11-10 and decision date 2011-11-11. Current illustrative inventory applied to that dated scenario is not measured 2011 stock, a current purchasing recommendation or Kenyan validation. Exact formulas, identity/freshness gates, input rules and human-review boundary are in docs/DECISION_SUPPORT.md.

Executed so far (reports in docs/test-results):

- `.venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini -q --junitxml=docs/test-results/phase5-backend.xml`: **160 passed**, one upstream Starlette/AnyIO deprecation, 45.58 s. Initial existing regression check: 112 passed. First new decision run: **41 passed, 2 failed**, 12.15 s (`phase5-decisions-first.*`). Fixed duplicate-category fixture by reusing its category. Set immutable forecast relationship passive deletion so ORM reaches the explicit append-only guard instead of attempting to clear child PKs. Added real isolated loader failure checks and mapping-disable/unit acknowledgement tests. Latest source/migration refinements still require final rerun.
- `.venv/Scripts/python.exe -m pytest ml/tests -q --junitxml=docs/test-results/phase5-ml.xml`: **59 passed**, 8.82 s. These are previous regression tests on synthetic tiny fixtures, not retraining the frozen research model. Phase 4 research commands that rewrite evidence were not run.
- Upgraded retired Recharts 2.15.3 → 3.10.1 and installed react-is 19.1.0 to match React 19.1.0 via `pnpm add recharts@3.10.1 react-is@19.1.0`. First sandbox/store lookup failed; approved installed-cache execution succeeded. Exact install output: `phase5-chart-install.txt`. ML dependencies/protocol remain unchanged.
- `pnpm test --reporter=default --reporter=junit --outputFile.junit=../docs/test-results/phase5-frontend.xml`: **29 passed**, four files, 6.63 s. Initial sandbox esbuild startup failed with ancestor directory access denied; approved rerun passed. An attempted copy of the initial error used an incorrect path relative to frontend, so the copy failed; it did not affect source or tests. Build sandbox failure is separately preserved in `phase5-build-sandbox.txt`.
- `pnpm build`: passed, 620 modules, 4.39 s (`phase5-build.txt`); initial bundle 609.03 kB generated a >500 kB advisory. Added lazy dashboard loading; final build/tests will be rerun. Node 24.19.0/pnpm 11.19.0 used with pnpm automatic dependency precheck disabled after dependency install.
- `docker compose up --build -d`: images built with the exact Phase 4 dependency pins (large Linux XGBoost/NCCL downloads); **migration failed**, MySQL error 1419 on trigger creation. Actual outputs `phase5-compose-build.txt`, `phase5-first-migration-failure.txt`. MySQL committed the first evidence table before failing. Fixed migration resumability (existing-table/trigger checks), configured localhost-development `log_bin_trust_function_creators=1` without granting global SUPER to the application, added evidence timestamp/sequence consistency migration. Rebuild running (`phase5-compose-rebuild.txt`). No database reset/drop/downgrade or volume removal.

Remaining gate checks: final suites/build after refinements; successful Compose migration/rebuild; actual MySQL/HTTP inference, immutable triggers, concurrent retries, preserved operational ledger under real missing-artifact failure, browser workflow/screenshots, final documentation/evidence hash verification. Phase 5 is **not yet declared complete**.

## 2026-10-01 — Phase 4 research exit gate passed

Final review: reran `Python -m ml.cli verify-reproduction` successfully after documentation updates; research model/features/source fingerprints remain unchanged. `Python scripts/render_phase4_figures.py` regenerated the representative plot from preserved predictions with readable date labels; both comparison and representative figures were visually inspected. Clarified that the selected mean baseline uses only the last 28 observed quantities, while stored tree feature specifications describe the compared ML candidates. Proposal DOCX SHA-256 remains `9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2`.

### Implemented scope and actual research findings

Implemented the proposal/roadmap objective 1/2 offline research package only: source validation, auditable preprocessing, initial-training EDA, shifted features, fixed-origin recursive forecasting, baseline/RF/XGBoost comparison, validation-only selection, one frozen final holdout, selected artifact export/reload and forecast-v1 Python/CLI contract. Training never runs inside ordinary application requests. No Phase 5 risk, replenishment, procurement, dashboard or forecasting HTTP endpoint was added; no database schema changed.

Dataset: **UCI Online Retail II**, DOI 10.24432/C5CG6D, CC BY 4.0, public download without external accounts. Obtained 2026-09-30T22:14:04.092443+00:00 (2026-10-01 Nairobi). Exact source/terms/files/hashes are in docs/research/DATASET.md and dataset-manifest.json. M5 competition terms were reviewed; the open transaction-level alternative was explicitly selected before development/training. UK gift/wholesale online retail and GBP prices do not establish Kenyan physical-retail performance. Questionnaires and Phase 3 synthetic test files are excluded.

Actual workbook: 1,067,371 × 8 records/columns; two sheets 525,461 and 541,910 rows; dates 2009-12-01 07:45 through 2011-12-09 12:50; 5,305 raw stock codes and 43 destination countries. Valid positive transaction rows: 1,003,214; distinct valid product codes: 4,707. Exclusive rejections: {'cancelled_invoice': 18285, 'exact_duplicate': 33663, 'invalid_or_nonpositive_price': 2690, 'invalid_or_nonpositive_quantity': 3426, 'invalid_sku_or_nonproduct_code': 6093}. Customer IDs/descriptions are not model features; missing ones do not discard otherwise valid transactions. No category/store/events/promotions labels are supplied or invented. Exact duplicates are removed under a documented export-duplication assumption; legitimate indistinguishable repeated invoice lines are a limitation. Outliers are retained.

Initial-training-only cohort: seed 20261001, 365-day minimum history, >=60 positive days, 20 SKUs from each of three zero-fraction strata; **60 selected SKUs**. Full valid-code exclusion report: {'eligible_not_selected_seeded_sample': 1932, 'history_under_365_days': 665, 'included': 60, 'no_initial_training_history': 194, 'positive_days_under_60': 1856}. Expanded the report before freezing to include 194 future-only products; selected cohort/development/test file hashes did not change. Daily zeros after first observation mean no recorded purchase under the complete-export assumption, not proven absent demand. Quantity-weighted GBP prices are forward filled from the past only. Initial training: 37,753 SKU-days; validation: 3,360 targets; final test: 1,680 targets; complete study daily panel: 42,793 observations.

EDA: 26,891 zero training days (71.23%), median demand interval 4.327 days, median lag-7 correlation 0.0457, all 60 SKUs with price variation, median price/demand Spearman -0.0690. Saturday observed sales are zero in the constant-panel export; monthly/trailing trends and weekday differences are descriptive associations. Retained 4,635 upper-three-IQR flags, maximum selected training daily purchase 7,008 units. Actual plots/tables: docs/research/eda; interpretation: EDA.md. No causal price/promotion or Kenyan-performance finding is invented.

### Validation versus final test

Protocol was fixed before training in ml/protocol.json and EXPERIMENT_PROTOCOL.md: daily retailer-SKU; horizon 28; initial train through 2011-09-15; validation origins 2011-09-15 and 2011-10-13; final origin 2011-11-10, targets 2011-11-11 through 2011-12-08. December 9 incomplete source day was pre-excluded. One-hot SKU vocabulary is training-selected; demand lags 1/7/14/28, shifted rolling mean/std 7/28, known calendar and lagged price/change features are shared by training/inference. Recursive forecasts consume earlier own predictions and fixed-origin price, never future actual sales/prices.

Compared seasonal-naive and mean-28 baselines, RF leaf 5/15 (80 trees, depth 12), XGBoost depth 3/5 (200/150 trees, learning rate .05). Two expanding validation windows tune family configurations and select overall winner by pooled MAE, then RMSE/name. **mean_28** selected/frozen at 2026-09-30T22:55:08.275037+00:00; final labels accessed only at 2026-09-30T22:58:57.313109+00:00 after all frozen finalists fit/predicted. No final-test tuning, cohort revision or winner replacement. Every final candidate used exactly the same 1,680 actual SKU/date targets; every validation candidate used the same 3,360. Other hyperparameter configurations were not final-tested. MAPE omitted for mathematically undefined/misleading zero/intermittent demand; no epsilon or hidden positive-only subset.

| Candidate | Validation MAE | Validation RMSE | Final MAE | Final RMSE |
| --- | ---: | ---: | ---: | ---: |
| mean_28 | 4.753635 | 36.360016 | 5.335034 | 17.944564 |
| seasonal_naive | 6.078274 | 43.352902 | 4.939881 | 17.008524 |
| xgb_depth5 | 9.193968 | 46.835325 | 5.615669 | 18.846317 |
| xgb_depth3 | 9.327391 | 43.942535 | Not frozen finalist | — |
| rf_leaf5 | 10.080747 | 42.761740 | 6.545169 | 18.516365 |
| rf_leaf15 | 10.093938 | 39.320707 | Not frozen finalist | — |

Metrics are units/SKU-day, not percentages. Selected final MAE **5.335034**, RMSE **17.944564**, zero actual days 1169/1680. Full paired predictions, per-SKU scores, worst ten products and fixed training representatives are preserved. Poor forecasts are retained/reported. Exact effective parameters, dependency versions, seeds, timings and feature/source fingerprints are saved. No Git commit exists; source SHA-256 fingerprints replace an invented revision. Artifact: `ml/artifacts/uci-retail-v1-0cc2a83c3e40/selected.joblib`, SHA-256 `840837c7333d8a928fc170a7ef3245299bb2dfcd0750c6eb45b0f696a8f41031`; run `uci-retail-v1-0cc2a83c3e40`. Artifact reload reproduced 1,680 predictions within absolute tolerance 1e-10 and recalculated all four models' final MAE/RMSE from saved observations. CLI inference generated actual 28-day forecast-v1 JSON for known SKU 20700; schema and example are exported. Research StockCodes remain namespaced and are not silently imported/mapped to live products.

### Actual commands and checks

Commands ran at project root unless noted. Python denotes `.\.venv\Scripts\python.exe`; Docker denotes `C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`; pnpm denotes the bundled `dependencies\bin\fallback\pnpm.cmd`, using bundled Node 24.19.0 in PATH and `pnpm_config_verify_deps_before_run=false`. Research runtime Python 3.12.14, NumPy 2.2.6, Pandas 2.2.3, sklearn 1.6.1, XGBoost 3.0.2. Direct pins plus complete actual-environment lock saved under ml/.

| Actual command | Observed result / artifact |
| --- | --- |
| `Python -m pip install -r ml/requirements.txt` | Initial sandbox network WinError10013, approved rerun installed pinned libraries; environment-lock recorded with `Python -m pip freeze` |
| `Python scripts/download_phase4_dataset.py` | Initial sandbox network failure, approved public download passed; manifest hashes preserved |
| `Python -m ml.cli prepare` | Workbook schema/count/date/hash verification passed; second run completed full future-only exclusion audit before freeze; phase4-preprocessing.txt |
| `Python -m ml.cli eda`; `Python -m ml.cli features` | Actual training-only figures/tables and shifted training features exported; phase4-eda.txt / phase4-features.txt |
| `Python -m ml.cli validate` | First export failed on XGBoost default NaN parameter metadata; strict tagged metadata fix tested; same configs rerun successfully and frozen; phase4-validation-first.txt / phase4-validation.txt |
| `Python -m ml.cli final` | Four frozen finalists, identical observations, final scores/predictions and selected artifact saved once; phase4-final.txt |
| `Python -m ml.cli verify-reproduction` | Passed artifact hash/version/key/prediction checks and all-model metric recalculation; phase4-reproduction.txt / reproduction.json |
| `Python -m ml.reporting` | Actual five requested research documents/figures, worst products and final model details created; phase4-reports.txt |
| `Python -m ml.cli infer --sku 20700 --origin 2011-11-10 --horizon 28` | Actual saved artifact produced 28 nonnegative daily points and valid forecast-v1 JSON; phase4-inference.txt / last-inference.json |
| `Python -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase4-backend.xml` | **112 passed**, 1 upstream Starlette/AnyIO deprecation; phase4-backend.txt / XML |
| `Python -m pytest ml -c ml/pytest.ini -q --junitxml=docs/test-results/phase4-ml.xml` | **59 passed**; chronological ordering, cohort independence, shifted features, recursive future mutations, zeros/missing/unknown/history/horizons, JSON contract, deterministic models/reload, metadata/version/hash/path guards; phase4-ml.txt / XML |
| In frontend: `pnpm test --reporter=junit --outputFile=../docs/test-results/phase4-frontend.xml` | Sandbox esbuild directory denial; approved rerun **20 passed**, no failures/errors; phase4-frontend.txt / XML |
| In frontend: `pnpm build` | Same sandbox denial; approved rerun **passed**, 32 modules, 3.06 seconds; phase4-frontend-build.txt |
| `Docker compose up -d`; `Docker compose ps -a --format json` | First sandbox launch StandardOutputEncoding/redirect failure; approved rerun existing services running, MySQL healthy, migration exit 0; phase4-compose.jsonl |
| `Docker compose exec -T backend alembic current`; `... alembic check` | **7cf0674f24d9 (head)**; no new upgrade operations; phase4-migration.txt. No schema change/downgrade |
| `Python scripts/verify_phase1.py` | Approved actual localhost MySQL/API/proxy/session verification: **15 live checks passed**, MySQL 8.4.11; copied non-secret JSON to phase4-live.json |
| `Python -m pip check`; `Python -m compileall -q ml` | Passed; no broken requirements or syntax errors; phase4-pip-check.txt |
| `Python scripts/finalize_phase4.py` | Verified actual artifact/report/test/runtime evidence before generating phase4-summary.json and this gate record |

### Failures, corrections and limits

Final figure polish initially imported Matplotlib before the workspace cache was configured; its default user-cache write was denied and it fell back to a temporary cache. Moved the date-format import after ml.eda's workspace-cache initialization and rerendered successfully. This affected plotting setup only; frozen model/metrics/source inputs were unchanged.

First validation trained/predicted correctly but strict JSON refused XGBoost's `missing=NaN` default parameter. This was a metadata-format error, not a missing-value substitution in training or a metric. Stopped before freeze/test; tagged only nonfinite estimator-default metadata, kept all forecast/metric JSON strictly finite, added a regression test and reran identical configs. First validation prediction SHA-256 was preserved for comparison. No hyperparameter/split changes followed scores. Network/esbuild/Docker environment failures were rerun with execution approval; no external account, default published credentials or destructive command was used. Some apply_patch context matches failed atomically before a successful edit; a wrong roadmap filename was corrected. Public web download rendering had a size limit, so the explicit public-download Python script was used. Proposal terminal text initially hit cp1252 subscript encoding; UTF-8 reads/outputs resolved inspection. Original DOCX remains unchanged.

Limitations: small fixed 60-SKU cohort, one final 28-day horizon, fewer than two full annual cycles, UK gift/wholesale online context, gross observed purchases rather than stockout-censored latent demand, no inventory availability/store/category/events, past-only weighted transactional GBP prices, unknown/new SKUs rejected, and all-vocabulary contiguous history required at inference. Actual forecasts are fractional; future decision rounding/mapping/storage belongs to Phase 5. No confidence/significance, Kenya fieldwork, participant usability, production hosting or full completed-system claim. Model joblib files and registry must be trusted; hashes do not make arbitrary pickle files safe. Earlier Recharts/dependency review and upstream deprecation remain future deployment work.

**Phase 4 exit gate passed on actual evidence. Stop here. Phase 5 has not begun.** Research docs, real comparison records, test/build/runtime artifacts and this log are complete. Next authorized increment may integrate the verified contract with explicit product mappings, persisted forecasts, explainable inventory decisions and dashboard; it requires a new user instruction.

### Additional reproduction evidence and corrected setup

`Python scripts/verify_phase4_validation_reproduction.py` independently refit all 12 predeclared candidate/origin combinations without using final labels or changing selection. All 20,160 predictions matched their recorded validation values within 1e-10; largest actual absolute difference **5.684e-14**. Parallel floating-point tree accumulation can change CSV bytes at very small precision. The first failed-export table was overwritten on retry; only its byte hash was retained, so exact numerical comparison with that first table is unavailable. Fresh independent refits of the preserved completed validation table were verified; no bit-for-bit tree CSV or binary promise is made.

Found and fixed fresh-checkout setup issues: tracked manifest with ignored raw files previously assumed files existed; downloader now reacquires missing files, verifies saved hashes and preserves original snapshot metadata. The isolated-workspace script copies research sources/terms/protocol and tests without prior processed targets, frozen results, model binaries or credentials. Ran `Python scripts/create_phase4_reproduction_workspace.py .local/phase4-reproduction`, then `Python .local/phase4-reproduction/scripts/download_phase4_dataset.py`. Sandbox socket access failed; approved public reacquisition completed and both original hashes matched. The actual setup and download logs are preserved. Two meaningful setup tests raised the final ML suite to **59 passed**. A complete independent retraining pipeline in that fresh workspace was not run; existing-record artifact reproduction, all-candidate validation refits and actual raw reacquisition were run. README includes precise isolated rerun commands.

The first `scripts/finalize_phase4.py` invocation occurred while reacquisition was still running; its gate correctly refused completion and wrote an AssertionError trace. Waited for successful hash verification, then reran finalization. First refusal preserved in phase4-finalization-first.txt. No result was inferred from an unfinished process.

## 2026-10-01 — Phase 3 sales and historical import completed

### Implemented scope and decisions

- Followed proposal sales/inventory use cases (3.12, 4.3–4.6) and the existing Phase 3 roadmap. Kept the modular N-tier architecture; no ML/Phase 4 code, additional domain services or automatic procurement.
- Manager-only operational sales with product/SKU snapshot, positive exact decimal quantity, timezone-aware sale date, optional KES unit price, authenticated actor and UUID retry key. Prices absent from history stay NULL. Dates are validated, normalized to UTC and shown/entered in Nairobi time; future dates and years outside MySQL DATETIME range are rejected.
- Lock product then refresh/lock inventory row, compare the submitted inventory version and require quantity <= on_hand - allocated. Incoming stock and safety stock do not authorize overselling. Stock, version, sale and its uniquely linked audit movement commit together or roll back together. Identical request-key retries return the existing sale without another decrement; conflicting reuse is rejected.
- Paginated sales history with product/user/date-range/source filters and stable newest-time/id ordering. Archived products retain history. No sale edit/delete/returns implementation was added.
- Separate bounded historical CSV preview/confirmation: UTF-8, exact schema, 1 MiB / 5,000 rows, product/date/decimal validation, explicit accepted preview and every rejected original row/reason. Confirmation is explicit, versioned, manager-owned and expires after 30 minutes. All accepted rows commit atomically; rejected rows remain visible/stored. Historical imports never change stock/version/movements.
- Exact committed file SHA-256 prevents repeat import; normalized imported-row identities enforce duplicates within/across files, with product/external ID when provided and content identity otherwise. Distinct identical transactions need distinct external IDs. A conflict after preview rolls back the entire confirmation and requires re-preview. This policy is explicit in UI and docs/SALES_IMPORT.md.
- React sales entry, sales history and CSV upload/preview/rejection/confirmation pages, read-only restrictions, success/error feedback and session expiration handling. Sale success remains visible if a subsequent stock reload fails, preventing an ambiguous double submission. History ignores late responses after filter/page changes.
- Additive migration `7cf0674f24d9` extends sales/audit and adds import batches; existing records preserved. Nullable legacy actor/SKU and a documented created-at sentinel avoid fabricating old attribution. Reviewed/explicitly updated movement-kind check (autogeneration omits changed check expressions). Unsafe data-bearing downgrades are refused; no downgrade/delete/volume reset occurred.

### Actual commands and results

Commands ran from the project root unless stated. `$Docker` is `C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`. `$Pnpm` is `C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`. Frontend commands set bundled Node bin on PATH and `pnpm_config_verify_deps_before_run=false`, consistent with the earlier installed dependency environment. Secrets are excluded.

| Command / action | Actual result |
| --- | --- |
| Inspected source/tests/docs; read roadmap and proposal sales/inventory excerpts | Confirmed Phase 3 only; first search used nonexistent docs/ROADMAP.md and tests/test_migrations.py, then used rg inventory to read actual filenames |
| In backend: `DATABASE_URL=sqlite:///migration-authoring.db`; `alembic upgrade head`; `alembic revision --autogenerate -m "transactional sales and historical import previews"` via .venv Python | Generated revision; manually reviewed/reworked batch alterations, named FKs/uniques and movement-kind check; new-database migration/metadata test passed |
| `.venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase3-backend.xml` (first run) | 106 passed, 1 failed, 4 setup/teardown errors in 60.89 seconds; short IDs and fixture quantity replacement fixed as below |
| Same complete backend command after fixture fixes | 109 passed, one upstream warning, 66.70 seconds |
| Same complete backend command after lower date bound / preview-ownership tests | **112 passed**, zero failures/errors/skips, one upstream warning, 60.42 seconds; final JUnit saved |
| In frontend: `& $Pnpm test --reporter=junit --outputFile=../docs/test-results/phase3-frontend.xml` (sandbox) | esbuild ancestor directory access denied; no tests claimed executed; approved rerun |
| Same frontend test command (approved, first executed run) | 20 executed, 3 failed; simulated file-selection/native validity fixture fixed |
| Frontend test command and `& $Pnpm build` after fixture fixes | 20 passed; 32-module production build passed, 5.14 seconds |
| Final frontend test command and build after history-response/read-only messaging refinement | **20 passed**, zero failures/errors; native production build passed, 32 modules, 3.79 seconds; final JUnit saved |
| `& $Docker compose up --build -d` (first Phase 3 build) | MySQL healthy, additive migration exited 0; API/frontend running |
| `& $Docker compose exec -T backend alembic current`; `... alembic check` | `7cf0674f24d9 (head)`; no new upgrade operations detected |
| `.venv/Scripts/python.exe scripts/verify_phase3.py` (approved host local API/MySQL access) | **43 live checks passed**; exact final code retested after rebuild, again 43 passed |
| Final `& $Docker compose up --build -d` with output saved to docs/test-results/phase3-compose.txt; `compose ps -a`; `compose exec -T backend alembic check` | All exited 0; MySQL healthy, API/frontend running on localhost, migrate exited 0, schema matches |
| `& $Docker compose exec -T frontend pnpm build` | Container Node 22 production build passed, 32 modules, 3.98 seconds; same asset hash as native final build |
| Actual in-app browser actions using cua_repl | Authorized manager sign-in, created tagged product/category, recorded sale, filtered history, uploaded actual CSV, previewed every rejection, confirmed, re-previewed repeated file, reloaded stock and inspected audit; archived fixtures and signed out |
| `.venv/Scripts/python.exe scripts/verify_phase3_browser_persistence.py` (approved MySQL access) | Browser fixture independently persisted: 17 kg/version 2, operational 3 kg plus historical 50 kg, only opening/sale movements; archived history preserved |
| Parse final JUnit/live/browser reports and write docs/test-results/phase3-summary.json | Zero suite failures/errors; all 43 live checks passed; browser persistence passed; Phase 4 false |

### Integrity/security evidence

Actual MySQL simultaneous sales attempted to sell 7 units twice from 10 at version 1. Responses [201,409]; exactly one sale persisted, on-hand 3/version 2, only one sale movement. Injected an audit-insert failure in an independent real MySQL service transaction: sale, stock, version and audit remained unchanged. Insufficient stock, stale inventory, invalid date/quantity/product, forged actor and archived product attempts changed no ledger records. Live researcher and anonymous sales/preview/confirm requests received 403/401; researcher could read history. Temporary researcher was disabled after logout; manager session revoked.

Historical preview found 2 valid and 4 rejected rows (duplicate, invalid quantity/date/SKU). Confirmation saved two historical observations, including quantity 100 against current stock 3, with current stock/version/allocations/incoming/audit unchanged. Exact-file and confirmation repeats created no additional rows. A different already-previewed overlapping batch failed unique identity at confirmation and rolled back every row, preserving preview status. Re-preview explicitly rejected the existing identity; old preview version and archived-after-preview confirmation were rejected. Date/product/actor/source history pagination passed.

Browser smoke: created 20 kg opening stock, sold 3 kg at KES 120.50 (sale #6), saw 17 kg/version 2 and one filtered operational record. Actual CSV upload contained a valid 50 kg historical row, a duplicate, and an invalid date/quantity row: 1 accepted/2 rejected shown with values/reasons. Confirmed valid row, repeated file recognized as committed, reloaded stock still 17 with only opening and operational-sale movements. Independent MySQL checks proved both browser sales and inventory/audit persisted. Test records archived; user data/history not deleted. This is a synthetic smoke test, not a research dataset or representative usability assessment.

### Failures and fixes

- Pytest embedded oversized CSV contents in parameter IDs, exceeding Windows' 32767-character environment variable bound at setup/teardown. Explicit short IDs fixed the test harness. Stored first-failure report is shortened to meaningful messages instead of retaining huge payload/environment dumps.
- A test fixture used `replace(',2', ',3')`, changing a date's year as well as quantity; replaced only the final `,2\n` field and asserted the conflicting import really contains two valid rows. No application success was inferred from the faulty fixture.
- Sandbox esbuild could not read ancestor runtime directories; approved execution succeeded. First real frontend run had three failing preview tests because jsdom's required file-input validation did not accept a mocked file-selection event. Explicit test form submission fixed the fixture; actual browser file chooser upload/submit succeeded.
- Browser native checkbox setValue changed checked state without dispatching React's event; observed the still-disabled confirmation, used documented uncheck/check actions, then verified committed status. No import was claimed from the first click.
- Documentation script defaulted to Windows cp1252, introduced punctuation encoding and failed on a UTF-8 quote. Corrected reads/writes to explicit UTF-8 and repaired affected text; roadmap/status replacements then applied correctly.
- No unresolved application/test failure remains at this gate. One upstream Starlette/AnyIO deprecation warning remains; dependency security review from earlier phases is not claimed completed.

### Evidence, exit gate and remaining limitations

Reports/screenshots/input are under docs/test-results: phase3-backend.xml (112), phase3-frontend.xml (20), first-failure reports, phase3-live.json (43), phase3-browser.json, phase3-browser-persistence.json, phase3-summary.json, phase3-compose.txt, phase3-browser-upload.csv and four browser screenshots. API/database/architecture/testing/roadmap/README updated; SALES_IMPORT.md documents schema/policies.

**Phase 3 exit gate passed.** Sales persist with atomic stock/audit, failed transactions roll back, real concurrent sales are safe, historical imports do not affect current stock, duplicate/idempotent imports and roles are verified, complete backend/frontend suites and native/container production builds pass, actual MySQL/API/browser verification passed, and this log records real evidence. **Stop at Phase 3; no Phase 4 work begun.** Compose services remain available on localhost; browser signed out.

Limits: synchronous bounded CSV batches; no returns/refunds/sale correction, automatic operational/history overlap inference, multi-store/currency conversion, large-load benchmark, representative user evaluation or cross-browser certification. Identical legitimate historical transactions need external IDs. Offset page boundaries can move when new sales arrive. Source overlap/provenance and dataset/license/horizon must be confirmed before future research. Research forecasts, risk/replenishment/dashboard and full proposal evaluation remain Phases 4–6; no forecasting winner or accuracy is claimed.

## 2026-10-01 — Phase 2 catalog and inventory completed

### Implemented scope

- Category/product create, read, update and recoverable archive/restore. Active products prevent category archive. Reserved category names and normalized unique SKUs remain reserved after archive.
- Product metadata, category, unit, lead time (1–365 days), nonnegative safety stock and configured overstock multiplier (>1, <=100). Threshold means future forecast target × multiplier; no Phase 2 forecasting/risk claims.
- Exactly one current inventory row per new product, created atomically with opening stock and its audit record. Separate inventory form edits on-hand, confirmed incoming and allocated quantities with a required reason.
- Manager-only writes; authenticated researcher reads; anonymous/expired/revoked requests rejected. Same authorization enforced on server regardless of hidden browser controls.
- Append-only API stock movement history: opening/adjustment types, actor, reason, UTC time and before/after snapshots for all three stock quantities. Product/category archive preserves stock and history.
- SQL row locking and stock version check prevent stale editor overwrites. Audit and stock changes commit/rollback together. Refresh locked inventory objects to avoid using values from an earlier ORM identity-map snapshot.
- React Products/Categories/Inventory navigation, CRUD/configuration forms, archive visibility/restoration, clear validation/conflict errors, manager/researcher views, reload action, stock history in Nairobi time and reset forms after saves.
- Migration `4ceb0a570e41`, after `1792a942441c`, applied to real MySQL. Existing current-stock rows receive version 1. No downgrade, hard delete or volume removal executed.

### Actual commands, results and fixes

`$Docker` and `$Pnpm` denote the exact executable paths recorded in the Phase 1 entry below. Frontend commands used the bundled Node PATH and `pnpm_config_verify_deps_before_run=false`; Docker/network/esbuild commands required approved execution outside the sandbox. Phase 2 development began on September 30 and verification continued into October 1 (Africa/Nairobi).

| Command/action | Actual result |
| --- | --- |
| In backend, with `DATABASE_URL=sqlite:///migration-authoring.db`: `python -m alembic upgrade head`; `python -m alembic revision --autogenerate -m 'catalog archives and inventory audit'` | Created revision `4ceb0a570e41`; reviewed and used batch constraint operations for SQLite/MySQL compatibility |
| `.venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase2-backend.xml` (initial Phase 2) | 52 passed, one upstream warning, 14.28 seconds |
| Code review of locked inventory reads | Identified potential stale preloaded ORM values; added `populate_existing` to the locked read and a regression scenario. This was found by review, not falsely reported as an observed failed test |
| Same backend command after fix/regression | **53 passed**, one upstream Starlette/AnyIO deprecation warning, 13.43 seconds; report preserved |
| In frontend: `& $Pnpm test --reporter=junit --outputFile=../docs/test-results/phase2-frontend.xml`; `& $Pnpm build` | Initial 9 frontend tests and build passed; native build 31 modules, 2.12 seconds |
| `& $Docker compose up --build -d` (Phase 2, then after concurrency/form-reset fix) | Both builds/startups passed; MySQL volume preserved, migration exited 0, backend/frontend recreated |
| `& $Docker compose exec -T backend alembic current` | `4ceb0a570e41 (head)` |
| `& $Docker compose exec -T backend alembic check` | No new upgrade operations detected against actual MySQL schema |
| `& $Docker compose exec -T frontend pnpm build` | Production build passed in Node 22 container: 31 modules, 3.83 seconds |
| `.venv/Scripts/python.exe scripts/verify_phase2.py` | **33 live checks passed**, including MySQL persistence, category/product CRUD, precision, invalid inputs, unique SKU, archive/restore, researcher restrictions and concurrent stock writes [200, 409]. Verification records archived with audit preserved; temporary researcher disabled after logout |
| Final `& $Pnpm test --reporter=junit --outputFile=../docs/test-results/phase2-frontend.xml` after form reset correction | **9 passed**, zero failures/errors; reported suite time 2.445 seconds |
| Actual in-app browser localhost workflow | Manager signed in; category/product created; opening stock 25 kg, safety 4.5, lead time 5, multiplier 2.5 saved; lead time edited to 6; stock changed to 30.5, incoming 10, allocated 2 with reason; before/after actor history verified; product/category archived; logout returned to sign-in |
| Browser category automation selector | Exact label selector found no dropdown; inspected unchanged state and selected observed `select[name=category_id]` successfully. No application save failure |

Several patch attempts failed to match existing text and made no partial edits; corrected contexts before applying. HTML allocation maximum originally used the old stock value, which could obstruct valid combined increases; removed that stale maximum and retained server/database allocation validation. New-category/product forms now reset after successful creates. No failed tests were invented; all executed test outcomes are recorded above.

### Evidence and remaining work

- Backend: `docs/test-results/phase2-backend.xml` (53 passed). Frontend: `docs/test-results/phase2-frontend.xml` (9 passed). Live MySQL/API: `docs/test-results/phase2-live.json` (33 passed). Actual browser screenshot: `docs/screenshots/phase2-inventory.png` (test data, not research findings).
- Reusable Phase 1 script now checks the current migration head and writes a separate `phase1-live-latest.json`, preserving the original pre-Phase-2 gate evidence.
- Final `.venv/Scripts/python.exe scripts/verify_phase1.py` against the Phase 2 schema passed all 15 live foundation checks again; evidence saved separately in `phase1-live-latest.json`.
- Excluded local SQLite migration-authoring files from the backend Docker build context; they are diagnostic test artifacts, not application data.
- Final `& $Docker compose up --build -d` and `& $Docker compose ps -a` passed after that exclusion: MySQL remained healthy, migrations exited 0, API/frontend running. `compose exec -T backend python` checked backend readiness via urllib (200); `compose exec -T frontend node` checked the Vite API proxy via fetch (200). MySQL volume and audit records preserved.
- Confirmed XML reports contain 53 backend tests with zero failures/errors and 9 frontend tests with zero failures/errors; all saved live checks are passed. `git check-ignore .env .local/verification-account.json` confirms both local credential locations are excluded from Git.
- **Phase 2 gate passed.** This is 62 automated tests plus 33 separate live checks. It does not imply all 24 proposal-wide cases have passed: sales/import/forecasting/decision-support/usability cases remain pending.
- Phase 3 remains unimplemented under the explicit Phase-2-only instruction. MySQL/API/frontend services remain running on localhost. Generated local manager credentials remain ignored under `.local`; browser is signed out. No external account or procurement action occurred.
- Remaining: Phase 3 sales/import after authorization; Phase 4 confirmed dataset/horizon and genuine experiments; Phase 5 decision rules/charts/reports; Phase 6 full evaluation. Multi-browser compatibility, representative user testing, performance benchmarks and dependency security review are not claimed complete.

## 2026-09-30 — Phase 1 live verification and Phase 2 gate

At the start of this increment Phase 1 was not complete. Its required live/runtime gates subsequently passed, as recorded below, before Phase 2 source changes. No Phase 3 implementation is authorized in this increment.

### Commands and observed results

Commands ran from the project root unless a working directory is stated. `$Docker` below denotes `C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`; `$Pnpm` denotes the bundled `dependencies/bin/fallback/pnpm.cmd`. Passwords/tokens are deliberately omitted from evidence.

| Command | Actual result / corrective action |
| --- | --- |
| `docker compose version`; `Get-Command docker`; standard Docker Desktop path/service/registry checks (sandbox) | Docker not found in sandbox PATH/standard system installation; no startup claim |
| `wsl.exe --list --verbose` (sandbox) | WSL access denied; reran with execution approval |
| `wsl.exe --list --verbose` (approved) | Found running `docker-desktop`, WSL version 2 |
| `Get-Command docker` (approved) and Docker discovery | Found per-user Docker CLI at `$Docker`; prior absence conclusion corrected |
| `& $Docker version` | Client/engine 29.8.1; Docker Desktop 4.93.0, desktop-linux context |
| Inline Python local-env creation attempt | Failed with Python SyntaxError caused by shell quoting; wrote a reusable Python file instead |
| `& $Docker compose up --build -d` (first attempt) | Failed: required MySQL environment variables missing; no containers claimed started |
| `.venv/Scripts/python.exe scripts/create_local_env.py` | Created ignored `.env` with random local MySQL credentials; existing files are never overwritten |
| `& $Docker compose up --build -d` (retry) | Passed: db healthy, migrations exited 0, backend/frontend started; required images built |
| `.venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase1-reverification-backend.xml` | 16 passed, one upstream Starlette/AnyIO warning, 4.18 seconds |
| `.venv/Scripts/python.exe -m pip check` | No broken requirements |
| In frontend: `& $Pnpm build` with bundled Node PATH and `pnpm_config_verify_deps_before_run=false` | Sandbox esbuild failed with ancestor-directory access denied; approved rerun passed: 30 modules, 1.84 seconds |

Added `scripts/verify_phase1.py` to run against the actual MySQL/API stack after migration. It creates an authorized manager using Argon2id and saves generated local credentials only in ignored `.local/verification-account.json`; non-secret results go to `docs/test-results/phase1-live.json`. It does not mock API responses or database access.

| Further command | Actual result |
| --- | --- |
| `& $Docker compose ps -a` | MySQL healthy, API/frontend running, migration container exited 0; ports 3306/8000/5173 bound to localhost |
| `& $Docker compose exec -T backend alembic upgrade head` | Passed; idempotent application to current database |
| `& $Docker compose exec -T backend alembic current` | `1792a942441c (head)` |
| `.venv/Scripts/python.exe scripts/verify_phase1.py` (approved local network execution) | 15 live checks passed: MySQL 8.4.11, revision, active manager, Argon2id, live/ready 200, anonymous 401, wrong password 401, login 200, protected 200, logout 204, revoked 401, expired 401, frontend 200, proxy readiness 200 |
| In frontend: `& $Pnpm test --reporter=junit --outputFile=../docs/test-results/phase1-reverification-frontend.xml` | 2 passed; component tests use simulated API responses, separate from live checks |

**Phase 1 gate passed before Phase 2 source changes.** Required Compose services, actual MySQL connectivity, migrations, health, authorized-account creation/session behavior, complete backend suite (16 passed) and production frontend build all passed. Earlier unavailable-Docker status is superseded by per-user CLI discovery and actual execution. Phase 2 now begins; Phase 3 remains excluded.

## 2026-09-30 — Proposal analysis and foundational increment

### Completed work

- Inspected the initial workspace: only the consolidated five-chapter DOCX proposal existed. Read all chapters, tables, references and appendices; extracted text and inspected seven embedded diagrams. Preserved the source file.
- Documented functional/non-functional requirements, the four-objective evidence mapping, architecture/database/API design, research protocol, phased roadmap and all 24 proposal test cases.
- Created backend/frontend/ML/data/docs structure, local environment template, ignore rules, Git repository, Python virtual environment, dependency pins/locks and Compose/Docker configurations.
- Implemented FastAPI health/readiness, SQLAlchemy operational schema and Alembic initial migration, authorized-account CLI, Argon2id password hashing, expiring database-backed sessions, generic sign-in failures, account lockout and server-side logout revocation.
- Implemented accessible React sign-in and authenticated welcome shell with Tailwind; configured Recharts for later reports. No fake charts or research values displayed.
- Added automated authentication, database integrity, failure, CORS, migration and frontend state-transition checks.

### Decisions and alignment

- Modular N-tier monolith; independent offline ML package/inference boundary; no added domain microservices.
- MySQL is the application database; isolated SQLite is a test adapter only. One current inventory row/product is explicitly allowed by proposal 3.12. Category normalization fulfills the user's requirement; sessions support meaningful logout.
- Forecast/recommendation/model-run persistence will arrive with verified interfaces in phases 4–5. Dataset/horizon/models remain provisional; no winner or accuracy invented.
- Historical imports will not change current stock; operational sales require atomic stock adjustment. Recommendations retain human review and assumptions; automatic procurement is excluded.
- Chronological validation selects/tunes models; an untouched final test estimates performance. This prevents optimizing against the final holdout.

### Errors and corrective work

- Initial pip and pnpm downloads failed with sandbox socket permission errors. Reran with network approval; Python dependencies installed successfully.
- pnpm installed dependencies but blocked esbuild's lifecycle script. Added an explicit esbuild allowlist. Noninteractive reinstall then required CI mode. Sandbox reinstall could not access the external package cache and attempted network downloads; stopped it and reran installation with approval. Final installation/build results are recorded below when complete.
- Initial tests exposed deprecated UTC construction warnings. Corrected UTC construction; retest reduced warnings to one upstream Starlette/AnyIO deprecation.

### Executed checks so far

- Initial backend: 15 passed, 25 warnings, 5.18 seconds.
- Backend after UTC correction and migration check: 16 passed, one upstream warning, 7.37 seconds.
- Migration generated and reviewed; includes operational PK/FK/unique/check constraints and indexes. SQLite migration consistency passed. MySQL execution remains unverified.
- Final stored backend report: 16 passed, one upstream warning, 5.88 seconds; `pip check` reports no broken requirements.
- Final stored frontend report: 2 passed, zero failures/errors. Production Vite build passed (30 modules, 2.58 seconds). Total: 18 meaningful foundation checks, not the completed 24-case system evaluation.
- Sandboxed esbuild failed with ancestor-directory access denied; approved test/build execution succeeded. Disabled pnpm's environment-sensitive automatic dependency precheck for that verification command after frozen installation succeeded.
- Git initialized without a commit or remote. A branch rename was blocked while updating HEAD; correcting the new empty repository reference required filesystem approval. No existing source history was changed.
- Approved Git correction first encountered sandbox-created repository ownership. A command-scoped `safe.directory` exception resolved it; HEAD now references `main`. No global Git configuration changed.
- Alembic initial migration compiled successfully for MySQL offline mode; SQL retained in `docs/test-results/mysql-initial-schema.sql`. This is not a MySQL execution result.
- Proposal SHA-256: `9b0d71f1e00b9e8fb979e577c8e48cacda0051388f0745dfe740ed170e1d24a2`. Original DOCX preserved. Node runtime used for verification: 24.19.0; Docker config uses Node 22 and remains unexecuted.
- Dependency installer flagged Recharts 2.x as retired. The currently locked package is not used in foundation UI; upgrade and verify chart contracts before phase 5. Dependency update/security review remains necessary before deployment. No audit or production security certification claimed.

### Remaining work

- Local foundation checks and stored reports completed. Docker/MySQL runtime checks require a usable Docker engine or authorized MySQL instance; do not claim them passed. The runtime gate remains open before phase 2 integration.
- Phase 2: manager authorization, category/product/inventory APIs and forms, stock movement history, validated replenishment settings and MySQL integration tests.
- Phase 3: transactional sales and historical import.
- Phase 4: confirmed dataset/license/horizon, EDA, time-safe baseline/model experiment, real comparison evidence and versioned inference.
- Phase 5: explainable risk/replenishment, dashboard/charts/reports.
- Phase 6: all 24 actual case results, compatibility, performance and approved usability evaluation.
- Supervisor/outlet/instrument confirmations from Appendix VI remain external research prerequisites; none inferred or fabricated.
