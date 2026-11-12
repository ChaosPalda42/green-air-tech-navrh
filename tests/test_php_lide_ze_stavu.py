"""Akceptace: člověk přidaný v administraci se objeví na webu.

Tahle brána měří VYKRESLENOU stránku ostrého webu (ZdrojDb = soubory
přelepené stavem administrace), ne volání funkcí. Rozhoduje se tu trojí:

1. přidaný člověk je na stránce a odebraný na ní není,
2. nahraná fotka je jeden <img src="media/…"> — v manifestu obrázků není
   (ten vzniká při sestavení), takže z ní nejde udělat <picture> se
   srcsetem; kdyby to šablona zkusila, vykreslení skončí výjimkou,
3. role (klíč `lide.<id>`) u přidaného člověka ještě není přeložená —
   na stránce musí být prázdno, ne cesta klíče „lide.zofie-novakova".

Logiku stavu hlídá tests/test_php_stav_lidi.py, meze
tests/test_php_meze_lidi.py; tohle je ta stránka na konci.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
declare(strict_types=1);
require 'KOREN/web/app/Jadro/Autoload.php';

use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojDb;

$stav = json_decode(file_get_contents('STAV'), true);
$zdroj = new ZdrojDb('KOREN/web/data', 'KOREN/web/public/assets', $stav);
$kam = Odkazy::rozpoznej('CESTA', $zdroj->site());
echo Stranka::vykresli($kam, $zdroj, false, $zdroj, null);
"""

NOVA = {
    "id": "zofie-novakova",
    "jmeno": "Žofie Nováková",
    "telefon": "+420 777 111 222",
    "telefonHref": "+420777111222",
    "email": "zofie@greenairtech.cz",
    "inicialy": "ŽN",
    "fotka": "media/zofie-portret.webp",
}

STAV = {
    "texts": {},
    "realizace": {"added": [], "edited": {}, "removed": []},
    "portrety": {},
    "lide": {
        "added": [NOVA],
        "edited": {"radek-tyla": {"telefon": "+420 777 000 111", "telefonHref": "+420777000111"}},
        "removed": ["zdenek-bauska"],
    },
    "updatedAt": "2026-11-12T10:00:00.000Z",
}


def vykresli(tmp_path_factory, cesta: str, stav: dict) -> str:
    kam = tmp_path_factory.mktemp("stav") / "stav.json"
    kam.write_text(json.dumps(stav, ensure_ascii=False), "utf-8")
    program = (
        PROGRAM.replace("KOREN", str(KOREN))
        .replace("STAV", str(kam))
        .replace("CESTA", cesta)
    )
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True, cwd=KOREN)
    assert hotovo.returncode == 0, f"{cesta} se nevykreslila:\n{hotovo.stderr[-2000:]}"
    assert hotovo.stderr.strip() == "", f"{cesta}: PHP něco hlásí:\n{hotovo.stderr[-1500:]}"
    return hotovo.stdout


@pytest.fixture(scope="module")
def strany(tmp_path_factory):
    return {c: vykresli(tmp_path_factory, c, STAV) for c in ("kontakt.html", "o-nas.html")}


@pytest.fixture(scope="module")
def beze_zmen(tmp_path_factory):
    prazdny = {"texts": {}, "realizace": {"added": [], "edited": {}, "removed": []},
               "portrety": {}, "lide": {"added": [], "edited": {}, "removed": []},
               "updatedAt": None}
    return {c: vykresli(tmp_path_factory, c, prazdny) for c in ("kontakt.html", "o-nas.html")}


def test_stranky_se_vykreslily(strany, beze_zmen):
    """Kdyby šablona spadla, zbytek by měřil prázdno."""
    for c, html in list(strany.items()) + list(beze_zmen.items()):
        assert html.startswith("<!doctype html>"), f"{c}: nevykreslilo se"
        assert "karta-clovek" in html, f"{c}: na stránce není ani jedna karta člověka"


def test_pridany_clovek_je_na_strance(strany, beze_zmen):
    for c, html in strany.items():
        assert "Žofie Nováková" in html, f"{c}: přidaný člověk na stránce není"
        assert "zofie@greenairtech.cz" in html, f"{c}: chybí e-mail přidaného člověka"
        assert 'href="tel:+420777111222"' in html, f"{c}: chybí telefon přidaného člověka"
        assert html.count("karta-clovek") == beze_zmen[c].count("karta-clovek"), \
            f"{c}: jeden přidaný a jeden odebraný — počet karet má zůstat"


def test_odebrany_clovek_na_strance_neni(strany, beze_zmen):
    for c, html in strany.items():
        assert "Zdeněk Bauška" in beze_zmen[c], f"{c}: vzorek je slepý, ten člověk tam není ani bez změn"
        assert "Zdeněk Bauška" not in html, f"{c}: odebraný člověk je na stránce dál"


def test_zmeneny_telefon_se_projevi(strany, beze_zmen):
    for c, html in strany.items():
        assert 'href="tel:+420777000111"' in html, f"{c}: opravený telefon se nepropsal"


def test_nahrana_fotka_je_jeden_img(strany):
    """Nahraná fotka není v manifestu, takže varianty nemá — jen <img>."""
    for c, html in strany.items():
        nalez = re.findall(r"<img[^>]*media/zofie-portret\.webp[^>]*>", html)
        assert nalez, f"{c}: nahraná fotka se nevykreslila"
        for tag in nalez:
            assert "srcset" not in tag, f"{c}: nahraná fotka má srcset, ale varianty neexistují: {tag}"
            assert 'class="portret"' in tag, f"{c}: fotka přišla o třídu portret: {tag}"
        okoli = html[max(0, html.find(nalez[0]) - 120):html.find(nalez[0])]
        assert "<picture" not in okoli, f"{c}: nahraná fotka je zabalená v <picture>"


def test_nepreloena_role_zustane_prazdna(strany, beze_zmen):
    """I18n::t vrací při chybějícím klíči cestu klíče — ta na web nepatří."""
    for c, html in strany.items():
        assert "lide.zofie-novakova" not in html.replace('data-cms="lide.zofie-novakova"', ""), \
            f"{c}: na stránce svítí cesta klíče místo role"
        assert '<span class="role" data-cms="lide.zofie-novakova"></span>' in html, \
            f"{c}: role přidaného člověka není prázdná značka"
        assert '<span class="role" data-cms="lide.radek-tyla">' in html, \
            f"{c}: vzorek je slepý — role se nevykresluje vůbec"


# ------------------------------------------------------------- administrace
# Administrace se nediffuje bajt na bajt (tests/test_php_shoda_stranek.py ji
# vynechává), takže obě verze ovládání se měří tady — a vedle sebe, ať se
# nerozejdou.

@pytest.fixture(scope="module")
def administrace_php() -> str:
    program = r"""
require 'KOREN/web/app/Jadro/Autoload.php';
use App\Jadro\Config;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;
Config::nastav(['web' => 'https://www.greenairtech.cz']);
$zdroj = new ZdrojJson('KOREN/web/data', 'KOREN/web/public/assets');
echo Stranka::html('administrace.html', $zdroj, false);
""".replace("KOREN", str(KOREN))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True, cwd=KOREN)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return hotovo.stdout


@pytest.fixture(scope="module")
def administrace_ukazka() -> str:
    cesta = KOREN / "out" / "web" / "administrace.html"
    assert cesta.exists(), "ukázka není postavená — spusť `node build.mjs`"
    return cesta.read_text("utf-8")


ZNACKY = (
    "data-pridat-clovek",      # tlačítko „přidat člověka" v liště panelu
    "data-vyrez-mrizka",       # kam se přidaný řádek připojí
    "data-vyrez-vzor",         # <template>, ze kterého se řádek klonuje
    "data-dialog-clovek",      # dialog s údaji
    "data-clovek-form",
    "data-clovek-titulek",
    "data-zavrit-clovek",
    "data-clovek-soubor",      # skrytý výběr souboru pro novou fotku
)

V_RADKU = ("data-clovek-upravit", "data-clovek-fotka", "data-clovek-odebrat",
           "data-clovek-jmeno", "data-clovek-novy")


@pytest.mark.parametrize("znacka", ZNACKY)
def test_administrace_ma_ovladani_lidi(administrace_php, administrace_ukazka, znacka):
    assert znacka in administrace_php, f"ostrá administrace nemá {znacka}"
    assert znacka in administrace_ukazka, f"ukázka administrace nemá {znacka}"


@pytest.mark.parametrize("znacka", V_RADKU)
def test_kazdy_radek_ma_akce_a_vzor_taky(administrace_php, administrace_ukazka, znacka):
    """Řádek i <template> staví tatáž funkce, takže počty musí být stejné."""
    lide = json.loads((KOREN / "web" / "data" / "site.json").read_text("utf-8"))["lide"]
    kolik = len(lide) + 1  # + prázdný vzor v <template>
    assert administrace_php.count(znacka) == kolik, \
        f"ostrá administrace: {znacka} je {administrace_php.count(znacka)}×, čekal jsem {kolik}×"
    assert administrace_ukazka.count(znacka) == kolik, \
        f"ukázka: {znacka} je {administrace_ukazka.count(znacka)}×, čekal jsem {kolik}×"


def test_vyber_souboru_bere_jen_obrazky(administrace_php, administrace_ukazka):
    for kde, html in (("ostrá", administrace_php), ("ukázka", administrace_ukazka)):
        nalez = re.search(r"<input[^>]*data-clovek-soubor[^>]*>", html)
        assert nalez, f"{kde}: výběr souboru chybí"
        tag = nalez.group(0)
        assert 'type="file"' in tag, f"{kde}: {tag}"
        assert "image/jpeg" in tag and "image/png" in tag and "image/webp" in tag, f"{kde}: {tag}"
        assert "hidden" in tag, f"{kde}: výběr souboru má být skrytý, kliká se na tlačítko: {tag}"


def test_dialog_ma_jmeno_povinne(administrace_php, administrace_ukazka):
    for kde, html in (("ostrá", administrace_php), ("ukázka", administrace_ukazka)):
        nalez = re.search(r'<input[^>]*name="jmeno"[^>]*>', html)
        assert nalez and "required" in nalez.group(0), f"{kde}: jméno musí být povinné: {nalez}"
        for pole in ("role", "telefon", "email"):
            assert re.search(r'<input[^>]*name="%s"' % pole, html), f"{kde}: chybí pole {pole}"
