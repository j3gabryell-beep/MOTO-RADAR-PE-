"""Motor de oportunidades e score. Funções puras: fáceis de testar."""
from ..config import LIQUIDEZ

POSITIVAS = ["urgente", "preciso vender", "baixei o preço", "revisada", "particular", "oportunidade", "negociável", "negociavel"]
NEGATIVAS = ["motor batendo", "sem documento", "não transfere", "nao transfere", "sinistro", "leilão", "leilao", "retificada", "problema mecânico", "problema mecanico"]
DOCS_RUINS = {"sem documento", "não transfere", "nao transfere", "leilão", "leilao", "sinistro"}

def desconto(fipe: float, preco: float) -> float:
    return (fipe - preco) / fipe * 100

def classificar(d: float) -> str | None:
    if d > 30: return "Suspeita"
    if d >= 20: return "Excelente"
    if d >= 15: return "Ótima"
    if d >= 10: return "Boa"
    return None  # abaixo de 10% não é oportunidade

def lucro(fipe: float, preco: float) -> tuple[float, float]:
    l = fipe * 0.95 - preco
    return l, (l / preco * 100 if preco else 0)

def score(d: float, liq_key: str, texto: str) -> int:
    t = (texto or "").lower()
    pts_desc = min(30.0, max(0.0, d) / 30 * 30) if d <= 30 else 10.0  # >30% é suspeito: pontua menos
    pts_liq = LIQUIDEZ.get(liq_key, 5) * 2.5
    estado = 15 + 3 * sum(w in t for w in POSITIVAS) - 6 * sum(w in t for w in NEGATIVAS)
    docs = 20 - 10 * sum(w in t for w in DOCS_RUINS)
    total = pts_desc + pts_liq + max(0, min(25, estado)) + max(0, min(20, docs))
    return int(round(max(0, min(100, total))))

def rotulo(s: int) -> str:
    return "COMPRA IMEDIATA" if s >= 85 else "BOA OPORTUNIDADE" if s >= 70 else "AVALIAR"
