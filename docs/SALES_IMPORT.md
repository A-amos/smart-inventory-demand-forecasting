# Operational sales and historical sales import

Operational sales represent stock leaving the shop now. They reduce unallocated on-hand stock and increment its version, with an actor and linked immutable movement. Negative stock/overselling is prohibited. Allocated stock remains reserved; confirmed incoming and safety stock cannot authorize a sale. Backdating the sale time does not bypass the current-stock reduction. History is append-only in this increment; corrections/returns and sale deletion are outside Phase 3.

Historical CSV imports are observations whose stock impact has already been accounted for. They **never change current inventory, its version or stock movements**, even when historical quantity exceeds current stock. Do not upload operational sales again as history: historical deduplication applies to imported identities, not operational records. Dataset provenance and overlap between sources must be reviewed before Phase 4; no automatic source-merging/ML research is performed here.

## CSV format

UTF-8 (optional BOM), standard comma-separated CSV, unique exact lower-case headers. Maximum 1 MiB and 5,000 data records per file; no missing/extra columns. A CSV data record is numbered with the header as record 1; quoted multiline fields count as one record. Blank lines are ignored by the standard CSV reader. Required columns: sku,sale_date,quantity. Optional: unit_price,external_id.

```csv
sku,sale_date,quantity,unit_price,external_id
RICE-1,2026-09-01T10:00:00+03:00,2.500,120.50,retail-export-001
RICE-1,2026-09-02T07:00:00Z,1.000,,retail-export-002
```

SKU is trimmed/uppercased and must identify an active product. Quantity must be positive and finite, with at most 14 total and 3 fractional digits. Unit price may be blank (unknown), otherwise a finite nonnegative KES value with at most 14 total and 2 fractional digits. Sale date requires ISO 8601 with a timezone, must be within MySQL's DATETIME range (year 1000 or later) and not in the future. Date-only, ambiguous local, invalid calendar and numeric epoch dates are rejected. External ID, when present, is trimmed and limited to 120 characters; IDs are case sensitive through their hashed identity.

## Review and duplicate policy

1. Select the CSV on the CSV import page and choose Preview CSV. Structural/encoding/size errors block the upload with a clear error. Invalid data records become rejected rows with original values and specific reasons.
2. Review counts, the first 100 valid rows (larger previews explicitly say how many valid rows will import), and **all** rejected rows. A preview writes only its bounded import record, not sales or stock.
3. Explicitly accept valid rows and confirm. All accepted rows commit together. Rejections remain visible and stored. If there are no valid rows, no confirmation is offered.
4. A preview expires after 30 minutes. It can be refreshed by previewing the same file again. Refresh increments its version, so an older confirmation cannot import a different selection. Only the manager who generated the current preview can confirm it. Committed results may be seen by authorized managers in this single-store prototype.

With external_id, the duplicate identity is product ID + external ID. Without it, identity is product ID + normalized UTC sale time + exact decimal quantity + optional price. Equivalent decimal spellings and timezone representations yield the same content identity. Duplicate identities within one file or previously committed files are rejected explicitly. Reusing an external ID with changed values is also rejected, rather than replacing history. Distinct legitimate transactions with identical content require distinct external IDs; generate/export transaction IDs upstream rather than silently treating duplicates as independent demand.

SHA-256 of exact file bytes identifies repeated files globally. Re-preview/reconfirm of a committed file returns its original result/counts without additional inserts. Byte-different files still undergo row-identity checks. If another import wins a duplicate race after preview, or a product is archived/renamed, the entire confirmation rolls back with 409 and instructions to preview again. No other accepted rows are silently saved during that failed confirmation. Correct rejected records and upload a new file if they should be accepted. Historical source overlap/intent is a human data-provenance responsibility; identical operational and imported events are not inferred automatically.

## Evidence and boundaries

Automated backend/frontend reports, actual MySQL/API checks and actual browser screenshots/CSV are saved under docs/test-results. The browser fixture is synthetic test history, not a research dataset. Imports are bounded synchronous requests; no large-file/background import, returns/refunds, sales correction workflow, multi-store configuration, multi-currency conversion or representative performance benchmark is claimed. Sales history uses newest-first offset pagination; newly arriving sales can move page boundaries between requests. Final research preparation will decide how to handle sales affected by stockouts, missing dates and overlapping sources without inventing demand.
