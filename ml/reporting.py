"""Render factual research reports from preserved experiment records, never tune."""
import pandas as pd

from ml.common import RESEARCH, read_json, write_json
from ml.eda import finish, plt


def reports():
    source = read_json(RESEARCH / 'results/preprocessing.json')
    eda = read_json(RESEARCH / 'eda/summary.json')
    validation = read_json(RESEARCH / 'results/validation.json')
    frozen = read_json(RESEARCH / 'results/frozen-selection.json')
    final = read_json(RESEARCH / 'results/final-test.json')
    registry = read_json(RESEARCH / 'results/model-registry.json')
    by_sku = pd.read_csv(RESEARCH / 'results/final-test-by-sku.csv', dtype={'sku': 'string'})
    selected = final['selected_by_validation_only']
    worst = by_sku[by_sku.model.eq(selected)].sort_values(['mae', 'rmse', 'sku'], ascending=[False, False, True]).head(10)
    worst.to_csv(RESEARCH / 'results/selected-worst-10-skus.csv', index=False)
    folder = RESEARCH / 'results'
    names = list(frozen['finalists'])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, metric in zip(axes, ['mae', 'rmse'], strict=True):
        positions = range(len(names))
        ax.bar([n - .18 for n in positions], [validation['scores'][name][metric] for name in names], .36,
               label='Validation (selection)', color='#087f8c')
        ax.bar([n + .18 for n in positions], [final['scores'][name][metric] for name in names], .36,
               label='Final test (frozen)', color='#e69f00')
        ax.set_xticks(list(positions), names, rotation=25, ha='right')
        ax.set(title=metric.upper(), ylabel='Error in units / SKU-day')
        ax.legend(fontsize=8)
    fig.suptitle('Identical observations within each split; final scores do not change selection')
    finish(fig, folder / 'model-comparison.png')
    predictions = pd.read_csv(folder / 'final-test-predictions.csv', dtype={'sku': 'string'}, parse_dates=['date'])
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, sku in zip(axes, eda['representative_skus'], strict=True):
        rows = predictions[predictions.sku.eq(sku)]
        truth = rows[rows.model.eq(selected)].sort_values('date')
        ax.plot(truth.date, truth.actual, color='#233449', label='Actual', linewidth=1.6)
        for name in names:
            forecast = rows[rows.model.eq(name)].sort_values('date')
            ax.plot(forecast.date, forecast.prediction, label=name, linewidth=.9, alpha=.85)
        ax.set(title=f'SKU {sku} (representative chosen from training)', ylabel='Units/day')
    axes[0].legend(ncol=3, fontsize=8)
    axes[-1].set_xlabel('Final test date')
    finish(fig, folder / 'representative-final-forecasts.png')
    e = f'''# Initial-training exploratory analysis

Executed analysis uses **{eda['daily_observations']:,} daily observations across 60 training-selected SKUs**, {eda['period_start']} to {eda['period_end']}. Validation and final-test targets are excluded. Source workbook structure and rejection counts are audited across the export for provenance; behavioral analysis is training-only.

The workbook contains {source['source_dimensions'][0]:,} rows, 8 columns, {source['source_unique_stock_codes']:,} distinct raw StockCode values and {source['source_countries']} destination countries. These include non-product codes. There is one UK-based online retailer; no store or category identifier and no promotion/event table is provided. Customer countries are destinations, not stores.

Missing source descriptions: {source['audit']['missing_by_column']['Description']:,}; missing Customer IDs: {source['audit']['missing_by_column']['Customer ID']:,}. Neither field enters forecasting. Core date, price, quantity, invoice and stock-code fields have no nulls, although invalid values/non-product codes and cancellations require filtering. Overlapping masks and exclusive rejection counts are in results/preprocessing.json; {source['audit']['kept_records']:,} records remain after documented filtering. Exact duplicate candidates: {source['audit']['overlapping_filter_counts']['exact_duplicate']:,}; exclusive duplicate rejections: {source['audit']['exclusive_rejections']['exact_duplicate']:,}. Repeated identical export rows are assumed duplicates; indistinguishable legitimate repeated invoice lines remain a data limitation.

Initial-training cohort decisions: {source['cohort_exclusions']}. Eligibility concerns products with initial-training history only; future-only/new products are outside the fixed vocabulary. The sample is 20 SKUs from each zero-fraction stratum. Exact IDs/statistics are in results/cohort.csv; sampling is not based on validation/test error.

Zero-recorded-purchase days: **{eda['zero_observations']:,} ({eda['zero_fraction']:.2%})**. Median per-SKU zero fraction: {eda['median_sku_zero_fraction']:.2%}; median average demand interval: {eda['median_average_demand_interval']:.2f} days. No recorded transaction means zero under the complete-export assumption, not proof that demand is absent. Unobserved availability/stockouts cannot be resolved. Positive-demand CV squared and per-SKU statistics are saved in eda/sku-summary.csv.

The constant 60-SKU panel starts {eda['common_panel_start']} and contains {eda['common_panel_days']} calendar days. Weekday mean units per SKU-day (Mon–Sun): {', '.join(f'{value:.2f}' for value in eda['weekday_means'])}. Saturday is particularly sparse in this export; business operating patterns can explain weekday associations. Median lag-7 autocorrelation is {eda['median_lag7_correlation']:.3f}. Monthly means/trailing daily totals show changing volumes and seasonal gift-retail patterns, but fewer than two full annual cycles, partial months and wholesale orders prevent strong causal or stable annual-seasonality claims.

All {eda['skus_with_price_variation']} selected SKUs show variation in observed or carried prices; median price-demand Spearman association is {eda['median_price_demand_spearman']:.3f}. Quantity-weighted daily transaction prices reflect customer/wholesale mix, not a known advertised price. These associations do not establish a price effect. Future prices are prohibited; forecasting carries the last known price.

Upper three-IQR daily flags: {eda['statistical_outlier_flags_retained']:,}; largest selected training daily purchase: {eda['max_daily_purchase_quantity']:,.0f} units. All flagged quantities are retained, since high purchases may be legitimate wholesale orders. Flagged rows are saved for review; they are not removed to improve scores.

![Training trend](eda/training-trend.png)
![Weekday and intermittency](eda/weekday-and-zeros.png)
![Monthly descriptive pattern](eda/monthly-seasonality.png)
![Fixed training representatives](eda/representative-training-skus.png)

EDA supports prior demand/calendar and past price features, weekly and mean baselines, and tree models for nonlinear associations. It does not guarantee their superiority; selection remains an empirical validation comparison. No Kenyan retail performance is inferred.
'''
    (RESEARCH / 'EDA.md').write_text(e, encoding='utf-8')
    table = '| Candidate | Validation MAE | Validation RMSE | Final MAE | Final RMSE | Final observations |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
    for name in validation['ranking']:
        v = validation['scores'][name]
        t = final['scores'].get(name)
        table += f"| {name} | {v['mae']:.6f} | {v['rmse']:.6f} | {format(t['mae'], '.6f') if t else 'Not a frozen finalist'} | {format(t['rmse'], '.6f') if t else '—'} | {t['observations'] if t else '—'} |\n"
    score = final['scores'][selected]
    baseline = final['scores']['seasonal_naive']
    improvement = (baseline['mae'] - score['mae']) / baseline['mae'] * 100
    worst_table = '| SKU | MAE | RMSE | Zero days / 28 |\n| --- | ---: | ---: | ---: |\n'
    for row in worst.itertuples():
        worst_table += f'| {row.sku} | {row.mae:.4f} | {row.rmse:.4f} | {row.zero_actual_count} |\n'
    content = f'''# Executed forecasting comparison

The validation-only winner is **{selected}**, frozen at {frozen['frozen_at_utc']}; the final test was accessed at {read_json(folder / 'final-test-access.json')['opened_at_utc']}. Model selection used pooled validation MAE, then RMSE/name, including baselines. It did not use final-test rankings. The best configuration from each tree family and both baselines were frozen before the final test. The other two configurations were not run against final labels.

{table}
Every validation candidate forecasts the same 3,360 SKU/origin/day targets (60 SKUs × two 28-day windows). Every final candidate forecasts the same 1,680 targets (60 × 28), 2011-11-11 through 2011-12-08. Both dates and actual quantities are checked across models; no missing observations are silently removed. MAE/RMSE are pooled equally per SKU-day and measured in purchased units, not percentages. MAPE is omitted for zero/intermittent sales. Final-test zero days: {score['zero_actual_count']} / {score['observations']} ({score['zero_actual_count'] / score['observations']:.2%}).

The validation-selected model's final MAE changes by {improvement:.2f}% relative to seasonal naive (positive denotes lower error). Raw predictions, per-SKU metrics, exact effective fitted parameters, training/inference timings, seeds, dependency versions and data/code hashes are preserved in results/. The selected model remains {selected} even if another model has lower final error. No confidence intervals or statistical significance are claimed from this one final horizon. Validation/test seasonal regimes differ, and pooled means can hide weak SKUs.

Worst ten selected-model products by final MAE (all retained):

{worst_table}
Figures show the frozen finalist errors and the three representative SKUs selected before training from the zero-fraction strata. Full per-SKU performance is in final-test-by-sku.csv. Investigating these failures is descriptive; it does not trigger test-driven retuning. Bulk purchases, intermittent zeros, missing inventory availability and fixed-origin recursive error can all limit observed-sales prediction. The 60-SKU UK gift-retail case study is not a universal or Kenyan-performance estimate.

![Comparison](results/model-comparison.png)
![Representative forecasts](results/representative-final-forecasts.png)
'''
    (RESEARCH / 'MODEL_COMPARISON.md').write_text(content, encoding='utf-8')
    description = f'''# Final frozen model and application boundary

Selected candidate: **{selected}**; model version retail-demand-v1; run ID **{registry['model_id']}**. This candidate won the predeclared validation rule. Final test MAE **{score['mae']:.6f}**, RMSE **{score['rmse']:.6f}**, measured in units / SKU-day on 1,680 targets. Final labels were not used to choose the candidate, hyperparameters or cohort. Configuration: `{registry['parameters']}`. Refit cutoff: {registry['trained_through']}.

Selected artifact: `{registry['artifact_path']}` (SHA-256 `{registry['artifact_sha256']}`). Its bundle contains feature specification, preprocessing, effective model metadata and evaluation metadata. The external registry, predictions and frozen selection are under docs/research/results. Raw data, processed data and binary model artifacts are Git-ignored but exist locally; download/reproduction commands are in ml/README.md. The repository has no commit yet; SHA-256 fingerprints of research Python sources/protocol/requirements are frozen instead of inventing a Git revision. Timings and serialized file bytes may vary across hardware; prediction reproducibility is checked with absolute tolerance 1e-10 in the recorded environment.

All models operate at daily retailer-SKU granularity. Forecasts support 1–28 days and require at least 365 contiguous prior observations ending at the origin for every fixed-vocabulary SKU. Origin must be on/after the model training cutoff. Unknown SKU, missing/gapped history, invalid horizon and incompatible artifact/feature/library versions fail explicitly. Historical data is required at each requested origin; this is not a general cold-start model.

Features use shifted demand lags/rolling statistics, known calendar values, lagged quantity-weighted GBP prices and fixed SKU one-hot vocabulary. Tree models recursively feed only their own predictions through the fixed horizon; future prices remain held at the last known origin observation. No future sales, promotions or price changes are read. Predictions are finite/nonnegative and remain fractional estimates; rounding stock decisions belongs to Phase 5. If a baseline wins, its registered formula rather than invented tree importance is used. Training tree importance, when present, is descriptive split importance, not a causal explanation.

The callable boundary is `ml.experiment.forecast_contract`, exposed by `python -m ml.cli infer --sku <known SKU> --origin 2011-11-10 --horizon 28`. It loads the hash/version-checked selected artifact, then returns forecast-v1 JSON with source namespace, SKU, origin, daily horizon/dates, predicted quantities, model ID/version, trained-through cutoff and timezone-aware creation timestamp. JSON Schema and a successfully generated example are in results/forecast-schema.json and example-forecast.json. No forecasting HTTP endpoint or forecast persistence schema was introduced in Phase 4. Actual application endpoint inference is therefore outside this increment; the genuine saved artifact and Python/CLI contract were executed and verified.

Research StockCodes are namespaced `uci-online-retail-ii` and are not automatically mapped into operational MySQL products. A later integration must explicitly validate mappings/history, apply Kenyan context validation, persist forecasts if required and use then-current inventory/lead time/safety stock. Phase 4 does not calculate risks, recommendations, purchase orders or dashboards.

Model files use joblib/pickle and must be trusted local artifacts; a hash does not make an attacker-controlled artifact/registry safe. Loader rejects paths outside ml/artifacts and incompatible versions. Never deserialize a user upload. Forecasts estimate recorded gross sales, not uncensored demand; no availability, store/category/promotions or inventory labels are provided. Negative/cancelled sales are excluded, legitimate extremes retained. No unseen-SKU, cold-start, changed-assortment, multi-store or Kenyan generalization claim is made.
'''
    (RESEARCH / 'FINAL_MODEL.md').write_text(description, encoding='utf-8')
    write_json(folder / 'report-generation.json', {'selected': selected, 'documents': ['EDA.md', 'MODEL_COMPARISON.md', 'FINAL_MODEL.md'],
               'figures': ['model-comparison.png', 'representative-final-forecasts.png'], 'derived_from_preserved_results': True})
    print('Actual EDA, model comparison, failure analysis and final-model reports rendered', flush=True)


if __name__ == '__main__':
    reports()
