"""Akceptační test C-010 — src/lib/fotky.mjs (galerie fotek u realizace).

Klient chtěl k realizacím nahrávat fotky. Tahle vrstva je čistá logika:
pořadí, limity a formátování. Zmenšování přes canvas a čtení souboru dělá
admin.js, sem se dostane až hotová data URL.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("fotky.mjs", body, args=args)

    return call


def fotka(ident: str, bajty: int = 100_000, data: str | None = None) -> dict:
    return {
        "id": ident,
        "nazev": f"{ident}.jpg",
        "typ": "image/jpeg",
        "sirka": 1600,
        "vyska": 1000,
        "bajty": bajty,
        "dataUrl": data or f"data:image/jpeg;base64,{ident}",
    }


# ------------------------------------------------------------ normalizace


def test_normalizuj_propusti_jen_platne(js):
    vstup = [
        fotka("a"),
        None,
        "nesmysl",
        {"id": "", "dataUrl": "data:image/png;base64,x"},
        {"id": "b", "dataUrl": "https://example.com/x.jpg"},
        {"id": "c", "dataUrl": "data:image/png;base64,c"},
    ]
    vysledek = js("out(m.normalizujGalerie(A.vstup));", vstup=vstup)
    assert [f["id"] for f in vysledek] == ["a", "c"]


def test_normalizuj_doplni_chybejici_pole(js):
    vysledek = js('out(m.normalizujGalerie([{ id: "x", dataUrl: "data:image/png;base64,x" }])[0]);')
    assert vysledek["nazev"] == ""
    assert vysledek["typ"] == ""
    assert vysledek["sirka"] == 0 and vysledek["vyska"] == 0 and vysledek["bajty"] == 0


def test_normalizuj_zahodi_duplicitni_id(js):
    vstup = [fotka("a"), fotka("a", data="data:image/jpeg;base64,jiny"), fotka("b")]
    assert [f["id"] for f in js("out(m.normalizujGalerie(A.vstup));", vstup=vstup)] == ["a", "b"]


def test_normalizuj_zvladne_nesmysly(js):
    for vstup in ("null", "undefined", '"text"', "42", "{}"):
        assert js(f"out(m.normalizujGalerie({vstup}));") == []


def test_normalizuj_nemutuje_vstup(js):
    vysledek = js(
        """
        const vstup = [{ id: "a", dataUrl: "data:image/png;base64,a" }];
        const out1 = m.normalizujGalerie(vstup);
        out1[0].nazev = "zmena";
        out({ puvodni: vstup[0].nazev === undefined, novy: out1[0].nazev });
        """
    )
    assert vysledek == {"puvodni": True, "novy": "zmena"}


# -------------------------------------------------------------- kontrola


def test_prijme_bezne_obrazky(js):
    for typ in ("image/jpeg", "image/png", "image/webp"):
        vysledek = js(
            'out(m.zkontrolujSoubor({ nazev: "a", typ: A.typ, velikost: 2000000 }));', typ=typ
        )
        assert vysledek == {"ok": True, "chyba": None}


def test_odmitne_jiny_typ(js):
    for typ in ("application/pdf", "image/heic", "text/plain", ""):
        assert js('out(m.zkontrolujSoubor({ typ: A.typ, velikost: 100 }).chyba);', typ=typ) == "typ"


def test_odmitne_prilis_velky_soubor(js):
    assert js('out(m.zkontrolujSoubor({ typ: "image/jpeg", velikost: 13 * 1024 * 1024 }).chyba);') == "velikost"
    assert js('out(m.zkontrolujSoubor({ typ: "image/jpeg", velikost: 12 * 1024 * 1024 }).ok);') is True


# --------------------------------------------------------------- rozměry


def test_cilovy_rozmer_zmensi_a_zachova_pomer(js):
    assert js("out(m.cilovyRozmer(4000, 3000, 1600));") == {"sirka": 1600, "vyska": 1200}
    assert js("out(m.cilovyRozmer(3000, 4000, 1600));") == {"sirka": 1200, "vyska": 1600}


def test_cilovy_rozmer_nezvetsuje(js):
    assert js("out(m.cilovyRozmer(800, 600, 1600));") == {"sirka": 800, "vyska": 600}


def test_cilovy_rozmer_vychozi_hrana(js):
    assert js("out(m.cilovyRozmer(4000, 2000));") == {"sirka": 1600, "vyska": 800}


def test_cilovy_rozmer_nesmyslny_vstup(js):
    for vstup in ("0, 100", "100, 0", "-5, 10", '"a", 10'):
        assert js(f"out(m.cilovyRozmer({vstup}, 1600));") == {"sirka": 0, "vyska": 0}


def test_cilovy_rozmer_nikdy_nenuluje_kratkou_stranu(js):
    assert js("out(m.cilovyRozmer(4000, 3, 1600));")["vyska"] >= 1


# ---------------------------------------------------------- odhad velikosti


def test_odhadni_bajty_z_data_url(js):
    # "AAAA" = 3 bajty, "AAA=" = 2 bajty, "AA==" = 1 bajt
    assert js('out(m.odhadniBajty("data:image/png;base64,AAAA"));') == 3
    assert js('out(m.odhadniBajty("data:image/png;base64,AAA="));') == 2
    assert js('out(m.odhadniBajty("data:image/png;base64,AA=="));') == 1


def test_odhadni_bajty_mimo_data_url(js):
    for vstup in ('"https://a.cz/x.png"', '""', "null", "42"):
        assert js(f"out(m.odhadniBajty({vstup}));") == 0


# ---------------------------------------------------------------- přidání


def test_pridani_prida_na_konec(js):
    galerie = [fotka("a")]
    vysledek = js("out(m.pridejFotky(A.galerie, [A.nova]));", galerie=galerie, nova=fotka("b"))
    assert [f["id"] for f in vysledek["galerie"]] == ["a", "b"]
    assert vysledek["pridano"] == 1
    assert vysledek["odmitnuto"] == []


def test_pridani_nemutuje_vstup(js):
    vysledek = js(
        """
        const g = [A.a];
        const r = m.pridejFotky(g, [A.b]);
        out({ puvodni: g.length, novy: r.galerie.length });
        """,
        a=fotka("a"),
        b=fotka("b"),
    )
    assert vysledek == {"puvodni": 1, "novy": 2}


def test_pridani_odmitne_duplikat(js):
    galerie = [fotka("a", data="data:image/jpeg;base64,stejny")]
    nova = fotka("b", data="data:image/jpeg;base64,stejny")
    vysledek = js("out(m.pridejFotky(A.galerie, [A.nova]));", galerie=galerie, nova=nova)
    assert vysledek["pridano"] == 0
    assert vysledek["odmitnuto"] == [{"nazev": "b.jpg", "duvod": "duplikat"}]


def test_pridani_odmitne_duplikat_i_v_jedne_davce(js):
    davka = [fotka("a", data="data:image/jpeg;base64,x"), fotka("b", data="data:image/jpeg;base64,x")]
    vysledek = js("out(m.pridejFotky([], A.davka));", davka=davka)
    assert vysledek["pridano"] == 1
    assert [o["duvod"] for o in vysledek["odmitnuto"]] == ["duplikat"]


def test_pridani_hlida_pocet(js):
    galerie = [fotka(f"f{i}", bajty=1000) for i in range(8)]
    vysledek = js("out(m.pridejFotky(A.galerie, [A.nova]));", galerie=galerie, nova=fotka("novy", bajty=1000))
    assert vysledek["pridano"] == 0
    assert vysledek["odmitnuto"] == [{"nazev": "novy.jpg", "duvod": "pocet"}]


def test_pridani_hlida_misto(js):
    galerie = [fotka("a", bajty=1_400_000)]
    vysledek = js("out(m.pridejFotky(A.galerie, [A.nova]));", galerie=galerie, nova=fotka("b", bajty=200_000))
    assert vysledek["pridano"] == 0
    assert vysledek["odmitnuto"] == [{"nazev": "b.jpg", "duvod": "misto"}]


def test_pridani_pokracuje_po_odmitnuti(js):
    """Jedna velká fotka nesmí shodit ty malé za ní."""
    davka = [
        fotka("velka", bajty=1_600_000, data="data:image/jpeg;base64,velka"),
        fotka("mala", bajty=50_000, data="data:image/jpeg;base64,mala"),
    ]
    vysledek = js("out(m.pridejFotky([], A.davka));", davka=davka)
    assert vysledek["pridano"] == 1
    assert [f["id"] for f in vysledek["galerie"]] == ["mala"]
    assert [o["duvod"] for o in vysledek["odmitnuto"]] == ["misto"]


def test_pridani_respektuje_vlastni_limity(js):
    vysledek = js(
        "out(m.pridejFotky([], [A.a, A.b], { maxFotek: 1 }));",
        a=fotka("a", data="data:image/jpeg;base64,a"),
        b=fotka("b", data="data:image/jpeg;base64,b"),
    )
    assert vysledek["pridano"] == 1
    assert [o["duvod"] for o in vysledek["odmitnuto"]] == ["pocet"]


def test_pridani_doplni_chybejici_id(js):
    nova = {k: v for k, v in fotka("x").items() if k != "id"}
    vysledek = js("out(m.pridejFotky([], [A.nova]).galerie[0].id);", nova=nova)
    assert isinstance(vysledek, str) and vysledek != ""


# ------------------------------------------------------------ pořadí a mazání


def test_odebrani(js):
    galerie = [fotka("a"), fotka("b"), fotka("c")]
    assert [f["id"] for f in js('out(m.odeberFotku(A.g, "b"));', g=galerie)] == ["a", "c"]
    assert [f["id"] for f in js('out(m.odeberFotku(A.g, "neznamy"));', g=galerie)] == ["a", "b", "c"]


def test_presun_tam_a_zpet(js):
    galerie = [fotka("a"), fotka("b"), fotka("c")]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "c", -1));', g=galerie)] == ["a", "c", "b"]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "a", 1));', g=galerie)] == ["b", "a", "c"]


def test_presun_na_kraji_nic_nedela(js):
    galerie = [fotka("a"), fotka("b")]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "a", -1));', g=galerie)] == ["a", "b"]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "b", 1));', g=galerie)] == ["a", "b"]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "a", 0));', g=galerie)] == ["a", "b"]
    assert [f["id"] for f in js('out(m.presunFotku(A.g, "x", -1));', g=galerie)] == ["a", "b"]


def test_titulni_jde_na_zacatek(js):
    galerie = [fotka("a"), fotka("b"), fotka("c")]
    assert [f["id"] for f in js('out(m.nastavTitulni(A.g, "c"));', g=galerie)] == ["c", "a", "b"]
    assert [f["id"] for f in js('out(m.nastavTitulni(A.g, "x"));', g=galerie)] == ["a", "b", "c"]


def test_titulni_vraci_prvni(js):
    galerie = [fotka("a"), fotka("b")]
    assert js("out(m.titulni(A.g).id);", g=galerie) == "a"
    assert js("out(m.titulni([]));") is None
    assert js("out(m.titulni(null));") is None


# ---------------------------------------------------------------- souhrn


def test_souhrn_scita(js):
    galerie = [fotka("a", bajty=1000), fotka("b", bajty=2500)]
    assert js("out(m.souhrn(A.g));", g=galerie) == {"pocet": 2, "bajty": 3500}
    assert js("out(m.souhrn([]));") == {"pocet": 0, "bajty": 0}


def test_format_velikosti(js):
    assert js("out([0, 1024, 812000].map(m.formatVelikost));") == ["0 kB", "1 kB", "793 kB"]
    assert js("out([1048576, 1572864, 3670016].map(m.formatVelikost));") == ["1,0 MB", "1,5 MB", "3,5 MB"]


def test_format_velikosti_nesmysly(js):
    assert js('out([-5, NaN, null, "x"].map(m.formatVelikost));') == ["0 kB"] * 4


# ------------------------------------------------- nálezy z review C-010


def test_kontrola_odmitne_chybejici_velikost(js):
    """Soubor bez použitelné velikosti nesmí limit obejít."""
    for velikost in ("undefined", "0", "-1", "NaN", '"x"'):
        chyba = js(f'out(m.zkontrolujSoubor({{ typ: "image/jpeg", velikost: {velikost} }}).chyba);')
        assert chyba == "velikost", f"velikost {velikost} prošla"


def test_pridani_oznaci_nesmysl_jako_neplatny(js):
    davka = [None, "text", {"nazev": "bez-url.jpg"}]
    vysledek = js("out(m.pridejFotky([], A.davka));", davka=davka)
    assert vysledek["pridano"] == 0
    assert [o["duvod"] for o in vysledek["odmitnuto"]] == ["neplatny"] * 3
