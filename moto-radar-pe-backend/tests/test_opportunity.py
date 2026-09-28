from app.services import opportunity as o

def test_desconto_e_classificacao():
    d = o.desconto(17200, 13900)
    assert round(d, 1) == 19.2 and o.classificar(d) == "Ótima"
    assert o.classificar(5) is None and o.classificar(35) == "Suspeita"

def test_lucro():
    l, roi = o.lucro(17200, 13900)
    assert round(l) == 2440 and round(roi, 1) == 17.6

def test_score_penaliza_texto_ruim():
    bom = o.score(19, "cg", "CG 160 revisada particular")
    ruim = o.score(19, "cg", "CG 160 sem documento sinistro")
    assert bom > ruim
