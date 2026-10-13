"""Bounded publication scan of candidate/staged bytes; never prints secret values."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def git(*args):
    # This checkout was initialized by the sandbox user; trust only its exact path.
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--staged',action='store_true')
    args=parser.parse_args()
    raw=git('ls-files','--cached','-z') if args.staged else git('ls-files','--cached','--others','--exclude-standard','-z')
    names=sorted(set(x.decode('utf-8') for x in raw.split(b'\0') if x))
    secrets=[]
    for env in [ROOT/'.env',ROOT/'backend/.env']:
        if env.exists():
            for line in env.read_text(encoding='utf-8').splitlines():
                key,_,value=line.partition('=')
                if key in {'MYSQL_PASSWORD','MYSQL_ROOT_PASSWORD'} and len(value.strip())>=8:
                    secrets.append(value.strip().encode())
    for relative in ['.local/verification-account.json','.local/phase6-repro/account.json']:
        file=ROOT/relative
        if file.exists():
            password=json.loads(file.read_text(encoding='utf-8')).get('password','')
            if len(password)>=8:secrets.append(password.encode())
    patterns=[('GitHub credential',rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
              ('private key',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
              ('AWS access identifier',rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')]
    denied=[];hits=[];large=[];total=0
    for name in names:
        path=Path(name)
        parts=path.parts
        if any(x in {'.git','.local','.venv','venv','env','node_modules','__pycache__','.pytest_cache','.pnpm-store','dist','mysql_data','docker-volumes'} for x in parts) or (path.name.startswith('.env') and not path.name.endswith('.example')) or path.suffix.lower() in {'.pyc','.db','.sqlite','.sqlite3','.log','.pem','.key','.p12','.pfx'}:
            denied.append(name)
        content=git('show',':'+name) if args.staged else (ROOT/name).read_bytes()
        total+=len(content)
        if len(content)>40*1024*1024:large.append({'path':name,'bytes':len(content)})
        chunks=[content]
        if path.suffix=='.docx':
            from io import BytesIO
            with zipfile.ZipFile(BytesIO(content)) as archive:
                chunks.extend(archive.read(n) for n in archive.namelist() if n.endswith('.xml'))
        for chunk in chunks:
            if any(value in chunk for value in secrets):hits.append({'path':name,'kind':'known local credential value'})
            for label,pattern in patterns:
                if re.search(pattern,chunk):hits.append({'path':name,'kind':label})
    ignored=git('check-ignore','.env','backend/.env','.local/verification-account.json','.venv','frontend/node_modules','data/raw/online_retail_II.xlsx').decode().splitlines()
    reference=json.loads((ROOT/'backend/app/core/phase4-reference.json').read_text(encoding='utf-8'))
    frozen=json.loads((ROOT/'docs/research/results/frozen-selection.json').read_text(encoding='utf-8'))
    frozen_checks=[]
    for name,expected in (reference|frozen['source_fingerprints']).items():
        content=git('show',':'+name) if args.staged else (ROOT/name).read_bytes()
        frozen_checks.append({'path':name,'matches':hashlib.sha256(content).hexdigest()==expected})
    passed=not denied and not hits and not large and len(ignored)==6 and all(x['matches'] for x in frozen_checks)
    report={'executed_at_utc':datetime.now(UTC).isoformat(),'mode':'staged' if args.staged else 'candidate','passed':passed,'files':len(names),'bytes':total,'denied_paths':denied,'credential_findings':hits,'large_files':large,'ignored_checks':ignored,'protected_hash_checks':frozen_checks,'limits':'Exact known local secret values and common token/key signatures; not a universal secret-detection guarantee. Source tests use synthetic dummy passwords only. No secret values printed.'}
    (ROOT/f'docs/test-results/publication-repository-{report["mode"]}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'{report["mode"]}: {len(names)}files, {total}bytes; denied_paths={len(denied)}, credential_findings={len(hits)}, large_files={len(large)}, protected_hashes={len(frozen_checks)}; passed={passed}')
    assert passed,'Repository review failed; inspect finding paths without printing secrets'

if __name__=='__main__':main()
