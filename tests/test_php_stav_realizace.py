"""Akceptační test C-025 — App\\Obsah\\StavRealizace (přidané, změněné a smazané realizace).

Stejné orákulum jako u textů (tests/orakulum/cms-store.json, vzorky z běhu
src/lib/cms-store.mjs nad skutečnými daty webu), jen jiná část: upsertRealizace,
removeRealizace a mergeRealizace.
"""
from __future__ import annotations

import pytest

from tests.phpmod import ocekavane, rozdily, vstupy, z_php

JMENO = "cms-store"
MOJE = {"upsertRealizace", "removeRealizace", "mergeRealizace"}


@pytest.fixture(scope="module")
def vysledky():
    return z_php(JMENO)


def test_orakulum_ma_co_merit():
    ocek = ocekavane(JMENO)
    chybi = MOJE - set(ocek)
    assert not chybi, f"orákulum nezná {sorted(chybi)}"
    for funkce in sorted(MOJE):
        assert ocek[funkce], f"{funkce}: žádné vzorky"


def test_orakulum_hlida_razeni_i_polozku_bez_data():
    """Dvě pravidla, na která se zapomíná: novější první a položka bez data
    je nejstarší, tedy úplně poslední."""
    vysledek = ocekavane(JMENO)["mergeRealizace"]
    dlouhy = max(vysledek, key=len)
    data = [p.get("datum") for p in dlouhy]
    assert data == sorted([d for d in data if d], reverse=True), "vzorek neukazuje řazení odzadu"
    sbez = [v for v in vysledek if any(not p.get("datum") for p in v)]
    assert sbez, "chybí vzorek s položkou bez data"
    for v in sbez:
        assert not v[-1].get("datum"), "položka bez data musí být poslední"


def test_zadna_polozka_si_neodnese_pomocny_priznak():
    """Příznak 'ze základu / přidaná' je jen pro řazení a nesmí prosáknout ven."""
    for vysledek in ocekavane(JMENO)["mergeRealizace"]:
        for p in vysledek:
            assert "_source" not in p, "ve vzorcích je _source — orákulum je vadné"


def test_php_se_chova_jako_ukazka(vysledky):
    neshody = rozdily(JMENO, vysledky, jen=MOJE)
    assert not neshody, f"{len(neshody)} neshod:\n" + "\n".join(neshody[:10])


def test_id_se_vyrabi_z_nazvu_az_do_kolize(vysledky):
    """Mezi vzorky musí být případ, kdy se stejný název přidává dvakrát —
    jinak brána neuvidí, jestli se při kolizi připojuje -2."""
    args = vstupy(JMENO)["upsertRealizace"]
    bezId = [a for a in args if not (a[1] or {}).get("id")]
    assert len(bezId) >= 2, "chybí vzorky bez zadaného id"
    nazvy = [(a[1] or {}).get("nazev") for a in bezId]
    assert len(nazvy) != len(set(nazvy)), "chybí vzorek s kolizí názvů"


def test_vstup_se_nemeni(vysledky):
    druhy = z_php(JMENO)
    moje = {f: v for f, v in vysledky.items() if f in MOJE}
    assert moje == {f: v for f, v in druhy.items() if f in MOJE}, \
        "druhý běh dal jiné výsledky — nějaká metoda mutuje vstup"
