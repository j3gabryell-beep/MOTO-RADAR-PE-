import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import APIRouter, FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from .config import settings, MODELS
from .db import Base, engine, get_db, SessionLocal
from .models import Moto
from .services import pipeline, cache
from .auth import router as auth_router, current_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

def _job():
    with SessionLocal() as db:
        pipeline.rodar(db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.require_auth and settings.jwt_secret == "change-me":
        raise RuntimeError("Defina JWT_SECRET ou use REQUIRE_AUTH=false")
    Base.metadata.create_all(engine)
    sch = BackgroundScheduler()
    sch.add_job(_job, "interval", minutes=settings.refresh_minutes)  # atualização automática
    sch.start()
    yield
    sch.shutdown()

app = FastAPI(title="Moto Radar PE", lifespan=lifespan)
# CORS liberado geral: a API é só leitura pública (sem auth no modo pessoal) e
# precisa ser chamada do navegador (zapp.run, Flutter Web) em outro domínio.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
api = APIRouter(dependencies=[Depends(current_user)])  # tudo aqui exige JWT

def _dict(m: Moto):
    return {c.name: getattr(m, c.name) for c in m.__table__.columns}

@api.get("/motos")
def motos(db: Session = Depends(get_db), modelo: str | None = None, cidade: str | None = None,
          ano: int | None = None, km_max: int | None = None, preco_min: float | None = None,
          preco_max: float | None = None, desconto_min: float | None = None, score_min: int | None = None):
    q = db.query(Moto)
    if modelo: q = q.filter(Moto.modelo.ilike(f"%{modelo}%"))
    if cidade: q = q.filter(Moto.cidade.ilike(f"%{cidade}%"))
    if ano: q = q.filter(Moto.ano == ano)
    if km_max: q = q.filter(Moto.km <= km_max)
    if preco_min: q = q.filter(Moto.preco >= preco_min)
    if preco_max: q = q.filter(Moto.preco <= preco_max)
    if desconto_min: q = q.filter(Moto.desconto >= desconto_min)
    if score_min: q = q.filter(Moto.score >= score_min)
    return [_dict(m) for m in q.order_by(Moto.score.desc()).limit(200)]

@api.get("/oportunidades")
@cache.cached("oportunidades")
def oportunidades(db: Session = Depends(get_db)):
    q = db.query(Moto).filter(Moto.desconto > 10, Moto.desconto <= 30).order_by(Moto.score.desc()).limit(50)
    return [_dict(m) for m in q]

@api.get("/motos/{moto_id}")
def moto(moto_id: int, db: Session = Depends(get_db)):
    m = db.get(Moto, moto_id)
    if not m: raise HTTPException(404, "Moto não encontrada")
    return _dict(m)

@api.post("/buscar")
def buscar(bg: BackgroundTasks, modelo: str | None = Query(None, description=f"Um de: {list(MODELS)}")):
    if modelo and modelo not in MODELS: raise HTTPException(400, "Modelo não monitorado")
    def run():
        with SessionLocal() as db:
            pipeline.rodar(db, [modelo] if modelo else None)
    bg.add_task(run)
    return {"status": "busca iniciada"}

@api.get("/dashboard")
@cache.cached("dashboard")
def dashboard(db: Session = Depends(get_db)):
    base = db.query(Moto).filter(Moto.desconto > 10)
    top = base.order_by(Moto.score.desc()).limit(20).all()
    return {
        "quantidade": base.count(),
        "media_desconto": round(db.query(func.avg(Moto.desconto)).filter(Moto.desconto > 10).scalar() or 0, 1),
        "maior_desconto": _dict(base.order_by(Moto.desconto.desc()).first()) if top else None,
        "maior_lucro": _dict(base.order_by(Moto.lucro_estimado.desc()).first()) if top else None,
        "top20": [_dict(m) for m in top],
    }


@app.get("/health")
def health():
    return {"status": "ok"}

# Painel web simples (dashboard + oportunidades) servido direto pela própria API,
# assim as chamadas fetch() são same-origin e não dependem de CORS.
_STATIC_DIR = Path(__file__).parent / "static"

@app.get("/")
def painel():
    return FileResponse(_STATIC_DIR / "index.html")

app.include_router(auth_router)
app.include_router(api)
