# Phase 5 decision support — Objective 3

This module implements proposal sections 3.12–3.13 in the existing FastAPI service tier. It never trains, retunes or replaces a model in a request. The validation-selected **mean_28** baseline remains frozen; seasonal naïve is a comparison, including its better final-test result. Phase 4 JSON/CSV evidence and the selected binary are SHA-256 guarded by `backend/app/core/phase4-reference.json`. Final-test results are not rewritten. This document describes rules and verification; synthetic inventory examples are not research findings.

## Available history and identity

The selected trusted artifact is `uci-retail-v1-0cc2a83c3e40`, model version `retail-demand-v1`, feature version `features-v1`, binary SHA-256 `840837c7333d8a928fc170a7ef3245299bb2dfcd0750c6eb45b0f696a8f41031`. The original Phase 4 `load_registered` and `forecast_contract` perform inference. Compatible development histories end **2011-11-10**. The adapter does not read sealed final labels, shift dates to today, invent missing days, fit an estimator, or substitute a different model. At present only origin 2011-11-10 is supported. Horizons are integer 1–28 days.

UCI Online Retail II describes UK online gift/wholesale retail, not validated Kenyan retail. No application sales are silently mixed into that research panel. No fresh operational forecasting is available with this frozen history. The ordinary stock/sales/import system continues to work. The dashboard defaults to current inventory, labels products **UNASSESSED**, and makes no present-day purchasing claim.

A manager must explicitly append a documented product → supported research StockCode mapping, including a reason and UK-demo acknowledgement. Even an application SKU that matches a supported StockCode requires this explicit mapping. The product must use `unit` (individual counts); kg/other units have no undocumented conversion. Mappings retain actor, product SKU/unit at mapping time, namespace, monotonically increasing per-product sequence and timestamp. Disabling/remapping appends another mapping; previous evidence survives. SKU/unit edits invalidate the previous mapping. Archived products retain readable history but reject new evidence.

Unmapped, disabled or unsupported series return HTTP 422: **“Forecast unavailable — insufficient or unsupported historical series.”** A changed SKU/unit/mapping returns 409. Manager-only writes are enforced server-side; researchers can read snapshots and comparisons.

## Decision dates and staleness

For a daily decision as of day D, origin must be exactly D−1 and daily forecast coverage must include every calendar day D through D+L−1. Horizon day numbers must be contiguous, dates must agree with origin+day, point count must equal the stated horizon and all quantities must be finite and nonnegative. Lead time must be a configured integer 1–365, and no more than the available forecast horizon. No single-day shortcut or extrapolation is used.

Operational decisions additionally require the actual Nairobi date; a historical origin fails the freshness gate. The pure rules have a tested valid-current-origin path; actual inference cannot produce that path without new compatible history. A **research_demo** decision requires explicit acknowledgement and decision date **2011-11-11**, using the unchanged 2011-11-10 origin. This is a historical UK forecast combined with present illustrative/test inventory, **not measured 2011 stock**, current operational validation or Kenyan performance. The UI keeps this context visible. Historical snapshots stay readable after expiry/configuration changes; the overview counts them only if context/date, SKU/unit/mapping, inventory version, lead time, safety stock and multiplier still match.

## Deterministic rules

All forecast and inventory quantities use the product unit. Currency/GBP prices are not demand quantities and are not converted to KES.

```
inventory_position = on_hand + confirmed_in_transit − allocated
lead_time_demand = sum(daily forecast quantity for each of L lead-time days)
target_stock = lead_time_demand + safety_stock
suggested_reorder_raw = max(0, target_stock − inventory_position)
suggested_reorder = suggested_reorder_raw
overstock_threshold = target_stock × configured_overstock_multiplier
```

Existing constraints require on-hand/incoming/allocation/safety to be nonnegative, allocated ≤ on-hand and multiplier >1. Invalid/missing replenishment parameters return 422. A missing forecast returns 404; mismatched product/SKU/unit/source/model/artifact/feature version, stale date or inadequate coverage returns 409. Rejection creates no recommendation.

Classification:

| State | Rule |
|---|---|
| REPLENISH | target stock > inventory position; shortage equals raw reorder |
| OVERSTOCK | no shortage and inventory position **strictly exceeds** configured threshold |
| ADEQUATE | no shortage and inventory position ≤ configured threshold |
| UNASSESSED | overview has no currently applicable immutable snapshot; this is not adequate/safe |

Safety stock is the manager's configured quantity, not an inferred confidence interval. All confirmed incoming quantity is assumed to arrive within lead time because ETA is not recorded; users must review this assumption. Allocation is excluded from usable stock. These are deterministic classifications, not calibrated stockout probabilities. There are no pack-size rules or procurement rounding. Stored daily forecast quantities use `NUMERIC(24,9)`, half-up at nine decimal places solely for database precision; the original full-precision forecast-v1 JSON is retained. Calculation uses Decimal and the stored daily quantities, preserving reproducible sums. Raw and suggested quantities are displayed. No automatic purchase or purchase-order execution exists.

Example of the rules only, **synthetic**: forecasts [1,2,3] units, L=3, safety=4; on-hand=5, incoming=3, allocated=2. Position=6, demand=6, target=10, reorder=4, multiplier=2, threshold=20 → REPLENISH. At position 20 the state is ADEQUATE; at 21 it is OVERSTOCK. These values are test inputs, not model metrics.

## Append-only provenance and failure isolation

Forecast headers preserve UUID, product/SKU/unit, mapping and source, context, origin/horizon, model/feature versions, artifact digest, authenticated actor, UTC creation time and unmodified forecast-v1 contract. Child records persist every date/horizon day/quantity. Recommendation headers preserve UUID, associated forecast, product, context/date, inventory version, risk, rules version and actor/time. Their JSON snapshots retain all formula components, shortage/raw/final reorder, threshold/multiplier, forecast/version identifiers and explanatory assumptions. ORM guards and MySQL UPDATE/DELETE triggers protect all four evidence tables. No edit/delete endpoint is exposed. No old snapshot is recalculated when stock changes; a new generation creates a new record.

Generation locks the product then current inventory where needed to obtain a consistent stock/configuration snapshot. It commits evidence only; no sales/stock/import/audit row changes. UUID request keys are unique. Exact retry with the same actor/body returns the original immutable record (including after stock changes); changed actor/body using that key returns 409. New keys explicitly append new snapshots. Concurrent same-key requests serialize and persist a single record. Mapping writes append a reasoned revision; they do not have a retry key.

Missing artifact/history → explicit 503. Corrupt/unregistered/changed metadata, binary hash, contract vocabulary or dependency version → explicit 503. The preserved registry forbids silently changing the selected model. Unavailable results are shown as errors, never zero/fake accuracy. Normal catalog/stock/sales/import routes do not load the ML module, so a forecast failure does not disable inventory. Live testing temporarily hides **only the container copy** of the artifact, restores it in `finally`, and verifies unchanged SHA-256 digests of products, sales, stock, movements and imports. The host research artifact is never moved/modified.

## Dashboard and boundaries

React dashboard uses Recharts 3.10.1 with matching react-is 19.1.0 (React 19.1.0), historical source points checked against the preserved development hash, and actual stored predictions. An accessible daily table accompanies the chart. Overview exposes current stock components and position; immutable product decisions expose every assumption/formula component and version, and mark snapshots not applicable to the current overview. Context changes clear previous overview counts while loading. Forecast/recommendation histories are paginated (20/page). The model-comparison table reads genuine Phase 4 validation and final JSON separately; untested configurations show “Not final-tested”, never zero. MAPE remains omitted for zero/intermittent demand. Research/UK limitations stay visible.

The dashboard is loaded lazily so ordinary authentication/catalog use does not download chart code immediately. Docker copies trusted selected research files and daily development data only; raw customer records and sealed final-test data are excluded. The image installs the unchanged pinned Phase 4 runtime; its Linux XGBoost wheel includes large GPU-library dependencies even though this selected baseline uses no GPU. No ML microservice or new infrastructure was introduced.

Compose enables `log_bin_trust_function_creators=1` for the localhost development MySQL instance so the existing database-scoped user can install immutability triggers without global SUPER privileges. MySQL DDL commits implicitly; migrations can resume after partial table/trigger creation. Production privilege/replication policies require a separately reviewed deployment configuration. See [MySQL 8.4 stored-program binary logging](https://dev.mysql.com/doc/refman/8.4/en/stored-programs-logging.html), [Recharts](https://recharts.github.io/) and [Recharts 3 migration guidance](https://github.com/recharts/recharts/wiki/3.0-migration-guide).

The Phase 5 gate uses actual suites, build, MySQL/API checks and browser evidence under `docs/test-results`. Phase 6 software/evidence evaluation is now recorded; participant research and current Kenyan validity remain unestablished.


Final browser/MySQL scenario: position18, lead demand83.571428571, target87.571428571, suggested reorder69.571428571, immutable inventory version3. Historical quantity50 leaves current stock17 unchanged. Separate overstock/zero-order and all identity/date/version/failure boundaries passed live verification. Current2026inference remains intentionally unavailable. See OBJECTIVE_TRACEABILITY.md, SYSTEM_LIMITATIONS.md and test-results/final-24-test-cases.md.
