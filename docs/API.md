# API documentation

API version: 0.1.0; base path `/api/v1`. Run the backend and open `http://localhost:8000/docs` for Swagger or `/openapi.json` for machine-readable contracts.

## Phase 5 forecast and recommendation contracts

All paths below use `/api/v1` and existing revocable bearer authentication. Managers append/generate evidence; researchers read. No endpoint trains or executes purchases.

| Method/path | Role | Behavior |
|---|---|---|
| GET /forecast-support | Authenticated | Verified mean_28 identity/version/digest, 60 supported UK StockCodes, maximum horizon, historical origin and explicit current-unavailable/UK limitation |
| GET /products/{product_id}/forecast-mappings | Authenticated | Original mapping revisions, latest sequence first; offset≥0, limit 1–100 (default 50) |
| POST /products/{product_id}/forecast-mappings | Manager | Append supported mapping/revision or disable, with reason, unit `unit` and UK-demo acknowledgement; 201 |
| GET /forecasts/{product_id} | Authenticated | Immutable forecasts/points/original forecast-v1 JSON; creation descending then UUID; offset≥0, limit 1–100 (default 20) |
| POST /forecasts/{product_id}/generate | Manager | Frozen-artifact inference using checked development history; atomic append, no inventory mutation; 201 including exact retry |
| GET /forecasts/{product_id}/{forecast_id}/history | Authenticated | Last 56 verified historical demand days through origin for the recorded UK series |
| GET /recommendations/{product_id} | Authenticated | Original immutable decisions, never recalculated; same pagination as forecasts |
| POST /recommendations/{product_id}/generate | Manager | Validate identity/versions/date/coverage, lock stock/configuration, append formula snapshot; 201 including exact retry |
| GET /dashboard?context=operational | Authenticated | Active stock components/position and applicable snapshot counts; context operational or research_demo; invalid context 422 |
| GET /research/models | Authenticated | Genuine validation/final metrics, distinct periods and mean_28 selection; absent final configurations return null |

Example request bodies for an explicitly acknowledged **synthetic historical research scenario**:

```json
{"series_sku":"20728","enabled":true,"confirm_research_demo":true,"reason":"Synthetic stock mapped explicitly to supported UK series"}
```

```json
{"request_key":"7d9a6118-4d4c-4918-b7b9-24174683b069","forecast_origin":"2011-11-10","horizon":28,"context":"research_demo","confirm_research_demo":true}
```

Recommendation body: a new request UUID, the real stored forecast UUID, `context:"research_demo"`, `decision_as_of:"2011-11-11"`, `confirm_research_demo:true`. Defaults are operational context and actual Nairobi decision date, which safely reject stale/unavailable generation with this frozen 2011 history. Origin must equal the day before the decision date and cover every lead-time day. Request extras are forbidden; horizon is strict integer 1–28; UUIDs/dates are validated. No dates are shifted to today.

Forecast response: UUID `id`, product/SKU/unit, mapping/series/source/context, origin/horizon, model/model-version/artifact-digest/feature-version, actor/created_at, original `contract`, and `points[{forecast_id,forecast_date,horizon_day,predicted_quantity}]`. Recommendation response: UUID `id`, product/SKU, forecast/context/as-of, inventory version, risk/rules version, actor/creation and `snapshot` with all input/result quantities and identity/version/assumptions. Decimal quantities are strings; creation timestamps are UTC (naive database UTC; UI displays Nairobi). Source/decision dates retain the historical calendar.

Errors: 401 missing/expired/revoked session; 403 researcher write; 404 absent/archived mutation product or missing/other-product history forecast; 422 unsupported/unmapped/disabled series, unit mismatch or invalid parameters/body; 409 stale/mismatched product/mapping/model/artifact/feature/date/horizon/context or UUID reused for different actor/body; 503 missing/incompatible/corrupt artifact/history or preserved results. Inventory/sales/import routes remain usable during inference failure. Archived products retain readable evidence. New UUID explicitly appends; identical actor/body/UUID replays original evidence without recalculation or duplicates. See DECISION_SUPPORT.md and generated OpenAPI.

| Method/path | Authorization | Response |
| --- | --- | --- |
| GET /health/live | Public | 200 status ok; process alive |
| GET /health/ready | Public | 200 status ready on SELECT 1; safe 503 if database unavailable |
| POST /auth/login | Public | JSON email/password; 200 access_token, bearer type, seconds to expiry, safe user; generic 401 for failure/disabled/locked account; 422 invalid shape |
| GET /auth/me | Bearer | 200 id/name/email/role; 401 for missing/expired/revoked/disabled session |
| POST /auth/logout | Bearer | 204 and server session deletion; subsequent reuse returns 401 |

Never log passwords or tokens. Login uses `Cache-Control: no-store`. The frontend holds tokens only in memory. Forecasting and comparison endpoints are implemented as documented above; this sentence supersedes the historical foundation scope.

## Phase 2 catalog and inventory

All reads require an active authenticated account. Every write requires the `manager` role; researchers have read-only access. Anonymous/expired/revoked sessions receive 401, authenticated researchers attempting writes receive 403. Invalid inputs return 422, absent/archived records 404, conflicting identifiers/reference usage/stale stock edits 409.

| Method/path | Contract |
| --- | --- |
| GET /categories; GET /categories/{id} | List/read categories. Lists accept include_archived, offset >= 0, limit 1–500 (default 100) |
| POST /categories | name (trimmed, 1–120 characters), active (default true); 201 with id |
| PUT /categories/{id} | Replace name/active; supports restoration; referenced active products prevent archival |
| DELETE /categories/{id} | Archive empty category, 204; preserves stored record |
| GET /products; GET /products/{id} | Product and nested current inventory. Same pagination/archive parameters |
| POST /products | sku, name, category_id; optional unit, lead_time_days, safety_stock, overstock_multiplier, active, initial_stock; creates product, one inventory row and opening movement atomically; 201 |
| PUT /products/{id} | Replace product metadata/configuration; opening quantity cannot be changed here; supports restoration under an active category |
| DELETE /products/{id} | Archive product, 204; preserves SKU reservation, stock and movement history |
| GET /products/{id}/inventory | on_hand, confirmed_in_transit, allocated, version and UTC updated_at |
| PUT /products/{id}/inventory | All three quantities, loaded version and reason (trimmed, 3–240 characters); locks/refreshes the current row, rejects stale version, saves new version and audit atomically |
| GET /products/{id}/movements | Latest-first immutable opening/adjustment/sale snapshots, actor ID, reason and UTC timestamp; offset/limit supported; also readable for archived products |

SKU is trimmed, uppercased and restricted to ASCII letters/digits/dot/underscore/hyphen, with a leading letter/digit and maximum length 64. Duplicate checks include archived records and are backed by database uniqueness. Names/units cannot be blank. Lead time is an integer from 1 to 365 days. Safety stock and physical quantities are nonnegative decimals with at most three fractional digits and 14 total digits; allocations cannot exceed on-hand. Overstock multiplier is greater than 1 and at most 100, with three fractional digits. Its eventual threshold is target stock × multiplier; no forecast risk is calculated during Phase 2.

PUT requests supply required fields rather than partial patch semantics. Product form edits submit all metadata/configuration; stock changes use the separate inventory endpoint. A 409 stock conflict requires reloading records before resubmission. Expired authentication returns the browser to sign-in. No movement-edit/delete endpoint exists; Operational sales use the dedicated transactional sales endpoint; automatic purchases remain excluded.

## Phase 3 sales and historical imports

| Method/path | Authorization / contract |
| --- | --- |
| POST /sales | Manager; product_id, positive quantity, timezone-aware sale_date, inventory_version and UUID request_key; optional unit_price. 201 with stored sale; 200 on an identical request retry |
| GET /sales | Any authenticated user; product_id, actor_id, source (operational/historical), inclusive date_from/date_to, offset >= 0, limit 1–200 (default 50); items/total/offset/limit envelope, newest sale_date then id first |
| POST /sales/imports/preview?filename=sales.csv | Manager; raw UTF-8 CSV body with Content-Type text/csv, not JSON or multipart. Returns preview ID/version/status, counts, first 100 accepted rows (explicit truncation flag), and every rejected row with original values and reason |
| POST /sales/imports/{id}/confirm | Manager who created the current preview; JSON preview_version and accept_valid_rows=true. Commits all accepted rows atomically; rejected rows remain stored/reported. Reconfirmation of a committed batch returns its result without inserting rows |

Example operational body:

```json
{"product_id":1,"quantity":"2.500","sale_date":"2026-09-01T10:00:00+03:00","unit_price":"120.50","inventory_version":1,"request_key":"4d90205c-85f7-4d68-a6a0-9e18a46f26eb"}
```

New sale actors come from the authenticated session; client-supplied actor/source fields are rejected. Quantities are positive finite decimals (14 digits total, at most 3 fractional); prices are optional nonnegative finite decimals (14 digits total, at most 2 fractional), interpreted as KES in this Kenyan prototype. Missing price is NULL, not an invented zero. Dates must be ISO 8601 timestamps with timezone, year >= 1000, and no later than now. Stored timestamps are UTC; sales responses include Z and UI timestamps use Nairobi. Backdated operational sales still reduce stock now; use historical import for observations whose stock impact is already accounted for.

Recording a sale locks the product then the current inventory row, refreshes ORM state, compares the submitted version and requires quantity <= on_hand - allocated. Incoming/safety stock do not authorize overselling. Sale, stock/version and linked audit commit together. Invalid/archived product: 404; insufficient/stale stock or conflicting request key: 409; validation: 422. Reuse a request_key only for a retry of the same actor/product/time/quantity/price; a changed sale needs a new key. The inventory_version may be stale on an identical committed retry because replay does not adjust stock again. Phase 6 fixes a verified gap-lock deadlock: only MySQL1213 retries after complete rollback, up to three total attempts, with10/20ms backoff, same request key and fresh stock/version checks. Other errors/exhaustion return503; stale/insufficient stock remains409. See test-results/PERFORMANCE.md.

CSV contract and duplicate policy are specified in SALES_IMPORT.md. Upload bound: 1 MiB and 5,000 nonblank CSV data records; malformed schema/UTF-8/quoting: 422, incorrect content type: 415, empty/oversized file or too many rows: 413. Invalid data rows are reported in a successful preview rather than silently dropped. Preview persists no sales or stock changes. Confirmation requires an unexpired (30 minute) current preview version, at least one valid row, explicit acceptance, and active products with the previewed SKU. Re-previewing an uncommitted file refreshes validation/version; an older form then receives 409. A product or duplicate conflict rolls back the whole confirmation; preview again. Exact committed file bytes remain idempotent globally. Researchers cannot preview or confirm; 403 is enforced before body processing. Historical imports never write inventory/version/movement rows.

## Historical Phase 4 contract (superseded by implemented Phase 5 HTTP integration)

No forecasting HTTP route was introduced; existing authenticated APIs remain unchanged. The verified callable ml.experiment.forecast_contract and ml.cli infer load the selected trusted artifact and return Pydantic forecast-v1 JSON with namespaced SKU, origin, consecutive 1–28-day points/quantities, model ID/version, trained-through cutoff and created timestamp. Unknown SKU, invalid horizon, inadequate/gapped history and incompatible artifact fail explicitly. JSON Schema/example are in research/results/forecast-schema.json and example-forecast.json. This Python/CLI interface was executed; it is not listed as a deployed HTTP endpoint. Product mapping, persistence and authenticated application integration are Phase 5 work.


Final review: current routes are documented above and verified in phase6-decisions-live.json. Original Phase 4 CLI inference writes last-inference.json; use scripts/phase6_infer.py to preserve frozen results. Current2026inference remains unavailable. See OBJECTIVE_TRACEABILITY.md.
