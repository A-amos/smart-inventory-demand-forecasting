# Chapter 5 — evidence-based findings and conclusions

## 5.1 Introduction

This draft relates actual historical research and prototype evaluation to the four specific proposal objectives. No field respondents, current Kenyan forecasts, commercial benefits or security/compatibility certification are inferred from technical tests. See [objective matrix](../OBJECTIVE_TRACEABILITY.md) and [Chapter 4 evidence](CHAPTER_4_EVIDENCE.md).

Publication follow-up is recorded separately in [PUBLICATION_REVIEW.md](../PUBLICATION_REVIEW.md). It documents compatible application security updates and packaging of the small frozen runtime files without changing the original Phase4metrics or Phase6findings below. The original research reproduction lock retains its recorded advisories. Participant evaluation remains pending.

## 5.2 Summary of Findings

### 5.2.1 Objective 1 Findings

Objective 1: analyzed a training-only sample of 60 SKUs from actual UCI Online Retail II UK sales. Training contains 37,753 SKU-days and 26,891 zero days (71.23%). Median lag-7 correlation is 0.046; median price-demand association is −0.069. Tables/plots show intermittency, weekday differences and extreme purchases. These descriptive associations do not establish causal demand factors. No inventory, promotion, store or Kenyan observations exist.

### 5.2.2 Objective 2 Findings

Objective 2: compared two baselines and selected RF/XGBoost configurations chronologically. Validation MAE selected mean_28 (4.753635), frozen before final labels were opened. On 1,680 final targets its MAE is 5.335034 and RMSE is 17.944564. Seasonal naive performed better on the final window: MAE 4.939881 and RMSE 17.008524. The selected model was not changed using test results. MAPE is omitted for zero/intermittent data; weak series remain in the results. Phase 6 read-only verification matches frozen metrics and 31 protected hashes; no retraining or rewriting occurred.

### 5.2.3 Objective 3 Findings

Objective 3: implemented deterministic stock-risk/reorder rules using current stock, confirmed incoming, allocations, lead time, safety stock and an excess multiplier. The actual synthetic browser scenario has position 18, target 87.571428571 and suggested reorder 69.571428571, classified REPLENISH. A separate high-stock scenario produces OVERSTOCK and zero reorder. Immutable history preserves original conditions. Operational sales commit stock, sale and audit atomically; historical imports never change current stock. Human review is retained. No procurement execution, global optimality or measured stockout reduction is claimed.

### 5.2.4 Objective 4 Findings

Objective 4: executed 251 automated tests (163 backend, 59 ML, 29 frontend), with zero failures/skips and one upstream warning. Build, Compose, MySQL, live API and a full browser workflow passed. **23 of 24 proposal-wide test cases passed; TC24 remains pending external participant evaluation.** The final 440-request localhost performance run had zero errors after a measured deadlock defect was fixed; concurrent inference p95 is about 16.824 seconds. Bounded security checks worked, but dependency advisories remain unresolved. Edge smoke testing passed; Chrome is partial and Firefox was policy-blocked. Representative-user effectiveness and field requirements validation remain unmeasured.

## 5.3 Conclusion

The prototype combines genuine historical forecasting comparison with a working web inventory application and auditable, explainable decisions. Tests support the observed contracts, transaction integrity and scenario arithmetic; they do not establish commercial effectiveness. A simple mean baseline won validation, showing that greater model complexity did not guarantee better accuracy in this study. The historical UK held-out window provides valid historical metrics, not current 2026 or Kenyan accuracy. Unsupported/stale current requests are intentionally rejected, and UNASSESSED does not mean safe. Recent compatible history and approved evaluation are required for genuine current forecasts. Participant usability remains pending; the project is not claimed fully evaluated.

## 5.4 Recommendations

Use the local acknowledged historical demonstration until recent compatible data and retailer validation are available. Obtain supervisor/outlet permissions and voluntary participants for the usability instrument and requirements elicitation. Complete Chrome/Firefox checks through a supported automation surface or supervised manual protocol. Review dependency advisories and compatible framework upgrades before remote exposure; rerun functional/security/build checks while preserving research fingerprints. Retain human review of assumptions, quantity and date/model/stock versions.

## 5.5 Limitations

The UK online gift/wholesale dataset covers 2009–2011, with 60 selected SKUs, two validation origins and one final 28-day horizon. It cannot establish current Kenyan accuracy, causal features or unmet demand. Model quality varies across series; extremes and zeros affect errors. This undergraduate prototype uses synthetic decision stock, fixed safety stock and deterministic incoming assumptions, with fractional raw reorder quantities. It excludes automatic procurement and supplier-network optimization. No commercial capacity, cost improvement or stockout reduction is certified. There are no participant responses; compatibility is partial; dependency advisories and one warning remain. Trusted ignored model/data files are required for reproduction; a source-only checkout cannot assume their presence. See [full limitations](../SYSTEM_LIMITATIONS.md).

## 5.6 Areas for Future Work

After separate approval, future work may collect recent consenting retailer data and inventory availability, evaluate Kenyan transferability, add rolling origins/horizons and uncertainty analysis, and compare intermittent-demand methods without tuning against this sealed final window. Other opportunities include ETA-aware incoming, service-level safety/cost/pack rules, returns/corrections, realistic mixed-load testing, performance profiling, participant usability, accessibility evaluation and deployment/dependency hardening. None is implemented or claimed achieved in Phase 6. Automatic purchase execution remains out of scope.
