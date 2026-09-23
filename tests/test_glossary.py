"""Akceptační test C-001 — src/lib/glossary.mjs (vysvětlivky zkratek)."""
from __future__ import annotations

import pytest

TERMS = [
    {"abbr": "TZB", "full": "technická zařízení budov", "popis": "Vše, co v budově rozvádí vzduch, teplo, chlad a vodu."},
    {"abbr": "VZT", "full": "vzduchotechnika", "popis": "Systém rozvodu a úpravy vzduchu."},
    {"abbr": "PENB", "full": "průkaz energetické náročnosti budovy", "popis": "Povinný dokument."},
    {"abbr": "PM2,5", "full": "jemné prachové částice", "popis": "Částice do 2,5 mikrometru."},
    {"abbr": "PM", "full": "prachové částice", "popis": "Polétavý prach."},
    {"abbr": "ČSN", "full": "česká technická norma", "popis": "Norma."},
]


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("glossary.mjs", body, args={"terms": TERMS, **args})

    return call


def test_obali_samostatnou_zkratku(js):
    html = js('out(m.annotate("Projekce TZB na klíč", A.terms));')
    assert html == 'Projekce <abbr class="zkratka" tabindex="0" data-abbr="TZB">TZB</abbr> na klíč'


def test_nesaha_dovnitr_znacek(js):
    src = '<a href="/servis-tzb" title="TZB" data-x="VZT">servis</a>'
    assert js('out(m.annotate(A.src, A.terms));', src=src) == src


def test_nezdvojuje_existujici_abbr(js):
    src = 'servis <abbr class="zkratka" data-abbr="VZT">VZT</abbr> zařízení'
    assert js('out(m.annotate(A.src, A.terms));', src=src) == src


def test_respektuje_hranice_slova(js):
    assert "abbr" not in js('out(m.annotate("TZBX a XTZB a VZTkou", A.terms));')
    zavorka = js('out(m.annotate("norma (ČSN) platí", A.terms));')
    assert zavorka == 'norma (<abbr class="zkratka" tabindex="0" data-abbr="ČSN">ČSN</abbr>) platí'


def test_delsi_zkratka_ma_prednost(js):
    html = js('out(m.annotate("obsah PM2,5 ve vzduchu", A.terms));')
    assert 'data-abbr="PM2,5"' in html
    assert 'data-abbr="PM"' not in html


def test_volba_once_obali_jen_prvni_vyskyt(js):
    html = js('out(m.annotate("VZT a zase VZT", A.terms, { once: true }));')
    assert html.count("<abbr") == 1
    assert html.endswith("a zase VZT")


def test_prazdny_seznam_nic_nemeni(js):
    assert js('out(m.annotate("VZT a TZB", []));') == "VZT a TZB"


def test_text_bez_zkratek_zustava(js):
    assert js('out(m.annotate("Servis a údržba budov", A.terms));') == "Servis a údržba budov"


def test_find_term_je_case_insensitive(js):
    nalez = js('out(m.findTerm(A.terms, "tzb"));')
    assert nalez["full"] == "technická zařízení budov"
    assert js('out(m.findTerm(A.terms, "XYZ"));') is None


def test_sort_terms_radi_ceskou_abecedou(js):
    poradi = js('out(m.sortTerms(A.terms).map(t => t.abbr));')
    assert poradi == ["ČSN", "PENB", "PM", "PM2,5", "TZB", "VZT"]


def test_group_terms_seskupi_podle_pismene(js):
    skupiny = js('out(m.groupTerms(A.terms));')
    mapa = {g["letter"]: [t["abbr"] for t in g["items"]] for g in skupiny}
    assert mapa["P"] == ["PENB", "PM", "PM2,5"]
    assert mapa["Č"] == ["ČSN"]
    assert [g["letter"] for g in skupiny] == ["Č", "P", "T", "V"]
