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

| Package | Installed | Returned records | Distinct advisory IDs | Audit-reported fixes |
|---|---|---:|---:|---|
| cryptography | 44.0.3 | 10 | 6 | 46.0.5, 46.0.6, 48.0.1, 49.0.0, 50.0.0 |
| pytest | 8.3.5 | 2 | 1 | 9.0.3 |
| starlette | 0.46.2 | 14 | 7 | 0.47.2, 0.49.1, 1.0.1, 1.1.0, 1.3.0, 1.3.1 |


Frontend `pnpm audit --json` also exited1: **10 advisory entries:2low,5moderate,2high,1critical**. Seven concern Vite6.3.5 (reported patch levels6.3.6–6.4.3); two Vitest3.1.3 (critical fixed3.2.6, another4.1.11); one @vitest/mocker (4.1.11). [Raw frontend audit](phase6-frontend-audit.json) includes advisory URLs and affected paths. Vitest/pytest are development tools; no Vitest UI was launched. Vite is the local Compose development server, so its advisories cannot be dismissed solely as dev dependencies. Exploit reachability was not established for every advisory. Dependency consistency and passing functional tests do not negate audit findings.

**Unresolved:** dependency advisories, upstream Starlette/AnyIO warning, TLS and deployment hardening, shared-edge rate limiting, broader input/authorization attack coverage and security assessment. A reviewed dependency-upgrade increment is recommended before any remote deployment. FastAPI0.115.12 constrains Starlette; replacing it blindly with1.x would require compatible framework upgrades and regression. No forced major upgrades or frozen ML dependency changes occurred in Phase6. Local services bind127.0.0.1; localhost HTTP is unsuitable as an assumed remote-production configuration.
