import io
import json
import zipfile

import pytest

from scripts import create_phase4_reproduction_workspace as workspace
from scripts import download_phase4_dataset as download


def test_manifest_with_missing_ignored_raw_files_can_reacquire(tmp_path, monkeypatch):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w') as archive:
        archive.writestr('online_retail_II.xlsx', b'test workbook bytes, not research data')
    folder = tmp_path / 'data/raw/online-retail-ii'
    folder.mkdir(parents=True)
    archive_path = folder / 'online-retail-ii.zip'
    archive_path.write_bytes(payload.getvalue())
    workbook = folder / 'online_retail_II.xlsx'
    workbook.write_bytes(b'test workbook bytes, not research data')
    manifest = {'files': [{'path': path.relative_to(tmp_path).as_posix(), 'sha256': download.sha256(path)}
                          for path in [archive_path, workbook]], 'obtained_at_utc': 'original timestamp'}
    manifest_path = tmp_path / 'docs/research/dataset-manifest.json'
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest))
    original = manifest_path.read_bytes()
    archive_path.unlink(); workbook.unlink()  # test-owned temporary fixtures only
    monkeypatch.setattr(download, 'ROOT', tmp_path)
    monkeypatch.setattr(download.urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(payload.getvalue()))
    download.main()
    assert archive_path.exists() and workbook.exists() and manifest_path.read_bytes() == original
    workbook.write_bytes(b'corrupted fixture')
    with pytest.raises(RuntimeError, match='hash changed'): download.main()


def test_reproduction_setup_preserves_sources_and_excludes_frozen_results(tmp_path, monkeypatch):
    root = tmp_path / 'source'
    for directory in ['ml/tests', 'scripts', 'docs/research/results']:
        (root / directory).mkdir(parents=True)
    for file in ['ml/common.py', 'ml/protocol.json', 'ml/tests/test_example.py',
                 'scripts/download_phase4_dataset.py', 'scripts/create_phase4_reproduction_workspace.py',
                 'docs/research/DATASET.md', 'docs/research/EXPERIMENT_PROTOCOL.md',
                 'docs/research/dataset-manifest.json', 'docs/research/results/frozen-selection.json']:
        (root / file).write_text('fixture')
    monkeypatch.setattr(workspace, 'ROOT', root)
    destination = workspace.create('.local/reproduction')
    assert (destination / 'ml/common.py').read_text() == 'fixture'
    assert not (destination / 'docs/research/results').exists()
    assert not (destination / '.env').exists()
    with pytest.raises(ValueError, match='overwrite'): workspace.create('.local/reproduction')
    with pytest.raises(ValueError, match='under project'): workspace.create('../outside')
