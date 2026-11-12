"""Brána — App\\Obsah\\StavLidi: přidaný, změněný a odebraný člověk v týmu.

Tým se dá v administraci doplnit i zkrátit. Ostrý web skládá seznam na
serveru (PHP), ukázka v prohlížeči (src/lib/cms-store.mjs) — a obojí musí
vyjít na totéž, jinak se stránky rozejdou v bajtech
(tests/test_php_shoda_stranek.py).

Orákulum je zaznamenaný běh knihovny z ukázky nad skutečnými lidmi ze
site.json (tools/orakulum-knihovny.mjs → tests/orakulum/cms-store.json).
Pravidlo je v těch vzorcích, ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.phpmod import ocekavane, rozdily, vstupy, z_php

KOREN = Path(__file__).resolve().parents[1]

JMENO = "cms-store"
MOJE = {
    "inicialyZJmena", "telefonHref", "doplnenyClovek",
    "upsertClovek", "removeClovek", "mergeLide",
}


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    chybi = MOJE - set(ocek)
    assert not chybi, f"orákulum nezná {sorted(chybi)}"
    for funkce in sorted(MOJE):
        assert ocek[funkce], f"{funkce}: žádné vzorky"


def test_php_se_chova_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky, jen=MOJE)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_id_se_vyrabi_ze_jmena_az_do_kolize():
    """Dvakrát stejné jméno musí dát dvě různá id, jinak by druhý člověk
    přepsal prvního."""
    args = vstupy(JMENO)["upsertClovek"]
    vysledky = ocekavane(JMENO)["upsertClovek"]
    bezId = [(a, v) for a, v in zip(args, vysledky) if not (a[1] or {}).get("id")]
    assert len(bezId) >= 3, "chybí vzorky bez zadaného id"
    id_stejneho_jmena = []
    for a, v in bezId:
        if (a[1] or {}).get("jmeno") == "Žofie Nováková":
            id_stejneho_jmena.append([p["id"] for p in v["lide"]["added"]])
    assert id_stejneho_jmena, "orákulum nemá vzorek se stejným jménem dvakrát"
    nejdelsi = max(id_stejneho_jmena, key=len)
    assert len(nejdelsi) == len(set(nejdelsi)), f"kolize id: {nejdelsi}"
    assert "zofie-novakova" in nejdelsi and "zofie-novakova-2" in nejdelsi, nejdelsi


def test_odebrany_clovek_si_bere_vyrez_s_sebou():
    """Výřez se klíčuje id člověka. Kdyby po odebrání zůstal, nesl by se
    v každé stránce webu záznam, ke kterému už nikdo nepatří — a kdyby se
    člověk vrátil, dostal by starý posun fotky."""
    args = vstupy(JMENO)["removeClovek"]
    vysledky = ocekavane(JMENO)["removeClovek"]
    nalezeno = 0
    for a, v in zip(args, vysledky):
        stav, id_ = a[0], a[1]
        if not (stav.get("portrety") or {}).get(id_):
            continue
        nalezeno += 1
        assert id_ not in (v["portrety"] or {}), f"{id_} má po odebrání pořád výřez"
    assert nalezeno >= 2, "orákulum nemá dost vzorků, kde odebraný člověk výřez měl"


def test_odebrany_clovek_zmizi_ze_seznamu_a_pridany_je_na_konci():
    args = vstupy(JMENO)["mergeLide"]
    vysledky = ocekavane(JMENO)["mergeLide"]
    videli_odebraneho = False
    videli_pridaneho = False
    for a, v in zip(args, vysledky):
        stav, zaklad = a[0], a[1]
        lide = stav.get("lide") or {}
        odebrani = lide.get("removed") or []
        pridani = [p["id"] for p in (lide.get("added") or [])]
        id_ve_vysledku = [p["id"] for p in v]
        for id_ in odebrani:
            videli_odebraneho = True
            assert id_ not in id_ve_vysledku, f"{id_} je odebraný, a přece v seznamu"
        if pridani and zaklad:
            videli_pridaneho = True
            assert id_ve_vysledku[-len(pridani):] == pridani, \
                f"přidaní nejsou na konci: {id_ve_vysledku}"
        assert len(id_ve_vysledku) == len(set(id_ve_vysledku)), id_ve_vysledku
    assert videli_odebraneho, "orákulum nemá vzorek s odebraným člověkem"
    assert videli_pridaneho, "orákulum nemá vzorek s přidaným člověkem"


def test_zkratka_a_telefon_se_doplni_samy():
    """Správce píše do dialogu jméno a telefon, ne zkratku a tel: odkaz.
    Doplnit se musí na jednom místě, jinak by je PHP a JS napsaly jinak."""
    args = vstupy(JMENO)["upsertClovek"]
    vysledky = ocekavane(JMENO)["upsertClovek"]
    nalezeno = 0
    for a, v in zip(args, vysledky):
        zadane = a[1] or {}
        if zadane.get("id") or not zadane.get("jmeno"):
            continue
        novy = [p for p in v["lide"]["added"] if p.get("jmeno") == zadane["jmeno"].strip()]
        if not novy:
            continue
        nalezeno += 1
        osoba = novy[-1]
        assert osoba.get("inicialy"), f"{osoba} bez zkratky"
        if zadane.get("telefon", "").strip():
            assert osoba.get("telefonHref", "").startswith(("+", "7", "6", "0", "4")), osoba
    assert nalezeno >= 2, "orákulum nemá dost vzorků s novým člověkem"


def test_oprava_pridaneho_cloveka_zustane_v_added():
    """Ostrá administrace dostává do stránky SLOUČENÝ seznam lidí, takže
    „základ" v prohlížeči přidané lidi už obsahuje. Kdyby o místě zápisu
    rozhodoval základ, oprava přidaného člověka by spadla do `edited` —
    a tu spojení zahodí, protože v site.json takové id není. Správce by
    uložil telefon a po načtení stránky by tam byl ten starý."""
    args = vstupy(JMENO)["upsertClovek"]
    vysledky = ocekavane(JMENO)["upsertClovek"]
    nalezeno = 0
    for a, v in zip(args, vysledky):
        stav, osoba, zaklad = a[0], a[1] or {}, a[2] or []
        id_ = osoba.get("id")
        if not id_:
            continue
        pridani = [p["id"] for p in ((stav.get("lide") or {}).get("added") or [])]
        zakladni = [z.get("id") for z in zaklad]
        if id_ not in pridani or id_ not in zakladni:
            continue
        nalezeno += 1
        assert not (v["lide"]["edited"] or {}), \
            f"{id_}: oprava přidaného člověka skončila v edited: {v['lide']['edited']}"
        osoby = [p for p in v["lide"]["added"] if p["id"] == id_]
        assert len(osoby) == 1, osoby
        for pole, hodnota in osoba.items():
            if pole == "id":
                continue
            assert osoby[0].get(pole) == hodnota, f"{id_}.{pole}: {osoby[0].get(pole)!r}"
    assert nalezeno >= 1, "orákulum nemá vzorek, kde je id v added i v základu"


def test_oprava_cisla_prepocita_odkaz_na_telefon():
    """Odvozená pole (zkratka, tel:) musí jít za zdrojem.

    Našlo se to klikáním v živé administraci: po opravě čísla u přidaného
    člověka zůstal v `telefonHref` starý údaj, takže karta na webu ukazovala
    nové číslo a volala na staré.
    """
    program = r"""
require 'KOREN/web/app/Jadro/Autoload.php';
use App\Obsah\StavLidi;
$s = StavLidi::ulozClovek([], ['jmeno' => 'Žofie Nováková', 'telefon' => '+420 777 123 456'], []);
$s = StavLidi::ulozClovek($s, ['id' => 'zofie-novakova', 'telefon' => '+420 777 999 000'], []);
$zaklad = [['id' => 'radek-tyla', 'jmeno' => 'Radek Týla', 'inicialy' => 'RT',
           'telefon' => '+420 111 111 111', 'telefonHref' => '+420111111111']];
$u = StavLidi::ulozClovek([], ['id' => 'radek-tyla', 'telefon' => '+420 222 222 222'], $zaklad);
$v = StavLidi::ulozClovek([], ['id' => 'radek-tyla', 'telefon' => '+420 333', 'telefonHref' => '+420999'], $zaklad);
echo json_encode(['pridany' => $s['lide']['added'][0],
                  'zakladni' => $u['lide']['edited']['radek-tyla'],
                  'rucne' => $v['lide']['edited']['radek-tyla']]);
""".replace("KOREN", str(KOREN))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True, cwd=KOREN)
    assert hotovo.returncode == 0, hotovo.stderr[-1500:]
    ven = json.loads(hotovo.stdout)
    assert ven["pridany"]["telefonHref"] == "+420777999000", \
        f"přidaný člověk: odkaz na telefon zůstal starý: {ven['pridany']}"
    assert ven["zakladni"]["telefonHref"] == "+420222222222", \
        f"základní člověk: do změny nejde nový odkaz: {ven['zakladni']}"
    assert ven["rucne"]["telefonHref"] == "+420999", \
        f"ručně zadaný odkaz má přednost: {ven['rucne']}"


def test_zmena_jmena_prepocita_zkratku():
    program = r"""
require 'KOREN/web/app/Jadro/Autoload.php';
use App\Obsah\StavLidi;
$zaklad = [['id' => 'radek-tyla', 'jmeno' => 'Radek Týla', 'inicialy' => 'RT']];
$u = StavLidi::ulozClovek([], ['id' => 'radek-tyla', 'jmeno' => 'Nové Jméno'], $zaklad);
echo json_encode($u['lide']['edited']['radek-tyla']);
""".replace("KOREN", str(KOREN))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True, cwd=KOREN)
    assert hotovo.returncode == 0, hotovo.stderr[-1500:]
    assert json.loads(hotovo.stdout).get("inicialy") == "NJ", \
        f"po změně jména zůstala stará zkratka: {hotovo.stdout}"
