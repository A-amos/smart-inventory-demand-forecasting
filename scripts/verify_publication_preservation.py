"""Verify protected Phase 4 bytes and infer without overwriting previous evidence."""
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    reference=json.loads((ROOT/'backend/app/core/phase4-reference.json').read_text(encoding='utf-8'))
    frozen=json.loads((ROOT/'docs/research/results/frozen-selection.json').read_text(encoding='utf-8'))
    expected=reference|frozen['source_fingerprints']
    files=[{'path':name,'expected':value,'actual':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name,value in expected.items()]
    assert all(x['expected']==x['actual'] for x in files)
    from ml.artifacts import load_registered
    from ml.data import load_daily
    from ml.experiment import forecast_contract
    model,registry=load_registered()
    output=forecast_contract(model,registry,load_daily(),'20728','2011-11-10',28)
    assert output.horizon_days==28 and len(output.points)==28
    (ROOT/'docs/test-results/publication-inference.json').write_text(output.model_dump_json(indent=2),encoding='utf-8')
    report={'executed_at_utc':datetime.now(UTC).isoformat(),'unchanged':True,'protected_files':files,'inference':'Historical20728/origin2011-11-10/28days; no fitting or frozen report writes'}
    (ROOT/'docs/test-results/publication-preservation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'{len(files)} protected hashes unchanged; genuine frozen historical inference passed.')

if __name__=='__main__':main()
