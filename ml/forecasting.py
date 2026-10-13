from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from ml.features import build_features, feature_columns, next_features, validate_daily


def parameter_metadata(parameters):
    """JSON-safe tagged estimator sentinels; metrics/predictions stay strictly finite."""
    return {key: {'nonfinite_float': str(value)} if isinstance(value, float) and not np.isfinite(value) else value
            for key, value in parameters.items()}


@dataclass
class Forecaster:
    name: str
    parameters: dict
    skus: list
    estimator: object = None
    trained_through: str | None = None

    def fit(self, data, origin, seed):
        origin = pd.Timestamp(origin)
        history = data[data.date.le(origin)].copy()
        validate_daily(history)
        self.trained_through = origin.date().isoformat()
        kind = self.parameters['kind']
        start = perf_counter()
        rows = None
        if kind not in ['seasonal_naive', 'mean_28']:
            frame = build_features(history, self.skus).dropna(subset=feature_columns(self.skus))
            if frame.empty:
                raise ValueError('Insufficient feature history')
            params = {k: v for k, v in self.parameters.items() if k != 'kind'}
            if kind == 'random_forest':
                self.estimator = RandomForestRegressor(**params, random_state=seed, n_jobs=2)
            elif kind == 'xgboost':
                self.estimator = XGBRegressor(**params, random_state=seed, n_jobs=2, tree_method='hist',
                    objective='reg:squarederror', reg_lambda=5, subsample=1, colsample_bytree=1)
            else:
                raise ValueError('Unsupported model kind')
            self.estimator.fit(frame[feature_columns(self.skus)].to_numpy(dtype=float), frame.demand.to_numpy(dtype=float))
            rows = len(frame)
        return {'training_seconds': perf_counter() - start, 'feature_training_rows': rows,
                'warmup_rows_excluded': len(history) - rows if rows is not None else 0,
                'effective_parameters': parameter_metadata(self.estimator.get_params()) if self.estimator is not None else self.parameters}

    def predict(self, data, origin, horizon=28, minimum_history=365):
        if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= 28:
            raise ValueError('Horizon must be an integer from 1 to 28')
        if self.trained_through is None:
            raise ValueError('Model is not fitted')
        origin = pd.Timestamp(origin)
        if origin < pd.Timestamp(self.trained_through):
            raise ValueError('Forecast origin predates model training cutoff')
        if set(data.sku) - set(self.skus):
            raise ValueError('Unknown SKU outside model vocabulary')
        history = data[data.date.le(origin)].copy()
        validate_daily(history)
        series = {}
        for sku in sorted(self.skus):
            rows = history[history.sku.eq(sku)].sort_values('date')
            if len(rows) < minimum_history or rows.date.iloc[-1] != origin:
                raise ValueError(f'Insufficient contiguous history through origin for SKU {sku}')
            series[sku] = {'demand': rows.demand.to_list(), 'price': rows.price.to_list()}
        weekly = {sku: values['demand'][-7:] for sku, values in series.items()}
        mean = {sku: float(np.mean(values['demand'][-28:])) for sku, values in series.items()}
        result = []
        for step in range(1, horizon + 1):
            date = origin + pd.Timedelta(days=step)
            kind = self.parameters['kind']
            if kind == 'seasonal_naive': predictions = [weekly[sku][(step - 1) % 7] for sku in sorted(self.skus)]
            elif kind == 'mean_28': predictions = [mean[sku] for sku in sorted(self.skus)]
            else:
                predictions = self.estimator.predict(next_features(series, date, self.skus).to_numpy(dtype=float))
            for sku, prediction in zip(sorted(self.skus), predictions, strict=True):
                value = float(prediction)
                if not np.isfinite(value): raise ValueError('Model returned nonfinite forecast')
                value = max(0.0, value)
                result.append({'sku': sku, 'origin': origin.date().isoformat(), 'date': date.date().isoformat(),
                               'horizon_day': step, 'prediction': value, 'model': self.name})
                series[sku]['demand'].append(value)
                series[sku]['price'].append(series[sku]['price'][-1])
        return pd.DataFrame(result)


def metrics(predictions):
    if predictions.empty or not {'actual', 'prediction'} <= set(predictions):
        raise ValueError('Nonempty paired predictions/actuals required')
    values = predictions[['actual', 'prediction']].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Finite nonnegative actuals/predictions required')
    error = values[:, 1] - values[:, 0]
    return {'observations': len(error), 'mae': float(np.abs(error).mean()), 'rmse': float(np.sqrt(np.square(error).mean())),
            'zero_actual_count': int((values[:, 0] == 0).sum()), 'mape': None,
            'mape_policy': 'omitted: zero/intermittent demand; no epsilon substitution or unstated positive-only subset'}
