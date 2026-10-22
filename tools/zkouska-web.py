#!/usr/bin/env python3
"""Živá zkouška ostrého webu přes HTTP: přihlášení, práva, API, poptávka.

Tiskne jen jména kontrol, stavové kódy a počty — nikdy obsah stránek ani
hesla. Pouští se proti zkušebnímu nasazení (Docker na localhostu).

    python3 tools/zkouska-web.py [adresa]
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]
ADRESA = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080").rstrip("/")
SEED = json.loads((KOREN / "nasazeni" / "seed-uzivatele.json").read_text("utf8"))["uzivatele"]
UCET = {u["role"]: u for u in SEED}

vysledky: list[tuple[str, bool, str]] = []


def kontrola(jmeno: str, podminka: bool, poznamka: str = "") -> None:
    vysledky.append((jmeno, bool(podminka), poznamka))


class Klient:
    """Jedno sezení v prohlížeči: drží cookie a umí poslat JSON i formulář."""

    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar()),
            BezPresmerovani(),
        )

    def posli(self, metoda: str, cesta: str, telo=None, hlavicky=None, syrove=None):
        url = cesta if cesta.startswith("http") else ADRESA + cesta
        data = None
        h = dict(hlavicky or {})
        if syrove is not None:
            data = syrove
        elif telo is not None:
            data = json.dumps(telo).encode()
            h.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=data, method=metoda, headers=h)
        try:
            with self.opener.open(req, timeout=20) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    def csrf(self) -> str:
        _, telo, _ = self.posli("GET", "/administrace.html")
        m = re.search(rb'name="csrf" value="([^"]+)"', telo)
        return m.group(1).decode() if m else ""

    def prihlas(self, role: str, heslo: str | None = None):
        u = UCET[role]
        token = self.csrf()
        telo = urllib.parse.urlencode({
            "akce": "prihlasit",
            "jmeno": u["jmeno"],
            "heslo": heslo if heslo is not None else u["heslo"],
            "csrf": token,
        }).encode()
        return self.posli(
            "POST", "/administrace.html", syrove=telo,
            hlavicky={"Content-Type": "application/x-www-form-urlencoded"},
        )


class BezPresmerovani(urllib.request.HTTPRedirectHandler):
    """Přesměrování chceme vidět, ne následovat."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


import urllib.parse  # noqa: E402  (až po definici, kvůli čitelnosti výše)


def jsonu(telo: bytes) -> dict:
    try:
        d = json.loads(telo)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main() -> int:
    host = Klient()

    stav, telo, _ = host.posli("GET", "/")
    kontrola("rozcestník odpovídá", stav == 200 and b"data-rozcestnik" in telo or stav == 200, f"HTTP {stav}")

    stav, telo, _ = host.posli("GET", "/administrace.html")
    kontrola("administrace je za přihlášením", stav == 200 and b'name="csrf"' in telo, f"HTTP {stav}")
    kontrola("nepřihlášenému se neposílá uživatel", b"window.GAT_UZIVATEL = null" in telo or b"GAT_UZIVATEL" not in telo)

    stav, _, h = host.prihlas("spravce", heslo="tohle-je-spatne")
    kontrola("špatné heslo neprojde", stav in (302, 303) and "chyba=1" in h.get("Location", ""), f"HTTP {stav}")

    stav, _, h = host.prihlas("spravce")
    kontrola("správce se přihlásí", stav in (302, 303) and "chyba" not in h.get("Location", ""), f"HTTP {stav}")

    stav, telo, _ = host.posli("GET", "/administrace.html")
    kontrola("přihlášený dostane svá data", stav == 200 and b'"role":"spravce"' in telo.replace(b" ", b""), f"HTTP {stav}")

    stav, telo, _ = host.posli("GET", "/api/stav")
    kontrola("API vydá stav přihlášenému", stav == 200 and "stav" in jsonu(telo), f"HTTP {stav}")

    novy = {"texts": {"cs": {"nav.sluzby": "Co děláme (zkouška)"}}, "realizace": {"added": [], "edited": {}, "removed": []}}
    stav, telo, _ = host.posli("PUT", "/api/stav", telo=novy)
    kontrola("zápis bez CSRF neprojde", stav == 403 and jsonu(telo).get("chyba") == "bez-csrf" or stav == 403, f"HTTP {stav}")

    token = host.csrf()
    stav, telo, _ = host.posli("PUT", "/api/stav", telo=novy, hlavicky={"X-CSRF": token})
    kontrola("zápis stavu s CSRF projde", stav == 200, f"HTTP {stav}")

    stav, telo, _ = Klient().posli("GET", "/domacnosti.html")
    kontrola("změna je vidět na veřejné stránce", stav == 200 and "Co děláme (zkouška)".encode() in telo, f"HTTP {stav}")

    # fotka: malý skutečný jpeg vyrobený v PHP leží v nasazeni/zkouska.jpg
    fotka = KOREN / "nasazeni" / "zkouska.jpg"
    if fotka.is_file():
        hranice = "----zkouska"
        telo_f = (
            f"--{hranice}\r\nContent-Disposition: form-data; name=\"fotka\"; filename=\"zkouska.jpg\"\r\n"
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode() + fotka.read_bytes() + f"\r\n--{hranice}--\r\n".encode()
        stav, telo, _ = host.posli(
            "POST", "/api/fotka", syrove=telo_f,
            hlavicky={"Content-Type": f"multipart/form-data; boundary={hranice}", "X-CSRF": token},
        )
        d = jsonu(telo)
        kontrola("fotka se nahraje a zmenší", stav == 200 and str(d.get("fotka", {}).get("soubor", "")).endswith(".webp"), f"HTTP {stav}")
        if stav == 200:
            s2, _, h2 = Klient().posli("GET", "/" + d["fotka"]["soubor"])
            kontrola("nahraná fotka se dá stáhnout", s2 == 200 and "image" in h2.get("Content-Type", ""), f"HTTP {s2}")
    else:
        kontrola("fotka se nahraje a zmenší", False, "chybí nasazeni/zkouska.jpg")

    stav, telo, _ = host.posli("GET", "/api/statistiky?dni=30")
    d = jsonu(telo)
    kontrola(
        "statistiky odpoví (nebo řeknou, že nejsou)",
        (stav == 200 and "dny" in d) or (stav == 503 and d.get("chyba") == "statistiky-nejsou"),
        f"HTTP {stav} {d.get('chyba', '')}",
    )

    verejny = Klient()
    stav, telo, _ = verejny.posli("POST", "/api/poptavka", telo={
        "jmeno": "Zkouška Nasazení", "email": "zkouska@greenairtech.test",
        "telefon": "+420 601 123 456", "typ": "vzt", "zprava": "Zkušební poptávka z testu nasazení.",
        "souhlas": True, "jazyk": "cs",
    })
    kontrola("poptávka projde", stav == 200 and jsonu(telo).get("ok") is True, f"HTTP {stav}")

    stav, telo, _ = verejny.posli("POST", "/api/poptavka", telo={"jmeno": "", "email": "neplatny", "souhlas": False})
    kontrola("vadná poptávka se odmítne s poli", stav == 422 and bool(jsonu(telo).get("chyby")), f"HTTP {stav}")
    # Hláska PHP v těle rozbije JSON i hlavičky a prozradí cesty na serveru.
    # Hlídá se počet nalezených stop, obsah odpovědi se netiskne.
    stopy = sum(1 for z in (b"<b>Warning", b"Fatal error", b"Stack trace", b"<br />") if z in telo)
    kontrola("odmítnutá poptávka neprozradí nic z PHP", stopy == 0, f"{stopy} stop po hlášení PHP")

    stav, telo, _ = verejny.posli("POST", "/api/poptavka", telo={
        "jmeno": "Robot", "email": "robot@example.com", "telefon": "+420601123456",
        "typ": "vzt", "zprava": "spam", "souhlas": True, "vebsajt": "http://spam",
    })
    kontrola("medová past spam spolkne", stav == 200, f"HTTP {stav}")

    editor = Klient()
    editor.prihlas("editor")
    stav, telo, _ = editor.posli("GET", "/api/uzivatele")
    kontrola("editor nesmí na uživatele", stav == 403 and jsonu(telo).get("chyba") == "nesmis", f"HTTP {stav}")
    stav, telo, _ = editor.posli("GET", "/api/statistiky?dni=30")
    kontrola("editor nesmí na statistiky", stav == 403, f"HTTP {stav}")

    autor = Klient()
    autor.prihlas("autor")
    t = autor.csrf()
    # Pozor: stav už v databázi JE, takže poslat ho znovu není změna textu a
    # právem by to prošlo. Autor proto musí poslat jinou hodnotu.
    autoruv = {"texts": {"cs": {"nav.sluzby": "Co děláme (autor)"}},
               "realizace": {"added": [], "edited": {}, "removed": []}}
    stav, telo, _ = autor.posli("PUT", "/api/stav", telo=autoruv, hlavicky={"X-CSRF": t})
    kontrola("autor nesmí přepsat texty", stav == 403, f"HTTP {stav}")

    # uklidit: stav zpátky na prázdno
    token = host.csrf()
    prazdny = {"texts": {}, "realizace": {"added": [], "edited": {}, "removed": []}}
    stav, _, _ = host.posli("PUT", "/api/stav", telo=prazdny, hlavicky={"X-CSRF": token})
    kontrola("stav se dá vrátit na prázdno", stav == 200, f"HTTP {stav}")

    odhlas = urllib.parse.urlencode({"akce": "odhlasit", "csrf": host.csrf()}).encode()
    stav, _, _ = host.posli("POST", "/administrace.html", syrove=odhlas,
                            hlavicky={"Content-Type": "application/x-www-form-urlencoded"})
    kontrola("odhlášení projde", stav in (302, 303), f"HTTP {stav}")
    stav, _, _ = host.posli("GET", "/api/stav")
    kontrola("po odhlášení API nevydá nic", stav == 401, f"HTTP {stav}")

    spatne = [v for v in vysledky if not v[1]]
    for jmeno, ok, pozn in vysledky:
        print(f"  {'ok     ' if ok else 'NESOUHLASÍ'} {jmeno}" + (f"  ({pozn})" if pozn and not ok else ""))
    print(f"\n{len(vysledky)} kontrol, {len(spatne)} špatně")
    return 1 if spatne else 0


if __name__ == "__main__":
    sys.exit(main())
