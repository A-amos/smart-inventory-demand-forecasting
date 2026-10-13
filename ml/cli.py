import argparse
from datetime import date

from ml.common import RESEARCH, protocol, write_json


def main():
    parser = argparse.ArgumentParser(description='Reproducible Phase 4 research; final evaluation requires a frozen selection.')
    parser.add_argument('stage', choices=['prepare', 'eda', 'features', 'validate', 'final', 'verify-reproduction', 'infer'])
    parser.add_argument('--sku')
    parser.add_argument('--origin')
    parser.add_argument('--horizon', type=int, default=28)
    args = parser.parse_args()
    if args.stage == 'prepare':
        from ml.data import prepare
        prepare()
    elif args.stage == 'eda':
        from ml.eda import run_eda
        run_eda()
    elif args.stage == 'features':
        from ml.experiment import generate_features
        generate_features()
    elif args.stage == 'validate':
        from ml.experiment import validate_and_freeze
        validate_and_freeze()
    elif args.stage == 'final':
        from ml.experiment import final_evaluate
        final_evaluate()
    elif args.stage == 'verify-reproduction':
        from ml.experiment import verify_reproduction
        verify_reproduction()
    elif args.stage == 'infer':
        if not args.sku or not args.origin: parser.error('infer requires --sku and --origin YYYY-MM-DD')
        from ml.artifacts import load_registered
        from ml.data import load_daily
        from ml.experiment import forecast_contract
        model, registry = load_registered()
        origin = date.fromisoformat(args.origin)
        output = forecast_contract(model, registry, load_daily(), args.sku, origin.isoformat(), args.horizon)
        write_json(RESEARCH / 'results/last-inference.json', output.model_dump(mode='json'))
        print(output.model_dump_json(indent=2))


if __name__ == '__main__':
    main()
