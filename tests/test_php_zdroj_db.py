"""Akceptační test C-017 — App\\Obsah\\ZdrojDb (obsah z databáze nad výchozími soubory).

ZdrojDb je tentýž Zdroj jako ZdrojJson, jen přes něj prosakují změny z
administrace (stav): přepsané texty a přidané, změněné nebo smazané realizace.
Co administrace nepřepsala, musí zůstat BAJTOVĚ stejné jako ze souborů — na
tom stojí shoda ostrého webu s ukázkou.

Pravidlo je v tomhle testu, ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

# Stav, jaký vyrobí administrace: přepsaný text v češtině, přepsaná zkratka,
# jedna přidaná realizace, jedna přejmenovaná a jedna smazaná.
STAV = {
    "texts": {
        "cs": {
            "nav.sluzby": "Co umíme",
            "slovnik.terminy.TZB.full": "Technická zařízení budov (upraveno)",
        },
        "en": {"nav.sluzby": "What we do"},
    },
    "realizace": {
        "added": [
            {
                "id": "nova-cistirna-ricany",
                "nazev": "Nová čistírna Říčany",
                "datum": "2099-01-01",
                "vetev": "firmy",
                "kategorie": "voda",
            }
        ],
        "edited": {},
        "removed": [],
    },
    "updatedAt": "2026-10-22T10:00:00.000Z",
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require __DIR__ . '/../web/app/Jadro/Autoload.php';

$stav = json_decode((string) file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);
$data = __DIR__ . '/../web/data';
$aktiva = __DIR__ . '/../web/public/assets';

$json = new App\Obsah\ZdrojJson($data, $aktiva);
$db = new App\Obsah\ZdrojDb($data, $aktiva, $stav);

$site = $db->site();
$ids = array_map(static fn (array $r): string => $r['id'], $site['realizace']);
$jmena = [];
foreach ($site['realizace'] as $r) {
    $jmena[$r['id']] = $r['nazev'];
}

echo json_encode([
    'cs_prepsany' => $db->dict('cs')['nav']['sluzby'],
    'cs_neprepsany' => $db->dict('cs')['nav']['kontakt'],
    'cs_puvodni' => $json->dict('cs')['nav']['sluzby'],
    'en_prepsany' => $db->dict('en')['nav']['sluzby'],
    'de_nedotceny' => $db->dict('de')['nav']['sluzby'] === $json->dict('de')['nav']['sluzby'],
    'cs_jinak_stejny' => $db->dict('cs') === App\Obsah\I18n::unflatten(array_merge(
        App\Obsah\I18n::flatten($json->dict('cs')),
        $stav['texts']['cs'],
    )),
    'slovnik_prepsany' => $db->slovnik('cs')['TZB']['full'],
    'slovnik_jinak' => $db->slovnik('cs')['VZT']['full'] === $json->slovnik('cs')['VZT']['full'],
    'realizace_ids' => $ids,
    'realizace_jmena' => $jmena,
    'realizace_pocet_json' => count($json->site()['realizace']),
    'sluzby_stejne' => $site['sluzby'] === $json->site()['sluzby'],
    'firma_stejna' => $site['firma'] === $json->site()['firma'],
    'obrazky_stejne' => $db->obrazky() === $json->obrazky(),
    'aktiva_stejna' => $db->verzeAktiv() === $json->verzeAktiv(),
    'stav_vrati' => $db->stav() === $stav,
    'bez_stavu_je_jako_json' => (new App\Obsah\ZdrojDb($data, $aktiva, []))->dict('cs') === $json->dict('cs'),
    'bez_stavu_realizace' => count((new App\Obsah\ZdrojDb($data, $aktiva, []))->site()['realizace']),
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def vysledek(tmp_path_factory):
    # smazaná a přejmenovaná realizace se berou ze skutečných dat webu
    site = json.loads((KOREN / "web" / "data" / "site.json").read_text("utf8"))
    zaklad = [r["id"] for r in site["realizace"]]
    assert len(zaklad) >= 3, "v datech webu musí být aspoň tři realizace"
    stav = json.loads(json.dumps(STAV))
    stav["realizace"]["edited"] = {zaklad[0]: {"nazev": "Přejmenovaná realizace"}}
    stav["realizace"]["removed"] = [zaklad[1]]

    dir = tmp_path_factory.mktemp("zdrojdb")
    (dir / "stav.json").write_text(json.dumps(stav), "utf8")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("__DIR__ . '/..", f"'{KOREN}"), "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(dir / "stav.json")],
        capture_output=True, text=True, timeout=120,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout), zaklad, stav


def test_prepsane_texty_prosaknou(vysledek):
    v, _, _ = vysledek
    assert v["cs_prepsany"] == "Co umíme"
    assert v["en_prepsany"] == "What we do"
    assert v["cs_puvodni"] != "Co umíme", "ZdrojJson se nesmí měnit"


def test_co_administrace_neprepsala_zustava(vysledek):
    v, _, _ = vysledek
    assert v["cs_neprepsany"], "nepřepsaný klíč zmizel"
    assert v["de_nedotceny"] is True, "přepis v češtině zasáhl němčinu"
    assert v["cs_jinak_stejny"] is True, "slovník jazyka se liší od souboru s přepsanými klíči"
    assert v["sluzby_stejne"] is True
    assert v["firma_stejna"] is True
    assert v["obrazky_stejne"] is True
    assert v["aktiva_stejna"] is True


def test_prepis_dosahne_i_do_zkratek(vysledek):
    v, _, _ = vysledek
    assert v["slovnik_prepsany"] == "Technická zařízení budov (upraveno)"
    assert v["slovnik_jinak"] is True


def test_realizace_pridana_zmenena_smazana(vysledek):
    v, zaklad, _ = vysledek
    ids = v["realizace_ids"]
    assert ids[0] == "nova-cistirna-ricany", "přidaná realizace s nejnovějším datem musí být první"
    assert zaklad[1] not in ids, "smazaná realizace se pořád vykresluje"
    assert v["realizace_jmena"][zaklad[0]] == "Přejmenovaná realizace"
    assert len(ids) == v["realizace_pocet_json"] + 1 - 1, "počet nesouhlasí (jedna přidaná, jedna smazaná)"


def test_prazdny_stav_se_chova_jako_soubory(vysledek):
    v, _, _ = vysledek
    assert v["bez_stavu_je_jako_json"] is True, "bez stavu se texty liší od souborů"
    assert v["bez_stavu_realizace"] == v["realizace_pocet_json"]


def test_stav_jde_precist_zpatky(vysledek):
    v, _, stav = vysledek
    assert v["stav_vrati"] is True
