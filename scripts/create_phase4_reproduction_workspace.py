"""Isolate a research rerun without copying credentials or completed results."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def create(destination):
    destination = (ROOT / destination).resolve()
    allowed = (ROOT / '.local').resolve()
    if not destination.is_relative_to(allowed) or destination == allowed:
        raise ValueError('Reproduction destination must be a new directory under project .local')
    if destination.exists():
        raise ValueError('Destination exists; refusing overwrite')
    (destination / 'ml/artifacts').mkdir(parents=True)
    for source in (ROOT / 'ml').iterdir():
        if source.is_file(): shutil.copy2(source, destination / 'ml' / source.name)
    shutil.copytree(ROOT / 'ml/tests', destination / 'ml/tests', ignore=shutil.ignore_patterns('__pycache__'))
    (destination / 'scripts').mkdir()
    for name in ['download_phase4_dataset.py', 'create_phase4_reproduction_workspace.py']:
        shutil.copy2(ROOT / 'scripts' / name, destination / 'scripts' / name)
    (destination / 'docs/research').mkdir(parents=True)
    for name in ['DATASET.md', 'EXPERIMENT_PROTOCOL.md', 'dataset-manifest.json']:
        shutil.copy2(ROOT / 'docs/research' / name, destination / 'docs/research' / name)
    (destination / 'docs/test-results').mkdir()
    print(f'Created isolated research workspace: {destination}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', help='new directory below .local, e.g. .local/reproduction-1')
    create(parser.parse_args().destination)
