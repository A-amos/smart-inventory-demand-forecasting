"""Validation selection is frozen before final-test opening; scores use matched keys."""
from datetime import UTC, datetime
from time import perf_counter

import joblib
import numpy as np
import pandas as pd

from ml.common import ARTIFACTS, PROCESSED, RESEARCH, ROOT, environment, now, protocol, read_json, sha256, source_fingerprints, write_json
from ml.contracts import ForecastOutput, ForecastPoint
from ml.data import load_daily
from ml.features import FEATURE_VERSION, build_features, feature_columns, specification
from ml.forecasting import Forecaster, metrics

KEYS = ['sku', 'origin', 'date', 'horizon_day']


def pair_actual(prediction, data):
    truth = data[['sku', 'date', 'demand']].copy()
    truth['date'] = pd.to_datetime(truth.date).dt.date.astype(str)
    merged = prediction.merge(truth.rename(columns={'demand': 'actual'}), on=['sku', 'date'], how='left', validate='many_to_one')
    if merged.actual.isna().any():
        raise ValueError('Missing evaluation observation; never silently drop it')
    return merged


def assert_identical_observations(predictions):
    groups = list(predictions.groupby('model', sort=True))
    if not groups: raise ValueError('No candidate predictions')
    reference = groups[0][1][KEYS + ['actual']].sort_values(KEYS).reset_index(drop=True)
    if reference.duplicated(KEYS).any(): raise ValueError('Duplicate evaluation keys')
    for name, rows in groups[1:]:
        actual = rows[KEYS + ['actual']].sort_values(KEYS).reset_index(drop=True)
        if not reference.equals(actual): raise ValueError(f'Candidates evaluated on different observations: {name}')


def rank_candidates(scores):
    if not scores: raise ValueError('No validation scores')
    return sorted(scores, key=lambda name: (scores[name]['mae'], scores[name]['rmse'], name))


def verify_inputs():
    metadata = read_json(RESEARCH / 'results/preprocessing.json')
    manifest = read_json(RESEARCH / 'dataset-manifest.json')
    workbook = next(item for item in manifest['files'] if item['path'].endswith('.xlsx'))
    if workbook['sha256'] != metadata['source_sha256'] or sha256(ROOT / workbook['path']) != metadata['source_sha256']:
        raise ValueError('Raw source changed; stop for provenance review')
    if metadata['protocol_sha256'] != sha256(ROOT / 'ml/protocol.json'):
        raise ValueError('Protocol changed after preprocessing; stop for research review')
    for name, digest in metadata['processed_files'].items():
        if sha256(PROCESSED / name) != digest:
            raise ValueError('Processed source changed; stop for reproducibility review')
    return metadata


def generate_features():
    metadata = verify_inputs()
    config = protocol()
    data = load_daily()
    frame = build_features(data[data.date.le(config['train_end'])], metadata['selected_skus'])
    frame.to_csv(PROCESSED / 'training-features.csv', index=False)
    write_json(RESEARCH / 'results/features.json', specification(metadata['selected_skus']))
    print('Initial-training shifted features exported; validation/test targets excluded', flush=True)


def validate_and_freeze():
    frozen_path = RESEARCH / 'results/frozen-selection.json'
    if frozen_path.exists() or (RESEARCH / 'results/final-test.json').exists():
        raise ValueError('Selection already frozen; no retuning in this completed experiment')
    metadata = verify_inputs()
    config = protocol()
    data = load_daily()  # final labels are in a different file and never opened here
    all_predictions, training_records = [], []
    for name, params in config['candidates'].items():
        for origin in config['validation_origins']:
            print(f'Validation: fitting {name} through {origin}', flush=True)
            history = data[data.date.le(origin)].copy()
            model = Forecaster(name, params, metadata['selected_skus'])
            fit = model.fit(history, origin, config['seed'])
            start = perf_counter()
            predicted = model.predict(history, origin, config['horizon'], config['minimum_history'])
            fit.update(candidate=name, origin=origin, inference_seconds=perf_counter() - start)
            training_records.append(fit)
            all_predictions.append(pair_actual(predicted, data))
    predictions = pd.concat(all_predictions, ignore_index=True)
    assert_identical_observations(predictions)
    scores = {name: metrics(rows) for name, rows in predictions.groupby('model')}
    ranked = rank_candidates(scores)
    rf = next(name for name in ranked if config['candidates'][name]['kind'] == 'random_forest')
    xgb = next(name for name in ranked if config['candidates'][name]['kind'] == 'xgboost')
    finalists = ['seasonal_naive', 'mean_28', rf, xgb]
    predictions.to_csv(RESEARCH / 'results/validation-predictions.csv', index=False)
    write_json(RESEARCH / 'results/validation.json', {'phase': 'validation', 'scores': scores, 'ranking': ranked,
               'training_records': training_records, 'environment': environment(), 'created_at_utc': now()})
    frozen = {'model_version': 'retail-demand-v1', 'frozen_at_utc': now(),
              'selection_policy': 'lowest pooled validation MAE, then RMSE, then candidate name; baselines eligible',
              'selected': ranked[0], 'finalists': {name: config['candidates'][name] for name in finalists},
              'validation_scores': scores, 'protocol_sha256': sha256(ROOT / 'ml/protocol.json'),
              'development_sha256': metadata['processed_files']['development.csv'],
              'sealed_test_sha256': metadata['processed_files']['sealed-test.csv'],
              'source_sha256': metadata['source_sha256'], 'skus': metadata['selected_skus'],
              'feature_specification': specification(metadata['selected_skus']), 'environment': environment(),
              'source_fingerprints': source_fingerprints(),
              'validation_prediction_sha256': sha256(RESEARCH / 'results/validation-predictions.csv')}
    write_json(frozen_path, frozen)
    print(f'Frozen validation-only winner: {ranked[0]}. Final test still unevaluated.', flush=True)
    return frozen


def final_evaluate():
    completed = RESEARCH / 'results/final-test.json'
    access = RESEARCH / 'results/final-test-access.json'
    if completed.exists() or access.exists():
        raise ValueError('Final test already evaluated. Use verify-reproduction; do not retune or overwrite.')
    metadata = verify_inputs()
    config = protocol()
    frozen_path = RESEARCH / 'results/frozen-selection.json'
    frozen = read_json(frozen_path)
    if frozen['protocol_sha256'] != sha256(ROOT / 'ml/protocol.json') or frozen['development_sha256'] != metadata['processed_files']['development.csv']:
        raise ValueError('Frozen experiment inputs changed; stop before opening final labels')
    if (frozen['sealed_test_sha256'] != metadata['processed_files']['sealed-test.csv']
            or frozen['source_sha256'] != metadata['source_sha256']
            or frozen['source_fingerprints'] != source_fingerprints()
            or frozen['environment']['packages'] != environment()['packages']
            or frozen['feature_specification'] != specification(metadata['selected_skus'])):
        raise ValueError('Frozen source, code, dependencies or features changed; stop before opening final labels')
    history = load_daily()
    origin = config['test_origin']
    run_id = 'uci-retail-v1-' + sha256(frozen_path)[:12]
    folder = ARTIFACTS / run_id
    folder.mkdir(parents=True, exist_ok=True)
    output, timings, models = [], [], {}
    for name, params in frozen['finalists'].items():
        print(f'Final frozen fit/evaluation: {name}', flush=True)
        model = Forecaster(name, params, frozen['skus'])
        fit = model.fit(history, origin, config['seed'])
        start = perf_counter()
        prediction = model.predict(history, origin, config['horizon'], config['minimum_history'])
        fit.update(candidate=name, origin=origin, inference_seconds=perf_counter() - start)
        timings.append(fit)
        output.append(prediction)
        models[name] = model
    # All frozen models fitted/predicted without test labels. Durable guard stops
    # an interrupted evaluation from silently reopening the holdout for tuning.
    with access.open('x', encoding='utf-8') as marker:
        import json
        json.dump({'opened_at_utc': now(), 'frozen_selection_sha256': sha256(frozen_path)}, marker, indent=2)
    test = load_daily('sealed-test.csv')
    if test.date.min() != pd.Timestamp(config['test_origin']) + pd.Timedelta(days=1) or test.date.max() != pd.Timestamp(config['test_end']):
        raise ValueError('Unexpected final test period; stop for review')
    predictions = pd.concat([pair_actual(item, test) for item in output], ignore_index=True)
    assert_identical_observations(predictions)
    predictions.to_csv(RESEARCH / 'results/final-test-predictions.csv', index=False)
    scores = {name: metrics(rows) for name, rows in predictions.groupby('model')}
    by_sku = [{**metrics(rows), 'model': name, 'sku': sku} for (name, sku), rows in predictions.groupby(['model', 'sku'])]
    pd.DataFrame(by_sku).to_csv(RESEARCH / 'results/final-test-by-sku.csv', index=False)
    selected = frozen['selected']
    model = models[selected]
    artifact = folder / 'selected.joblib'
    joblib.dump(model, artifact, compress=3)
    registry = {'model_id': run_id, 'model_version': 'retail-demand-v1', 'feature_version': FEATURE_VERSION,
                'candidate': selected, 'skus': frozen['skus'], 'feature_columns': feature_columns(frozen['skus']),
                'artifact_path': artifact.relative_to(ROOT).as_posix(), 'artifact_sha256': sha256(artifact), 'environment': environment(),
                'trained_through': origin, 'created_at_utc': now(), 'source_sha256': metadata['source_sha256'],
                'frozen_selection_sha256': sha256(frozen_path), 'parameters': frozen['finalists'][selected],
                'preprocessing_metadata_sha256': sha256(RESEARCH / 'results/preprocessing.json')}
    write_json(RESEARCH / 'results/model-registry.json', registry)
    write_json(folder / 'model-metadata.json', registry)
    write_json(folder / 'features.json', frozen['feature_specification'])
    write_json(folder / 'preprocessing.json', metadata)
    if model.estimator is not None:
        importance = pd.DataFrame({'feature': feature_columns(frozen['skus']), 'importance': model.estimator.feature_importances_})
        importance.sort_values('importance', ascending=False).to_csv(RESEARCH / 'results/selected-training-feature-importance.csv', index=False)
    final = {'phase': 'final_test', 'evaluated_at_utc': now(), 'frozen_selection_sha256': sha256(frozen_path),
             'selected_by_validation_only': selected, 'run_id': run_id, 'scores': scores, 'timings': timings,
             'source_sha256': metadata['source_sha256'], 'protocol_sha256': metadata['protocol_sha256'],
             'test_label_sha256': sha256(PROCESSED / 'sealed-test.csv'),
             'prediction_sha256': sha256(RESEARCH / 'results/final-test-predictions.csv'), 'environment': environment()}
    write_json(completed, final)
    write_json(folder / 'evaluation.json', final)
    print(f'Final test saved once; validation-selected model remains {selected}.', flush=True)
    return final


def forecast_contract(model, registry, data, sku, origin, horizon):
    if sku not in registry['skus']:
        raise ValueError('Unknown SKU; no fabricated fallback forecast')
    predictions = model.predict(data, origin, horizon, protocol()['minimum_history'])
    rows = predictions[predictions.sku.eq(sku)]
    return ForecastOutput(sku=sku, forecast_origin=pd.Timestamp(origin).date(), horizon_days=horizon,
                          model_id=registry['model_id'], trained_through=pd.Timestamp(model.trained_through).date(),
                          created_at=datetime.now(UTC), points=[ForecastPoint(forecast_date=row.date,
                          horizon_day=int(row.horizon_day), predicted_demand=float(row.prediction)) for row in rows.itertuples()])


def verify_reproduction():
    from ml.artifacts import load_registered
    metadata = verify_inputs()
    final = read_json(RESEARCH / 'results/final-test.json')
    if sha256(RESEARCH / 'results/final-test-predictions.csv') != final['prediction_sha256']:
        raise ValueError('Saved evaluation predictions changed')
    if sha256(RESEARCH / 'results/frozen-selection.json') != final['frozen_selection_sha256']:
        raise ValueError('Selection changed after final test; stop for evaluation review')
    model, registry = load_registered()
    config = protocol()
    predicted = model.predict(load_daily(), config['test_origin'], config['horizon'], config['minimum_history'])
    saved = pd.read_csv(RESEARCH / 'results/final-test-predictions.csv', dtype={'sku': 'string'})
    assert_identical_observations(saved)
    for name, rows in saved.groupby('model'):
        recalculated = metrics(rows)
        for key in ['mae', 'rmse']:
            if not np.isclose(recalculated[key], final['scores'][name][key], rtol=0, atol=1e-10):
                raise ValueError('Published metrics do not match saved evaluation observations')
    saved = saved[saved.model.eq(model.name)].sort_values(KEYS).reset_index(drop=True)
    predicted = predicted.sort_values(KEYS).reset_index(drop=True)
    if not predicted[KEYS].astype(str).equals(saved[KEYS].astype(str)):
        raise ValueError('Reloaded forecast keys differ from saved evaluation observations')
    if not np.allclose(predicted.prediction, saved.prediction, rtol=0, atol=1e-10):
        raise ValueError('Reloaded model predictions do not reproduce saved final predictions')
    recalculated = metrics(saved)
    expected = final['scores'][model.name]
    for key in ['mae', 'rmse']:
        if not np.isclose(recalculated[key], expected[key], rtol=0, atol=1e-10):
            raise ValueError('Published metrics do not match actual saved predictions')
    output = forecast_contract(model, registry, load_daily(), registry['skus'][0], config['test_origin'], config['horizon'])
    write_json(RESEARCH / 'results/example-forecast.json', output.model_dump(mode='json'))
    write_json(RESEARCH / 'results/forecast-schema.json', ForecastOutput.model_json_schema())
    result = {'passed': True, 'verified_at_utc': now(), 'model_id': registry['model_id'], 'observations': len(predicted),
              'recalculated_metrics': recalculated, 'prediction_tolerance': 1e-10,
              'checks': ['registered artifact hash and versions', 'same predictions after deserialization', 'metrics recalculated from saved actual/prediction pairs', 'versioned forecast contract']}
    write_json(RESEARCH / 'results/reproduction.json', result)
    print('Selected artifact reload, predictions, metrics and forecast contract reproduced successfully', flush=True)
    return result
