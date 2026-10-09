"""Akceptační test C-008 — tools/zadani_ze_schuzky.py.

Z přepisu schůzky vytáhne požadavky na web. Přepis je citlivý materiál, takže
nástroj běží jen proti lokálnímu modelu a do výstupu nesmí pustit kontaktní
údaje. Test nikdy nesahá na síť — klient modelu se předává parametrem.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

PREPIS = """\
Michael: Dobrý den, tak bychom prošli ten návrh webu.
Klient: Líbí se nám to. Jen bychom chtěli přidat sekci s ceníkem servisu.
Michael: Dobře. Něco dalšího?
Klient: A ty realizace nahradíme našimi, pošlu fotky na info@greenairtech.cz.
Michael: Super, zavolejte na +420 736 532 284, až to budete mít.
"""


@pytest.fixture()
def nastroj():
    sys.path.insert(0, str(ROOT))
    from tools import zadani_ze_schuzky

    return zadani_ze_schuzky


class FalesnyKlient:
    """Vrací připravené odpovědi a pamatuje si prompty."""

    def __init__(self, odpovedi):
        self.odpovedi = list(odpovedi)
        self.prompty = []

    def complete(self, prompt, **kwargs):
        self.prompty.append(prompt)
        return self.odpovedi.pop(0) if self.odpovedi else ""


# ----------------------------------------------------------------- dělení


def test_rozdel_prepis_nerozdeli_radek(nastroj):
    casti = nastroj.rozdel_prepis(PREPIS, max_znaku=80)
    assert len(casti) > 1
    for cast in casti:
        for radek in cast.splitlines():
            assert radek in PREPIS


def test_rozdel_prepis_zachova_vsechen_text(nastroj):
    casti = nastroj.rozdel_prepis(PREPIS, max_znaku=80)
    spojeno = "\n".join(c.strip("\n") for c in casti)
    assert sorted(spojeno.split()) == sorted(PREPIS.split())


def test_rozdel_prepis_kratky_vstup_je_jedna_cast(nastroj):
    assert len(nastroj.rozdel_prepis(PREPIS, max_znaku=10_000)) == 1


def test_rozdel_prepis_prazdny_vstup(nastroj):
    assert nastroj.rozdel_prepis("", max_znaku=100) == []


# ------------------------------------------------------------------ prompt


def test_prompt_rika_modelu_vynechat_osobni_udaje(nastroj):
    prompt = nastroj.sestav_prompt("nějaký text", 1, 3)
    nizky = prompt.lower()
    assert "jméno" in nizky or "jmen" in nizky
    assert "telefon" in nizky or "e-mail" in nizky or "email" in nizky
    assert "nějaký text" in prompt


def test_prompt_nese_poradi_casti(nastroj):
    prompt = nastroj.sestav_prompt("x", 2, 5)
    assert "2" in prompt and "5" in prompt


# ------------------------------------------------------------------- body


def test_posbirej_body_vytahne_odrazky(nastroj):
    odpoved = "Tady jsou požadavky:\n- Přidat ceník servisu\n* Nahradit realizace\n1. Doplnit fotky\nDěkuji."
    assert nastroj.posbirej_body(odpoved) == [
        "Přidat ceník servisu",
        "Nahradit realizace",
        "Doplnit fotky",
    ]


def test_posbirej_body_zahodi_prazdne_a_duplicity(nastroj):
    odpoved = "- Ceník\n-\n- ceník\n-   \n- Fotky"
    assert nastroj.posbirej_body(odpoved) == ["Ceník", "Fotky"]


def test_posbirej_body_bez_odrazek(nastroj):
    assert nastroj.posbirej_body("Žádné požadavky nezazněly.") == []


def test_sluc_body_spoji_a_odstrani_duplicity(nastroj):
    slouceno = nastroj.sluc_body([["Ceník", "Fotky"], ["fotky", "Kariéra"]])
    assert slouceno == ["Ceník", "Fotky", "Kariéra"]


# --------------------------------------------------- pojistka na osobní údaje


def test_rozpozna_kontaktni_udaje(nastroj):
    assert nastroj.obsahuje_kontaktni_udaj("Pošlou to na info@greenairtech.cz")
    assert nastroj.obsahuje_kontaktni_udaj("Volat na +420 736 532 284")
    assert nastroj.obsahuje_kontaktni_udaj("Číslo 736532284 je přímé")


def test_bezny_pozadavek_neni_kontaktni_udaj(nastroj):
    assert not nastroj.obsahuje_kontaktni_udaj("Přidat ceník servisu")
    assert not nastroj.obsahuje_kontaktni_udaj("Sekce s referencemi za rok 2026")


# ------------------------------------------------------------- zpracování


def test_zpracuj_vrati_body_z_modelu(nastroj):
    klient = FalesnyKlient(["- Přidat ceník servisu\n- Nahradit realizace"])
    vysledek = nastroj.zpracuj(PREPIS, klient, max_znaku=10_000)
    assert vysledek["body"] == ["Přidat ceník servisu", "Nahradit realizace"]
    assert vysledek["vyrazeno"] == []
    assert len(klient.prompty) == 1


def test_zpracuj_vyradi_body_s_kontaktnimi_udaji(nastroj):
    klient = FalesnyKlient(["- Přidat ceník\n- Fotky pošlou na info@greenairtech.cz"])
    vysledek = nastroj.zpracuj(PREPIS, klient, max_znaku=10_000)
    assert vysledek["body"] == ["Přidat ceník"]
    assert len(vysledek["vyrazeno"]) == 1


def test_zpracuj_projde_vsechny_casti(nastroj):
    klient = FalesnyKlient(["- První", "- Druhý", "- Třetí", "- Čtvrtý", "- Pátý"])
    vysledek = nastroj.zpracuj(PREPIS, klient, max_znaku=80)
    assert len(klient.prompty) == len(nastroj.rozdel_prepis(PREPIS, max_znaku=80))
    assert "První" in vysledek["body"]


def test_zpracuj_prezije_prazdnou_odpoved(nastroj):
    klient = FalesnyKlient(["", "- Ceník"])
    vysledek = nastroj.zpracuj(PREPIS, klient, max_znaku=80)
    assert "Ceník" in vysledek["body"]


def test_zpracuj_prazdny_prepis(nastroj):
    klient = FalesnyKlient([])
    assert nastroj.zpracuj("", klient, max_znaku=100) == {"body": [], "vyrazeno": []}


# ---------------------------------------------------------------- výstup


def test_zapis_markdown_ma_hlavicku_i_body(nastroj):
    text = nastroj.zapis_markdown({"body": ["Přidat ceník", "Nahradit realizace"], "vyrazeno": []}, "2026-10-09")
    assert text.startswith("#")
    assert "2026-10-09" in text
    assert "- Přidat ceník" in text
    assert "- Nahradit realizace" in text


def test_zapis_markdown_hlasi_vyrazene_body(nastroj):
    text = nastroj.zapis_markdown({"body": ["Ceník"], "vyrazeno": ["něco s e-mailem"]}, "2026-10-09")
    assert "1" in text
    assert "něco s e-mailem" not in text, "vyřazený bod se nesmí dostat do výstupu"


def test_klient_je_jen_loopback(nastroj):
    with pytest.raises(ValueError):
        nastroj.LocalClient(base_url="https://api.openai.com/v1", model="x")
