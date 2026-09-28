"""Cliente FIPE (API pública parallelum v2) com cache Redis."""
import re
import httpx
from . import cache
from ..config import settings

BASE = "https://fipe.parallelum.com.br/api/v2/motorcycles"

def _get(path: str):
    """GET com cache Redis (a FIPE é lenta e tem limite de requisições)."""
    key = f"fipe:{path}"
    hit = cache.get_json(key)
    if hit is not None:
        return hit
    r = httpx.get(f"{BASE}{path}", timeout=20)
    r.raise_for_status()
    data = r.json()
    cache.set_json(key, data, settings.fipe_ttl)
    return data

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower())

def consultar(marca: str, modelo: str, ano: int) -> dict | None:
    """Retorna {marca, modelo, ano, valor_fipe} ou None se não achar."""
    try:
        brand = next(b for b in _get("/brands") if _norm(b["name"]) == _norm(marca))
        alvo = _norm(modelo)
        models = [m for m in _get(f"/brands/{brand['code']}/models") if alvo in _norm(m["name"])]
        for m in models:  # tenta cada variante até achar o ano
            anos = _get(f"/brands/{brand['code']}/models/{m['code']}/years")
            y = next((a for a in anos if a["name"].startswith(str(ano))), None)
            if y:
                d = _get(f"/brands/{brand['code']}/models/{m['code']}/years/{y['code']}")
                valor = float(re.sub(r"[^\d,]", "", d["price"]).replace(",", "."))
                return {"marca": marca, "modelo": d["model"], "ano": ano, "valor_fipe": valor}
    except Exception:
        return None
    return None
