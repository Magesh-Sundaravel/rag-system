from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from src import security
from src.db import Base, engine, get_db
from src.models import RevokedToken, User
from src.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="auth-service", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    user = User(email=body.email, hashed_password=security.hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not security.verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenPair(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
    )


@app.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    claims = _decode_refresh(body.refresh_token)
    if db.get(RevokedToken, claims["jti"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token revoked")
    return TokenPair(
        access_token=security.create_access_token(claims["sub"]),
        refresh_token=security.create_refresh_token(claims["sub"]),
    )


@app.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)) -> None:
    claims = _decode_refresh(body.refresh_token)
    if not db.get(RevokedToken, claims["jti"]):
        db.add(
            RevokedToken(
                jti=claims["jti"],
                expires_at=datetime.fromtimestamp(claims["exp"], UTC),
            )
        )
        db.commit()


def _decode_refresh(token: str) -> dict:
    try:
        claims = security.decode_token(token)
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc
    if claims.get("type") != security.REFRESH:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    return claims
