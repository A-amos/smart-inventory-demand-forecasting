from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(Settings().database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session
