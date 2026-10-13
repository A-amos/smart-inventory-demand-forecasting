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
