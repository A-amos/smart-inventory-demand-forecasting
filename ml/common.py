import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'docs/research'
PROCESSED = ROOT / 'data/processed/phase4'
ARTIFACTS = ROOT / 'ml/artifacts'


def now():
    return datetime.now(UTC).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False, sort_keys=True), encoding='utf-8')


def protocol():
    return read_json(ROOT / 'ml/protocol.json')


def source_fingerprints():
    """Record executable research sources when no Git commit is available."""
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in
            sorted((ROOT / 'ml').glob('*.py')) + [ROOT / 'ml/protocol.json', ROOT / 'ml/requirements.txt']}


def environment():
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'packages': {name: importlib.metadata.version(name) for name in
                         ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'scipy', 'matplotlib', 'openpyxl', 'joblib', 'pydantic']}}
