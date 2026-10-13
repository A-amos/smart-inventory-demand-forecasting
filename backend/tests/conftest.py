import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import create_app
from app.models import User


@pytest.fixture
def environment():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        db.add(User(name="Inventory Manager", email="manager@example.com", password_hash=hash_password("test-password-123")))
        db.commit()
    app = create_app()
    app.state.session_factory = factory
    def override_db():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, factory
    engine.dispose()


@pytest.fixture
def login(environment):
    client, _ = environment
    result = client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "test-password-123"})
    assert result.status_code == 200
    return {"Authorization": f"Bearer {result.json()['access_token']}"}
