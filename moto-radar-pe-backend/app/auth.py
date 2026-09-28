"""Autenticação JWT (HS256) + senhas com bcrypt."""
import datetime as dt
import bcrypt, jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/auth", tags=["auth"])

def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode()[:72], bcrypt.gensalt()).decode()  # bcrypt limita a 72 bytes

def check_pw(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode()[:72], h.encode())

def make_token(sub: str) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {"sub": sub, "iat": now, "exp": now + dt.timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode(token: str) -> str:
    """Retorna o e-mail do token ou levanta jwt.PyJWTError (expirado/inválido)."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})["sub"]

def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> User | None:
    if not settings.require_auth:
        return None  # modo pessoal (REQUIRE_AUTH=false): app sem tela de login
    err = HTTPException(401, "Não autenticado", headers={"WWW-Authenticate": "Bearer"})
    if not cred:
        raise err
    try:
        email = decode(cred.credentials)
    except jwt.PyJWTError:
        raise err
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise err
    return user

class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=72)

def _token_out(email: str) -> dict:
    return {"access_token": make_token(email), "token_type": "bearer"}

@router.post("/register", status_code=201)
def register(body: Credentials, db: Session = Depends(get_db)):
    if not settings.allow_registration:
        raise HTTPException(403, "Cadastro desabilitado")
    email = body.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "E-mail já cadastrado")
    db.add(User(email=email, password_hash=hash_pw(body.password)))
    db.commit()
    return _token_out(email)

@router.post("/login")
def login(body: Credentials, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter_by(email=email).first()
    if not user or not check_pw(body.password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")  # mesma msg p/ ambos os casos
    return _token_out(email)
