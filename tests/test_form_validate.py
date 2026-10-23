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


def test_is_phone_cz_bere_i_pevne_linky_na_ctyrku(js):
    """46x je Liberec, 49x Pardubicko. Bez čtyřky web odmítal skutečná čísla."""
    zapisy = ["+420 485 100 100", "+420 466 123 456", "+420 412 123 456"]
    assert js('out(A.zapisy.map(m.isPhoneCz));', zapisy=zapisy) == [True] * 3


def test_is_phone_cz_odmita_nesmysly(js):
    zapisy = ["12345", "+420 736 532 2840", "abc", "+1 555 0100",
              "+420 136 532 284", "+420 836 532 284"]
    assert js('out(A.zapisy.map(m.isPhoneCz));', zapisy=zapisy) == [False] * 6


def test_is_phone_bere_zahranicni_cisla(js):
    """Nález testera: na německé a anglické verzi webu nešel zadat telefon.
    `+49 30 1234567` i `+421905123456` končily chybou „zkontrolujte číslo“."""
    zapisy = ["+49 30 1234567", "+421905123456", "+43 1 234 5678",
              "0049 30 1234567", "+44 20 7123 4567",
              "+420 736 532 284", "736532284"]
    assert js('out(A.zapisy.map(m.isPhone));', zapisy=zapisy) == [True] * 7


def test_is_phone_odmita_nesmysly(js):
    """Krátká čísla, chybějící předvolba, nuly a cokoli nad E.164."""
    zapisy = ["+1 555 0100", "12345", "abc", "", "+0123456789",
              "+4912345678901234", "49301234567", "+420 136 532 284"]
    assert js('out(A.zapisy.map(m.isPhone));', zapisy=zapisy) == [False] * 8


def test_zahranicni_telefon_projde_formularem(js):
    vysledek = js('out(m.validateContact({ ...A.platny, telefon: "+49 30 1234567" }));')
    assert vysledek["ok"] is True, vysledek["errors"]


def test_normalize_phone_sjednoti_tvar(js):
    zapisy = ["736 532 284", "+420736532284", "00420 736 532 284"]
    assert js('out(A.zapisy.map(m.normalizePhone));', zapisy=zapisy) == ["+420736532284"] * 3


def test_normalize_phone_prelozi_nuly_na_plus(js):
    zapisy = ["0049 30 1234567", "00421905123456", "00", "0012"]
    assert js('out(A.zapisy.map(m.normalizePhone));', zapisy=zapisy) == [
        "+49301234567", "+421905123456", "00", "0012",
    ]


# -------------------------------------------------------------- hlášky


def test_chyby_lze_prelozit_pres_slovnik(js):
    hlaska = js(
        'out(m.validateContact({ ...A.platny, telefon: "", email: "" }, { kontakt: "Nechte nám kontakt." }).messages.kontakt);'
    )
    assert hlaska == "Nechte nám kontakt."


def test_bez_slovniku_vrati_kod(js):
    assert js('out(m.validateContact({ ...A.platny, jmeno: "" }).messages.jmeno);') == "required"
