"""Akceptační test C-030 — App\\Auth\\Pozvanka (první heslo z pozvánky).

Nezávislý test balíčku našel, že uživatel založený v administraci se nikdy
nepřihlásí: v databázi má `heslo_hash NULL` a nikde v balíčku nebyla cesta,
jak si heslo nastavit. Správce si nezměnil ani vlastní heslo z instalace.
API už pozvánku vystaví (POST /api/uzivatele, POST /api/pozvanka) a vrátí
token; tenhle soubor rozhoduje, co se smí stát, když s tím tokenem někdo
přijde na `administrace.html?pozvanka=<token>`.

Pravidla brány:
- Pozvánka platí jen tehdy, když se token DOSLOVA rovná tomu, co má účet
  v databázi, ještě neuplynula platnost a účet je aktivní. Cokoli jiného
  (prázdný token, neznámý účet, účet bez tokenu, propadlá platnost, vypnutý
  účet) je propadlá pozvánka — a mlčí stejně, aby se z odpovědi nedalo
  vyčíst, který token existuje.
- Formulář na stránce dostane jen token, jméno a e-mail. Hash hesla ani
  token z účtu se do stránky nedostanou.
- Heslo se bere jen tehdy, když projde kontrolou síly (Uzivatele::
  zkontrolujHeslo) a když je dvakrát stejné. Pořadí: nejdřív síla, pak
  shoda — ať krátké heslo napsané dvakrát stejně řekne „krátké".
- Zápis do databáze je ÚZKÝ: jen id, hash hesla a zrušení pozvánky. Jedno
  uplatnění pozvánky nesmí měnit roli, jméno ani e-mail — kdo pozvánku
  uplatní, nesmí si tím povýšit účet.
- Hash je ověřitelný heslem, nikdy není heslo samo a dvakrát za sebou je
  jiný (sůl).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

TOKEN = "a" * 64
JINY = "b" * 64
HESLO = "SpolehliveHeslo2026"

# účet tak, jak ho vrátí UlozisteDb::podleTokenu (PDO vrací čísla jako texty)
UCET = {
    "id": "7",
    "jmeno": "Editor Test",
    "email": "editor@priklad.cz",
    "role": "editor",
    "aktivni": "1",
    "heslo_hash": None,
    "pozvanka_token": TOKEN,
    "pozvanka_do": "+3 days",      # program si z toho udělá datum
    "vytvoreno": "2026-10-01 08:00:00",
}


def ucet(**zmeny) -> dict:
    novy = dict(UCET)
    novy.update(zmeny)
    return novy


# popis -> (účet nebo None, token v adrese, čekáme platnou pozvánku)
PLATNOST: dict[str, tuple[dict | None, str, bool]] = {
    "čerstvá pozvánka platí": (UCET, TOKEN, True),
    "prázdný token": (UCET, "", False),
    "neznámý token (účet se nenašel)": (None, TOKEN, False),
    "prázdný token a žádný účet": (None, "", False),
    "token z adresy nesouhlasí s účtem": (ucet(pozvanka_token=JINY), TOKEN, False),
    "účet pozvánku nemá": (ucet(pozvanka_token=None), TOKEN, False),
    "účet má pozvánku prázdnou": (ucet(pozvanka_token=""), "", False),
    "pozvánka propadla": (ucet(pozvanka_do="-1 hour"), TOKEN, False),
    "pozvánka propadla před chvílí": (ucet(pozvanka_do="-1 second"), TOKEN, False),
    "pozvánka platí ještě minutu": (ucet(pozvanka_do="+60 seconds"), TOKEN, True),
    "bez data platnosti": (ucet(pozvanka_do=None), TOKEN, False),
    "data platnosti nesmysl": (ucet(pozvanka_do="kdykoli"), TOKEN, False),
    "vypnutý účet pozvánku neuplatní": (ucet(aktivni="0"), TOKEN, False),
    "účet, který už heslo má": (ucet(heslo_hash="$2y$10$cosi"), TOKEN, True),
}

# popis -> (účet, token, heslo, heslo podruhé, čekaný stav, čekaný důvod)
PRIJETI: dict[str, tuple[dict | None, str, str, str, str, str | None]] = {
    "správné heslo dvakrát": (UCET, TOKEN, HESLO, HESLO, "ok", None),
    "propadlá pozvánka se správným heslem": (
        ucet(pozvanka_do="-1 hour"), TOKEN, HESLO, HESLO, "propadla", None),
    "cizí token": (None, JINY, HESLO, HESLO, "propadla", None),
    "vypnutý účet": (ucet(aktivni="0"), TOKEN, HESLO, HESLO, "propadla", None),
    "prázdné heslo": (UCET, TOKEN, "", "", "vadne-heslo", "prazdne"),
    "jen mezery": (UCET, TOKEN, "            ", "            ", "vadne-heslo", "prazdne"),
    "jedenáct znaků je málo": (UCET, TOKEN, "Abcdefgh123", "Abcdefgh123", "vadne-heslo", "kratke"),
    "dvanáct znaků stačí": (UCET, TOKEN, "Abcdefgh1234", "Abcdefgh1234", "ok", None),
    "krátké heslo dvakrát jinak řekne krátké": (
        UCET, TOKEN, "Abc1", "Xyz9", "vadne-heslo", "kratke"),
    "dobré heslo, ale opsané jinak": (UCET, TOKEN, HESLO, HESLO + "!", "nesouhlasi", None),
    "podruhé prázdné": (UCET, TOKEN, HESLO, "", "nesouhlasi", None),
    "propadlá pozvánka a vadné heslo mlčí o pozvánce": (
        ucet(pozvanka_token=None), TOKEN, "krátké", "krátké", "propadla", None),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Auth\Pozvanka;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

/** Relativní čas v `pozvanka_do` ("+3 days") se dopočítá teď, ať test nestárne. */
$ucet = static function (?array $u): ?array {
    if ($u === null) {
        return null;
    }
    $do = $u['pozvanka_do'] ?? null;
    if (is_string($do) && $do !== '' && ($do[0] === '+' || $do[0] === '-')) {
        $cas = strtotime($do);
        $u['pozvanka_do'] = $cas === false ? $do : date('Y-m-d H:i:s', $cas);
    }
    return $u;
};

$ven = ['platnost' => [], 'prijeti' => []];

foreach ($vstup['platnost'] as $klic => [$u, $token]) {
    $pro = $ucet($u);
    $kopie = $pro;
    $vysledek = Pozvanka::proStranku($pro, $token);
    $ven['platnost'][$klic] = [
        'vysledek' => $vysledek,
        'prazdne' => $vysledek === [],
        'klice' => array_keys($vysledek),
        'nemutuje' => $kopie === $pro,
    ];
}

foreach ($vstup['prijeti'] as $klic => [$u, $token, $heslo, $heslo2]) {
    $pro = $ucet($u);
    $kopie = $pro;
    $vysledek = Pozvanka::prijmi($pro, $token, $heslo, $heslo2);
    $zapis = $vysledek['zapis'] ?? null;
    $ven['prijeti'][$klic] = [
        'stav' => $vysledek['stav'] ?? null,
        'duvod' => $vysledek['duvod'] ?? null,
        'klice' => array_keys($vysledek),
        'zapis_klice' => is_array($zapis) ? array_keys($zapis) : null,
        'zapis_id' => is_array($zapis) ? ($zapis['id'] ?? null) : null,
        'zapis_token' => is_array($zapis) ? ($zapis['pozvanka_token'] ?? 'chybi') : null,
        'zapis_do' => is_array($zapis) ? ($zapis['pozvanka_do'] ?? 'chybi') : null,
        'hash_sedi' => is_array($zapis) && is_string($zapis['heslo_hash'] ?? null)
            ? password_verify($heslo, (string) $zapis['heslo_hash']) : null,
        'hash_je_heslo' => is_array($zapis) ? (($zapis['heslo_hash'] ?? null) === $heslo) : null,
        'nemutuje' => $kopie === $pro,
    ];
}

// Dvakrát totéž heslo musí dát dva různé hashe (sůl).
$a = Pozvanka::prijmi($ucet($vstup['platnost']['čerstvá pozvánka platí'][0]), '{TOKEN}', '{HESLO}', '{HESLO}');
$b = Pozvanka::prijmi($ucet($vstup['platnost']['čerstvá pozvánka platí'][0]), '{TOKEN}', '{HESLO}', '{HESLO}');
$ven['hashe_se_lisi'] = ($a['zapis']['heslo_hash'] ?? 1) !== ($b['zapis']['heslo_hash'] ?? 2);

echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("pozvanka")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps({
        "platnost": {k: [u, t] for k, (u, t, _) in PLATNOST.items()},
        "prijeti": {k: [u, t, h1, h2] for k, (u, t, h1, h2, _, _) in PRIJETI.items()},
    }, ensure_ascii=False), "utf8")
    program = dir / "program.php"
    program.write_text(
        PROGRAM.lstrip()
        .replace("{KOREN}", str(KOREN))
        .replace("{TOKEN}", TOKEN)
        .replace("{HESLO}", HESLO),
        "utf8",
    )
    hotovo = subprocess.run(
        ["php", str(program), str(vstup)], capture_output=True, text=True, timeout=60,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


@pytest.mark.parametrize("popis", list(PLATNOST))
def test_kdy_pozvanka_plati(popis, v):
    _, _, plati = PLATNOST[popis]
    o = v["platnost"][popis]
    assert o["prazdne"] is not plati, (
        f"{popis}: čekal jsem "
        + ("platnou pozvánku, a proStranku() vrátilo prázdno" if plati
           else "propadlou pozvánku, a proStranku() něco vrátilo")
    )


@pytest.mark.parametrize("popis", [p for p, (_, _, plati) in PLATNOST.items() if plati])
def test_platna_pozvanka_da_strance_jen_tri_veci(popis, v):
    o = v["platnost"][popis]
    assert sorted(o["klice"]) == ["email", "jmeno", "token"], (
        f"{popis}: do stránky patří token, jméno a e-mail a nic víc — "
        f"dostal jsem {o['klice']}"
    )
    assert o["vysledek"]["token"] == TOKEN, "formulář musí dostat zpátky token z adresy"
    assert o["vysledek"]["jmeno"] == UCET["jmeno"]
    assert o["vysledek"]["email"] == UCET["email"]


def test_propadla_pozvanka_nic_nenapovi(v):
    """Odpověď nesmí rozlišit „token neexistuje" od „propadl"."""
    prazdne = {p: o["vysledek"] for p, o in v["platnost"].items() if o["prazdne"]}
    assert all(x == [] for x in prazdne.values()), (
        "propadlá pozvánka musí vrátit prázdné pole, ne důvod: "
        + str({p: x for p, x in prazdne.items() if x != []})
    )


@pytest.mark.parametrize("popis", list(PRIJETI))
def test_stav_prijeti(popis, v):
    _, _, _, _, stav, duvod = PRIJETI[popis]
    o = v["prijeti"][popis]
    assert o["stav"] == stav, popis
    assert o["duvod"] == duvod, f"{popis}: čekal jsem důvod {duvod!r}, dostal {o['duvod']!r}"


@pytest.mark.parametrize("popis", [p for p, x in PRIJETI.items() if x[4] == "ok"])
def test_zapis_je_uzky(popis, v):
    o = v["prijeti"][popis]
    assert sorted(o["zapis_klice"]) == ["heslo_hash", "id", "pozvanka_do", "pozvanka_token"], (
        f"{popis}: zápis smí nést jen id, hash hesla a zrušení pozvánky — "
        f"dostal jsem {o['zapis_klice']}. Role, jméno ani e-mail se uplatněním "
        "pozvánky měnit nesmí."
    )
    assert o["zapis_id"] == 7, f"{popis}: id musí být číslo 7, dostal jsem {o['zapis_id']!r}"
    assert o["zapis_token"] is None, f"{popis}: uplatněná pozvánka musí token zrušit"
    assert o["zapis_do"] is None, f"{popis}: uplatněná pozvánka musí zrušit i platnost"


@pytest.mark.parametrize("popis", [p for p, x in PRIJETI.items() if x[4] == "ok"])
def test_hash_hesla(popis, v):
    o = v["prijeti"][popis]
    assert o["hash_sedi"] is True, f"{popis}: password_verify() hash neuznal"
    assert o["hash_je_heslo"] is False, f"{popis}: do databáze se uložilo heslo, ne hash"


def test_hashe_se_lisi(v):
    assert v["hashe_se_lisi"], "dvakrát totéž heslo dalo tentýž hash — chybí sůl"


@pytest.mark.parametrize("popis", list(PRIJETI))
def test_odmitnute_prijeti_nic_nezapise(popis, v):
    _, _, _, _, stav, _ = PRIJETI[popis]
    o = v["prijeti"][popis]
    if stav == "ok":
        return
    assert o["zapis_klice"] is None, f"{popis}: {stav} a přesto se chystá zápis do databáze"
    assert "zapis" not in o["klice"], popis


def test_ucet_na_vstupu_se_nemeni(v):
    for cast in ("platnost", "prijeti"):
        for popis, o in v[cast].items():
            assert o["nemutuje"], f"{cast}/{popis}: funkce přepsala pole, které jí dal volající"
