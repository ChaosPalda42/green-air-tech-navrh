"""Ikony, motivy a hero schéma v PHP se musí shodovat s ukázkou bajt na bajt.

Soubory web/app/Sablony/Ikony.php a Grafika.php se generují z ukázky
(tools/prevod-grafiky.mjs), protože jsou to deterministická data. Tento test
hlídá, že převod nic nezkomolil a že skládání SVG v PHP dává totéž co v JS.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, z_php

JMENO = "grafika"


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_vsechny_ikony_i_motivy():
    ocek = ocekavane(JMENO)
    assert len(ocek["ikona"]) >= 44, "orákulum nepokrývá všechny ikony"
    assert len(ocek["motivRealizace"]) >= 10, "orákulum nepokrývá cyklus motivů"
    assert ocek["heroSchema"][0].startswith("<svg class=\"hero-schema\"")


def test_php_kresli_stejne_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:6])


def test_popis_realizace_se_escapuje():
    """Název realizace jde v ostré verzi z databáze, takže se smí editovat.
    V ukázce se vkládal do atributu bez ošetření; tady to projít nesmí."""
    import json
    import subprocess

    from tests.phpmod import KOREN

    utok = 'Hala" onload="zle()'
    kod = (
        'require ' + json.dumps(str(KOREN / "web/app/Jadro/Autoload.php")) + ';'
        'echo json_encode([App\\Sablony\\Grafika::motivRealizace(3,["popis"=>'
        + json.dumps(utok) + ']),'
        'App\\Sablony\\Ikony::ikona("sip",["popis"=>' + json.dumps(utok) + '])]);'
    )
    hotovo = subprocess.run(["php", "-r", kod], capture_output=True, text=True, timeout=60)
    assert hotovo.returncode == 0, hotovo.stderr[:400]
    for vystup in json.loads(hotovo.stdout):
        assert 'onload="zle()"' not in vystup, "název se vložil do atributu neošetřený"
        assert "&quot;" in vystup, "uvozovka se neescapovala"
