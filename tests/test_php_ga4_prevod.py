"""Akceptační test C-026 — App\\Statistiky\\Ga4Prevod.

Dvě vrstvy. Jedna porovnává PHP proti vzorkům v tests/orakulum/ga4.json
(vyrobila je referenční implementace tools/gen-ga4-orakulum.py). Druhá opisuje
pravidla samostatně a měří je na výstupu PHP, takže by červeně svítila i tehdy,
kdyby se orákulum a kód mýlily stejně.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.phpmod import ocekavane, rozdily, vstupy, z_php

JMENO = "ga4"
KLICE_DNE = ["datum", "navstevy", "uzivatele", "zobrazeni", "poptavky", "cas", "opusteni"]


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    for funkce in ("dny", "rozpad"):
        assert ocek.get(funkce), f"{funkce}: žádné vzorky"
    # bez těchhle vzorků je brána slepá na to, na čem to padá
    args = vstupy(JMENO)
    assert any(a[1] > len(a[0].get("rows") or []) for a in args["dny"]), \
        "chybí vzorek, kde se musí doplnit chybějící dny"
    assert any((a[0].get("metricHeaders") or [{}])[0].get("name") != "sessions"
               for a in args["dny"]), \
        "chybí vzorek s jiným pořadím metrik (hledá se podle jména, ne pozice)"
    assert any(len(a[3] or {}) > 0 for a in args["dny"]), \
        "chybí vzorek s poptávkami z naší databáze"
    assert any(len(a[0].get("rows") or []) > a[2] for a in args["rozpad"]), \
        "chybí vzorek, kde se seznam krátí na maxRadku"


def test_php_odpovida_vzorkum(vysledky):
    neshody = rozdily(JMENO, vysledky)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_dny_jsou_souvisla_rada(vysledky):
    """Pravidlo samo: přesně $pocet dnů, nejstarší první, poslední je $konec,
    žádná mezera, klíče v daném pořadí a správné typy."""
    for i, (args, dny) in enumerate(zip(vstupy(JMENO)["dny"], vysledky["dny"])):
        assert isinstance(dny, list), f"vzorek {i}: {dny}"
        pocet, konec = args[1], args[2]
        assert len(dny) == pocet, f"vzorek {i}: {len(dny)} dnů místo {pocet}"
        ocekavane_datum = date.fromisoformat(konec) - timedelta(days=pocet - 1)
        for den in dny:
            assert list(den.keys()) == KLICE_DNE, f"vzorek {i}: klíče {list(den.keys())}"
            assert den["datum"] == ocekavane_datum.isoformat(), \
                f"vzorek {i}: {den['datum']} místo {ocekavane_datum}"
            for klic in ("navstevy", "uzivatele", "zobrazeni", "poptavky"):
                assert isinstance(den[klic], int) and den[klic] >= 0, \
                    f"vzorek {i} {den['datum']}: {klic} = {den[klic]!r}"
            assert isinstance(den["cas"], (int, float)) and den["cas"] >= 0
            assert 0 <= den["opusteni"] <= 100, (
                f"vzorek {i} {den['datum']}: opusteni {den['opusteni']} — "
                "GA4 dává 0..1, na nástěnku se posílají procenta"
            )
            ocekavane_datum += timedelta(days=1)


def test_rozpad_dava_dohromady_sto(vysledky):
    """Pravidlo samo: podíly jsou procenta, sečtou se přesně na 100, řadí se
    od největšího, nulové řádky se nevypisují a víc než maxRadku jich není."""
    for i, (args, radky) in enumerate(zip(vstupy(JMENO)["rozpad"], vysledky["rozpad"])):
        assert isinstance(radky, list), f"vzorek {i}: {radky}"
        maxRadku = args[2]
        assert len(radky) <= max(0, maxRadku), f"vzorek {i}: {len(radky)} řádků"
        if not radky:
            continue
        podily = [r["podil"] for r in radky]
        for r in radky:
            assert list(r.keys()) == ["nazev", "podil"], f"vzorek {i}: klíče {list(r.keys())}"
            assert isinstance(r["podil"], int), f"vzorek {i}: podíl {r['podil']!r} není celé číslo"
        assert podily == sorted(podily, reverse=True), f"vzorek {i}: {podily} není od největšího"
        celkem = sum(float(m["metricValues"][0]["value"]) for m in (args[0].get("rows") or []))
        if celkem > 0:
            assert sum(podily) == 100, f"vzorek {i}: součet {sum(podily)} místo 100"
            assert all(p > 0 for p in podily), f"vzorek {i}: nulový řádek se nemá vypisovat"
        else:
            assert all(p == 0 for p in podily), f"vzorek {i}: {podily} bez dat"
        jmena = [r["nazev"] for r in radky]
        assert len(jmena) == len(set(jmena)), f"vzorek {i}: {jmena} — stejná jména se mají sečíst"


def test_vstup_se_nemeni(vysledky):
    """Čistý převod: dvakrát totéž dá totéž a nic se po cestě nemutuje."""
    assert vysledky == z_php(JMENO), "druhý běh dal jiné výsledky"
