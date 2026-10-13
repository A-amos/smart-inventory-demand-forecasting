# Proposal analysis and requirements

Primary source: `Smart_Inventory_Consolidated_Five_Chapter_Proposal.docx`, read in full on 2026-09-30, including all tables, appendices and seven embedded diagrams. `proposal-extracted.txt` is a reading aid; the original DOCX remains authoritative. The initial directory contained that document only; no source code, database, tests, Git repository or AGENTS.md was found.

## Research traceability

| Specific objective, section 1.3.2 | Required evidence | Implementation phase |
| --- | --- | --- |
| 1. Analyze historical retail sales data and identify patterns and factors associated with product demand. | Dataset provenance, quality audit, exploratory plots, intermittent/zero-demand analysis, documented features | 4 |
| 2. Evaluate selected machine-learning models for forecasting future retail product demand. | Comparable baseline/ML experiments, chronological partitions, actual MAE/RMSE, qualified MAPE, versions and parameters | 4 |
| 3. Develop an inventory decision approach that uses forecast demand to identify stockout and overstock risks and recommend replenishment quantities. | Explainable inventory rule, assumption snapshots and scenario/integration tests | 5 |
| 4. Evaluate the forecasting accuracy and decision-support effectiveness of the proposed system. | Holdout results, executed software cases, response measurements, compatibility and actual usability feedback | 6 |

## Functional requirements

| ID | Proposal source | Acceptance condition |
| --- | --- | --- |
| FR1 | 3.8, authentication; 4.2.1 | Authorized sign-in; generic failure; protected functions reject anonymous/expired/revoked sessions; sign-out revokes server session; passwords hashed |
| FR2 | 3.8, product management; user category requirement | Add, view, update unique SKU, name, category, unit and replenishment parameters; reject invalid references and duplicates |
| FR3 | 3.8, sales management | Record dated sales with positive quantities and valid product; import validated historical files and report row counts/errors |
| FR4 | 3.8, inventory monitoring | View/update on-hand and confirmed incoming quantities; store allocations where available; operational sale and stock decrement commit atomically |
| FR5 | 3.8, forecasting | Forecast product and horizon with origin, model version and sufficient-history validation; handle unavailable model safely |
| FR6 | 3.8, risk analysis | Compare forecast and net availability; disclose stockout and configured overstock thresholds |
| FR7 | 3.8, replenishment | Nonnegative quantity, lead time, safety stock and availability shown; explicit pack rounding if supported; human purchasing authority retained |
| FR8 | 3.8, dashboard/reports | Interactive historical sales, forecasts, stock and risk views; updated after transactions; truthful empty and failure states |
| FR9 | 3.8, model evaluation | Reproducible dataset/model/split/metric records and comparison view |

Authentication applies to every business endpoint; only health and sign-in are public. Manager/researcher authorization will distinguish operational writes from experiment viewing. Historical research imports must not subtract old sales from today's on-hand inventory. Live sales must not make physical unallocated stock negative. Incoming stock is confirmed inventory expected within the relevant decision horizon; uncertain or late arrivals must be excluded or disclosed. Recommendations require matching product, model origin and horizon; stale forecasts cannot silently be reused.

## Non-functional requirements

| ID | Source / acceptance evidence |
| --- | --- |
| NFR1 usability | 3.9: familiar retail labels, readable forms, units, empty/error states; actual representative task completion and feedback |
| NFR2 performance | 3.9/4.5: record normal/concurrent response times, defined workload and machine; proposal gives no numerical SLA. Phase 6 benchmarks describe observed behavior without inventing a latency pass target; see test-results/PERFORMANCE.md |
| NFR3 security | 3.9: authentication, authorization, password hashing, parameterized SQL, safe text rendering, validation; documented checks without claiming a penetration audit |
| NFR4 reliability | 3.9: FK/unique/check constraints, transactional sales/stock writes, rollback, deterministic import rules, safe database/model failure |
| NFR5 maintainability | 3.9/3.10: modular tiers, migrations, repeatable setup, versioned API, independently tested forecasting and decisions |
| NFR6 compatibility | 3.9/4.5: test selected mainstream desktop browsers; retain actual observations |
| NFR7 explainability | 3.9: product, period, forecast, available stock, lead time, safety stock, threshold and rounding assumptions visible |
| Research reproducibility | 3.6, Appendix V: seeded experiments, immutable input hashes, environment lock, train/validation/test date ranges, saved predictions and real metrics |
| Ethics and resource bounds | 3.4/3.5: manageable subsets on approximately 8 GB RAM; approved voluntary fieldwork; no sensitive customer/payment data |

## Confirmations and boundaries

The user fixes React/Vite/Tailwind/Recharts, Python/FastAPI/SQLAlchemy/Pydantic, MySQL and Docker; these refine the proposal's intentionally open stack. No architectural departure is necessary. MySQL 8.4 is configured; SQLite is only a fast isolated test adapter and does not establish MySQL compatibility.

Appendix VI leaves dataset, horizon, supervisor identity, outlets, instruments and achieved sample size unconfirmed. M5 is discussed in 2.2.2 as a candidate, not a confirmed dataset. Obtain source/license and dataset/horizon confirmation before substantive experimentation. Obtain supervisor/outlet approvals before fieldwork. Do not request or create external accounts without user approval.

Scope excludes automatic purchases, ERP, supplier-network optimization, mandatory deep learning, live commercial deployment and claims of global optimality or Kenyan generalization from international data. Survey information informs requirements, never serves as forecasting training records. Table 4.1 explicitly contains TC01–TC24 despite nearby prose saying “at least twenty”; the user requires at least 24 meaningful cases, so use all 24 and supplement them.
