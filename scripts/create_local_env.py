"""Create a local environment once; never overwrite existing credentials."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
destination = root / '.env'
if destination.exists():
    raise SystemExit('Existing .env preserved; no changes made')
password = secrets.token_hex(24)
root_password = secrets.token_hex(24)
destination.write_text(
    'MYSQL_DATABASE=smart_inventory\nMYSQL_USER=smart_inventory\n'
    f'MYSQL_PASSWORD={password}\nMYSQL_ROOT_PASSWORD={root_password}\n'
    f'DATABASE_URL=mysql+pymysql://smart_inventory:{password}@localhost:3306/smart_inventory\n'
    'CORS_ORIGINS=["http://localhost:5173"]\nSESSION_TTL_MINUTES=480\n',
    encoding='utf-8',
)
print('Created ignored local environment with generated credentials; values omitted')
