"""Akceptační test C-028 — App\\Auth\\Zamek (hádání hesla do administrace).

Ukázka hlídala hádání hesla jen v sezení prohlížeče: po pár pokusech se
čekalo. Útočníkovi stačí zahodit cookie a počítadlo je zpátky na nule —
osm špatných hesel za sebou prošlo za čtvrt sekundy. Na ostrém webu se proto
pokusy počítají v databázi (tabulka `udalosti`) a tenhle soubor rozhoduje,
jestli je zamčeno a na jak dlouho.

Počítá se ve DVOU sadách, a to je celá pointa. Nezávislý test našel, že
desetkrát špatné heslo na jméno `qa-spravce` z deseti různých adres vyřadí
správce z administrace na čtvrt hodiny: kdo zná jeho login, drží ho venku a
nic k tomu nepotřebuje. Adresa a účet se proto počítají každá zvlášť a účet
má strop mnohem vyšší — je to záchranná síť proti hádání z mnoha adres, ne
vypínač na správce.

Pravidlo brány:
- Pokusy starší než OKNO se nepočítají (okno se posouvá).
- LIMIT_ADRESA pokusů z jedné adresy = zamčeno. LIMIT_UCET pokusů na jeden
  účet = zamčeno. Čeká se to delší z obou.
- Zámek drží do chvíle, kdy z okna vypadne LIMIT-tý nejnovější pokus —
  ne dokud nepřestanou chodit. Jinak by útočník držel správce venku, jak
  dlouho by chtěl.
- Pořadí časů na vstupu je jedno; čas v budoucnosti (rozejité hodiny
  serveru) se počítá taky.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

OKNO = 900
LIMIT_ADRESA = 10
LIMIT_UCET = 30
TED = 10_000

# popis -> (časy z adresy, časy na účet, čekáme zamčeno, čekáme sekund)
PRIPADY: dict[str, tuple[list[int], list[int], bool, int]] = {
    "nikdo nic nezkoušel": ([], [], False, 0),
    "devět pokusů z adresy ještě projde": ([9_500] * 9, [], False, 0),
    "desátý pokus z adresy zamkne": ([9_500] * 10, [], True, 400),
    "na pořadí časů nezáleží": ([9_500, 9_900, 9_500, 9_500, 9_500,
                                 9_500, 9_500, 9_500, 9_500, 9_500], [], True, 400),
    "co vypadlo z okna, se nepočítá": ([9_000] * 5 + [9_900] * 5, [], False, 0),
    "hranice okna je o sekundu uvnitř": ([9_101] * 10, [], True, 1),
    "hranice okna o sekundu venku": ([9_100] * 10, [], False, 0),
    "zámek drží od desátého nejnovějšího": ([9_200] * 5 + [9_800] * 10, [], True, 700),
    "dávné pokusy zámek neudrží": ([1_000] * 20 + [9_900] * 3, [], False, 0),
    "rozejité hodiny serveru": ([10_500] * 10, [], True, 1_400),
    "pokus právě teď se počítá": ([9_500] * 9 + [TED], [], True, 400),

    # ---- nález testera: účet se nesmí dát zamknout zvenčí tak snadno ----
    "deset pokusů na účet z cizích adres správce nevyřadí":
        ([], [9_500] * 10, False, 0),
    "ani devětadvacet pokusů na účet":
        ([], [9_500] * 29, False, 0),
    "třicátý pokus na účet zamkne i účet":
        ([], [9_500] * 30, True, 400),
    "vlastní adresa zamčená, účet čistý":
        ([9_500] * 10, [9_500] * 10, True, 400),
    "platí to delší čekání z obou":
        ([9_500] * 10, [9_800] * 30, True, 700),
    "účet nasbíraný dávno zámek nedrží":
        ([], [1_000] * 50 + [9_900] * 5, False, 0),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Auth\Zamek;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

$ven = [
    'okno' => Zamek::OKNO,
    'limit_adresa' => Zamek::LIMIT_ADRESA,
    'limit_ucet' => Zamek::LIMIT_UCET,
    'pripady' => [],
];
foreach ($vstup['pripady'] as $klic => $sady) {
    [$zAdresy, $uctu] = $sady;
    $kopieA = $zAdresy;
    $kopieU = $uctu;
    $ven['pripady'][$klic] = [
        'zamceno' => Zamek::zamceno($zAdresy, $uctu, $vstup['ted']),
        'ceka' => Zamek::ceka($zAdresy, $uctu, $vstup['ted']),
        'nemutuje' => $kopieA === $zAdresy && $kopieU === $uctu,
    ];
}
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("zamek")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps(
        {"ted": TED, "pripady": {k: [a, u] for k, (a, u, _, _) in PRIPADY.items()}}), "utf8")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(vstup)], capture_output=True, text=True, timeout=60,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_okno_a_limity_jsou_dane(v):
    assert v["okno"] == OKNO, "okno, ve kterém se pokusy počítají, je 15 minut"
    assert v["limit_adresa"] == LIMIT_ADRESA, "adresu zamyká desátý špatný pokus"
    assert v["limit_ucet"] == LIMIT_UCET, (
        "účet smí zamknout teprve třicátý pokus — nižší strop je vypínač na správce"
    )


@pytest.mark.parametrize("popis", list(PRIPADY))
def test_zamceno(popis, v):
    _, _, zamceno, _ = PRIPADY[popis]
    assert v["pripady"][popis]["zamceno"] is zamceno, popis


@pytest.mark.parametrize("popis", list(PRIPADY))
def test_jak_dlouho_jeste(popis, v):
    _, _, _, ceka = PRIPADY[popis]
    assert v["pripady"][popis]["ceka"] == ceka, popis


def test_vstupni_pole_se_nemeni(v):
    for popis, o in v["pripady"].items():
        assert o["nemutuje"], f"{popis}: funkce přepsala pole, které jí dal volající"


def test_odemceny_ucet_neceka(v):
    for popis, (_, _, zamceno, _) in PRIPADY.items():
        if not zamceno:
            assert v["pripady"][popis]["ceka"] == 0, popis
        else:
            assert v["pripady"][popis]["ceka"] >= 1, \
                f"{popis}: zamčeno, ale čekat se nemá — to by se tvářilo jako odemčeno"
