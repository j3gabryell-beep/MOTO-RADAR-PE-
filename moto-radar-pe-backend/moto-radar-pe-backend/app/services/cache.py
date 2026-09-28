"""Cache Redis com degradação graciosa: se o Redis cair, a API continua (sem cache)."""
import functools, json, logging
import redis
from ..config import settings

log = logging.getLogger("radar.cache")
_client: redis.Redis | None = None
PREFIX = "radar:"

def _r() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True,
                                       socket_connect_timeout=1, socket_timeout=1)
    return _client

def get_json(key: str):
    try:
        v = _r().get(PREFIX + key)
        return json.loads(v) if v is not None else None
    except redis.RedisError as e:
        log.warning("redis indisponível (get): %s", e)
        return None

def set_json(key: str, value, ttl: int | None = None) -> None:
    try:
        _r().set(PREFIX + key, json.dumps(value, default=str), ex=ttl or settings.cache_ttl)
    except redis.RedisError as e:
        log.warning("redis indisponível (set): %s", e)

def invalidate(prefix: str = "views:") -> None:
    try:
        for k in _r().scan_iter(f"{PREFIX}{prefix}*"):
            _r().delete(k)
    except redis.RedisError as e:
        log.warning("redis indisponível (invalidate): %s", e)

def cached(name: str, ttl: int | None = None):
    """Decorator para endpoints sem parâmetros de filtro (ex.: dashboard)."""
    def deco(fn):
        @functools.wraps(fn)  # preserva a assinatura para o Depends do FastAPI
        def wrapper(*a, **kw):
            key = f"views:{name}"
            hit = get_json(key)
            if hit is not None:
                return hit
            res = fn(*a, **kw)
            set_json(key, res, ttl)
            return res
        return wrapper
    return deco
