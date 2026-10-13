from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.security import token_digest, verify_password
from app.models import AuthSession, Category, Inventory, Product, Sale, User, utc_now


def test_valid_login_and_protected_profile(environment, login):
    client, factory = environment
    response = client.get("/api/v1/auth/me", headers=login)
    assert response.status_code == 200
    assert response.json()["role"] == "manager"
    assert "password_hash" not in response.json()
    with factory() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password("test-password-123", user.password_hash)
        stored = db.scalar(select(AuthSession))
        assert stored.token_hash == token_digest(login["Authorization"].split()[1])


def test_wrong_and_unknown_credentials_have_same_safe_error(environment):
    client, _ = environment
    responses = [client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
                 for email in ["manager@example.com", "unknown@example.com"]]
    assert all(r.status_code == 401 for r in responses)
    assert responses[0].json() == responses[1].json()


def test_anonymous_request_rejected(environment):
    assert environment[0].get("/api/v1/auth/me").status_code == 401


def test_logout_revokes_session(environment, login):
    client, _ = environment
    assert client.post("/api/v1/auth/logout", headers=login).status_code == 204
    assert client.get("/api/v1/auth/me", headers=login).status_code == 401


def test_expired_session_rejected(environment, login):
    client, factory = environment
    with factory() as db:
        db.scalar(select(AuthSession)).expires_at = utc_now() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/v1/auth/me", headers=login).status_code == 401


def test_disabled_account_loses_existing_access(environment, login):
    client, factory = environment
    with factory() as db:
        db.scalar(select(User)).active = False
        db.commit()
    assert client.get("/api/v1/auth/me", headers=login).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "test-password-123"}).status_code == 401


def test_repeated_failures_lock_account(environment):
    client, factory = environment
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "test-password-123"}).status_code == 401
    with factory() as db:
        db.scalar(select(User)).locked_until = utc_now() - timedelta(seconds=1)
        db.commit()
    assert client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "test-password-123"}).status_code == 200


def test_login_validation(environment):
    client, _ = environment
    assert client.post("/api/v1/auth/login", json={"email": "a"}).status_code == 422
    assert client.post("/api/v1/auth/login", json={"email": "a@b", "password": "x", "role": "manager"}).status_code == 422


def test_sql_injection_does_not_authenticate(environment):
    client, _ = environment
    assert client.post("/api/v1/auth/login", json={"email": "' OR 1=1 --", "password": "wrong"}).status_code == 401


def test_readiness_and_liveness(environment):
    client, _ = environment
    assert client.get("/api/v1/health/live").json() == {"status": "ok"}
    assert client.get("/api/v1/health/ready").status_code == 200


def test_database_failure_is_safe(environment):
    client, _ = environment
    def broken():
        raise OperationalError("SELECT", {}, Exception("private connection details"))
    client.app.state.session_factory = broken
    result = client.get("/api/v1/health/ready")
    assert result.status_code == 503
    assert "private" not in result.text


def test_duplicate_email_rejected(environment):
    _, factory = environment
    with factory() as db:
        db.add(User(name="Other", email="manager@example.com", password_hash="hash"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_sales_require_real_product_and_positive_quantity(environment):
    _, factory = environment
    with factory() as db:
        db.add(Sale(product_id=9999, sale_date=utc_now(), quantity=1, unit_price=1))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        category = Category(name="Groceries")
        db.add(category); db.flush()
        product = Product(sku="SKU-1", name="Rice", category_id=category.id)
        db.add(product); db.flush()
        db.add(Sale(product_id=product.id, sale_date=utc_now(), quantity=-1, unit_price=1))
        with pytest.raises(IntegrityError):
            db.commit()


def test_inventory_allocations_cannot_exceed_on_hand(environment):
    _, factory = environment
    with factory() as db:
        category = Category(name="Food")
        db.add(category); db.flush()
        product = Product(sku="SKU-2", name="Flour", category_id=category.id)
        db.add(product); db.flush()
        db.add(Inventory(product_id=product.id, on_hand=1, allocated=2))
        with pytest.raises(IntegrityError):
            db.commit()


def test_cors_restricts_unknown_origins(environment):
    client, _ = environment
    response = client.options("/api/v1/auth/login", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
