"""Read-only frozen inference; writes new Phase 6 evidence, never last-inference.json."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.artifacts import load_registered
from ml.data import load_daily
from ml.experiment import forecast_contract


def main():
    model, registry = load_registered()
    output = forecast_contract(model, registry, load_daily(), '20728', '2011-11-10', 28)
    destination = ROOT / 'docs/test-results/phase6-inference.json'
    destination.write_text(output.model_dump_json(indent=2), encoding='utf-8')
    print('Frozen inference: SKU 20728, origin 2011-11-10, 28 days; historical research only; no fit or frozen writes.')


if __name__ == '__main__': main()
