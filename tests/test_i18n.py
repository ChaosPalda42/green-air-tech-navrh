"""Akceptační test C-002 — src/lib/i18n.mjs (překlady, tečkové klíče)."""
from __future__ import annotations

import pytest

CS = {
    "nav": {"uvod": "Úvod", "sluzby": "Služby"},
    "hero": {"title": "Vzduch, který dává smysl", "lead": "Už {roky} let."},
    "prazdne": "",
}
EN = {"nav": {"uvod": "Home"}, "hero": {"lead": "For {roky} years."}}


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("i18n.mjs", body, args={"cs": CS, "en": EN, **args})

    return call


def test_get_cte_teckovou_cestu(js):
    assert js('out(m.get(A.cs, "nav.sluzby"));') == "Služby"


def test_get_vraci_null_pro_chybejici_klic(js):
    assert js('out(m.get(A.cs, "nav.kontakt"));') is None
    assert js('out(m.get(A.cs, "nav.uvod.hloubeji"));') is None


def test_t_pouzije_zaskok_kdyz_klic_chybi(js):
    assert js('out(m.t(A.en, "nav.sluzby", {}, A.cs));') == "Služby"


def test_t_dosadi_promenne(js):
    assert js('out(m.t(A.cs, "hero.lead", { roky: 30 }));') == "Už 30 let."


def test_t_vraci_klic_kdyz_neni_nikde(js):
    assert js('out(m.t(A.en, "nic.tady", {}, A.cs));') == "nic.tady"


def test_t_bere_zaskok_i_pro_prazdny_retezec(js):
    assert js('out(m.t({ prazdne: "" }, "prazdne", {}, { prazdne: "Náhrada" }));') == "Náhrada"


def test_flatten_vyrobi_teckove_klice(js):
    plochy = js('out(m.flatten(A.cs));')
    assert plochy["nav.uvod"] == "Úvod"
    assert plochy["hero.title"] == "Vzduch, který dává smysl"
    assert "nav" not in plochy


def test_flatten_zachova_pole_jako_indexy(js):
    plochy = js('out(m.flatten({ seznam: ["a", "b"] }));')
    assert plochy == {"seznam.0": "a", "seznam.1": "b"}


def test_unflatten_je_opacny_k_flatten(js):
    zpet = js('out(m.unflatten(m.flatten(A.cs)));')
    assert zpet == CS


def test_missing_keys_hlasi_chybejici_i_prazdne(js):
    chybi = js('out(m.missingKeys(A.cs, A.en));')
    assert set(chybi) == {"nav.sluzby", "hero.title"}


def test_missing_keys_hlasi_i_prazdnou_hodnotu_prekladu(js):
    chybi = js('out(m.missingKeys({ a: "text" }, { a: "   " }));')
    assert chybi == ["a"]


def test_missing_keys_je_prazdne_pro_uplny_slovnik(js):
    assert js('out(m.missingKeys(A.cs, A.cs));') == []
