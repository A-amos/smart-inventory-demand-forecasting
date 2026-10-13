"""Inference-only adapter. Frozen research code/results are never edited or fitted."""
from pathlib import Path
import hashlib
import json

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = Path(__file__).resolve().parents[1] / 'core/phase4-reference.json'
NAMESPACE = 'uci-online-retail-ii'
DEMO_ORIGIN = '2011-11-10'
DEMO_DAY = '2011-11-11'


def json_file(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def checked_json(name):
    relative = f'docs/research/results/{name}'
    path = ROOT / relative
    reference = json_file(REFERENCE)
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != reference.get(relative):
        raise ValueError('Frozen research metadata missing or changed')
    return json_file(path)


def load():
    try:
        from ml.artifacts import load_registered
        registry = checked_json('model-registry.json')
        frozen = checked_json('frozen-selection.json')
        if registry['candidate'] != 'mean_28' or frozen['selected'] != 'mean_28':
            raise ValueError('Frozen validation-selected mean baseline required')
        artifact = ROOT / registry['artifact_path']
        if not artifact.is_file(): raise FileNotFoundError('Selected artifact missing')
        reference = json_file(REFERENCE)
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != reference.get(registry['artifact_path']):
            raise ValueError('Selected artifact corrupt or incompatible')
        model, loaded = load_registered(ROOT / 'docs/research/results/model-registry.json')
        if loaded != registry: raise ValueError('Registry mismatch')
        return model, registry
    except FileNotFoundError:
        raise HTTPException(503, 'Forecast artifact or history missing; operational inventory remains available') from None
    except (ValueError, KeyError, ImportError, OSError, TypeError):
        raise HTTPException(503, 'Forecast artifact incompatible or corrupt; operational inventory remains available') from None


def infer(series_sku, origin, horizon):
    model, registry = load()
    if series_sku not in registry['skus']:
        raise HTTPException(422, 'Forecast unavailable — insufficient or unsupported historical series')
    try:
        from ml.data import load_daily
        from ml.experiment import forecast_contract
        from ml.common import sha256
        metadata = checked_json('preprocessing.json')
        if sha256(ROOT / 'data/processed/phase4/development.csv') != metadata['processed_files']['development.csv']:
            raise ValueError('Historical source changed')
        history = load_daily()
        output = forecast_contract(model, registry, history, series_sku, origin.isoformat(), horizon)
        return output, registry
    except FileNotFoundError:
        raise HTTPException(503, 'Forecast history missing; operational inventory remains available') from None
    except (ValueError, KeyError, OSError):
        raise HTTPException(409, 'Forecast unavailable — insufficient contiguous history at this origin. UK reference history ends 2011-11-10; dates are never shifted.') from None


def comparison():
    try:
        validation, final = checked_json('validation.json'), checked_json('final-test.json')
        frozen = checked_json('frozen-selection.json')
        return {'dataset': 'UCI Online Retail II', 'geography': 'UK gift/wholesale online retail',
                'limitation': 'UK retail research demonstration; not validated for Kenyan retail businesses.',
                'selected': frozen['selected'], 'selection_basis': 'Validation MAE, then RMSE; final test never selects the model',
                'validation_periods': ['2011-09-16 to 2011-10-13', '2011-10-14 to 2011-11-10'],
                'final_test_period': '2011-11-11 to 2011-12-08', 'mape_policy': 'Omitted for zero/intermittent demand',
                'models': [{'name': name, 'selected': name == frozen['selected'], 'validation': validation['scores'][name],
                            'final_test': final['scores'].get(name)} for name in validation['ranking']]}
    except (ValueError, KeyError, OSError):
        raise HTTPException(503, 'Preserved research results unavailable; no accuracy values substituted') from None
