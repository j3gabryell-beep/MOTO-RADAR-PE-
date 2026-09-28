import jwt, pytest
from app import auth
from app.config import settings
from app.services import cache

def test_senha_e_token():
    h = auth.hash_pw("segredo123")
    assert auth.check_pw("segredo123", h) and not auth.check_pw("errada", h)
    assert auth.decode(auth.make_token("a@b.com")) == "a@b.com"

def test_token_expirado_e_adulterado(monkeypatch):
    monkeypatch.setattr(settings, "jwt_expire_minutes", -1)
    with pytest.raises(jwt.PyJWTError):
        auth.decode(auth.make_token("a@b.com"))
    monkeypatch.setattr(settings, "jwt_expire_minutes", 5)
    t = auth.make_token("a@b.com")
    monkeypatch.setattr(settings, "jwt_secret", "outra")
    with pytest.raises(jwt.PyJWTError):
        auth.decode(t)

def test_cached_chama_funcao_uma_vez(monkeypatch):
    store, calls = {}, []
    monkeypatch.setattr(cache, "get_json", lambda k: store.get(k))
    monkeypatch.setattr(cache, "set_json", lambda k, v, ttl=None: store.__setitem__(k, v))
    @cache.cached("x")
    def f():
        calls.append(1); return [1]
    assert f() == [1] and f() == [1] and len(calls) == 1
