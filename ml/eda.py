"""Descriptive research on initial training only; final labels never opened."""
import os

import numpy as np
import pandas as pd

from ml.common import PROCESSED, RESEARCH, ROOT, now, protocol, read_json, write_json
from ml.data import load_daily

os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def finish(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def run_eda():
    config = protocol()
    metadata = read_json(RESEARCH / 'results/preprocessing.json')
    data = load_daily()
    data = data[data.date.le(config['train_end'])].copy()
    if data.date.max() > pd.Timestamp(config['train_end']):
        raise ValueError('EDA must not access validation or final test targets')
    folder = RESEARCH / 'eda'
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    outlier_frames = []
    for sku, rows in data.groupby('sku'):
        positive = rows[rows.demand.gt(0)].demand
        q1, q3 = rows.demand.quantile([0.25, 0.75])
        threshold = float(q3 + 3 * (q3 - q1))
        correlation = rows[['price', 'demand']].corr(method='spearman').iloc[0, 1] if rows.price.nunique() > 1 else np.nan
        records.append({'sku': sku, 'days': len(rows), 'positive_days': len(positive),
                        'zero_fraction': float(rows.demand.eq(0).mean()), 'mean_units': float(rows.demand.mean()),
                        'max_units': float(rows.demand.max()), 'median_positive_units': float(positive.median()),
                        'average_demand_interval': len(rows) / len(positive),
                        'positive_demand_cv_squared': float((positive.std(ddof=0) / positive.mean()) ** 2),
                        'lag1_correlation': float(rows.demand.autocorr(1)), 'lag7_correlation': float(rows.demand.autocorr(7)),
                        'distinct_observed_or_carried_prices': int(rows.price.nunique()),
                        'price_min_gbp': float(rows.price.min()), 'price_max_gbp': float(rows.price.max()),
                        'price_demand_spearman': float(correlation) if np.isfinite(correlation) else None,
                        'upper_3iqr_flag_count': int(rows.demand.gt(threshold).sum())})
        outlier_frames.append(rows[rows.demand.gt(threshold)].assign(flag_threshold=threshold))
    stats = pd.DataFrame(records)
    stats.to_csv(folder / 'sku-summary.csv', index=False)
    pd.concat(outlier_frames, ignore_index=True).sort_values('demand', ascending=False).to_csv(folder / 'flagged-daily-sales.csv', index=False)
    # A common panel avoids changing SKU counts when interpreting temporal totals.
    common_start = data.groupby('sku').date.min().max()
    common = data[data.date.ge(common_start)].copy()
    weekday = common.assign(weekday=common.date.dt.dayofweek).groupby('weekday').agg(
        mean_units_per_sku_day=('demand', 'mean'), observations=('demand', 'size')).reset_index()
    weekday.to_csv(folder / 'weekday.csv', index=False)
    monthly = common.assign(month=common.date.dt.to_period('M').astype(str)).groupby('month').agg(
        mean_units_per_sku_day=('demand', 'mean'), total_units=('demand', 'sum'), observations=('demand', 'size')).reset_index()
    monthly.to_csv(folder / 'monthly.csv', index=False)
    daily = common.groupby('date').demand.sum()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(daily.index, daily, color='#a8b7c9', linewidth=0.7, label='Actual daily total')
    ax.plot(daily.index, daily.rolling(28, min_periods=28).mean(), color='#087f8c', label='Trailing 28-day mean')
    ax.set(title='Initial training: observed daily sales in a constant 60-SKU panel', ylabel='Purchased units/day', xlabel='Date')
    ax.legend(); finish(fig, folder / 'training-trend.png')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], weekday.mean_units_per_sku_day, color='#087f8c')
    axes[0].set(title='Observed weekday effect', ylabel='Mean units / SKU-day')
    axes[1].hist(stats.zero_fraction, bins=12, color='#e69f00')
    axes[1].set(title='Selected training series intermittency', xlabel='Fraction of days with zero recorded purchases', ylabel='Number of SKUs')
    finish(fig, folder / 'weekday-and-zeros.png')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(monthly.month, monthly.mean_units_per_sku_day, color='#087f8c')
    ax.tick_params(axis='x', rotation=60)
    ax.set(title='Training monthly means (partial months retained and counted)', ylabel='Units / SKU-day', xlabel='Month')
    finish(fig, folder / 'monthly-seasonality.png')
    cohort = pd.read_csv(RESEARCH / 'results/cohort.csv', dtype={'StockCode': 'string'})
    representatives = []
    for group in ['low_zero', 'medium_zero', 'high_zero']:
        representatives.append(cohort[cohort.reason.eq('included') & cohort.stratum.eq(group)].sort_values('StockCode').iloc[0].StockCode)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, sku in zip(axes, representatives, strict=True):
        rows = data[data.sku.eq(sku)]
        ax.plot(rows.date, rows.demand, color='#087f8c', linewidth=0.9)
        ax.set(title=f'SKU {sku}: training-selected representative', ylabel='Units/day')
    axes[-1].set_xlabel('Date'); finish(fig, folder / 'representative-training-skus.png')
    zero = int(data.demand.eq(0).sum())
    summary = {'created_at_utc': now(), 'scope': 'initial training only; no validation/test demand EDA',
               'period_start': data.date.min().date().isoformat(), 'period_end': data.date.max().date().isoformat(),
               'selected_skus': len(stats), 'daily_observations': len(data), 'zero_observations': zero,
               'zero_fraction': zero / len(data), 'median_sku_zero_fraction': float(stats.zero_fraction.median()),
               'median_average_demand_interval': float(stats.average_demand_interval.median()),
               'median_lag7_correlation': float(stats.lag7_correlation.median()),
               'skus_with_price_variation': int(stats.distinct_observed_or_carried_prices.gt(1).sum()),
               'median_price_demand_spearman': float(stats.price_demand_spearman.median()),
               'max_daily_purchase_quantity': float(data.demand.max()),
               'statistical_outlier_flags_retained': int(stats.upper_3iqr_flag_count.sum()),
               'common_panel_start': common_start.date().isoformat(), 'common_panel_days': int(common.date.nunique()),
               'weekday_means': weekday.mean_units_per_sku_day.to_list(), 'representative_skus': representatives,
               'source_missing_counts': metadata['audit']['missing_by_column'],
               'categories_stores_events': 'Not supplied; no invented category/store/promotion labels',
               'interpretation_limits': 'Descriptive associations, not causal effects. Zero means no recorded purchase; stockout/nonavailability cannot be distinguished. Gift/wholesale/UK online case study; no Kenyan performance inference.'}
    write_json(folder / 'summary.json', summary)
    print(f'EDA complete: {len(data)} initial-training SKU-days; {zero} observed zeros; no held-out label analysis', flush=True)
    return summary
