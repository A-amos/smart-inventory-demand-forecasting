# Installation and safe reproduction

Tested environment: Windows11, Python3.12.14, Node24.19.0 and pnpm11; DockerDesktopWSL2 with Compose, containerPython3.12/Node22/MySQL8.4.11. Publication native checks used pnpm11.25.0; package/container configuration pins11.19.0. No external account is required to run locally. Commands start from the project root in PowerShell. Keep secrets local. See PUBLICATION_REVIEW.md for current dependency versions and actual checks; earlier Phase6records remain historical evidence.

## Trusted academic bundle

Source, pinned requirements and frontend lockfile are required, together with `docs/research/results/`, `backend/app/core/phase4-reference.json`, `ml/artifacts/uci-retail-v1-0cc2a83c3e40/selected.joblib` and `data/processed/phase4/development.csv`. Publication includes the original verified356byte baseline artifact and1.2MBdaily aggregate with no customer/invoice identifiers, so the ordinary clone can run historical inference without retraining. Raw archives/workbook, full training/sealed data and other binaries remain ignored. `.gitattributes` prevents newline conversion from breaking frozen hashes. Do not run training/final-evaluation/export commands over frozen results. If required files are missing/corrupt, stop forecasting and restore the trusted exact bundle; independent reproduction belongs in a new isolated workspace as documented in ml/README.md. Never deserialize user-uploaded joblib. Attribution/change notices are in ../NOTICE.md.

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

The original Phase6suites/build were executed on the main checkout, separately from isolated startup. They do not establish a cold-cache missing-artifact build. Publication now packages the two small verified runtime files and reruns application checks with compatible security updates; see PUBLICATION_REVIEW.md for actual final results. The unchanged original research lock remains for isolated historical reproduction, not for an internet-exposed application. Live fixture scripts use the ignored verification account and tagged records; read their scope first. Set `INVENTORY_TEST_REPORT_PREFIX=publication` to keep newer live reports separate. The decision verifier temporarily hides/restores only the container artifact and must run sequentially with other forecast checks. See DEVELOPMENT_LOG.md for commands.
