"""Repeat frozen validation configurations without changing selection or final labels."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.common import RESEARCH, now, protocol, read_json, sha256, source_fingerprints, write_json
from ml.data import load_daily
from ml.experiment import KEYS, verify_inputs
from ml.forecasting import Forecaster


def main():
    metadata = verify_inputs()
    frozen_path = RESEARCH / 'results/frozen-selection.json'
    frozen = read_json(frozen_path)
    initial_hash = sha256(frozen_path)
    assert frozen['source_fingerprints'] == source_fingerprints()
    config = protocol()
    saved = pd.read_csv(RESEARCH / 'results/validation-predictions.csv', dtype={'sku': 'string'})
    history = load_daily()
    records = []
    for name, params in config['candidates'].items():
        for origin in config['validation_origins']:
            print(f'Refit validation reproducibility: {name} at {origin}', flush=True)
            model = Forecaster(name, params, metadata['selected_skus'])
            model.fit(history, origin, config['seed'])
            repeated = model.predict(history, origin, config['horizon'], config['minimum_history']).sort_values(KEYS).reset_index(drop=True)
            reference = saved[saved.model.eq(name) & saved.origin.eq(origin)].sort_values(KEYS).reset_index(drop=True)
            assert repeated[KEYS].astype(str).equals(reference[KEYS].astype(str))
            differences = np.abs(repeated.prediction.to_numpy() - reference.prediction.to_numpy())
            assert np.allclose(repeated.prediction, reference.prediction, rtol=0, atol=1e-10), name
            records.append({'candidate': name, 'origin': origin, 'observations': len(reference),
                            'maximum_absolute_prediction_difference': float(differences.max()), 'passed': True})
    assert sha256(frozen_path) == initial_hash, 'Selection must remain unchanged'
    write_json(ROOT / 'docs/test-results/phase4-validation-reproduction.json',
               {'passed': True, 'executed_at_utc': now(), 'absolute_tolerance': 1e-10,
                'records': records, 'selection_unchanged_sha256': initial_hash,
                'final_labels_opened': False,
                'maximum_absolute_prediction_difference': max(row['maximum_absolute_prediction_difference'] for row in records)})
    print('All frozen validation configurations reproduce numerically; selection unchanged', flush=True)


if __name__ == '__main__':
    main()
