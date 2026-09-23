"""Akceptační test C-005 — src/lib/realizace-filter.mjs (filtr referencí)."""
from __future__ import annotations

import pytest

ITEMS = [
    {"id": "a", "nazev": "Bytový dům Praha 8", "datum": "2026-04-10", "kategorie": ["vzt"], "misto": "Praha", "perex": "Rekuperace bytů."},
    {"id": "b", "nazev": "Výrobní hala Milevsko", "datum": "2025-06-02", "kategorie": ["vzt", "chlazeni"], "misto": "Milevsko", "perex": "Chlazení lisovny."},
    {"id": "c", "nazev": "Poliklinika Písek", "datum": "2025-11-20", "kategorie": ["chlazeni"], "misto": "Písek", "perex": "Klimatizace ordinací."},
    {"id": "d", "nazev": "Škola Tábor", "datum": "2024-08-30", "kategorie": ["tepelna-cerpadla"], "misto": "Tábor", "perex": "Tepelná čerpadla."},
]


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("realizace-filter.mjs", body, args={"items": ITEMS, **args})

    return call


def ids(rows):
    return [r["id"] for r in rows]


def test_bez_filtru_vrati_vse(js):
    assert ids(js('out(m.filterItems(A.items, {}));')) == ["a", "b", "c", "d"]


def test_filtr_podle_kategorie(js):
    assert ids(js('out(m.filterItems(A.items, { kategorie: "vzt" }));')) == ["a", "b"]


def test_kategorie_vse_nefiltruje(js):
    assert len(js('out(m.filterItems(A.items, { kategorie: "vse" }));')) == 4


def test_fulltext_hleda_v_nazvu_miste_i_perexu(js):
    assert ids(js('out(m.filterItems(A.items, { dotaz: "milevsko" }));')) == ["b"]
    assert ids(js('out(m.filterItems(A.items, { dotaz: "klimatizace" }));')) == ["c"]


def test_fulltext_ignoruje_diakritiku_a_velikost(js):
    assert ids(js('out(m.filterItems(A.items, { dotaz: "PISEK" }));')) == ["c"]
    assert ids(js('out(m.filterItems(A.items, { dotaz: "tepelna cerpadla" }));')) == ["d"]


def test_filtr_podle_roku(js):
    assert ids(js('out(m.filterItems(A.items, { rok: 2025 }));')) == ["b", "c"]


def test_filtry_se_kombinuji(js):
    assert ids(js('out(m.filterItems(A.items, { kategorie: "chlazeni", rok: 2025, dotaz: "hala" }));')) == ["b"]


def test_prazdny_vysledek_je_pole(js):
    assert js('out(m.filterItems(A.items, { dotaz: "zzz" }));') == []


def test_collect_kategorie_se_spocty(js):
    assert js('out(m.collectKategorie(A.items));') == [
        {"id": "chlazeni", "count": 2},
        {"id": "vzt", "count": 2},
        {"id": "tepelna-cerpadla", "count": 1},
    ]


def test_collect_roky_sestupne(js):
    assert js('out(m.collectRoky(A.items));') == [2026, 2025, 2024]


def test_sort_items(js):
    assert ids(js('out(m.sortItems(A.items, "nejnovejsi"));')) == ["a", "c", "b", "d"]
    assert ids(js('out(m.sortItems(A.items, "nejstarsi"));')) == ["d", "b", "c", "a"]
    assert ids(js('out(m.sortItems(A.items, "nazev"));')) == ["a", "c", "d", "b"]


def test_sort_nemeni_vstupni_pole(js):
    assert js('out((() => { const kopie = A.items.slice(); m.sortItems(kopie, "nazev"); return kopie[0].id; })());') == "a"


def test_paginate(js):
    strana = js('out(m.paginate(A.items, 2, 3));')
    assert ids(strana["items"]) == ["d"]
    assert strana["page"] == 2
    assert strana["pages"] == 2
    assert strana["total"] == 4


def test_paginate_orizne_mimo_rozsah(js):
    strana = js('out(m.paginate(A.items, 99, 3));')
    assert strana["page"] == 2
    assert ids(strana["items"]) == ["d"]


def test_paginate_prazdny_seznam(js):
    strana = js('out(m.paginate([], 1, 3));')
    assert strana == {"items": [], "page": 1, "pages": 1, "total": 0}
