"""Single feature specification shared by training and recursive inference."""
import numpy as np
import pandas as pd

FEATURE_VERSION = 'features-v1'
LAGS = (1, 7, 14, 28)
WINDOWS = (7, 28)
NUMERIC_FEATURES = [*(f'lag_{n}' for n in LAGS), *(f'mean_{n}' for n in WINDOWS),
                    *(f'std_{n}' for n in WINDOWS), 'weekday', 'month', 'year_sin', 'year_cos',
                    'weekend', 'price_lag1', 'price_change7']


def validate_daily(data):
    required = {'sku', 'date', 'demand', 'price'}
    if not required <= set(data.columns) or data.empty:
        raise ValueError('Nonempty daily sku/date/demand/price data required')
    if data[['sku', 'date', 'demand', 'price']].isna().any().any():
        raise ValueError('Missing daily values must be resolved explicitly; absent dates are not observed zeros')
    if data.duplicated(['sku', 'date']).any():
        raise ValueError('Duplicate daily SKU/date observations')
    dates = pd.to_datetime(data.date, errors='coerce')
    if dates.isna().any() or not dates.eq(dates.dt.normalize()).all():
        raise ValueError('Valid midnight daily dates required')
    if not np.isfinite(data[['demand', 'price']].to_numpy()).all() or data.demand.lt(0).any() or data.price.le(0).any():
        raise ValueError('Finite nonnegative demand and positive price required')
    for _, rows in data.groupby('sku'):
        ordered = pd.to_datetime(rows.date).sort_values()
        if not ordered.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError('Daily date gaps cannot silently become zero demand')


def feature_columns(skus):
    return [*NUMERIC_FEATURES, *(f'sku:{sku}' for sku in sorted(skus))]


def build_features(data, skus):
    validate_daily(data)
    if set(data.sku) - set(skus):
        raise ValueError('Unknown SKU outside the training vocabulary')
    frame = data.sort_values(['sku', 'date']).copy()
    demand = frame.groupby('sku', sort=False).demand
    for lag in LAGS:
        frame[f'lag_{lag}'] = demand.shift(lag)
    for window in WINDOWS:
        frame[f'mean_{window}'] = demand.transform(lambda values: values.shift(1).rolling(window, min_periods=window).mean())
        frame[f'std_{window}'] = demand.transform(lambda values: values.shift(1).rolling(window, min_periods=window).std(ddof=0))
    dates = pd.to_datetime(frame.date)
    frame['weekday'], frame['month'] = dates.dt.dayofweek, dates.dt.month
    frame['year_sin'] = np.sin(2 * np.pi * dates.dt.dayofyear / 365.25)
    frame['year_cos'] = np.cos(2 * np.pi * dates.dt.dayofyear / 365.25)
    frame['weekend'] = (dates.dt.dayofweek >= 5).astype(int)
    price = frame.groupby('sku', sort=False).price
    frame['price_lag1'] = price.shift(1)
    frame['price_change7'] = frame.price_lag1 / price.shift(8) - 1
    for sku in sorted(skus):
        frame[f'sku:{sku}'] = frame.sku.eq(sku).astype(int)
    return frame


def next_features(history, date, skus):
    """Vectorized forecast row per SKU; use the same shifted definitions as training."""
    rows = []
    for sku in sorted(skus):
        data = history[sku]
        quantity = data['demand']
        prices = data['price']
        if len(quantity) < 28:
            raise ValueError('At least 28 previous daily observations are required for features')
        row = {f'lag_{lag}': quantity[-lag] for lag in LAGS}
        for window in WINDOWS:
            row[f'mean_{window}'] = float(np.mean(quantity[-window:]))
            row[f'std_{window}'] = float(np.std(quantity[-window:], ddof=0))
        row.update(weekday=date.dayofweek, month=date.month,
                   year_sin=float(np.sin(2 * np.pi * date.dayofyear / 365.25)),
                   year_cos=float(np.cos(2 * np.pi * date.dayofyear / 365.25)), weekend=int(date.dayofweek >= 5),
                   price_lag1=prices[-1], price_change7=prices[-1] / prices[-8] - 1)
        row.update({f'sku:{item}': int(item == sku) for item in sorted(skus)})
        rows.append(row)
    return pd.DataFrame(rows, columns=feature_columns(skus))


def specification(skus):
    return {'version': FEATURE_VERSION, 'columns': feature_columns(skus), 'lags': list(LAGS),
            'rolling_windows': list(WINDOWS), 'rolling_shift': 1, 'standard_deviation_ddof': 0,
            'price_policy': 'lag1; price change lag1/lag8-1; fixed-origin future price held at last origin observation',
            'sku_encoding': 'fixed one-hot vocabulary selected using initial training only',
            'calendar': 'known future weekday/month/year sine/cosine/weekend'}
