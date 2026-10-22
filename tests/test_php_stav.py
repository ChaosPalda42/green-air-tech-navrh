"""Akceptační test C-016 — App\\Obsah\\Stav (změny z administrace nad výchozím obsahem).

Porovnává PHP proti ZAZNAMENANÝM vzorkům z ukázky (tests/orakulum/cms-store.json),
které vznikly spuštěním src/lib/cms-store.mjs nad skutečnými daty webu. Pravidlo je
ve vzorcích, ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

JMENO = "cms-store"


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    assert ocek, "orákulum je prázdné"
    for funkce, vzorky in ocek.items():
        assert vzorky, f"{funkce}: žádné vzorky"


def test_php_se_chova_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_vstup_se_nemeni(vysledky):
    """Stav je nemněnný: metody vracejí nový stav, vstupní pole nechají být.
    Kdyby PHP mutovalo vstup, pozdější vzorky by viděly cizí změny a výsledky
    by se rozešly — proto se stejná sada pouští dvakrát a musí dát totéž."""
    assert vysledky == z_php(JMENO), "druhý běh dal jiné výsledky — nějaká metoda mutuje vstup"
