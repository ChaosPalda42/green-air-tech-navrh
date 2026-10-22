"""Akceptační test C-012 — App\\Obsah\\I18n (překlady a práce s klíči).

Porovnává PHP proti ZAZNAMENANÝM vzorkům z ukázky (tests/orakulum/i18n.json),
které vznikly spuštěním src/lib nad skutečným obsahem webu. Pravidlo je ve
vzorcích, ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

JMENO = "i18n"


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
