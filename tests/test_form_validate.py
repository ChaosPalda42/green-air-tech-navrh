"""Akceptační test C-004 — src/lib/form-validate.mjs (kontaktní formulář).

Po schůzce 9. 10. 2026 je formulář co nejkratší: povinné je jen „co řešíte“,
jméno, souhlas a aspoň jeden kontaktní údaj. Zpráva je nepovinná.
"""
from __future__ import annotations

import pytest

PLATNY = {
    "typ": "servis",
    "jmeno": "Jan Novák",
    "telefon": "+420 736 532 284",
    "email": "",
    "zprava": "",
    "souhlas": True,
}


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("form-validate.mjs", body, args={"platny": PLATNY, **args})

    return call


# ------------------------------------------------------------- průchod


def test_staci_typ_jmeno_telefon_a_souhlas(js):
    vysledek = js('out(m.validateContact(A.platny));')
    assert vysledek["ok"] is True
    assert vysledek["errors"] == {}


def test_misto_telefonu_staci_email(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "", email: "jan@novak.cz" }));')
    assert vysledek["ok"] is True


def test_zprava_neni_povinna(js):
    assert js('out(m.validateContact({ ...A.platny, zprava: "" }).ok);') is True
    assert js('out(m.validateContact({ ...A.platny, zprava: "   " }).ok);') is True


# ------------------------------------------------------------- povinná pole


def test_typ_poptavky_je_povinny(js):
    vysledek = js('out(m.validateContact({ ...A.platny, typ: "" }));')
    assert vysledek["errors"]["typ"] == "required"


def test_jmeno_je_povinne(js):
    assert js('out(m.validateContact({ ...A.platny, jmeno: "   " }).errors.jmeno);') == "required"


def test_souhlas_je_povinny(js):
    assert js('out(m.validateContact({ ...A.platny, souhlas: false }).errors.souhlas);') == "souhlas"


def test_bez_telefonu_i_emailu_chybi_kontakt(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "", email: "" }));')
    assert vysledek["errors"]["kontakt"] == "kontakt"
    assert "email" not in vysledek["errors"]
    assert "telefon" not in vysledek["errors"]


def test_prazdny_formular_hlasi_vsechno_podstatne(js):
    vysledek = js('out(m.validateContact({}));')
    assert vysledek["ok"] is False
    for pole in ("typ", "jmeno", "kontakt", "souhlas"):
        assert pole in vysledek["errors"], f"chybí hlášení pro {pole}"


# --------------------------------------------------------------- tvary


def test_spatny_email(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "", email: "jan@novak" }));')
    assert vysledek["errors"]["email"] == "email"
    assert "kontakt" not in vysledek["errors"], "vyplněný e-mail se počítá jako kontakt"


def test_spatny_telefon(js):
    assert js('out(m.validateContact({ ...A.platny, telefon: "12345" }).errors.telefon);') == "telefon"


def test_kratka_zprava_kdyz_je_vyplnena(js):
    assert js('out(m.validateContact({ ...A.platny, zprava: "Ahoj" }).errors.zprava);') == "zprava-kratka"
    assert js('out(m.validateContact({ ...A.platny, zprava: "Potřebuji servis klimatizace." }).ok);') is True


def test_is_email(js):
    assert js('out(["a@b.cz", "jan.novak@green-air.tech"].map(m.isEmail));') == [True, True]
    assert js('out(["a@b", "a b@c.cz", "@b.cz", "a@.cz", ""].map(m.isEmail));') == [False] * 5


def test_is_phone_cz_bere_bezne_zapisy(js):
    zapisy = ["+420 736 532 284", "736532284", "+420736532284", "736 532 284", "00420 736 532 284"]
    assert js('out(A.zapisy.map(m.isPhoneCz));', zapisy=zapisy) == [True] * 5


def test_is_phone_cz_odmita_nesmysly(js):
    zapisy = ["12345", "+420 736 532 2840", "abc", "+1 555 0100"]
    assert js('out(A.zapisy.map(m.isPhoneCz));', zapisy=zapisy) == [False] * 4


def test_normalize_phone_sjednoti_tvar(js):
    zapisy = ["736 532 284", "+420736532284", "00420 736 532 284"]
    assert js('out(A.zapisy.map(m.normalizePhone));', zapisy=zapisy) == ["+420736532284"] * 3


# -------------------------------------------------------------- hlášky


def test_chyby_lze_prelozit_pres_slovnik(js):
    hlaska = js(
        'out(m.validateContact({ ...A.platny, telefon: "", email: "" }, { kontakt: "Nechte nám kontakt." }).messages.kontakt);'
    )
    assert hlaska == "Nechte nám kontakt."


def test_bez_slovniku_vrati_kod(js):
    assert js('out(m.validateContact({ ...A.platny, jmeno: "" }).messages.jmeno);') == "required"
