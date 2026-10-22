"""Akceptační test C-011 — web/app/Obsah/Datum.php.

Ukázka formátovala datumy přes Intl.DateTimeFormat. Na klientově serveru
nechceme závislost na rozšíření intl ani na verzi ICU, takže PHP si měsíce
pojmenovává samo — a musí vracet přesně to, co stojí v ukázce.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, vstupy, z_php, zkratka

JMENO = "datum"


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_vsechny_datumy_odpovidaji_ukazce(vysledky):
    ocek = ocekavane(JMENO)["format"]
    mam = vysledky["format"]
    args = vstupy(JMENO)["format"]
    assert len(mam) == len(ocek)
    rozdily = [
        f"{a}: čekáno {o!r}, přišlo {m!r}"
        for a, o, m in zip(args, ocek, mam)
        if o != m
    ]
    assert not rozdily, "\n".join(rozdily[:12])


def test_orakulum_opravdu_neco_meri():
    ocek = ocekavane(JMENO)["format"]
    assert len(ocek) >= 60
    assert "22. října 2026" in ocek, "chybí plný český tvar"
    assert "říjen 2026" in ocek, "chybí měsíční český tvar"
    assert "24 December 2026" in ocek, "chybí anglický tvar"
    assert "24. Dezember 2026" in ocek, "chybí německý tvar"


def test_cizi_jazyk_nespadne_ale_vrati_text(vysledky):
    import json
    import subprocess
    from tests.phpmod import KOREN

    kod = (
        'require "' + str(KOREN / "web/app/Jadro/Autoload.php") + '";'
        'echo json_encode([App\\Obsah\\Datum::format("xx","2026-10-22","plny"),'
        'App\\Obsah\\Datum::format("cs","2026-10-22","neznamy")],JSON_UNESCAPED_UNICODE);'
    )
    hotovo = subprocess.run(["php", "-r", kod], capture_output=True, text=True, timeout=60)
    assert hotovo.returncode == 0, hotovo.stderr[:400]
    zalozni, neznamy_tvar = json.loads(hotovo.stdout)
    assert zalozni == "22. října 2026", f"neznámý jazyk má padnout na češtinu, přišlo {zalozni!r}"
    assert neznamy_tvar == "22. října 2026", f"neznámý tvar má dát plný datum, přišlo {neznamy_tvar!r}"
