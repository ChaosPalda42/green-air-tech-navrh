"""Akceptační test C-015 — App\\Formular\\Validace (validace poptávkového formuláře).

Porovnává PHP proti ZAZNAMENANÝM vzorkům z ukázky (tests/orakulum/formular.json),
které vznikly spuštěním src/lib nad skutečným obsahem webu. Pravidlo je ve
vzorcích, ne v PHP kódu, na který se ptáme.

Od 23. 10. 2026 jsou mezi vzorky i mezinárodní telefony: nezávislý test
našel, že `+49 30 1234567` ani `+421905123456` neprošly, takže na německé
a anglické verzi webu zahraniční zákazník telefon nezadal. Ukázka proto umí
`isPhone` (tvar podle E.164) a `validateContact` se ptá jí; doma dál platí
přísnější české pravidlo, v němž navíc chyběla čtyřka — web odmítal skutečné
pevné linky 46x Liberec a 49x Pardubicko.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

JMENO = "formular"


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
