"""Akceptační test C-023 — App\\Obsah\\RazeniCs (české řazení bez intl).

Porovnává PHP proti ZAZNAMENANÝM vzorkům z ukázky (tests/orakulum/razeni-cs.json),
které vznikly spuštěním src/lib nad skutečným obsahem webu. Pravidlo je ve
vzorcích, ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, vstupy, z_php

JMENO = "razeni-cs"


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


def test_orakulum_ma_cim_hlidat_diakritiku():
    """Bez páru, kde se liší jen diakritika nebo velikost, je brána slepá."""
    pary = [tuple(a) for a in vstupy(JMENO)["porovnej"]]
    assert ("c", "\u010d") in pary, "chybí pár c/č"
    assert ("ar", "\u00e1r") in pary, "chybí pár ar/ár (druhá úroveň)"
    assert ("ch", "i") in pary, "chybí pár ch/i (dvojhláska ch)"
    assert ("a", "A") in pary, "chybí pár a/A (velikost písmen)"
    assert len(pary) > 1000, "málo párů na comparator"
