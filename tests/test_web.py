"""Akceptační testy hotového webu: sestavíme out/web a kontrolujeme, co z toho vyleze."""
from __future__ import annotations

import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "out" / "web"


@pytest.fixture(scope="session")
def web() -> Path:
    proc = subprocess.run(["node", "build.mjs"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, f"build.mjs selhal:\n{proc.stdout}\n{proc.stderr}"
    assert WEB.exists()
    return WEB


@pytest.fixture(scope="session")
def stranky(web: Path) -> list[Path]:
    return sorted(web.rglob("*.html"))


@pytest.fixture(scope="session")
def cs_obsah() -> dict:
    return json.loads((ROOT / "data" / "content" / "cs.json").read_text(encoding="utf-8"))


class SberacOdkazu(HTMLParser):
    """Posbírá href/src/srcset z HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.odkazy: list[str] = []
        self.zdroje: list[str] = []
        self.nadpisy1 = 0
        self.jazyk = ""
        self.titulek = ""
        self._v_titulku = False
        self.popis = ""
        self.viewport = ""
        self.abbr: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.odkazy.append(a["href"])
        if tag in ("img", "script", "source", "canvas") and a.get("src"):
            self.zdroje.append(a["src"])
        if tag == "link" and a.get("href") and a.get("rel") in ("stylesheet", "icon", "apple-touch-icon", "preload"):
            self.zdroje.append(a["href"])
        if tag in ("img", "source") and a.get("srcset"):
            for kus in a["srcset"].split(","):
                cast = kus.strip().split(" ")[0]
                if cast:
                    self.zdroje.append(cast)
        if tag == "h1":
            self.nadpisy1 += 1
        if tag == "html":
            self.jazyk = a.get("lang", "")
        if tag == "title":
            self._v_titulku = True
        if tag == "meta" and a.get("name") == "description":
            self.popis = a.get("content", "")
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = a.get("content", "")
        if tag == "abbr" and a.get("data-abbr"):
            self.abbr.append(a["data-abbr"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._v_titulku = False

    def handle_data(self, data):
        if self._v_titulku:
            self.titulek += data


def rozebrat(cesta: Path) -> SberacOdkazu:
    p = SberacOdkazu()
    p.feed(cesta.read_text(encoding="utf-8"))
    return p


# --------------------------------------------------------------- struktura


def test_ceska_verze_ma_vsechny_stranky(web):
    ocekavane = [
        "index.html", "sluzby.html", "realizace.html", "realizace-detail.html",
        "novinky.html", "o-nas.html", "kariera.html", "kontakt.html",
        "slovnik.html", "ochrana-osobnich-udaju.html", "404.html", "administrace.html",
    ]
    for jmeno in ocekavane:
        assert (web / jmeno).exists(), f"chybí {jmeno}"


def test_kazda_sluzba_ma_svou_stranku(web):
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    for s in site["sluzby"]:
        assert (web / f"sluzba-{s['id']}.html").exists()


def test_kazda_realizace_a_novinka_ma_svou_stranku(web):
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    for r in site["realizace"]:
        assert (web / f"realizace-{r['id']}.html").exists()
    for n in site["novinky"]:
        assert (web / f"novinka-{n['id']}.html").exists()


def test_administrace_je_jen_cesky(web):
    assert (web / "administrace.html").exists()
    assert not (web / "en" / "administrace.html").exists()


# ------------------------------------------------------------- odkazy a zdroje


def test_vsechny_vnitrni_odkazy_vedou_na_existujici_soubor(stranky, web):
    rozbite: list[str] = []
    for stranka in stranky:
        p = rozebrat(stranka)
        for odkaz in p.odkazy:
            if odkaz.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            cil = urlsplit(odkaz).path
            if not cil:
                continue
            if not (stranka.parent / cil).resolve().exists():
                rozbite.append(f"{stranka.relative_to(web)} -> {odkaz}")
    assert not rozbite, "rozbité odkazy:\n" + "\n".join(rozbite[:25])


def test_vsechny_zdroje_existuji(stranky, web):
    chybi: list[str] = []
    for stranka in stranky:
        p = rozebrat(stranka)
        for zdroj in p.zdroje:
            if zdroj.startswith(("http://", "https://", "data:")):
                continue
            if not (stranka.parent / urlsplit(zdroj).path).resolve().exists():
                chybi.append(f"{stranka.relative_to(web)} -> {zdroj}")
    assert not chybi, "chybějící soubory:\n" + "\n".join(chybi[:25])


def test_odkazy_jsou_relativni(stranky):
    """Web musí fungovat i z file:// a z podadresáře na GitHub Pages."""
    spatne = [
        f"{s.name}: {o}"
        for s in stranky
        for o in rozebrat(s).odkazy
        if o.startswith("/")
    ]
    assert not spatne, spatne[:10]


# ------------------------------------------------------------------ hlavička


def test_kazda_stranka_ma_titulek_popis_a_jazyk(stranky):
    for stranka in stranky:
        p = rozebrat(stranka)
        assert p.titulek.strip(), f"{stranka.name} bez <title>"
        assert len(p.popis) > 40, f"{stranka.name} má krátký popis"
        assert p.jazyk in ("cs", "en", "de"), f"{stranka.name}: lang={p.jazyk!r}"
        assert "width=device-width" in p.viewport, f"{stranka.name} bez viewportu"


def test_kazda_stranka_ma_prave_jeden_h1(stranky):
    spatne = [(s.name, rozebrat(s).nadpisy1) for s in stranky]
    assert all(n == 1 for _, n in spatne), [x for x in spatne if x[1] != 1]


def test_stranky_jsou_neindexovane(stranky, web):
    for stranka in stranky:
        html = stranka.read_text(encoding="utf-8")
        assert 'name="robots" content="noindex' in html, stranka.name
    assert "Disallow: /" in (web / "robots.txt").read_text(encoding="utf-8")


def test_kazda_stranka_ma_preskok_na_obsah(stranky):
    for stranka in stranky:
        html = stranka.read_text(encoding="utf-8")
        assert 'class="preskok" href="#obsah"' in html, stranka.name
        assert 'id="obsah"' in html, stranka.name


def test_kazda_stranka_ma_kontaktni_listu_i_paticku(stranky):
    for stranka in stranky:
        html = stranka.read_text(encoding="utf-8")
        assert 'class="spodni-lista"' in html, f"{stranka.name} bez mobilní kontaktní lišty"
        assert "tel:+420383809730" in html, f"{stranka.name} bez telefonu na dispečink"
        assert "<footer" in html, stranka.name


# -------------------------------------------------------------- obsah a kvalita


def test_v_html_nezustaly_nevyplnene_sablony(stranky):
    vzory = ["${", "[object Object]", "undefined<", ">undefined", "NaN", "Invalid Date"]
    nalezy = []
    for stranka in stranky:
        html = stranka.read_text(encoding="utf-8")
        for vzor in vzory:
            if vzor in html:
                nalezy.append(f"{stranka.name}: {vzor}")
    assert not nalezy, nalezy[:20]


def test_zadny_klic_neprosakl_misto_prekladu(stranky):
    """i18n.t vrací klíč, když překlad chybí — takový text se nesmí objevit."""
    vzor = re.compile(r">(?:home|sluzby|realizace|onas|novinky|kariera|kontakt|slovnik|ui|nav|footer|meta|admin)\.[a-zA-Z0-9_.-]+<")
    nalezy = [f"{s.name}: {m.group(0)}" for s in stranky for m in vzor.finditer(s.read_text(encoding='utf-8'))]
    assert not nalezy, nalezy[:20]


def test_uvodni_stranka_ukazuje_vsech_sedm_oboru(web, cs_obsah):
    html = (web / "index.html").read_text(encoding="utf-8")
    for klic, sluzba in cs_obsah["sluzby"]["polozky"].items():
        assert sluzba["nazev"] in html, f"na úvodu chybí služba {klic}"


def test_zkratky_jsou_obalene_a_maji_vysvetleni(web, cs_obsah):
    p = rozebrat(web / "index.html")
    assert p.abbr, "na úvodní stránce není obalená ani jedna zkratka"
    for zkratka in p.abbr:
        assert zkratka in cs_obsah["slovnik"]["terminy"], f"{zkratka} není ve slovníku"


def test_slovnik_obsahuje_vsechny_terminy(web, cs_obsah):
    html = (web / "slovnik.html").read_text(encoding="utf-8")
    for zkratka, popis in cs_obsah["slovnik"]["terminy"].items():
        assert f"<dt>{zkratka}</dt>" in html, f"slovník neobsahuje {zkratka}"
        assert popis["full"] in html


def test_slovnik_je_v_datech_pro_prohlizec(web, cs_obsah):
    html = (web / "index.html").read_text(encoding="utf-8")
    data = re.search(r"window\.GAT_SLOVNIK = (\{.*?\});", html, re.S)
    assert data, "chybí GAT_SLOVNIK"
    terminy = json.loads(data.group(1))["terminy"]
    assert set(terminy) == set(cs_obsah["slovnik"]["terminy"])


def test_kontaktni_formular_ma_vsechna_pole(web):
    html = (web / "kontakt.html").read_text(encoding="utf-8")
    for pole in ("jmeno", "email", "telefon", "typ", "zprava", "souhlas"):
        assert f'name="{pole}"' in html, f"formulář nemá pole {pole}"
    assert 'name="vebsajt"' in html, "chybí medová past proti robotům"


def test_obrazky_maji_rozmery_a_alternativni_text(stranky):
    vzor = re.compile(r"<img\b[^>]*>", re.S)
    problemy = []
    for stranka in stranky:
        for znacka in vzor.findall(stranka.read_text(encoding="utf-8")):
            if 'alt="' not in znacka:
                problemy.append(f"{stranka.name}: bez alt — {znacka[:80]}")
            if "width=" not in znacka or "height=" not in znacka:
                problemy.append(f"{stranka.name}: bez rozměrů — {znacka[:80]}")
    assert not problemy, problemy[:15]


def test_fotky_maji_webp_i_zalozni_variantu(web):
    html = (web / "index.html").read_text(encoding="utf-8")
    assert "foto-strojovna-960.webp" in html
    assert (web / "assets" / "img" / "foto-strojovna-960.webp").exists()
    assert (web / "assets" / "img" / "foto-strojovna-960.jpg").exists()


def test_logo_klienta_zustalo_zachovane(web, stranky):
    assert (web / "assets" / "img" / "logo.png").exists()
    for stranka in stranky:
        assert "img/logo.png" in stranka.read_text(encoding="utf-8"), stranka.name


# ------------------------------------------------------------- administrace


def test_administrace_nabizi_editovatelne_klice(web, cs_obsah):
    html = (web / "administrace.html").read_text(encoding="utf-8")
    data = re.search(r'<script type="application/json" data-admin-data>(.*?)</script>', html, re.S)
    assert data, "chybí data pro administraci"
    payload = json.loads(data.group(1))
    assert len(payload["klice"]) > 150, "editovatelných klíčů je podezřele málo"
    assert len(payload["realizace"]) == len(json.loads((ROOT / "data" / "site.json").read_text())["realizace"])
    assert "cs" in payload["slovniky"]
    for klic in payload["klice"]:
        assert klic in payload["slovniky"]["cs"], f"klíč {klic} chybí ve slovníku textů"


def test_administrace_umi_pridat_realizaci(web):
    html = (web / "administrace.html").read_text(encoding="utf-8")
    for pole in ("nazev", "misto", "datum", "perex", "rozsah", "technologie", "vysledek"):
        assert f'name="{pole}"' in html, f"formulář realizace nemá pole {pole}"


def test_editovatelne_klice_odpovidaji_datum(web, cs_obsah):
    """Každý data-cms klíč musí existovat v českém obsahu."""
    import sys

    sys.path.insert(0, str(ROOT / "tests"))
    from jsmod import run_js

    klice = sorted({m for s in WEB.rglob("*.html") for m in re.findall(r'data-cms="([^"]+)"', s.read_text(encoding="utf-8"))})
    plochy = run_js("i18n.mjs", "out(m.flatten(A.cs));", args={"cs": cs_obsah})
    chybi = [k for k in klice if k not in plochy]
    assert not chybi, chybi[:20]


# ------------------------------------------------------------------ skripty


def test_javascript_bezi_bez_modulu(web):
    """Bundle musí být klasický skript — jinak web z file:// nenaběhne."""
    app = (web / "assets" / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"^\s*import\s", app, re.M)
    assert not re.search(r"^\s*export\s", app, re.M)
    for modul in ("glossary", "i18n", "cmsStore", "formValidate", "realizaceFilter"):
        assert f"GAT.{modul} =" in app, f"v bundlu chybí {modul}"
    for stranka in WEB.rglob("*.html"):
        assert 'type="module"' not in stranka.read_text(encoding="utf-8"), stranka.name


def test_bundle_je_platny_javascript(web):
    proc = subprocess.run(
        ["node", "--check", str(web / "assets" / "app.js")], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    proc = subprocess.run(
        ["node", "--check", str(web / "assets" / "admin.js")], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr


def test_fonty_jsou_lokalni(stranky):
    for stranka in stranky:
        html = stranka.read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in html, stranka.name
        assert "fonts.gstatic.com" not in html, stranka.name
