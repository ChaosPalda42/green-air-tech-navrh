"""Akceptační test C-034 — výřez portrétu v kolečku týmu.

Zadání (12. 11. 2026). Klient si stěžoval na ořez dvou portrétů. Změřilo se,
že v předlohách, které jsme od něj dostali, sedí hlava tak nízko, že brada je
pod spodní hranou snímku (obrysová čára obličeje končí na 108 % a 110 % výšky;
zbytek týmu má bradu na 70–83 %). Ořezem souboru se to spravit nedá, a i kdyby
se nová fotka objevila, je nesmysl kvůli posunu o pár procent volat vývojáře.
Proto se výřez stal nastavitelným: `lide[].vyrez` v datech, v administraci
posuvník s náhledem v živé velikosti.

Co se tu měří a proč takhle:
  * Pravidlo o hodnotách (přiblížení 100–250 %, posun omezený přiblížením,
    celá procenta) je v ZAZNAMENANÝCH vzorcích z ukázky — PHP se srovnává
    s nimi, ne samo se sebou (tests/orakulum/cms-store.json).
  * Výřez musí dojít až do VYKRESLENÉ stránky a do CSS; proto se čte výsledné
    HTML a styl, ne to, že se někde volá správná funkce. Hodnota v atributu
    bez pravidla v CSS neudělá nic a naopak.
  * Hranice vstupu: stav s portréty musí projít mezemi API a nesmyslné
    hodnoty se musí zarazit, jinak si kdokoli s právem psát texty nafoukne
    stránku vlastním polem.

Zaznamenaný vzorek (tento stroj, PHP 8.5.10, 12. 11. 2026):
  PŘED: v 139 vykreslených stránkách 0 portrétů s výřezem; CSS vlastnost
        --vz/--vx/--vy nepoužívalo; stav s klíčem 'portrety' API odmítlo
        (chyba 'nezname-pole').
  PO:   dva portréty nesou style="--vz:1.15;--vx:0%;--vy:0%", CSS je čte
        v transformu portrétu, stav s portréty projde a výřez mimo mez se
        zkrátí na mez.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

KOREN = Path(__file__).resolve().parents[1]
JMENO = "cms-store"
MOJE = {"normalizeVyrez", "jeVychoziVyrez", "stylVyrezu", "setVyrez", "getVyrez", "mergeVyrezy"}

# Komu se výřez nastavil v datech (oba portréty s odříznutou bradou).
S_VYREZEM = {"radek-tyla", "zdenek-bauska"}


def php(program: str) -> str:
    hotovo = subprocess.run(
        ["php", "-r", program.replace("{KOREN}", str(KOREN))],
        capture_output=True, text=True, cwd=KOREN,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return hotovo.stdout


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


@pytest.fixture(scope="module")
def stranka_tymu() -> str:
    """Kontaktní stránka vykreslená PHP verzí — tam jsou karty lidí."""
    return php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Jadro\Config;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;
Config::nastav(['web' => 'https://www.greenairtech.cz']);
$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
echo Stranka::html('kontakt.html', $zdroj, false);
""")


# ------------------------------------------------------------ pravidlo hodnot

def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    chybi = MOJE - set(ocek)
    assert not chybi, f"orákulum nezná {sorted(chybi)}"
    for funkce in sorted(MOJE):
        assert ocek[funkce], f"{funkce}: žádné vzorky"


def test_orakulum_hlida_mez_posunu_i_pulky():
    """Bez těchhle vzorků je brána slepá na to, na čem to padá: posun se musí
    zkrátit podle přiblížení a půlky se musí zaokrouhlovat jako v JS."""
    vst = ocekavane(JMENO)
    assert {"zoom": 100, "x": 0, "y": 0} in vst["normalizeVyrez"], \
        "chybí vzorek, kde se posun bez přiblížení zahodí"
    assert {"zoom": 120, "x": 10, "y": -10} in vst["normalizeVyrez"], \
        "chybí vzorek, kde se posun zkrátí na mez"
    assert {"zoom": 161, "x": -11, "y": 12} in vst["normalizeVyrez"], \
        "chybí vzorek s půlkou (Math.round v JS zaokrouhluje -11.5 na -11)"
    assert "" in vst["stylVyrezu"], "chybí vzorek, kde výchozí výřez nepíše nic"
    assert "--vz:1.15;--vx:0%;--vy:0%" in vst["stylVyrezu"], \
        "chybí vzorek s dvěma desetinnými místy u přiblížení"


def test_php_se_chova_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky, jen=MOJE)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_vstup_se_nemeni(vysledky):
    druhy = z_php(JMENO)
    moje = {f: v for f, v in vysledky.items() if f in MOJE}
    assert moje == {f: v for f, v in druhy.items() if f in MOJE}, \
        "druhý běh dal jiné výsledky — nějaká metoda mutuje vstup"


# ------------------------------------------------------- výřez v datech a HTML

def test_vyrez_je_v_obou_stromech_dat():
    """Data ukázky a ostrého webu se nesmí rozejít, jinak padne bajtová shoda."""
    for strom in ("data/site.json", "web/data/site.json"):
        site = json.loads((KOREN / strom).read_text("utf8"))
        nalezene = {
            o["id"] for o in site["lide"]
            if isinstance(o.get("vyrez"), dict) and o["vyrez"].get("zoom", 100) != 100
        }
        assert nalezene == S_VYREZEM, f"{strom}: výřez má {sorted(nalezene)}"


def test_vykreslena_karta_nese_vyrez(stranka_tymu):
    """Měří se vykreslená stránka: co prohlížeč dostane, ne co se volá."""
    ocekavany = php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
echo App\Obsah\StavVyrezu::styl(['zoom' => 115, 'x' => 0, 'y' => 0]);
""").strip()
    assert ocekavany != "", "StavVyrezu::styl nic nevrátil"

    karty = re.findall(r'<img[^>]*class="portret"[^>]*>', stranka_tymu)
    assert len(karty) >= 7, f"na stránce je jen {len(karty)} portrétů"
    se_stylem = [k for k in karty if "style=" in k]
    assert len(se_stylem) == len(S_VYREZEM), \
        f"styl má {len(se_stylem)} portrétů, čekáme {len(S_VYREZEM)}"
    for img in se_stylem:
        assert f'style="{ocekavany}"' in img, f"jiný styl: {img[:160]}"
    for id_osoby in S_VYREZEM:
        assert any(f"portret-{id_osoby}" in k and "style=" in k for k in karty), \
            f"{id_osoby} výřez nedostal"


def test_portret_bez_vyrezu_zadny_styl_nedostane(stranka_tymu):
    """Výchozí výřez nesmí do HTML připsat nic — jinak se rozejdou bajty."""
    for img in re.findall(r'<img[^>]*class="portret"[^>]*>', stranka_tymu):
        if any(f"portret-{i}" in img for i in S_VYREZEM):
            continue
        assert "style=" not in img, f"portrét bez výřezu má styl: {img[:160]}"


def test_css_vyrez_opravdu_pouziva():
    """Hodnota v atributu bez pravidla v CSS je k ničemu."""
    css = (KOREN / "src" / "assets" / "style.css").read_text("utf8")
    pravidla = [r for r in css.split("}") if ".portret" in r and "transform:" in r]
    assert pravidla, "v CSS není pravidlo s transformem portrétu"
    cte_zoom = [r for r in pravidla if "var(--vz" in r]
    cte_posun = [r for r in pravidla if "var(--vx" in r and "var(--vy" in r]
    assert cte_zoom, "transform portrétu nečte přiblížení --vz"
    assert cte_posun, "transform portrétu nečte posun --vx/--vy"


def test_vsechny_stavy_portretu_cte_stejne_vlastnosti():
    """Klidový i odkrytý stav portrétu musí výřez držet — jinak fotka při
    přejetí myší poskočí na nenastavený výřez."""
    css = (KOREN / "src" / "assets" / "style.css").read_text("utf8")
    with_transform = [
        r for r in css.split("}")
        if ".portret" in r and re.search(r"transform:\s*[^;]*scale", r)
    ]
    assert len(with_transform) >= 2, "čekáme klidový i odkrytý stav portrétu"
    bez = [r for r in with_transform if "var(--vz" not in r]
    assert not bez, f"{len(bez)} stavů portrétu výřez ignoruje"


# ------------------------------------------------------------- hranice vstupu

def test_stav_s_portrety_projde_mezemi():
    vystup = php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Obsah\Meze;
$stav = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []],
         'portrety' => ['radek-tyla' => ['zoom' => 160, 'x' => -12, 'y' => -20]], 'updatedAt' => null];
echo json_encode(Meze::stav($stav, []));
""")
    assert json.loads(vystup)["ok"] is True, f"meze stav s portréty odmítly: {vystup}"


@pytest.mark.parametrize("portrety, proc", [
    ('["seznam"]', "portréty nejsou seznam"),
    ('["x" => ["zoom" => 160, "x" => 0, "y" => 0, "navic" => 1]]', "neznámé pole výřezu"),
    ('["x" => ["zoom" => "velký", "x" => 0, "y" => 0]]', "přiblížení není číslo"),
    ('["x" => ["zoom" => 900, "x" => 0, "y" => 0]]', "přiblížení nad mez"),
    ('["x" => ["zoom" => 160, "x" => 999, "y" => 0]]', "posun mimo mez"),
    ('["JE ŠPATNÉ id" => ["zoom" => 160, "x" => 0, "y" => 0]]', "id není id"),
])
def test_nesmyslny_vyrez_se_zarazi(portrety, proc):
    vystup = php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Obsah\Meze;
$stav = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []],
         'portrety' => PORTRETY, 'updatedAt' => null];
echo json_encode(Meze::stav($stav, []));
""".replace("PORTRETY", portrety))
    assert json.loads(vystup)["ok"] is False, f"prošlo, i když {proc}: {vystup}"


def test_moc_portretu_se_zarazi():
    vystup = php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Obsah\Meze;
$portrety = [];
for ($i = 0; $i < 200; $i++) {
    $portrety['clovek-' . $i] = ['zoom' => 150, 'x' => 0, 'y' => 0];
}
$stav = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []],
         'portrety' => $portrety, 'updatedAt' => null];
echo json_encode(Meze::stav($stav, []));
""")
    assert json.loads(vystup)["ok"] is False, f"dvě stě portrétů prošlo: {vystup}"


def test_zmena_vyrezu_je_oblast_textu():
    """Kdo smí přepisovat texty webu, smí i posunout fotku; autor novinek ne."""
    vystup = php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Api\Zmeny;
$stary = App\Obsah\Stav::prazdny();
$novy = App\Obsah\StavVyrezu::nastavVyrez($stary, 'radek-tyla', ['zoom' => 160, 'x' => 0, 'y' => -10]);
echo json_encode([
    'oblasti' => Zmeny::oblasti($stary, $novy),
    'spravce' => Zmeny::smiZmenit('spravce', $stary, $novy),
    'editor' => Zmeny::smiZmenit('editor', $stary, $novy),
    'autor' => Zmeny::smiZmenit('autor', $stary, $novy),
]);
""")
    v = json.loads(vystup)
    assert v["oblasti"] == ["texty"], f"oblasti změny: {v['oblasti']}"
    assert v["spravce"] is True and v["editor"] is True, "správce ani editor nesmí posunout fotku"
    assert v["autor"] is False, "autor novinek nesmí měnit portréty"


# --------------------------------------------------------------- administrace

@pytest.fixture(scope="module")
def administrace() -> str:
    return php(r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
use App\Jadro\Config;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;
Config::nastav(['web' => 'https://www.greenairtech.cz']);
$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
echo Stranka::html('administrace.html', $zdroj, false);
""")


def test_administrace_ma_ovladani_vyrezu(administrace):
    """Měří se vykreslená administrace: panel, posuvník a náhled v živé velikosti."""
    site = json.loads((KOREN / "web" / "data" / "site.json").read_text("utf8"))
    lide = [o["id"] for o in site["lide"]]
    assert 'data-panel="portrety"' in administrace, "administrace nemá panel portrétů"
    for id_osoby in lide:
        assert f'data-vyrez="{id_osoby}"' in administrace, f"chybí ovládání pro {id_osoby}"
    assert administrace.count("data-vyrez-zoom") >= len(lide), "chybí posuvník přiblížení"
    assert administrace.count("data-vyrez-nahled") >= len(lide), "chybí náhled v živé velikosti"
