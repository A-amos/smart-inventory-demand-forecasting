"""Acquire the licensed public source without external accounts; never overwrite it."""
import hashlib
import json
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    folder = ROOT / 'data/raw/online-retail-ii'
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'online-retail-ii.zip'
    manifest_path = ROOT / 'docs/research/dataset-manifest.json'
    if manifest_path.exists():
        recorded = json.loads(manifest_path.read_text(encoding='utf-8'))
        for record in recorded['files']:
            if (ROOT / record['path']).exists() and sha256(ROOT / record['path']) != record['sha256']:
                raise RuntimeError('Source hash changed; stop for dataset review')
        if all((ROOT / record['path']).exists() for record in recorded['files']):
            print('Existing licensed source and manifest hashes verified; no files overwritten')
            return
    if not archive.exists():
        partial = archive.with_suffix('.download')
        with urllib.request.urlopen(URL, timeout=60) as response, partial.open('wb') as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        partial.replace(archive)
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        if names != ['online_retail_II.xlsx']:
            raise RuntimeError(f'Unexpected source archive files: {names}; stop for review')
        workbook = folder / names[0]
        if not workbook.exists():
            with workbook.open('wb') as target:
                target.write(source.read(names[0]))
    if manifest_path.exists():
        for record in recorded['files']:
            if sha256(ROOT / record['path']) != record['sha256']:
                raise RuntimeError('Reacquired source differs from recorded snapshot; stop for dataset review')
        print('Missing raw files reacquired and verified against existing manifest; provenance preserved')
        return
    manifest = {'dataset': 'UCI Online Retail II', 'repository_id': 502,
                'doi': '10.24432/C5CG6D', 'citation': 'Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository.',
                'source_page': 'https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii',
                'download_url': URL, 'license': 'CC BY 4.0',
                'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                'obtained_at_utc': datetime.now(UTC).isoformat(), 'source_donation_date': '2019-09-20',
                'geographic_context': 'UK-based non-store online gift retailer with international customers',
                'version_policy': 'No upstream semantic version; exact archive/workbook SHA-256 identifies the source snapshot',
                'modifications': 'None in raw files. Later preprocessing and aggregation are recorded separately.',
                'files': [{'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'bytes': path.stat().st_size,
                           'sha256': sha256(path)} for path in [archive, workbook]]}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Downloaded UCI Online Retail II; raw archive/workbook hashes and acquisition metadata recorded')


if __name__ == '__main__':
    main()
