# Database design

MySQL 8.4 with InnoDB, migration-controlled schema. `Numeric` quantities use decimal storage to avoid binary rounding; timestamps are stored as UTC and converted for display. The first migration contains operational entities only. Do not use `create_all` to change a deployed database; apply Alembic revisions.

| Table | Keys and purpose | Integrity |
| --- | --- | --- |
| users | id PK; unique normalized email; name, role, password_hash, active, failed_logins, locked_until | role manager/researcher; only password hash stored |
| auth_sessions | token_hash PK; user_id FK; expires_at | server revocation/expiration; no plaintext token |
| categories | id PK; unique name; active | reusable product category; archive retains identity |
| products | id PK; unique SKU; category_id FK; name, unit, lead_time_days, safety_stock, overstock_multiplier, active | positive lead time, nonnegative safety stock, multiplier > 1; SKU retained after archive |
| inventory | product_id PK/FK; on_hand, confirmed_in_transit, allocated, updated_at, version | one current row/product; quantities >= 0; allocations <= physical stock; version > 0 |
| stock_movements | id PK; product_id/actor_id FKs; kind, reason; before/after quantities for on-hand, transit, allocations; indexed created_at | opening/adjustment/sale; unique nullable sale_id FK links sale audit; nonnegative snapshots, valid allocations; no API updates/deletes |
| sales | id PK; indexed product_id FK and sale_date; quantity, unit_price, source | quantity > 0, optional price >= 0, operational/historical source; actor_id FK, SKU snapshot, created_at; unique nullable request_key/import_identity; import_batch_id FK, optional external_id |

| sales_imports | UUID PK; unique file hash; actor FK; status/version; accepted/rejected JSON; created/committed timestamps | bounded preview and idempotent confirmation; retains all rejection evidence |

There are no cascading destructive deletes. DELETE category/product operations archive records and PUT can restore them. A category cannot be archived while it has active products. Product creation creates one current-stock row plus its opening movement atomically. Inventory changes lock the product/current-stock rows, refresh any preloaded ORM instance, compare the submitted version, and commit stock plus audit in one transaction. This refresh matters under MySQL's repeatable-read snapshots. Two editors submitting the same version produce one success and one 409; rejected updates do not add movements. The actual MySQL concurrency check passed.

Phase 3 operational sales now decrement inventory in the same transaction, lock/refresh product then stock, compare inventory version and reject quantity above on-hand minus allocated. Sale/audit/stock/version roll back together on failure. Historical imports create sales history only, without inventory or movement writes. Incoming quantities never permit physically unavailable sales.

Migration `4ceb0a570e41` adds archives, stock version and movement audit after initial revision `1792a942441c`; both were applied to MySQL 8.4.11. SQLite migration tests use batch operations for the version constraint. Phase 3 revision `7cf0674f24d9` adds sales actors/snapshots/retry/import identity, optional price, import batches and unique sale-to-movement linkage. Phase 4 keeps frozen model-run metadata as files. Phase 5 adds mappings, forecasts/points and recommendation snapshots; current head e52ad70491b2 was applied to actual MySQL and `alembic check` detects no pending differences. No downgrades were run.

Run `alembic upgrade head` from backend. Review generated SQL before applying to an existing database. Downgrades remove tables/data and require approval; none were executed. SQLite tests enable foreign keys and test constraints. Live MySQL checks separately cover migrations, persistence, duplicate SKU handling and concurrent inventory edits; Phase 3 verification separately establishes sales/import behavior (see test results).

## Phase 3 persistence and compatibility

`sales_imports`: UUID id PK; globally unique SHA-256 file_hash; bounded filename; actor_id FK; status preview/committed; positive version; accepted_rows/rejected_rows JSON; UTC created_at/committed_at. JSON retains normalized accepted values and every rejection with its original CSV values. This is a bounded upload store, not a background queue or new service. Imported identity is a unique SHA-256 of product/external ID, or of normalized content when no external ID exists. Multiple NULL identities/request keys are allowed for other sources. Product/SKU archives do not delete history. New API sales always have an authenticated actor and SKU snapshot; no update/delete sale endpoint is exposed.

Pre-Phase-3 sales have nullable actor/SKU metadata. Their created_at is a documented 1970-01-01 sentinel when migrated (original sale_date is preserved); attribution or original creation time is not fabricated. Newly written ORM/API rows receive actual UTC created_at. Legacy unknown actors are labelled in history. The migration preserves existing records and changes the movement kind check explicitly (Alembic autogeneration does not discover changed check expressions). Batch operations support the SQLite migration adapter. Downgrade refuses existing Phase 3 data to prevent accidental loss or inventing absent unit prices; downgrades require separate approval and were not executed.

Confirmation locks its batch and products in increasing ID order; it never locks/writes inventory. Database unique identity constraints resolve racing overlapping imports: a collision rolls back every row in that confirmation and leaves the preview uncommitted. No partial implicit import occurs. Actual MySQL verification confirms rollback, concurrent operational sales, idempotent imports and unchanged stock/audit/version.

## Historical Phase 4 model boundary (current schema is in Phase 5 below)

Phase 4 adds no tables or migrations. MySQL remains at 7cf0674f24d9; live alembic check reports no pending upgrade operations. Research model-run/preprocessing/feature/frozen-evaluation metadata and forecast-v1 JSON are versioned files. The trusted binary model lives under ml/artifacts. Research StockCodes are namespaced uci-online-retail-ii and are not automatically MySQL product IDs. Forecast/model/recommendation persistence and explicit SKU/history mapping are deferred to Phase 5. See research/FINAL_MODEL.md and results/forecast-schema.json.

## Phase 5 persistence

Revision c64a93b80de1 adds four append-only tables; e52ad70491b2 ensures sequence uniqueness/check and microsecond MySQL creation timestamps, including recovery from the first partial development build. Existing catalog/sales/stock/import schema is preserved. The model registry remains the frozen Phase 4 file; no separate mutable model-run duplicate is created.

| Table | Keys and evidence |
|---|---|
| forecast_mappings | UUID PK; product/actor FKs; original product SKU/unit; supported research StockCode/namespace; enabled; unique product+positive sequence; reason; UTC creation time |
| forecasts | UUID PK; product/mapping/actor FKs; product SKU/unit and series/namespace; context; origin; horizon 1–28; model/feature versions and artifact digest; unique UUID request key/fingerprint; original forecast-v1 JSON; creation time |
| forecast_points | Composite forecast FK + horizon-day PK; day 1–28; date; finite nonnegative NUMERIC(24,9) predicted quantity; no cascade deletion |
| recommendations | UUID PK; product/forecast/actor FKs; SKU; context and as-of date; positive inventory version; constrained ADEQUATE/REPLENISH/OVERSTOCK status; rules version; immutable snapshot JSON; unique request key/fingerprint; creation time |

Forecast child rows are ordered by horizon day. Histories are ordered creation time descending then ID; MySQL DATETIME(6) prevents loss of subsecond ordering. Mapping identity instead uses monotonically increasing sequence under a locked product row. Foreign keys preserve archives/history. No update/delete evidence endpoint exists. ORM UPDATE/DELETE listeners and eight database triggers reject evidence mutation, including SQL bypass of the ORM. Mapping changes append another revision. Every recommendation retains the complete formula components and original model/date/stock/configuration versions; later stock edits never rewrite it. Decimal quantities serialize as strings, avoiding float quantity/money conversion; the raw original forecast-v1 JSON retains original precision.

MySQL DDL is not transactional. The first development startup failed on trigger creation (binary logging privilege, error 1419) after creating forecast_mappings. Migration now resumes table/trigger installation without dropping evidence. Local Compose enables log_bin_trust_function_creators=1 to permit its scoped DB user to create triggers; no global SUPER grant or database reset is used. Downgrades explicitly refuse destructive evidence changes. Deployment privilege/replication settings need separate review; see DECISION_SUPPORT.md and actual migration logs.


## Final Phase 6 verification

No new schema/migration. Actual MySQL8.4.11 is at e52ad70491b2; alembiccheck finds no differences. Eight immutable triggers and direct browser-created sale/stock/audit/forecast/decision persistence are verified. Same-stock sales serialize safely; audit failure rolls back all writes. Cross-product load exposed a gap-lock deadlock; bounded1213retries fix the measured defect without weakening stock/version rules. Reproduction uses a new project-scoped volume and retains both volumes. No reset, drop or downgrade was run. See test-results/phase6-stack.json, phase6-sales-live.json, phase6-browser-persistence.json and phase6-reproduction.json.
