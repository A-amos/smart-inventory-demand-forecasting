from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, new_token, token_digest, verify_password
from app.models import AuthSession, User, utc_now

# Equal password-verification work for unknown accounts reduces timing differences.
_dummy_hash = hash_password(new_token())


def authenticate(db: Session, email: str, password: str, ttl: int):
    user = db.scalar(select(User).where(User.email == email.strip().lower()).with_for_update())
    now = utc_now()
    verified = verify_password(password, user.password_hash if user else _dummy_hash)
    if not user or not user.active or (user.locked_until and user.locked_until > now):
        return None
    if not verified:
        user.failed_logins += 1
        if user.failed_logins >= 5:
            user.locked_until = now + timedelta(minutes=15)
            user.failed_logins = 0
        db.commit()
        return None
    user.failed_logins = 0
    user.locked_until = None
    token = new_token()
    db.add(AuthSession(token_hash=token_digest(token), user_id=user.id,
                       expires_at=now + timedelta(minutes=ttl)))
    db.commit()
    return token, user


def resolve_session(db: Session, token: str):
    session = db.get(AuthSession, token_digest(token))
    if not session or session.expires_at <= utc_now():
        return None
    user = db.get(User, session.user_id)
    return user if user and user.active else None
