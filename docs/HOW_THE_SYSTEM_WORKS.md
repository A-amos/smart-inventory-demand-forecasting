# How the system works — study guide

The application records stock operations and uses a genuinely evaluated historical forecasting model to explain inventory decisions. The frozen research uses UK data from2009–2011. It does not establish current Kenyan accuracy. Source paths below are relative to the repository; every business endpoint starts with `/api/v1` and requires authentication.

## A. Overall architecture

The browser displays forms/charts, FastAPI validates requests and calls services, and SQLAlchemy reads/writes MySQL. The Python ML module supplies frozen inference; offline experiments run separately. This keeps interface, rules and persistence responsibilities clear without domain microservices. Files: `frontend/src`, `backend/app/api`, `backend/app/services`, `backend/app/models.py`, `ml`. Tables and endpoints are explained below. [Architecture](ARCHITECTURE.md) contains the diagram.

## B. Frontend

React renders components and manages form/session state. Vite builds/serves the interface, Tailwind styles it and Recharts plots demand. A proxy forwards `/api` to the backend, allowing the browser to use one origin. Files: `App.jsx`, `Workspace.jsx`, `SalesPages.jsx`, `Dashboard.jsx`, `api.js`, `vite.config.js`. The frontend never writes MySQL directly; it displays authenticated API responses and meaningful errors. Hiding a button is convenience, not authorization.

## C. FastAPI backend

FastAPI maps a URL/method to a handler. Pydantic checks dates, types and constraints before services execute business rules. SQLAlchemy manages transactions. Files: `backend/app/main.py`, schema modules, `api/*`, `services/*`. `/health/live` checks the process; `/health/ready` checks database connectivity. `/docs` and `/openapi.json` describe executable API contracts. The backend handles role checks even if a caller bypasses the UI.

## D. MySQL database

MySQL stores users, sessions, catalog, stock, movements, sales/imports and immutable forecast/decision evidence. Foreign keys preserve references; unique SKU/request/import identities prevent duplicates; decimal columns preserve quantities/money. Alembic applies migrations instead of silently changing deployed tables. Files: `models.py`, `database.py`, `backend/migrations/versions`. Current head:e52ad70491b2. No reset/downgrade is needed for normal startup. See [database](DATABASE.md).

## E. Authentication and sessions

`POST /auth/login` validates credentials against Argon2id hashes and returns a random bearer token. Only its SHA256digest and expiry are stored in `auth_sessions`; React keeps the token in memory. Each protected request checks the session, active user and role. `/auth/me` reads identity; `POST /auth/logout` deletes the session, so reuse fails. Files: `core/security.py`, `services/auth.py`, `api/auth.py`, `bootstrap.py`; tables:`users`, `auth_sessions`. Five wrong passwords lock an account15minutes. Reload requires login; there is no public registration/default password.

## F. Categories and products

A category groups products. Managers create/edit/archive via `/categories` and `/products`; researchers read. SKU is normalized and unique, including archived products. Product creation also creates its current inventory and opening movement in one transaction. Files:`api/catalog.py`, `services/catalog.py`, `catalog_schemas.py`, `Workspace.jsx`; tables:`categories`, `products`, `inventory`, `stock_movements`. Archive preserves history, unlike destructive deletion. Product settings hold unit, lead time, safety stock and overstock multiplier.

## G. Inventory

There is one current `inventory` row per product: physical on-hand, confirmed incoming, allocated, version and timestamp. `PUT /products/{id}/inventory` locks/refetches the row, checks submitted version, validates allocations and writes an adjustment movement atomically. Version checks prevent an old form overwriting a newer edit. `GET /products/{id}/movements` shows before/after history. Files:`services/catalog.py`, `Workspace.jsx`; tables:`inventory`, `stock_movements`, `products`. Incoming is expected stock, not physical stock available for a sale.

## H. Operational sales

Manager `POST /sales` supplies active product, positive quantity, sale timestamp, optional KESprice, inventory version and request UUID. The service locks product/stock, rejects stale stock or quantity above on-hand−allocated, inserts the sale, decrements stock/version and links a movement. One commit makes all changes durable; any failure rolls them all back. Exact UUID retries return the same sale. Only a rolled-back MySQL1213deadlock gets bounded transaction retry. Files:`services/sales.py`, `sales_schemas.py`, `api/sales.py`, `SalesPages.jsx`; tables:`sales`, `inventory`, `stock_movements`. `GET /sales` provides filtered, paginated, newest-first history. Historical/backdated operational sales still consume stock now.

## I. Historical CSV import

`POST /sales/imports/preview` parses raw UTF-8CSV, required `sku,sale_date,quantity`, optional `unit_price,external_id`, maximum1MiB/5000rows. It validates every row, reports rejects and persists a bounded preview in `sales_imports`, with no stock change. Confirmation `/sales/imports/{id}/confirm` requires the preview owner, current version, explicit valid-only acceptance and an unexpired preview. It inserts accepted rows into `sales` with historical source. File hashes and per-row identities prevent repeats; conflicts roll back the whole batch. No inventory/movement writes occur. Files:`services/sales.py`, `SalesPages.jsx`; tables:`sales_imports`, `sales`. See [import policies](SALES_IMPORT.md).

## J. ML preprocessing

The offline experiment audits the UCI workbook, excludes invalid/nonpositive/cancelled/nonproduct transactions and documented duplicates, aggregates purchased units per SKU/day, and carries past observed prices forward. Customer/invoice identifiers are not features. Training-only eligibility/seeded strata select60SKUs. Missing export dates are not automatically treated as zero; complete no-transaction days use the documented zero assumption. Legitimate bulk extremes remain. Files:`ml/data.py`, `ml/eda.py`, `ml/protocol.json`, `scripts/download_phase4_dataset.py`; no application table/endpoint trains a model. Results and plots are under `docs/research`. Do not rerun destructive research stages over preserved results.

## K. Chronological splitting

Initial training ends2011-09-15. Validation uses origins2011-09-15 and2011-10-13 with28day windows. Final origin2011-11-10 predicts11-11through12-08. This models forecasting from the past into an unseen future. Randomly mixing dates could leak future information into training. Prior lags/rolling statistics are shifted; tree forecasts recursively use prior predictions rather than future actual demand/prices. Files:`ml/features.py`, `ml/experiment.py`, protocol/results JSON. No database/API training workflow exists.

## L. Baseline, Random Forest and XGBoost

Mean_28 repeats the last28observed-day mean; seasonal naive repeats the last observed week. Global Random Forest averages many decision trees. XGBoost combines trees fitted to remaining prediction errors. The study compared two configurations from each tree family on the same3360validation targets. Four frozen finalists used the same1680final targets. MAE/RMSE are measured in units per SKU-day. Files:`ml/forecasting.py`, `ml/experiment.py`, saved predictions/comparison. `GET /research/models` reads actual recorded scores; it does not retrain them.

## M. Why mean_28 was selected

The predeclared rule ranks validation MAE, then RMSE/name. Mean_28had the lowest validation MAE4.753635, so it was frozen before final labels were opened. Seasonal naive later had lower final error, but changing the winner then would use the supposedly unseen test to select the model. The mean remains selected; no tree-success story is invented. Files:`frozen-selection.json`, `validation.json`, `final-test.json`, `MODEL_COMPARISON.md`; API:`/research/models`; no model-selection database mutation.

## N. Frozen artifact

The trusted356byte `ml/artifacts/uci-retail-v1-0cc2a83c3e40/selected.joblib` stores the selected baseline object and fixed SKU vocabulary. Model metadata/feature layout/results are recorded separately. Loaders verify digest, model/feature versions, vocabulary and exact core ML library versions before inference. It is a baseline object, not a trained forest disguised as one. Files:`ml/artifacts.py`, `services/forecast_runtime.py`, `core/phase4-reference.json`, registry JSON. Never deserialize user-uploaded pickle/joblib. Publication includes this tiny verified artifact; no retraining is needed to run it.

## O. Explicit SKU mapping

Application SKUs and UCIStockCodes belong to different namespaces. Managers append a supported research mapping using `/products/{id}/forecast-mappings`, explicit reason/unit and UK-demo acknowledgement. The table `forecast_mappings` keeps sequence/actor/original product identity. SKU/unit changes invalidate applicability. Files:`decision_schemas.py`, `services/decisions.py`, `Dashboard.jsx`. Mapping is required to prevent silently forecasting an unrelated arbitrary product; it does not prove Kenyan validity.

## P. Forecast generation and storage

`POST /forecasts/{product_id}/generate` validates mapping, origin, horizon1–28, context and retry UUID, then invokes the unchanged frozen inference contract with verified development history. It saves original forecast-v1JSON and daily decimal points atomically in `forecasts`/`forecast_points`. `GET /forecasts/{product_id}` lists immutable snapshots; `/forecasts/{product_id}/{forecast_id}/history` reads the verified historical series. Files:`forecast_runtime.py`, `services/decisions.py`, `ml/contracts.py`, `Dashboard.jsx`. Compatible history ends2011-11-10; current requests fail safely. No forecast generation changes stock or trains a model.

## Q. Inventory position

Position=on-hand+confirmed incoming−allocated. It describes supply available for a replenishment scenario. Example17+3−2=18. The sale rule is stricter: only physical unallocated stock may be sold. Files:`services/decisions.py`; tables:`inventory`, `recommendations`; API:`POST /recommendations/{product_id}/generate`. Each stored recommendation snapshots the components so later edits cannot rewrite its reasoning.

## R. Target stock

Target=sum of forecast quantities for every lead-time day+safety stock. A3day lead time requires all three appropriate future dates, not a random total over28days. Missing/date-mismatched coverage is rejected. Example83.571428571+4=87.571428571. Files:`services/decisions.py`, `decision_schemas.py`; tables:`forecast_points`, `products`, `recommendations`; recommendation-generation API above.

## S. Safety stock

Safety stock is a manager-configured nonnegative buffer stored on `products`, edited through product APIs and copied into a recommendation. It is added to lead-time demand. This prototype does not estimate a service-level quantile or prove the buffer optimal. Files:`catalog_schemas.py`, `services/decisions.py`, `Workspace.jsx`; tables:`products`, `recommendations`.

## T. Stockout risk

If valid forecast target exceeds position, the deterministic rule returns REPLENISH. It is a risk/shortage indicator, not a calibrated probability or proof of an actual stockout. Without an applicable current snapshot the dashboard returns UNASSESSED, not ADEQUATE. Files:`services/decisions.py`, `Dashboard.jsx`; tables:`recommendations`, `inventory`; APIs:recommendation generation and `GET /dashboard`.

## U. Overstock risk

Threshold=target×configured multiplier. Position strictly greater than threshold produces OVERSTOCK; equality does not. Multiplier must exceed1. This configurable rule does not solve supplier-network or cost optimization. Files:`services/decisions.py`, `catalog_schemas.py`; tables:`products`, `recommendations`; product-settings and recommendation APIs.

## V. Reorder recommendation

Suggested quantity=max(0,target−position). Example87.571428571−18=69.571428571. Raw fractional quantity is preserved without procurement/pack rounding. The snapshot records incoming assumptions, safety, lead time, units, model/digest/date/stock versions and human-review boundary. Eight MySQLtriggers plus ORM guards reject evidence UPDATE/DELETE. Exact UUID retry returns the original snapshot; new UUID appends a new one. Files:`services/decisions.py`, `models.py`, evidence migrations; table:`recommendations`; APIs:generate/list recommendations. No purchase endpoint exists.

## W. Dashboard

`Dashboard.jsx` reads `/dashboard`, `/research/models`, forecast/history and recommendation APIs. It shows stock components, applicable counts, genuine historical/predicted lines, an accessible daily table and immutable decision explanations. Current/historical context is labelled, and old decisions retain original inputs. Model comparison separates validation/final scores and missing final configurations. Tables:`inventory`, `products`, immutable evidence tables; experiment metrics stay frozen files rather than mutable duplicate DBrows.

## X. Testing

Backend pytest uses temporary SQLite for fast contracts/rollback/role checks; separate live scripts verify actual MySQL locking, triggers and persistence. ML tests use small synthetic fixtures for leakage/alignment/schema/version guards, separately from real retail experiments. Frontend Vitest uses mocked API responses; actual browser/API workflows prove deployed behavior. Historical Phase6results:163backend+59ML+29frontend=251passes,23of24proposal cases passed,TC24pending participants. Publication reruns have separate reports and do not replace older evidence. Files:`backend/tests`, `ml/tests`, `frontend/src/*.test.jsx`, `scripts/verify_*`, `docs/test-results`; health/API endpoints are exercised rather than inferred working from compilation.

## Y. Limitations

UK2009–2011sales,60SKUs, bounded horizon, intermittent zeros/extremes, no stockout-censored demand or Kenyan accuracy. Historical frozen forecasts cannot establish current risk. Incoming has noETA; safety is fixed; reorder is deterministic/fractional and requires human review. No automatic procurement or demonstrated cost/service improvement. Zero participants/responses; Chrome/Firefox checks can remain tool-blocked. Dependency advisories and any publication fixes are reported in [publication review](PUBLICATION_REVIEW.md), preserving original Phase6security records. The modular architecture supports future approved data/validation work, but an interface alone does not establish valid current predictions.
