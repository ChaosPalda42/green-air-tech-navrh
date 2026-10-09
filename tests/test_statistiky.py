"""Akceptační test C-009 — src/lib/statistiky.mjs (nástěnka v administraci).

Ukázková analytika: data se generují deterministicky ze semínka, aby náhled
vypadal pokaždé stejně, a agregace musí sedět na korunu.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("statistiky.mjs", body, args=args)

    return call


# ------------------------------------------------------------- generování


def test_data_jsou_deterministicka(js):
    assert js('out(m.vygenerujData("gat", 30));') == js('out(m.vygenerujData("gat", 30));')


def test_jine_seminko_jina_data(js):
    a = js('out(m.vygenerujData("gat", 30));')
    b = js('out(m.vygenerujData("jiny", 30));')
    assert a != b


def test_pocet_dni_a_tvar_zaznamu(js):
    data = js('out(m.vygenerujData("gat", 14));')
    assert len(data) == 14
    for den in data:
        assert set(den) == {
            "datum", "navstevy", "uzivatele", "zobrazeni",
            "poptavky", "cas", "opusteni",
        }
        assert den["navstevy"] > 0
        assert den["uzivatele"] <= den["navstevy"]
        assert den["zobrazeni"] >= den["navstevy"]
        assert 0 <= den["opusteni"] <= 100
        assert den["cas"] > 0


def test_datumy_jdou_po_sobe_a_konci_dnes(js):
    data = js('out(m.vygenerujData("gat", 5));')
    datumy = [d["datum"] for d in data]
    assert datumy == sorted(datumy)
    assert len(set(datumy)) == 5
    import datetime

    assert datumy[-1] == datetime.date.today().isoformat()


def test_nulovy_pocet_dni(js):
    assert js('out(m.vygenerujData("gat", 0));') == []


# -------------------------------------------------------------- výběr období


def test_filtruj_obdobi_vezme_konec_rady(js):
    vysledek = js(
        """
        const data = m.vygenerujData("gat", 30);
        const vyber = m.filtrujObdobi(data, 7);
        out({ delka: vyber.length, posledni: vyber[vyber.length - 1].datum === data[data.length - 1].datum });
        """
    )
    assert vysledek == {"delka": 7, "posledni": True}


def test_filtruj_obdobi_delsi_nez_data(js):
    assert js('out(m.filtrujObdobi(m.vygenerujData("gat", 5), 30).length);') == 5


# ------------------------------------------------------------------ souhrn


def test_souhrn_scita_a_prumeruje(js):
    vysledek = js(
        """
        const data = [
          { datum: "2026-10-01", navstevy: 100, uzivatele: 80, zobrazeni: 300, poptavky: 2, cas: 120, opusteni: 40 },
          { datum: "2026-10-02", navstevy: 200, uzivatele: 150, zobrazeni: 500, poptavky: 4, cas: 180, opusteni: 60 },
        ];
        out(m.souhrn(data));
        """
    )
    assert vysledek["navstevy"] == 300
    assert vysledek["uzivatele"] == 230
    assert vysledek["zobrazeni"] == 800
    assert vysledek["poptavky"] == 6
    # čas a míra opuštění se váží návštěvami, ne prostým průměrem
    assert vysledek["cas"] == pytest.approx((120 * 100 + 180 * 200) / 300, rel=1e-6)
    assert vysledek["opusteni"] == pytest.approx((40 * 100 + 60 * 200) / 300, rel=1e-6)


def test_souhrn_prazdnych_dat(js):
    assert js('out(m.souhrn([]));') == {
        "navstevy": 0, "uzivatele": 0, "zobrazeni": 0,
        "poptavky": 0, "cas": 0, "opusteni": 0,
    }


def test_zmena_proti_predchozimu_obdobi(js):
    assert js('out(m.zmenaProti(150, 100));') == 50
    assert js('out(m.zmenaProti(50, 100));') == -50
    assert js('out(m.zmenaProti(100, 100));') == 0


def test_zmena_z_nuly(js):
    assert js('out(m.zmenaProti(10, 0));') is None
    assert js('out(m.zmenaProti(0, 0));') is None


# ------------------------------------------------------------- rozdělení


def test_rozdeleni_dava_dohromady_sto(js):
    polozky = ["Vyhledávání", "Přímý přístup", "Sociální sítě", "Odkazy"]
    vysledek = js('out(m.rozdeleni("gat-zdroje", A.polozky));', polozky=polozky)
    assert [r["nazev"] for r in vysledek] == polozky
    assert sum(r["podil"] for r in vysledek) == 100
    assert all(r["podil"] > 0 for r in vysledek)


def test_rozdeleni_je_deterministicke(js):
    polozky = ["A", "B", "C"]
    a = js('out(m.rozdeleni("x", A.polozky));', polozky=polozky)
    b = js('out(m.rozdeleni("x", A.polozky));', polozky=polozky)
    assert a == b


def test_rozdeleni_jedne_polozky(js):
    assert js('out(m.rozdeleni("x", ["Jediná"]));') == [{"nazev": "Jediná", "podil": 100}]


def test_rozdeleni_prazdneho_seznamu(js):
    assert js('out(m.rozdeleni("x", []));') == []


# ------------------------------------------------------------- formátování


def test_format_cisla_po_tisicich(js):
    assert js('out(["1", "999", "1000", "12345", "1234567"].map(n => m.formatCislo(Number(n))));') == [
        "1", "999", "1 000", "12 345", "1 234 567",
    ]


def test_format_casu(js):
    assert js('out([0, 59, 60, 161, 3600].map(m.formatCas));') == [
        "0:00", "0:59", "1:00", "2:41", "60:00",
    ]


def test_format_procent(js):
    assert js('out([0, 42.4, 42.5, 100].map(m.formatProcenta));') == ["0 %", "42 %", "43 %", "100 %"]


def test_format_zmeny_ma_znamenko(js):
    assert js('out([12, -8, 0].map(m.formatZmena));') == ["+12 %", "−8 %", "0 %"]
    assert js('out(m.formatZmena(null));') == "—"


# ---------------------------------------------------------------- graf


def test_osa_grafu_vrati_body_i_rozsah(js):
    vysledek = js(
        """
        const data = [
          { datum: "2026-10-01", navstevy: 10 },
          { datum: "2026-10-02", navstevy: 30 },
          { datum: "2026-10-03", navstevy: 20 },
        ];
        out(m.osaGrafu(data, "navstevy"));
        """
    )
    assert vysledek["min"] == 10
    assert vysledek["max"] == 30
    assert len(vysledek["body"]) == 3
    # x roste rovnoměrně od 0 do 100, y je 0 dole a 100 nahoře
    assert vysledek["body"][0]["x"] == 0
    assert vysledek["body"][-1]["x"] == 100
    assert vysledek["body"][1]["y"] == 100
    assert vysledek["body"][0]["y"] == 0


def test_osa_grafu_pri_stejnych_hodnotach(js):
    vysledek = js(
        'out(m.osaGrafu([{ navstevy: 5 }, { navstevy: 5 }], "navstevy"));'
    )
    assert vysledek["min"] == 5 and vysledek["max"] == 5
    assert all(b["y"] == 50 for b in vysledek["body"])


def test_osa_grafu_prazdna_data(js):
    assert js('out(m.osaGrafu([], "navstevy"));') == {"body": [], "min": 0, "max": 0}
