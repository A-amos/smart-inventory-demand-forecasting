"""Only load the internal registered artifact, with externally recorded hash/version checks."""
from pathlib import Path

import joblib

from ml.common import ARTIFACTS, RESEARCH, ROOT, environment, read_json, sha256
from ml.features import FEATURE_VERSION, feature_columns
from ml.forecasting import Forecaster


def load_registered(registry_path=None):
    registry = read_json(registry_path or RESEARCH / 'results/model-registry.json')
    if registry['model_version'] != 'retail-demand-v1' or registry['feature_version'] != FEATURE_VERSION:
        raise ValueError('Incompatible model/feature version')
    current = environment()
    for name in ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'joblib']:
        if registry['environment']['packages'][name] != current['packages'][name]:
            raise ValueError(f'Incompatible dependency version: {name}')
    registered = Path(registry['artifact_path'])
    if registered.is_absolute():
        raise ValueError('Registered artifact paths must be project-relative')
    path = (ROOT / registered).resolve()
    if not path.is_relative_to(ARTIFACTS.resolve()) or not path.is_file():
        raise ValueError('Only internally registered artifacts under ml/artifacts may be loaded')
    if sha256(path) != registry['artifact_sha256']:
        raise ValueError('Artifact hash mismatch; refusing deserialization')
    if registry['feature_columns'] != feature_columns(registry['skus']):
        raise ValueError('Incompatible feature layout')
    model = joblib.load(path)
    if not isinstance(model, Forecaster) or model.skus != registry['skus'] or model.name != registry['candidate']:
        raise ValueError('Artifact does not match registered model identity/vocabulary')
    return model, registry
