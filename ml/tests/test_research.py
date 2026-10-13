from datetime import UTC, date, datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from ml import artifacts, experiment
from ml.common import environment, protocol, sha256, write_json
from ml.contracts import ForecastOutput, ForecastPoint
from ml.data import REQUIRED, choose_cohort, clean_transactions, daily_series
from ml.features import build_features, feature_columns, next_features, validate_daily
from ml.forecasting import Forecaster, metrics

SKUS = ['10001', '10002']
ORIGIN = pd.Timestamp('2011-02-04')  # 400 prior daily observations
PARAMS = [dict(kind='seasonal_naive'), dict(kind='mean_28'),
          dict(kind='random_forest', n_estimators=5, max_depth=3, min_samples_leaf=5),
          dict(kind='xgboost', n_estimators=5, max_depth=2, learning_rate=.1, min_child_weight=2)]


def model(data, params=PARAMS[0]):
    result = Forecaster(params['kind'], params, SKUS)
    result.fit(data, ORIGIN, 42)
    return result


def test_chronological_protocol():
    config = protocol()
    assert pd.Timestamp(config['train_end']) == pd.Timestamp(config['validation_origins'][0])
    assert pd.Timestamp(config['validation_end']) == pd.Timestamp(config['test_origin'])
    for first, second in zip(config['validation_origins'], config['validation_origins'][1:]):
        assert pd.Timestamp(first) + pd.Timedelta(days=config['horizon']) <= pd.Timestamp(second)
    assert pd.Timestamp(config['test_origin']) + pd.Timedelta(days=config['horizon']) == pd.Timestamp(config['test_end'])


def test_cohort_is_seeded_and_independent_of_future_products_or_sales(daily):
    config = {**protocol(), 'series_count': 6, 'train_start': '2010-01-01', 'train_end': ORIGIN.date().isoformat()}
    source = pd.concat([daily[daily.sku.eq('10001')].assign(StockCode=str(10001 + index),
                        Quantity=lambda rows: rows.demand + index) for index in range(9)], ignore_index=True)
    before, _, _ = choose_cohort(source, config)
    changed = source.copy()
    changed.loc[changed.date.gt(ORIGIN), 'Quantity'] = 1000000
    changed = pd.concat([changed, changed[changed.date.gt(ORIGIN)].assign(StockCode='99999')])
    after, _, _ = choose_cohort(changed, config)
    assert before == after and len(before) == 6 and '99999' not in after


def test_final_requires_frozen_selection_before_loading_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, 'RESEARCH', tmp_path)
    monkeypatch.setattr(experiment, 'verify_inputs', lambda: {})
    monkeypatch.setattr(experiment, 'load_daily', lambda *args: pytest.fail('Holdout opened before freeze'))
    with pytest.raises(FileNotFoundError): experiment.final_evaluate()


def test_changed_code_is_rejected_before_final_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, 'RESEARCH', tmp_path)
    metadata = {'processed_files': {'development.csv': 'development', 'sealed-test.csv': 'sealed'},
                'source_sha256': 'source', 'selected_skus': SKUS}
    monkeypatch.setattr(experiment, 'verify_inputs', lambda: metadata)
    monkeypatch.setattr(experiment, 'load_daily', lambda *args: pytest.fail('Labels opened after source changed'))
    write_json(tmp_path / 'results/frozen-selection.json',
               {'protocol_sha256': sha256(experiment.ROOT / 'ml/protocol.json'),
                'development_sha256': 'development', 'sealed_test_sha256': 'sealed',
                'source_sha256': 'source', 'source_fingerprints': {'changed': 'bad'}})
    with pytest.raises(ValueError, match='Frozen source'): experiment.final_evaluate()


def test_features_use_prior_targets_and_prices_only(daily):
    original = build_features(daily, SKUS)
    changed = daily.copy()
    changed.loc[changed.date.ge(ORIGIN), ['demand', 'price']] = [999999, 999]
    revised = build_features(changed, SKUS)
    mask = original.date.le(ORIGIN)
    pd.testing.assert_frame_equal(original.loc[mask, feature_columns(SKUS)], revised.loc[mask, feature_columns(SKUS)])


def test_shifted_values_and_separate_skus(daily):
    frame = build_features(daily, SKUS)
    for sku in SKUS:
        row = frame[frame.sku.eq(sku) & frame.date.eq(ORIGIN)].iloc[0]
        prior = daily[daily.sku.eq(sku) & daily.date.lt(ORIGIN)]
        assert row.lag_1 == prior.demand.iloc[-1]
        assert row.mean_7 == pytest.approx(prior.demand.tail(7).mean())
        assert row.std_28 == pytest.approx(prior.demand.tail(28).std(ddof=0))
        assert row.price_lag1 == prior.price.iloc[-1]


def test_training_inference_feature_equivalence(daily):
    history = {sku: {'demand': rows.demand.tolist(), 'price': rows.price.tolist()}
               for sku in SKUS for rows in [daily[daily.sku.eq(sku) & daily.date.lt(ORIGIN)]]}
    actual = next_features(history, ORIGIN, SKUS)
    expected = build_features(daily, SKUS).loc[lambda frame: frame.date.eq(ORIGIN), feature_columns(SKUS)].reset_index(drop=True)
    np.testing.assert_allclose(actual.to_numpy(), expected.to_numpy(), rtol=0, atol=1e-12)


@pytest.mark.parametrize('params', PARAMS)
def test_future_labels_and_prices_do_not_change_fit_or_forecast(daily, params):
    changed = daily.copy()
    changed.loc[changed.date.gt(ORIGIN), ['demand', 'price']] = [1000000, 1000]
    first, second = model(daily, params), model(changed, params)
    pd.testing.assert_frame_equal(first.predict(daily, ORIGIN), second.predict(changed, ORIGIN))


@pytest.mark.parametrize('params', PARAMS)
def test_fixed_seed_deterministic_and_serialization_roundtrip(daily, tmp_path, params):
    first = model(daily, params)
    expected = first.predict(daily, ORIGIN)
    pd.testing.assert_frame_equal(expected, model(daily, params).predict(daily, ORIGIN))
    path = tmp_path / 'trusted-test.joblib'
    joblib.dump(first, path)
    pd.testing.assert_frame_equal(expected, joblib.load(path).predict(daily, ORIGIN))


@pytest.mark.parametrize('params', PARAMS)
def test_zero_demand_is_finite(daily, params):
    daily['demand'] = 0.0
    prediction = model(daily, params).predict(daily, ORIGIN)
    assert np.isfinite(prediction.prediction).all()
    assert prediction.prediction.eq(0).all()


@pytest.mark.parametrize('horizon', [0, 29, -1, 2.5, True])
def test_invalid_horizon(daily, horizon):
    with pytest.raises(ValueError, match='Horizon'):
        model(daily).predict(daily, ORIGIN, horizon)


def test_forecast_alignment_and_last_origin_week_repeat(daily):
    predicted = model(daily).predict(daily, ORIGIN, 28)
    assert len(predicted) == 56
    assert not predicted.duplicated(experiment.KEYS).any()
    for sku in SKUS:
        rows = predicted[predicted.sku.eq(sku)]
        assert rows.horizon_day.tolist() == list(range(1, 29))
        assert pd.to_datetime(rows.date).tolist() == pd.date_range(ORIGIN + pd.Timedelta(days=1), periods=28).tolist()
        assert rows.prediction.tolist() == daily[daily.sku.eq(sku) & daily.date.le(ORIGIN)].demand.tail(7).tolist() * 4


@pytest.mark.parametrize('mutation', ['missing', 'gap', 'duplicate', 'negative', 'infinite', 'invalid_date', 'intraday'])
def test_invalid_daily_data_rejected(daily, mutation):
    if mutation == 'missing': daily.loc[0, 'demand'] = np.nan
    if mutation == 'gap': daily = daily.drop(index=3)
    if mutation == 'duplicate': daily = pd.concat([daily, daily.iloc[[0]]])
    if mutation == 'negative': daily.loc[0, 'demand'] = -1
    if mutation == 'infinite': daily.loc[0, 'price'] = np.inf
    if mutation == 'invalid_date': daily.loc[0, 'date'] = pd.NaT
    if mutation == 'intraday': daily.loc[0, 'date'] += pd.Timedelta(hours=1)
    with pytest.raises(ValueError): validate_daily(daily)


def test_unknown_sku_insufficient_history_and_early_origin(daily):
    fitted = model(daily)
    changed = daily.copy()
    changed.loc[0, 'sku'] = 'unknown'
    with pytest.raises(ValueError, match='Unknown SKU'): fitted.predict(changed, ORIGIN)
    with pytest.raises(ValueError, match='Insufficient'): fitted.predict(daily[daily.date.gt('2010-12-01')], ORIGIN)
    with pytest.raises(ValueError, match='predates'): fitted.predict(daily, '2011-01-01')
    with pytest.raises(ValueError, match='not fitted'): Forecaster('mean', PARAMS[1], SKUS).predict(daily, ORIGIN)


@pytest.mark.parametrize('value', [np.nan, np.inf])
def test_nonfinite_estimator_output_rejected(daily, value):
    class BrokenEstimator:
        def predict(self, features):
            return np.full(len(features), value)
    fitted = model(daily, PARAMS[2])
    fitted.estimator = BrokenEstimator()
    with pytest.raises(ValueError, match='nonfinite'): fitted.predict(daily, ORIGIN)


def test_metrics_with_zeros_known_values():
    result = metrics(pd.DataFrame({'actual': [0, 4], 'prediction': [2, 4]}))
    assert result['mae'] == 1 and result['rmse'] == pytest.approx(np.sqrt(2))
    assert result['zero_actual_count'] == 1 and result['mape'] is None


def test_xgboost_default_missing_sentinel_has_explicit_json_metadata(daily):
    import json
    fitted = Forecaster('xgboost', PARAMS[3], SKUS)
    metadata = fitted.fit(daily, ORIGIN, 42)
    assert metadata['effective_parameters']['missing'] == {'nonfinite_float': 'nan'}
    json.dumps(metadata, allow_nan=False)


def test_missing_actuals_and_misaligned_model_observations_fail(daily):
    first = model(daily).predict(daily, ORIGIN, 2)
    paired = experiment.pair_actual(first, daily)
    with pytest.raises(ValueError, match='Missing'): experiment.pair_actual(first, daily[daily.date.le(ORIGIN)])
    second = paired.copy()
    second['model'] = 'other'
    with pytest.raises(ValueError, match='different'): experiment.assert_identical_observations(pd.concat([paired, second.iloc[1:]]))
    with pytest.raises(ValueError, match='Duplicate'): experiment.assert_identical_observations(pd.concat([paired, paired]))
    experiment.assert_identical_observations(pd.concat([paired, second]))


def test_selection_uses_validation_scores_and_deterministic_ties():
    assert experiment.rank_candidates({'b': {'mae': 2, 'rmse': 2}, 'a': {'mae': 1, 'rmse': 3}}) == ['a', 'b']
    assert experiment.rank_candidates({'b': {'mae': 1, 'rmse': 2}, 'a': {'mae': 1, 'rmse': 2}}) == ['a', 'b']


def test_positive_transaction_cleaning_and_prior_price_fill():
    # Explicit column names keep this fixture independent of source order.
    good = dict(Country='UK', **{'Customer ID': 1}, Description='Item', Invoice='001',
                InvoiceDate=pd.Timestamp('2010-01-01'), Price=2., Quantity=3., StockCode='10001')
    raw = pd.DataFrame([good, good, {**good, 'Invoice': 'C002'}, {**good, 'Invoice': '003', 'Quantity': -2},
                        {**good, 'Invoice': '004', 'Price': 0}, {**good, 'Invoice': '005', 'StockCode': 'POST'},
                        {**good, 'Invoice': '006', 'InvoiceDate': 'bad'},
                        {**good, 'Invoice': '007', 'InvoiceDate': pd.Timestamp('2010-01-03'), 'Price': 4}])
    cleaned, audit = clean_transactions(raw)
    assert len(cleaned) == 2 and sum(audit['exclusive_rejections'].values()) == 6
    daily = daily_series(cleaned, ['10001'], '2010-01-04')
    assert daily.demand.tolist() == [3, 0, 3, 0]
    assert daily.price.tolist() == [2, 2, 4, 4]
    with pytest.raises(ValueError, match='Missing source'): clean_transactions(raw.drop(columns='Quantity'))


def valid_contract():
    return dict(sku='10001', forecast_origin=date(2011, 2, 4), horizon_days=2, model_id='test',
                trained_through=date(2011, 2, 4), created_at=datetime.now(UTC),
                points=[dict(forecast_date=date(2011, 2, 4) + timedelta(days=step), horizon_day=step, predicted_demand=1.)
                        for step in [1, 2]])


def test_contract_round_trip():
    value = ForecastOutput(**valid_contract())
    assert ForecastOutput.model_validate_json(value.model_dump_json()) == value
    assert value.schema_version == 'forecast-v1'


@pytest.mark.parametrize('mutation', ['negative', 'nan', 'wrong_date', 'wrong_step', 'missing_day', 'future_training', 'version', 'naive_timestamp', 'bool_horizon'])
def test_contract_rejects_inconsistent_output(mutation):
    value = valid_contract()
    if mutation == 'negative': value['points'][0]['predicted_demand'] = -1
    if mutation == 'nan': value['points'][0]['predicted_demand'] = np.nan
    if mutation == 'wrong_date': value['points'][0]['forecast_date'] = date(2011, 2, 4)
    if mutation == 'wrong_step': value['points'][0]['horizon_day'] = 2
    if mutation == 'missing_day': value['points'].pop()
    if mutation == 'future_training': value['trained_through'] = date(2011, 2, 5)
    if mutation == 'version': value['model_version'] = 'other'
    if mutation == 'naive_timestamp': value['created_at'] = datetime(2011, 1, 1)
    if mutation == 'bool_horizon': value['horizon_days'] = True
    with pytest.raises(ValidationError): ForecastOutput(**value)


@pytest.mark.parametrize('mutation', ['hash', 'model_version', 'feature_version', 'columns', 'dependency', 'outside'])
def test_artifact_compatibility_checked_before_loading(daily, tmp_path, monkeypatch, mutation):
    monkeypatch.setattr(artifacts, 'ROOT', tmp_path)
    monkeypatch.setattr(artifacts, 'ARTIFACTS', tmp_path / 'ml/artifacts')
    folder = tmp_path / 'ml/artifacts'
    folder.mkdir(parents=True)
    path = folder / 'selected.joblib'
    fitted = model(daily)
    joblib.dump(fitted, path)
    record = dict(model_version='retail-demand-v1', feature_version='features-v1', environment=environment(),
                  artifact_path='ml/artifacts/selected.joblib', artifact_sha256=sha256(path),
                  feature_columns=feature_columns(SKUS), skus=SKUS, candidate=fitted.name)
    if mutation == 'hash': record['artifact_sha256'] = 'bad'
    if mutation == 'model_version': record['model_version'] = 'bad'
    if mutation == 'feature_version': record['feature_version'] = 'bad'
    if mutation == 'columns': record['feature_columns'] = []
    if mutation == 'dependency': record['environment']['packages']['numpy'] = 'bad'
    if mutation == 'outside': record['artifact_path'] = '../../outside.joblib'
    registry = tmp_path / 'registry.json'
    write_json(registry, record)
    with pytest.raises(ValueError): artifacts.load_registered(registry)


def test_final_test_cannot_open_without_freeze_or_reopen_after_access(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, 'RESEARCH', tmp_path)
    (tmp_path / 'results').mkdir()
    write_json(tmp_path / 'results/final-test-access.json', {'interrupted': True})
    monkeypatch.setattr(experiment, 'load_daily', lambda *args: pytest.fail('Labels must never be opened'))
    with pytest.raises(ValueError, match='already evaluated'): experiment.final_evaluate()
