# Supervisor demonstration guide

This guide demonstrates working software using synthetic stock and historical UK forecasts. It does not demonstrate current Kenyan forecasting accuracy or participant satisfaction. Use a manager account and a new demonstration SKU, so earlier evidence remains intact. See [user manual](USER_MANUAL.md) for form details.

## 1. Start Docker

Start Docker Desktop and wait until its engine is running. In PowerShell:

```powershell
Set-Location C:\Users\user\Projects\SmartInventory
python scripts/create_local_env.py
docker compose up --build -d
docker compose ps --all
```

The environment generator preserves existing credentials. MySQL should be healthy, the migration job should exit0, and backend/frontend should run. If Docker is absent from PATH on this laptop, replace `docker` with `& 'C:/Users/user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'`. Never run `docker compose down -v`: it deletes database data.

## 2. Open the application

Open <http://localhost:5173>. Backend readiness is <http://localhost:8000/api/v1/health/ready>; interactive API documentation is <http://localhost:8000/docs>.

## 3. Log in

Use an authorized manager account. If necessary, create one with the hidden password prompt:

```powershell
docker compose exec backend python -m app.bootstrap --email manager@example.com --name "Inventory Manager"
```

There is no default password or public registration. Do not show passwords, tokens or local credential files during the presentation. Explain that researchers can view data but the backend rejects their writes.

## 4. Create a category

Open Categories and add a unique name, such as `Supervisor demonstration October`. Explain that categories organize products and are archived rather than deleted when history exists.

## 5. Create a product

Open Products. Use a new unique SKU, for example `DEFENSE-DEMO-01`, and name `Synthetic defense demonstration stock`. Choose the category, unit `unit`, initial stock20, lead time3days, safety stock4 and overstock multiplier2. Explain that the SKU identifies an operational product and does not automatically identify a research series.

## 6. Set inventory

Open Inventory, select the product, retain on-hand20, set confirmed incoming3 and allocated2, and enter a reason such as `Synthetic supervisor demonstration`. Save. Explain physical stock, confirmed deliveries and stock already reserved for other commitments. Show the inventory version: old forms cannot overwrite newer stock.

## 7. Record a sale

Open Sales entry. Select the new product, quantity3, an actual nonfuture date/time and optional KES price120.50. Save once. Explain that the sale, stock decrement and audit entry commit together. On-hand becomes17; incoming remains3 and allocated remains2. A sale cannot consume reserved stock or a delivery not yet received.

## 8. Inspect stock movements

Return to Inventory and show history: opening, explicit adjustment and sale. Show actor/time and before/after values. Point out that a failed sale rolls back all three writes; this is verified by actual MySQL tests, not demonstrated by corrupting the supervisor's data.

## 9. Import historical CSV

Create a small UTF-8 CSV on your laptop using the exact new SKU:

```csv
sku,sale_date,quantity,unit_price,external_id
DEFENSE-DEMO-01,2011-10-01T10:00:00Z,50,120.50,DEFENSE-HIST-01
DEFENSE-DEMO-01,2011-10-01T10:00:00Z,50,120.50,DEFENSE-HIST-01
DEFENSE-DEMO-01,invalid,-1,120.50,DEFENSE-HIST-02
```

Open CSV import, choose the file and Preview CSV. Expect one valid row and two rejected rows (duplicate and invalid date/quantity). Review all reasons, acknowledge valid-only import and confirm. Show Sales history: the historical quantity50 is stored, while on-hand remains17. Repeating the same file/confirmation does not insert it twice. Explain the1MiB/5000row limits and30minute preview expiry.

## 10. Explain forecast mapping

Open Dashboard. First show that current inventory is UNASSESSED: this does not mean stock is adequate. Select the synthetic product. For a historical demonstration only, acknowledge the UK research limitation, map it explicitly to supported series `20728`, and give a reason such as `Synthetic stock paired with UK20728 for historical defense demonstration`.

This mapping is an illustrative association, not proof the synthetic product is the same real UK item or a Kenyan forecast. Historical CSV import is not automatically a compatible research training feed.

## 11. Generate or view the historical forecast

Select the acknowledged UK historical research context, dated2011-11-11. Generate a28day forecast at origin2011-11-10, or inspect an existing stored historical forecast. Show dates, units, selected `mean_28`, model/version/digest, graph and accessible daily table. The27.857142857unit daily estimate for20728 comes from the last28observed daily quantities. Dates are never shifted to today. Genuine current forecasts are unavailable with the frozen2011history.

## 12. Generate or view the recommendation

Generate a recommendation using that forecast and the historical decision date2011-11-11. With the stated synthetic stock/settings:

| Component | Calculation / value |
|---|---|
| Inventory position |17+3−2=18 |
| Three-day forecast demand |83.571428571 |
| Target |83.571428571+4=87.571428571 |
| Suggested reorder |max(0,87.571428571−18)=69.571428571 |
| Excess threshold |87.571428571×2=175.142857142 |
| Status |REPLENISH |

Explain that quantities are fractional estimates without pack rounding. All incoming is assumed within lead time because there is no ETA. The decision is an immutable historical scenario snapshot, requires human review and never places an order. Do not claim this was measured2011stock or improved a retailer's costs.

## 13. Explain the dashboard

Show current stock components, applicable status counts, historical scenario context and stored histories. Explain why the historical snapshot is not applicable to today's inventory decision. A later stock/configuration change does not rewrite an old recommendation; create a new snapshot explicitly.

## 14. Show model comparison

Explain the separate validation and final-test columns. Mean_28 won validation MAE4.753635. Its final MAE/RMSE are5.335034/17.944564. Seasonal naive has lower final errors4.939881/17.008524, but final labels were not allowed to change selection. RF and XGBoost were genuinely compared; greater complexity did not guarantee better results. MAPE is omitted because many actual sales are zero.

## 15. Explain limitations honestly

UK online gift/wholesale data covers2009–2011,60selectedSKUs and a28day horizon. It does not validate current Kenyan accuracy. Deterministic stock rules are not probabilities or globally optimal procurement. Twenty-three of24proposal cases passed; TC24remains pending real participants, with zero responses. Discuss actual performance delays, any remaining dependency advisories and browser restrictions from [publication review](PUBLICATION_REVIEW.md). Original research results were not changed to improve presentation. Use [defense notes](PROJECT_DEFENSE_GUIDE.md) for oral answers.

## 16. Log out

Select Sign out and show the login form. Explain server session revocation. To stop services afterwards while preserving data, run `docker compose stop`.

Actual earlier workflow screenshots are indexed in [final screenshots](screenshots/final/README.md). They are recorded evidence, not a substitute for running today's demonstration.
