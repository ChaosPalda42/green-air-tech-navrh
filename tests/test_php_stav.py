"""Akceptační test C-016 — App\\Obsah\\Stav (texty z administrace, slug, import JSONu).

Porovnává PHP proti ZAZNAMENANÝM vzorkům z ukázky (tests/orakulum/cms-store.json),
které vznikly spuštěním src/lib/cms-store.mjs nad skutečnými daty webu. Pravidlo je
ve vzorcích, ne v PHP kódu, na který se ptáme.

Realizace (upsertRealizace, removeRealizace, mergeRealizace) hlídá
tests/test_php_stav_realizace.py — jsou v samostatné třídě App\\Obsah\\StavRealizace.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

JMENO = "cms-store"
MOJE = {"emptyState", "slugify", "setText", "getText", "mergeTexts", "importJson"}


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    chybi = MOJE - set(ocek)
    assert not chybi, f"orákulum nezná {sorted(chybi)}"
    for funkce in sorted(MOJE):
        assert ocek[funkce], f"{funkce}: žádné vzorky"


def test_orakulum_hlida_mazani_i_diakritiku():
    """Bez těchhle vzorků je brána slepá na dvě věci, na kterých to padá:
    prázdná hodnota má klíč smazat a slug musí srovnat českou diakritiku."""
    vst = ocekavane(JMENO)
    assert "" in [v for v in vst["slugify"]], "chybí vzorek, kde slug vyjde prázdný"
    assert "uplne-velka-zlutoucka-zprava" in vst["slugify"], "chybí vzorek s velkou diakritikou"
    assert any(v == {"nav.sluzby": "Co umíme"} for v in vst["mergeTexts"]), \
        "chybí vzorek, kde spojTexty vrací JEN slovník textů"


def test_php_se_chova_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky, jen=MOJE)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_vstup_se_nemeni(vysledky):
    """Stav je nemněnný: metody vracejí nový stav, vstupní pole nechají být.
    Kdyby PHP mutovalo vstup, pozdější vzorky by viděly cizí změny a výsledky
    by se rozešly — proto se stejná sada pouští dvakrát a musí dát totéž."""
    druhy = z_php(JMENO)
    moje = {f: v for f, v in vysledky.items() if f in MOJE}
    assert moje == {f: v for f, v in druhy.items() if f in MOJE}, \
        "druhý běh dal jiné výsledky — nějaká metoda mutuje vstup"
