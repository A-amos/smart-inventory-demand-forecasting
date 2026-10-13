# Dataset confirmation before model development

Selected: **UCI Online Retail II**, repository ID 502, DOI [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D). Attribution: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. [Official source](https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii), [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/). Preserve attribution, license link and change notices when sharing derived material. Raw data are ignored by Git; customer identifiers are not forecasting features or exported research predictions.

The initial project contained no research dataset. The Phase 3 CSV is explicitly synthetic test input and is excluded from research. Questionnaires are requirements evidence, never ML training data.

M5 was reviewed as the proposal-supported candidate. The [organizers' repository](https://github.com/Mcompetitions/M5-methods) links the official dataset; [Kaggle rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules), read in the actual browser, specify academic/non-commercial use plus formal-agreement/data-security restrictions. No account, competition agreement or data download was attempted. Online Retail II is selected openly because it provides actual product-level transactions and prices matching the application's single-retailer sales workflow, with an explicit open license and public download. This changes the research case study from Walmart to an online gift retailer; it does not alter the application architecture or research objectives. Store/category/promotion fields are unavailable and will not be invented.

The retailer is UK based; prices are GBP, not KES. International customer destinations do not turn this into a Kenyan retail study. Results cannot establish Kenyan shop performance, and any future M5 US results likewise cannot establish Kenyan performance. The gift/wholesale/online setting differs from local physical retail, and observed transactions do not reveal unmet demand or stockouts.

Acquisition script: `python scripts/download_phase4_dataset.py`. Exact download timestamp, file list, sizes, hashes and source snapshot are written to dataset-manifest.json only after successful acquisition. Publisher dimensions/date coverage are claims to verify from the workbook; no actual dimensions, EDA, trained model or scores are claimed in this initial confirmation document.

## Actual acquired snapshot and verified coverage

The valid-product cohort audit lists 4,707 normalized codes across the export, including 194 with no initial-training history. Of initial-history codes, 665 lack 365 days, 1,856 lack 60 positive days, 1,932 eligible codes were not selected by the seeded sampling rule, and 60 were included. No future-only product enters the training vocabulary. Complete exclusions and exact IDs are in results/cohort.csv.

Downloaded at **2026-09-30T22:14:04.092443+00:00** (2026-10-01 01:14:04, Africa/Nairobi), without an external account. The source supplies no semantic version; the snapshot is identified by these exact files:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| online-retail-ii.zip | 45,622,418 | 572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb |
| online_retail_II.xlsx | 45,622,278 | bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980 |

Actual workbook verification: **1,067,371 rows × 8 columns**. Worksheets Year 2009-2010: 525,461 rows; Year 2010-2011: 541,910 rows. Actual timestamps span **2009-12-01 07:45:00 through 2011-12-09 12:50:00**. There are 5,305 distinct raw StockCode values (including non-product codes) and 43 customer destination countries. Columns are Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID and Country. No category/store/event/promotions table is supplied.

Filtering leaves **1,003,214** positive noncancelled valid-product transactions. Missing Customer ID/Description values are retained if core fields are valid; customer/invoice identifiers never enter the forecasting features or derived prediction outputs. The entire original workbook remains locally ignored and should not be published with customer identifiers. The cohort/exclusion list, overlapping quality masks, exclusive rejected-line counts and exact processed-file hashes are preserved in results/preprocessing.json and results/cohort.csv.

Study unit is retailer-SKU/day with a seeded training-only 60-SKU sample. Initial training contains **37,753 SKU-days**; validation has **3,360 target observations**; final test has **1,680 target observations**. End-of-export December 9 is excluded by the predeclared incomplete-day policy. See EXPERIMENT_PROTOCOL.md for the exact periods and rules. These verified values supplement the pre-acquisition confirmation above; neither synthetic application test records nor questionnaire data are used.
