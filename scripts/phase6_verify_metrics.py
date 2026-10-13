"""Recalculate errors from saved predictions; never fit or overwrite research."""
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
checks=[]
for phase in ['validation','final-test']:
    predictions=pd.read_csv(ROOT/f'docs/research/results/{phase}-predictions.csv')
    recorded=json.loads((ROOT/f'docs/research/results/{phase}.json').read_text())
    scores=recorded['scores']
    for name, rows in predictions.groupby('model'):
        error=rows.prediction.to_numpy()-rows.actual.to_numpy()
        mae=float(np.abs(error).mean());rmse=float(np.sqrt(np.square(error).mean()))
        expected=scores[name]
        passed=abs(mae-expected['mae'])<1e-10 and abs(rmse-expected['rmse'])<1e-10 and len(rows)==expected['observations'] and expected['mape'] is None
        checks.append({'phase':phase,'model':name,'passed':passed,'observations':len(rows),'mae':mae,'rmse':rmse,'mape':None,'zero_actual_count':int((rows.actual==0).sum())})
        assert passed,(phase,name)
(ROOT/'docs/test-results/phase6-metrics.json').write_text(json.dumps({'executed_at_utc':datetime.now(UTC).isoformat(),'method':'Read-only recomputation from frozen saved predictions; no fitting or model selection','checks':checks},indent=2),encoding='utf-8')
print(f'{len(checks)} saved-prediction MAE/RMSE comparisons match frozen evidence within 1e-10.')
