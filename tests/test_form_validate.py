"""Akceptační test C-004 — src/lib/form-validate.mjs (kontaktní formulář)."""
from __future__ import annotations

import pytest

PLATNY = {
    "jmeno": "Jan Novák",
    "email": "jan@novak.cz",
    "telefon": "+420 736 532 284",
    "typ": "servis",
    "zprava": "Potřebujeme servis vzduchotechniky v hale.",
    "souhlas": True,
}


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("form-validate.mjs", body, args={"platny": PLATNY, **args})

    return call


def test_platny_formular_projde(js):
    vysledek = js('out(m.validateContact(A.platny));')
    assert vysledek["ok"] is True
    assert vysledek["errors"] == {}


def test_chybejici_povinna_pole(js):
    vysledek = js('out(m.validateContact({ souhlas: false }));')
    assert vysledek["ok"] is False
    assert vysledek["errors"]["jmeno"] == "required"
    assert vysledek["errors"]["email"] == "required"
    assert vysledek["errors"]["zprava"] == "required"
    assert vysledek["errors"]["souhlas"] == "souhlas"


def test_telefon_neni_povinny(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "" }));')
    assert vysledek["ok"] is True


def test_samotne_mezery_jsou_prazdna_hodnota(js):
    vysledek = js('out(m.validateContact({ ...A.platny, jmeno: "   " }));')
    assert vysledek["errors"]["jmeno"] == "required"


def test_spatny_email(js):
    vysledek = js('out(m.validateContact({ ...A.platny, email: "jan@novak" }));')
    assert vysledek["errors"]["email"] == "email"


def test_kratka_zprava(js):
    vysledek = js('out(m.validateContact({ ...A.platny, zprava: "Ahoj" }));')
    assert vysledek["errors"]["zprava"] == "zprava-kratka"


def test_spatny_telefon(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "12345" }));')
    assert vysledek["errors"]["telefon"] == "telefon"


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


def test_chyby_lze_prelozit_pres_slovnik(js):
    hlaska = js(
        'out(m.validateContact({ ...A.platny, email: "x" }, { email: "Zkontrolujte e-mail." }).messages.email);'
    )
    assert hlaska == "Zkontrolujte e-mail."
