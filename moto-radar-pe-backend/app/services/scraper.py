"""Scraper OLX-PE (Playwright + BeautifulSoup).
ATENÇÃO: os seletores do HTML da OLX mudam com frequência; ajuste em _parse_cards.
Respeite os Termos de Uso/robots.txt da OLX e mantenha intervalos razoáveis."""
import re, urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def _num(s: str) -> int | None:
    d = re.sub(r"\D", "", s or "")
    return int(d) if d else None

def _parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for card in soup.select("section.olx-ad-card, li[data-ds-component='DS-AdCard']"):
        a = card.select_one("a[href]")
        title = card.select_one("h2")
        price = card.select_one("h3, [data-ds-component='DS-Text'][class*=price]")
        if not (a and title and price):
            continue
        txt = card.get_text(" ", strip=True)
        ano = re.search(r"\b(19|20)\d{2}\b", txt)
        km = re.search(r"([\d\.]+)\s*km", txt, re.I)
        out.append({
            "titulo": title.get_text(strip=True), "url": a["href"],
            "preco": _num(price.get_text()), "ano": int(ano.group()) if ano else None,
            "km": _num(km.group(1)) if km else None,
            "cidade": (card.select_one("[class*=location], [class*=Location]") or title).get_text(strip=True),
            "fotos": [i.get("src") for i in card.select("img") if i.get("src")][:5],
        })
    return out

def buscar(termo: str) -> list[dict]:
    url = f"https://www.olx.com.br/motos/estado-pe?q={urllib.parse.quote(termo)}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        html = page.content()
        browser.close()
    return _parse_cards(html)
