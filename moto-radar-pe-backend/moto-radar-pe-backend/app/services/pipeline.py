"""Orquestra: scraper -> FIPE -> oportunidade -> banco."""
import logging
from sqlalchemy.orm import Session
from ..config import MODELS
from ..models import Moto
from . import scraper, fipe, cache, opportunity as opp

log = logging.getLogger("radar")

def rodar(db: Session, termos: list[str] | None = None) -> int:
    novos = 0
    for termo in termos or list(MODELS):
        marca, liq = MODELS[termo]
        try:
            anuncios = scraper.buscar(termo)
        except Exception as e:
            log.error("scraper falhou para %s: %s", termo, e); continue
        for a in anuncios:
            if not (a["preco"] and a["ano"]):
                continue
            f = fipe.consultar(marca, termo, a["ano"])
            if not f:
                continue
            d = opp.desconto(f["valor_fipe"], a["preco"])
            if opp.classificar(d) is None:
                continue  # só guarda desconto > 10%
            l, _ = opp.lucro(f["valor_fipe"], a["preco"])
            s = opp.score(d, liq, a["titulo"])
            m = db.query(Moto).filter_by(url=a["url"]).first() or Moto(url=a["url"])
            m.modelo, m.marca, m.ano, m.preco = f["modelo"], marca, a["ano"], a["preco"]
            m.cidade, m.km, m.fotos = a["cidade"], a["km"], ",".join(a["fotos"])
            m.descricao = a["titulo"]
            m.valor_fipe, m.desconto, m.lucro_estimado, m.score = f["valor_fipe"], round(d, 1), round(l, 2), s
            m.classificacao = opp.rotulo(s)
            if m.id is None: db.add(m); novos += 1
        db.commit()
    cache.invalidate()  # dados novos: descarta dashboard/oportunidades em cache
    log.info("ciclo concluído: %d novos", novos)
    return novos
