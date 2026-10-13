# Project defense notes

Use these as short oral answers, supported by the original proposal, frozen research results and actual test evidence. Explain uncertainty honestly. [System study guide](HOW_THE_SYSTEM_WORKS.md) gives files/tables/endpoints; [demo guide](DEMO_GUIDE.md) gives the walkthrough.

**What problem does the system solve?** Retail stock decisions need both accurate operational records and a reasoned view of expected demand. This prototype records sales/stock and combines historically evaluated demand forecasts with explicit replenishment assumptions for human review.

**Where is the AI/ML?** The independent Python research package compares mean/seasonal baselines, Random Forest and XGBoost on actual historical retail sales with chronological validation/testing. The application loads the frozen validation-selected model and persists its forecasts; web requests never train it.

**Why is this more than ordinary inventory management?** It includes genuine comparable forecasting experiments and model evaluation, then links versioned predicted demand to explainable stock-risk and reorder snapshots. Accurate inventory management remains necessary for those decisions to be meaningful.

**Why UCI Online Retail II?** It supplies openly licensed, actual product/date/quantity/price transactions matching a single-retailer sales workflow. Source/licensing and quality checks are documented. It is UK online gift/wholesale data, not Kenyan store data; no missing promotions/stores were invented.

**Why did a simple baseline beat the tree models?** Validation evidence favored the last28day mean on this bounded60-SKUstudy. Intermittency, bulk purchases, limited predictors and changing regimes can limit complex models; the experiment does not establish one causal explanation or universal baseline superiority.

**Why keep mean_28 if seasonal naive was better on final test?** The winner was frozen using validation MAE before final labels were opened. Choosing again from final scores would use the test for selection and bias its role as unseen evaluation. We report seasonal naive's better final results honestly while preserving the selected model.

**What is data leakage?** It is using information unavailable at prediction time, such as future actual demand or future prices, to train, construct features or select models. It makes results unrealistically favorable.

**Why chronological splitting?** A retailer forecasts future dates from earlier observations. Training/validation/test must follow that direction. Initial training ends2011-09-15; expanding validation uses two28day windows; final origin2011-11-10predicts11-11through12-08. Final labels did not select features, SKUs, parameters or winner.

**What are MAE and RMSE?** MAE averages absolute prediction errors in purchased units per SKU-day. RMSE is the square root of average squared errors and penalizes large misses more. Selectedmean_28final MAE5.335034/RMSE17.944564 uses1680targets. These pooled averages can hide weak products.

**Why not MAPE?** 1169of1680final actuals are zero. Full-sample percentage errors are undefined there; adding epsilon or silently using only positive days would change interpretation. MAE/RMSE are retained and the omission is explicit.

**How does replenishment work?** Position=on-hand+confirmed incoming−allocated. Target=forecast demand across lead time+safety stock. Suggested quantity=max(0,target−position). Every component and assumption is saved with date/model/stock versions. It is a deterministic review aid, not proof of an optimal policy.

**What is safety stock?** A configurable buffer added to expected lead-time demand. This prototype uses a manager-supplied nonnegative value; it does not claim a statistically optimized service level.

**How is overstock detected?** Position strictly above target×configured multiplier is OVERSTOCK. The multiplier exceeds1. High availability yields zero suggested reorder, with the original explanation retained.

**Can the system buy stock automatically?** No. It produces human-reviewed recommendations and contains no purchase execution. Supplier-network optimization is also outside scope.

**How do you avoid overselling?** An operational sale locks product/current inventory, validates the current version and unallocated physical quantity, and commits sale, stock and audit together. Failure rolls all back. Actual same-stock concurrent requests returned one201and one409, with one decrement. Bounded deadlock retry does not waive these rules.

**Why does historical import not reduce stock?** Those observations describe earlier sales whose physical effect is already accounted for. The separate preview/confirmation workflow inserts history only, retains rejected rows and prevents duplicate imports. Operational sales consume stock now, even when backdated.

**Why explicit SKU mapping?** An arbitrary application SKU is not automatically a UCIStockCode. A manager must acknowledge the historical UK context and map a supported individual-count series with a reason. This prevents fabricated forecasts; it does not establish real product equivalence or transferability.

**Why are current forecasts unavailable?** Compatible frozen history ends2011-11-10. Changing dates to today would misrepresent old data. The application intentionally rejects stale/current requests and shows UNASSESSED. Genuine current forecasting needs recent compatible history and separate approved evaluation.

**Can results generalize to Kenya?** No such accuracy has been established. The research is UK2009–2011online gift/wholesale data; Kenyan assortment, customers, calendars and supply conditions differ. Appropriate local data and external validation are required.

**What did software testing establish?** HistoricalPhase6executed251automated tests and23of24proposal cases passed. ActualMySQL/API and full technical browser workflow verified persistence, permissions, rollback/import rules and snapshot arithmetic. Publication reruns are separately recorded. Passing software tests does not prove commercial effectiveness or representative-user usefulness.

**Was usability evaluated with participants?** No. There are zero participants and zero responses. The consent/tasks/five-point questionnaire are prepared; TC24remains pending approved external participants. Technical automation is not participant feedback.

**What are the compatibility/security limits?** Edge had a bounded observed workflow; Chrome was partial and Firefox tool-policy blocked. New follow-up results are documented, never inferred. Bounded security checks are not penetration testing. Dependency advisories were reviewed and compatible fixes regression tested; any residual research-environment advisories remain documented rather than changing frozen research.

**What are other limitations?** One historical retailer,60training-selectedSKUs, one final28day window, variable per-series errors, zeros/extremes and absent availability/promotions/store information. Incoming has noETA; safety/overstock rules are deterministic; fractional recommendations lack pack/cost optimization. Load tests are modest localhost measurements, not enterprise certification. No measured commercial benefit is claimed.

**What would you improve?** With approval: recent retailer data, Kenyan external validation, more rolling horizons, uncertainty/intermittent-demand comparisons, ETA/service-level rules, returns/corrections, accessibility/usability, realistic mixed load and deployment hardening. Preserve this sealed experiment rather than retuning on its final labels.

**How should I describe completion?** The software and recorded academic evidence can be complete for submission while real participant evaluation and other stated external limits remain pending. Say what was tested, cite actual reports and explain the scope. Never invent participants, current accuracy, security certification or commercial effectiveness.
