from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import token_digest
from app.database import get_db
from app.models import AuthSession
from app.schemas import LoginRequest, LoginResponse, UserRead
from app.services.auth import authenticate, resolve_session

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)):
    user = resolve_session(db, credentials.credentials) if credentials else None
    if not user:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return user


def manager_user(user=Depends(current_user)):
    if user.role != 'manager':
        raise HTTPException(403, 'Manager authorization required')
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    result = authenticate(db, payload.email, payload.password, request.app.state.settings.session_ttl_minutes)
    if not result:
        raise HTTPException(401, "Invalid credentials or account unavailable")
    token, user = result
    response.headers["Cache-Control"] = "no-store"
    return LoginResponse(access_token=token, expires_in=request.app.state.settings.session_ttl_minutes * 60,
                         user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user=Depends(current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(user=Depends(current_user), credentials=Depends(bearer), db: Session = Depends(get_db)):
    session = db.get(AuthSession, token_digest(credentials.credentials))
    db.delete(session)
    db.commit()
