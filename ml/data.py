"""Source audit and train-only cohort selection, independently sealed final labels."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ml.common import PROCESSED, RESEARCH, ROOT, now, protocol, read_json, sha256, write_json

REQUIRED = {'Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country'}


def clean_transactions(raw):
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f'Missing source columns: {sorted(missing)}')
    data = raw.copy()
    data['StockCode'] = data['StockCode'].astype('string').str.strip().str.upper()
    data['Invoice'] = data['Invoice'].astype('string').str.strip().str.upper()
    data['InvoiceDate'] = pd.to_datetime(data['InvoiceDate'], errors='coerce')
    for name in ['Quantity', 'Price']:
        data[name] = pd.to_numeric(data[name], errors='coerce')
    masks = {
        'invalid_date': data['InvoiceDate'].isna(),
        'invalid_sku_or_nonproduct_code': ~data['StockCode'].str.fullmatch(r'[0-9]{5}[A-Z]{0,2}', na=False),
        'missing_invoice': data['Invoice'].isna() | data['Invoice'].eq(''),
        'cancelled_invoice': data['Invoice'].str.startswith('C', na=False),
        'invalid_or_nonpositive_quantity': ~np.isfinite(data['Quantity']) | data['Quantity'].le(0),
        'invalid_or_nonpositive_price': ~np.isfinite(data['Price']) | data['Price'].le(0),
        'exact_duplicate': data.duplicated(subset=sorted(REQUIRED), keep='first'),
    }
    reason = pd.Series('', index=data.index, dtype='string')
    for name, mask in masks.items():
        reason.loc[mask & reason.eq('')] = name
    audit = {'raw_records': len(raw), 'missing_by_column': raw[list(sorted(REQUIRED))].isna().sum().astype(int).to_dict(),
             'overlapping_filter_counts': {name: int(mask.sum()) for name, mask in masks.items()},
             'exclusive_rejections': reason[reason.ne('')].value_counts().astype(int).to_dict(),
             'kept_records': int(reason.eq('').sum())}
    cleaned = data.loc[reason.eq(''), ['StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Country']].copy()
    cleaned['date'] = cleaned['InvoiceDate'].dt.normalize()
    # Customer/invoice identifiers never enter model or published derived records.
    return cleaned, audit


def choose_cohort(cleaned, config):
    cutoff = pd.Timestamp(config['train_end'])
    training = cleaned[cleaned['date'].between(config['train_start'], cutoff)].copy()
    daily = training.groupby(['StockCode', 'date']).Quantity.sum().reset_index()
    stats = daily.groupby('StockCode').agg(first_date=('date', 'min'), positive_days=('date', 'size'), total_units=('Quantity', 'sum'))
    stats['history_days'] = (cutoff - stats.first_date).dt.days + 1
    stats['zero_fraction'] = 1 - stats.positive_days / stats.history_days
    stats['reason'] = np.where(stats.history_days < config['minimum_history'], 'history_under_365_days',
                               np.where(stats.positive_days < config['minimum_positive_days'], 'positive_days_under_60', 'eligible'))
    eligible = stats[stats.reason.eq('eligible')].sort_index().copy()
    if len(eligible) < config['series_count']:
        raise ValueError('Too few eligible series; stop and revise protocol openly before training')
    # Ranking breaks tied zero fractions deterministically; qcut learns from training only.
    eligible['stratum'] = pd.qcut(eligible.zero_fraction.rank(method='first'), 3, labels=['low_zero', 'medium_zero', 'high_zero'])
    random = np.random.default_rng(config['seed'])
    chosen = []
    per_group = config['series_count'] // 3
    for group in ['low_zero', 'medium_zero', 'high_zero']:
        ids = eligible[eligible.stratum.eq(group)].index.to_numpy()
        chosen.extend(random.choice(ids, min(per_group, len(ids)), replace=False).tolist())
    if len(chosen) < config['series_count']:
        remainder = eligible.index.difference(chosen).to_numpy()
        chosen.extend(random.choice(remainder, config['series_count'] - len(chosen), replace=False).tolist())
    chosen = sorted(chosen)
    stats.loc[stats.reason.eq('eligible') & ~stats.index.isin(chosen), 'reason'] = 'eligible_not_selected_seeded_sample'
    stats.loc[stats.index.isin(chosen), 'reason'] = 'included'
    stats['stratum'] = eligible.stratum.astype('string').reindex(stats.index)
    return chosen, stats.reset_index(), training


def daily_series(cleaned, skus, end):
    selected = cleaned[cleaned.StockCode.isin(skus) & cleaned.date.le(pd.Timestamp(end))].copy()
    selected['price_units'] = selected.Price * selected.Quantity
    daily = selected.groupby(['StockCode', 'date']).agg(demand=('Quantity', 'sum'), price_units=('price_units', 'sum')).reset_index()
    daily['price'] = daily.price_units / daily.demand
    series = []
    for sku in skus:
        rows = daily[daily.StockCode.eq(sku)].set_index('date')
        if rows.empty:
            raise ValueError(f'No valid history for {sku}')
        frame = rows.reindex(pd.date_range(rows.index.min(), end, freq='D'))
        frame['demand'] = frame.demand.fillna(0)
        frame['price'] = frame.price.ffill()  # past-only; no backfill
        frame['sku'] = sku
        frame.index.name = 'date'
        series.append(frame[['sku', 'demand', 'price']].reset_index())
    return pd.concat(series, ignore_index=True).sort_values(['sku', 'date']).reset_index(drop=True)


def load_daily(name='development.csv'):
    return pd.read_csv(PROCESSED / name, dtype={'sku': 'string'}, parse_dates=['date'])


def prepare():
    if (RESEARCH / 'results/frozen-selection.json').exists():
        raise ValueError('Research selection already frozen; do not overwrite processed inputs')
    config = protocol()
    manifest = read_json(RESEARCH / 'dataset-manifest.json')
    workbook = next(record for record in manifest['files'] if record['path'].endswith('.xlsx'))
    path = ROOT / workbook['path']
    if sha256(path) != workbook['sha256']:
        raise ValueError('Raw workbook hash changed; stop for provenance review')
    print('Reading both actual UCI workbook sheets; this can take several minutes', flush=True)
    sheets = pd.read_excel(path, sheet_name=None, engine='openpyxl')
    if set(sheets) != {'Year 2009-2010', 'Year 2010-2011'}:
        raise ValueError('Unexpected worksheet version; stop for source review')
    raw = pd.concat(sheets.values(), ignore_index=True)
    cleaned, audit = clean_transactions(raw)
    if len(raw) != 1067371 or raw.InvoiceDate.min().date().isoformat() != '2009-12-01' or raw.InvoiceDate.max().date().isoformat() != '2011-12-09':
        raise ValueError('Actual source dimensions/dates differ from the documented snapshot; stop for review')
    skus, cohort, training = choose_cohort(cleaned, config)
    future_only = sorted(set(cleaned.StockCode) - set(cohort.StockCode))
    cohort = pd.concat([cohort, pd.DataFrame({'StockCode': future_only,
                       'reason': 'no_initial_training_history'})], ignore_index=True).sort_values('StockCode')
    # Target values are prepared mechanically, but the test file is opened only after freeze.
    full = daily_series(cleaned, skus, config['test_end'])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (RESEARCH / 'results').mkdir(parents=True, exist_ok=True)
    cohort.to_csv(RESEARCH / 'results/cohort.csv', index=False)
    full[full.date.le(config['validation_end'])].to_csv(PROCESSED / 'development.csv', index=False)
    full[full.date.gt(config['test_origin'])][['sku', 'date', 'demand']].to_csv(PROCESSED / 'sealed-test.csv', index=False)
    # Training-only raw fields used for dataset-level EDA, excluding customer identifiers.
    training.to_csv(PROCESSED / 'training-transactions.csv', index=False)
    metadata = {'created_at_utc': now(), 'source_sha256': workbook['sha256'], 'protocol_sha256': sha256(ROOT / 'ml/protocol.json'),
                'sheets': {name: {'rows': len(frame), 'columns': list(frame.columns)} for name, frame in sheets.items()},
                'source_dimensions': list(raw.shape), 'source_date_min': raw.InvoiceDate.min().isoformat(),
                'source_date_max': raw.InvoiceDate.max().isoformat(), 'source_unique_stock_codes': int(raw.StockCode.nunique()),
                'valid_product_skus_all_periods': int(cleaned.StockCode.nunique()),
                'products_no_initial_training_history': len(future_only),
                'source_countries': int(raw.Country.nunique()), 'stores': 'not provided', 'categories': 'not provided',
                'events_promotions': 'not provided', 'audit': audit, 'selected_skus': skus,
                'cohort_exclusions': cohort.reason.value_counts().astype(int).to_dict(),
                'training_transaction_rows': len(training), 'selected_daily_rows': len(full),
                'initial_train_daily_rows': int(full.date.le(config['train_end']).sum()),
                'validation_target_rows': int(full.date.between('2011-09-16', config['validation_end']).sum()),
                'test_target_rows': int(full.date.gt(config['test_origin']).sum()),
                'processed_files': {name: sha256(PROCESSED / name) for name in
                                    ['development.csv', 'sealed-test.csv', 'training-transactions.csv']},
                'cohort_sha256': sha256(RESEARCH / 'results/cohort.csv'),
                'preprocessing_policy': 'positive noncancelled valid product transactions, exact dedupe, daily sum, weighted price, past-only ffill; zero means no recorded purchase after first observation'}
    write_json(RESEARCH / 'results/preprocessing.json', metadata)
    print(f'Verified {len(raw):,} actual transactions; selected {len(skus)} SKUs; sealed {metadata["test_target_rows"]} final labels', flush=True)
    return metadata
