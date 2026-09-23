"""Akceptační test C-007 — tools/translate.py (překlad obsahu lokálním modelem).

Test nikdy nesahá na síť: klient modelu se do funkcí předává.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

PLOCHY = {
    "hero.title": "Vzduch, který dává smysl",
    "hero.lead": "Už {roky} let projektujeme TZB.",
    "nav.uvod": "Úvod",
}


@pytest.fixture()
def tool():
    sys.path.insert(0, str(ROOT))
    from tools import translate

    return translate


class FakeClient:
    """Vrací postupně připravené odpovědi a pamatuje si prompty."""

    def __init__(self, odpovedi):
        self.odpovedi = list(odpovedi)
        self.prompty = []

    def complete(self, prompt, **kwargs):
        self.prompty.append(prompt)
        return self.odpovedi.pop(0)


def test_chunk_strings_nerozdeli_jeden_klic(tool):
    davky = tool.chunk_strings(PLOCHY, max_chars=10)
    assert len(davky) == 3
    assert {k for d in davky for k in d} == set(PLOCHY)


def test_chunk_strings_sloucí_kratke_texty(tool):
    davky = tool.chunk_strings(PLOCHY, max_chars=10_000)
    assert davky == [PLOCHY]


def test_chunk_strings_prazdny_vstup(tool):
    assert tool.chunk_strings({}, max_chars=100) == []


def test_build_prompt_obsahuje_cilovy_jazyk_i_klice(tool):
    prompt = tool.build_prompt({"nav.uvod": "Úvod"}, "en", {"TZB": "building services"})
    assert "nav.uvod" in prompt and "Úvod" in prompt
    assert "TZB" in prompt and "building services" in prompt
    assert "English" in prompt or "english" in prompt.lower()


def test_build_prompt_pro_nemcinu(tool):
    prompt = tool.build_prompt({"nav.uvod": "Úvod"}, "de", {})
    assert "German" in prompt or "Deutsch" in prompt


def test_protect_placeholders(tool):
    chraneny, mapa = tool.protect_placeholders("Už {roky} let a {pocet} zakázek.")
    assert "{roky}" not in chraneny and "{pocet}" not in chraneny
    assert tool.restore_placeholders(chraneny, mapa) == "Už {roky} let a {pocet} zakázek."


def test_restore_placeholders_prezije_preklad_okoli(tool):
    chraneny, mapa = tool.protect_placeholders("Už {roky} let.")
    prelozeny = chraneny.replace("Už", "For").replace("let.", "years.")
    assert tool.restore_placeholders(prelozeny, mapa) == "For {roky} years."


def test_parse_response_vytahne_json_z_obalu(tool):
    text = 'Sure!\n```json\n{"nav.uvod": "Home"}\n```\nHotovo.'
    assert tool.parse_response(text, {"nav.uvod": "Úvod"}) == {"nav.uvod": "Home"}


def test_parse_response_odmitne_chybejici_klic(tool):
    with pytest.raises(ValueError):
        tool.parse_response('{"nav.uvod": "Home"}', {"nav.uvod": "Úvod", "nav.kontakt": "Kontakt"})


def test_parse_response_odmitne_nejson(tool):
    with pytest.raises(ValueError):
        tool.parse_response("Tady je překlad: Home", {"nav.uvod": "Úvod"})


def test_parse_response_zahodi_klice_navic(tool):
    assert tool.parse_response('{"a": "A", "b": "B"}', {"a": "Á"}) == {"a": "A"}


def test_translate_flat_prelozi_vsechny_klice(tool):
    klient = FakeClient([json.dumps({k: k.upper() for k in PLOCHY})])
    vysledek = tool.translate_flat(PLOCHY, "en", klient, max_chars=10_000)
    assert set(vysledek) == set(PLOCHY)
    assert klient.prompty


def test_translate_flat_opakuje_davku_po_chybe(tool):
    klient = FakeClient(["nesmysl bez json", json.dumps({k: "X" for k in PLOCHY})])
    vysledek = tool.translate_flat(PLOCHY, "en", klient, max_chars=10_000, pokusy=2)
    assert vysledek["nav.uvod"] == "X"
    assert len(klient.prompty) == 2


def test_translate_flat_po_vycerpani_pokusu_nechá_original(tool):
    klient = FakeClient(["nesmysl", "zase nesmysl"])
    vysledek = tool.translate_flat(PLOCHY, "en", klient, max_chars=10_000, pokusy=2)
    assert vysledek["nav.uvod"] == "Úvod"


def test_translate_flat_zachova_placeholdery(tool):
    klient = FakeClient([json.dumps({"hero.lead": "For {roky} years we design TZB."})])
    vysledek = tool.translate_flat({"hero.lead": PLOCHY["hero.lead"]}, "en", klient, max_chars=10_000)
    assert "{roky}" in vysledek["hero.lead"]


def test_translate_flat_preskoci_prazdne_hodnoty(tool):
    klient = FakeClient([json.dumps({"a": "A"})])
    vysledek = tool.translate_flat({"a": "Á", "b": ""}, "en", klient, max_chars=10_000)
    assert vysledek["b"] == ""


def test_klient_je_loopback_only(tool):
    with pytest.raises(ValueError):
        tool.LocalClient(base_url="https://api.openai.com/v1", model="x")
