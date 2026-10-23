"""Akceptační test C-029 — App\\Jadro\\Sitemapa (sitemap.xml a robots.txt).

Sitemapa se dřív zapsala jednou při instalaci ze souborů v data/. Jakmile
klient přidal realizaci v administraci, vznikla nová stránka, o které sitemapa
nevěděla — a nikdo ji nepřepíše, protože ten nástroj se pouští z příkazové
řádky. Proto sitemapu teď skládá tahle třída z TÉHOŽ seznamu adres, jaký web
umí poslat, a index.php ji vydává přímo.

Pravidlo brány:
- V sitemapě je každá adresa, kterou web umí poslat, kromě chybové stránky
  a administrace. Zaznamenaný stav: 139 adres celkem, z toho 4 vynechané
  (404 ve třech jazycích a administrace.html) → 135 v sitemapě.
- Realizace, která je jen ve stavu z administrace (v data/ není), musí být
  v sitemapě taky — to je celý důvod téhle třídy.
- Adresy jsou absolutní, bez duplikátů, XML se dá přečíst.
- robots.txt nepouští roboty do administrace ani do API a ukazuje na sitemapu.
"""
from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
DOMENA = "https://www.greenairtech.cz"
DNES = "2026-10-23"

CELKEM_ADRES = 139          # php tools/vykresli.php --seznam
MIMO = 4                    # 404.html, en/404.html, de/404.html, administrace.html
V_SITEMAPE = CELKEM_ADRES - MIMO

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Sitemapa;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$site = $zdroj->site();

/* Realizace přidaná v administraci: v data/ není, ve stavu ano. */
$sStavem = $site;
$sStavem['realizace'][] = [
    'id' => 'zkouska-ze-stavu',
    'vetev' => 'firmy',
    'rok' => 2026,
];

echo json_encode([
    'seznam' => Stranka::seznam($site),
    'xml' => Sitemapa::xml($site, '{DOMENA}', '{DNES}'),
    'xml_se_stavem' => Sitemapa::xml($sStavem, '{DOMENA}', '{DNES}'),
    'robots' => Sitemapa::robots('{DOMENA}'),
    'lomitko' => Sitemapa::xml($site, '{DOMENA}/', '{DNES}'),
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    program = tmp_path_factory.mktemp("sitemapa") / "program.php"
    program.write_text(
        PROGRAM.lstrip().replace("{KOREN}", str(KOREN))
        .replace("{DOMENA}", DOMENA).replace("{DNES}", DNES), "utf8")
    hotovo = subprocess.run(
        ["php", str(program)], capture_output=True, text=True, timeout=120)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def adresy(xml: str) -> list[str]:
    koren = ET.fromstring(xml)
    return [u.findtext("s:loc", "", NS) for u in koren.findall("s:url", NS)]


def test_xml_se_da_precist_a_ma_spravny_koren(v):
    koren = ET.fromstring(v["xml"])
    assert koren.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"


def test_v_sitemape_je_kazda_stranka_webu(v):
    cesty = {a.removeprefix(DOMENA + "/") for a in adresy(v["xml"])}
    cekane = {c for c in v["seznam"]
              if not c.endswith("404.html") and not c.endswith("administrace.html")}
    assert len(v["seznam"]) == CELKEM_ADRES, \
        f"web umí {len(v['seznam'])} adres, zaznamenáno bylo {CELKEM_ADRES}"
    assert cesty == cekane, f"chybí: {sorted(cekane - cesty)}, přebývá: {sorted(cesty - cekane)}"
    assert len(cesty) == V_SITEMAPE, f"v sitemapě je {len(cesty)} adres místo {V_SITEMAPE}"


def test_chybova_stranka_a_administrace_v_sitemape_nejsou(v):
    cesty = [a.removeprefix(DOMENA + "/") for a in adresy(v["xml"])]
    assert "index.html" in cesty
    for nema in ("404.html", "en/404.html", "de/404.html", "administrace.html"):
        assert nema not in cesty, nema


def test_realizace_pridana_v_administraci_je_v_sitemape(v):
    cesty = [a.removeprefix(DOMENA + "/") for a in adresy(v["xml_se_stavem"])]
    for jazyk in ("", "en/", "de/"):
        assert f"{jazyk}realizace-zkouska-ze-stavu.html" in cesty, \
            f"realizace ze stavu chybí v jazyce '{jazyk or 'cs'}'"
    assert len(cesty) == V_SITEMAPE + 3


def test_adresy_jsou_absolutni_a_jen_jednou(v):
    a = adresy(v["xml"])
    assert all(x.startswith(DOMENA + "/") for x in a), "relativní adresa v sitemapě"
    assert len(a) == len(set(a)), "některá adresa je v sitemapě dvakrát"


def test_lomitko_na_konci_domeny_se_nezdvoji(v):
    assert adresy(v["lomitko"]) == adresy(v["xml"])


def test_datum_zmeny_je_to_zadane(v):
    koren = ET.fromstring(v["xml"])
    datumy = {u.findtext("s:lastmod", "", NS) for u in koren.findall("s:url", NS)}
    assert datumy == {DNES}, datumy


def test_robots_pusti_roboty_na_web_ale_ne_do_administrace(v):
    r = v["robots"]
    assert "User-agent: *" in r
    assert "Allow: /" in r
    assert "Disallow: /administrace.html" in r
    assert "Disallow: /api/" in r
    assert f"Sitemap: {DOMENA}/sitemap.xml" in r
    assert "Disallow: /\n" not in r, "tohle by zakázalo celý web"
