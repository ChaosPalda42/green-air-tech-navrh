"""Akceptační test C-019 — App\\Api\\Zmeny (co se v administraci změnilo a kdo to smí).

Administrace posílá na server celý svůj stav. Server nesmí věřit tomu, co mu
přišlo: musí si sám spočítat, KTERÝCH oblastí se změna týká, a teprve podle
toho se podívat do matice práv. Autor článků tak nemůže přepsat ceník, i když
si upraví požadavek v prohlížeči.

Pravidlo (které oblasti patří ke kterým klíčům) je opsané tady v testu.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Zmeny;

$prazdny = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []]];
$text = $prazdny;
$text['texts']['cs'] = ['sluzby.polozky.projekce.popis' => 'Nový popis'];
$novinka = $prazdny;
$novinka['texts']['cs'] = ['novinky.polozky.prvni.titulek' => 'Nový titulek'];
$oboje = $prazdny;
$oboje['texts']['cs'] = [
    'novinky.polozky.prvni.titulek' => 'Nový titulek',
    'kontakt.adresa.mesto' => 'Jiné město',
];
$jinyJazyk = $prazdny;
$jinyJazyk['texts']['de'] = ['nav.sluzby' => 'Leistungen'];
$pridana = $prazdny;
$pridana['realizace']['added'] = [['id' => 'nova', 'nazev' => 'Nová']];
$zmenena = $prazdny;
$zmenena['realizace']['edited'] = ['stara' => ['nazev' => 'Jinak']];
$smazana = $prazdny;
$smazana['realizace']['removed'] = ['stara'];
$vse = $prazdny;
$vse['texts']['cs'] = ['nav.sluzby' => 'Co umíme', 'novinky.polozky.prvni.titulek' => 'T'];
$vse['realizace']['added'] = [['id' => 'nova', 'nazev' => 'Nová']];
$jenCas = $prazdny;
$jenCas['updatedAt'] = '2026-10-22T10:00:00.000Z';

$oblasti = static fn (array $a, array $b): array => Zmeny::oblasti($a, $b);

$sady = [
    'nic' => [$prazdny, $prazdny],
    'jen_cas' => [$prazdny, $jenCas],
    'text' => [$prazdny, $text],
    'novinka' => [$prazdny, $novinka],
    'oboje' => [$prazdny, $oboje],
    'jiny_jazyk' => [$prazdny, $jinyJazyk],
    'pridana' => [$prazdny, $pridana],
    'zmenena' => [$prazdny, $zmenena],
    'smazana' => [$prazdny, $smazana],
    'vse' => [$prazdny, $vse],
    'vraceni_textu' => [$text, $prazdny],
    'vraceni_realizace' => [$pridana, $prazdny],
    'zmena_hodnoty' => [$text, array_replace_recursive($text, ['texts' => ['cs' => ['sluzby.polozky.projekce.popis' => 'Ještě jinak']]])],
];
$vysledek = [];
foreach ($sady as $jmeno => [$a, $b]) {
    $o = $oblasti($a, $b);
    sort($o);
    $vysledek[$jmeno] = $o;
}

$smi = [];
foreach (['spravce', 'editor', 'autor'] as $role) {
    foreach ($sady as $jmeno => [$a, $b]) {
        $smi[$role . '|' . $jmeno] = Zmeny::smiZmenit($role, $a, $b);
    }
}

echo json_encode([
    'oblasti' => $vysledek,
    'smi' => $smi,
    'nesmysl' => Zmeny::oblasti([], ['texts' => 'nesmysl', 'realizace' => 5]),
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""

# která oblast patří ke které změně — pravidlo brány
CEKANO = {
    "nic": [],
    "jen_cas": [],
    "text": ["texty"],
    "novinka": ["novinky"],
    "oboje": ["novinky", "texty"],
    "jiny_jazyk": ["texty"],
    "pridana": ["realizace"],
    "zmenena": ["realizace"],
    "smazana": ["realizace"],
    "vse": ["novinky", "realizace", "texty"],
    "vraceni_textu": ["texty"],
    "vraceni_realizace": ["realizace"],
    "zmena_hodnoty": ["texty"],
}
# kdo co smí (z C-018: spravce vše, editor texty+realizace+novinky, autor jen novinky)
PRAVA = {"spravce": set(CEKANO), "editor": set(CEKANO),
         "autor": {"nic", "jen_cas", "novinka"}}


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("zmeny")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_spocita_spravne_oblasti(v):
    spatne = [f"{k}: čekáno {c}, přišlo {v['oblasti'][k]}"
              for k, c in CEKANO.items() if v["oblasti"][k] != c]
    assert not spatne, "\n".join(spatne)


def test_prava_podle_spoctenych_oblasti(v):
    spatne = []
    for role, smi in PRAVA.items():
        for sada in CEKANO:
            cekano = sada in smi
            mam = v["smi"][f"{role}|{sada}"]
            if mam is not cekano:
                spatne.append(f"{role} + {sada}: čekáno {cekano}, přišlo {mam}")
    assert not spatne, "\n".join(spatne)


def test_autor_nesmi_sahnout_na_ostatni_texty(v):
    assert v["smi"]["autor|novinka"] is True, "autor nesmí ani novinky"
    assert v["smi"]["autor|text"] is False, "autor přepsal text mimo novinky"
    assert v["smi"]["autor|oboje"] is False, "s novinkou prošla i cizí změna"
    assert v["smi"]["autor|pridana"] is False


def test_nesmyslny_vstup_nespadne(v):
    assert isinstance(v["nesmysl"], list)
