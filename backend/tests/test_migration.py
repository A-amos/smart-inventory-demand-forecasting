from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.database import Base


def test_initial_migration_matches_metadata(tmp_path, monkeypatch):
    backend = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(backend)
    url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(backend / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
    command.check(config)
    engine.dispose()
