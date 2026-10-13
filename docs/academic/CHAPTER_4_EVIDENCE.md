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

| Candidate | Validation MAE | Validation RMSE | Final MAE | Final RMSE |
|---|---:|---:|---:|---:|
| mean_28 | 4.753635 | 36.360016 | 5.3350340136054415 | 17.944563987477665 |
| seasonal_naive | 6.078274 | 43.352902 | 4.939880952380952 | 17.00852377346079 |
| rf_leaf5 | 10.080747 | 42.761740 | 6.545168748927346 | 18.516364750269418 |
| rf_leaf15 | 10.093938 | 39.320707 | Not final-tested | Not final-tested |
| xgb_depth5 | 9.193968 | 46.835325 | 5.6156688673585275 | 18.84631666771529 |
| xgb_depth3 | 9.327391 | 43.942535 | Not final-tested | Not final-tested |


All six validation candidates use 3,360 identical targets; all four finalists use 1,680 targets. MAPE is omitted because 1,169 final actuals are zero; no epsilon or hidden positive-only subset is used. Selected mean_28 final MAE is 5.335034 and RMSE is 17.944564. Seasonal naive has lower final error; selection remains validation-based. Weak individual series are retained, including SKU 22595 with MAE 80. No significance or universal accuracy claim follows. Read-only recalculation matched all ten score sets within 1e-10: [metrics](../test-results/phase6-metrics.json), [comparison figure](../research/results/model-comparison.png), [per-SKU errors](../research/results/final-test-by-sku.csv) and [representatives](../research/results/representative-final-forecasts.png).

## 4.6 Inventory Decision-Support Results

The browser's synthetic SKU P6-BROWSER-20261001 was explicitly linked to UK series 20728. Forecast origin is 2011-11-10 for 28 days; recommendation date is 2011-11-11. Stock 17 + incoming 3 − allocated 2 gives position 18. Three daily predictions total 83.571428571; safety stock 4 gives target 87.571428571. Multiplier 2 gives threshold 175.142857142. Suggested reorder 69.571428571 yields REPLENISH. Immutable forecast 4a1f9161-32f8-4559-b724-62f80907e944 and recommendation af82e6f7-3339-4455-bc8b-45d51b85c509 were independently read from MySQL. Historical quantity 50 did not change stock 17. A separate API stock-999 scenario produced OVERSTOCK/zero reorder while preserving the earlier decision. See [persisted formulas](../test-results/phase6-browser-persistence.json), [screen](../screenshots/final/recommendation.jpg) and [rules](../DECISION_SUPPORT.md).

All confirmed incoming is assumed to arrive within lead time; there is no ETA, pack/cost or probabilistic optimization. Synthetic 2026 test stock paired with a UK 2011 forecast is a demonstration, not measured 2011 inventory or economic effectiveness. Current inventory remains UNASSESSED and unsupported/current forecast requests are rejected. Recommendations require human review and execute no purchase.

## 4.7 Summary

Software integration, bounded transaction/decision behavior and genuine historical forecasting evidence are verified. Participant usefulness, complete Chrome/Firefox compatibility and dependency remediation remain outstanding. UK data ending in 2011 cannot validate current 2026 or Kenyan accuracy. See [objective traceability](../OBJECTIVE_TRACEABILITY.md) and [limitations](../SYSTEM_LIMITATIONS.md).
