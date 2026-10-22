#!/usr/bin/env python3
"""Vyrobí tests/orakulum/ga4.json — vzorky převodu odpovědí GA4 Data API
do tvaru nástěnky. Referenční implementace je tady a je to TO PRAVIDLO;
PHP ho musí reprodukovat.

Vzorky odpovědí: shape podle Data API v1beta (runReport). Jeden vzorek
('skutecna') se po živé zkoušce vymění za zaznamenanou odpověď z naší
testovací vlastnosti — do té doby je to jen tvar podle dokumentace.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

METRIKY = ["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"]


def zaokrouhli(x: float, mist: int) -> float:
    """Jako PHP round(): půlky nahoru (od nuly), ne bankovní."""
    q = Decimal(1).scaleb(-mist)
    d = Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP)
    return float(d)


# ---------------------------------------------------------------- reference

def dny(odpoved: dict, pocet: int, konec: str, poptavky: dict | None = None) -> list[dict]:
    poptavky = poptavky or {}
    hlavicky = [h.get("name", "") for h in odpoved.get("metricHeaders") or []]
    podle_data: dict[str, dict] = {}
    for radek in odpoved.get("rows") or []:
        rozmery = radek.get("dimensionValues") or []
        if not rozmery:
            continue
        syrove = str(rozmery[0].get("value", ""))
        if len(syrove) != 8 or not syrove.isdigit():
            continue
        datum = f"{syrove[0:4]}-{syrove[4:6]}-{syrove[6:8]}"
        hodnoty = [str(m.get("value", "0")) for m in radek.get("metricValues") or []]
        podle = {}
        for i, jmeno in enumerate(hlavicky):
            podle[jmeno] = float(hodnoty[i]) if i < len(hodnoty) and hodnoty[i] != "" else 0.0
        podle_data[datum] = podle

    posledni = date.fromisoformat(konec)
    ven = []
    for i in range(pocet - 1, -1, -1):
        den = posledni - timedelta(days=i)
        klic = den.isoformat()
        m = podle_data.get(klic, {})
        ven.append({
            "datum": klic,
            "navstevy": int(zaokrouhli(m.get("sessions", 0.0), 0)),
            "uzivatele": int(zaokrouhli(m.get("totalUsers", 0.0), 0)),
            "zobrazeni": int(zaokrouhli(m.get("screenPageViews", 0.0), 0)),
            "poptavky": int(poptavky.get(klic, 0)),
            "cas": zaokrouhli(m.get("averageSessionDuration", 0.0), 1),
            "opusteni": zaokrouhli(m.get("bounceRate", 0.0) * 100, 2),
        })
    return ven


def rozpad(odpoved: dict, preklad: dict | None = None, max_radku: int = 6) -> list[dict]:
    preklad = preklad or {}
    if max_radku < 1:
        return []
    poradi: list[str] = []
    soucty: dict[str, float] = {}
    for radek in odpoved.get("rows") or []:
        rozmery = radek.get("dimensionValues") or []
        metriky = radek.get("metricValues") or []
        if not rozmery:
            continue
        nazev = str(rozmery[0].get("value", ""))
        nazev = preklad.get(nazev, nazev)
        hodnota = float(str(metriky[0].get("value", "0")) or 0) if metriky else 0.0
        if nazev not in soucty:
            soucty[nazev] = 0.0
            poradi.append(nazev)
        soucty[nazev] += hodnota

    radky = [(nazev, soucty[nazev], i) for i, nazev in enumerate(poradi)]
    radky.sort(key=lambda r: (-r[1], r[2]))
    radky = radky[:max_radku]
    if not radky:
        return []

    celkem = sum(r[1] for r in radky)
    if celkem <= 0:
        return [{"nazev": r[0], "podil": 0} for r in radky]

    presne = [r[1] * 100.0 / celkem for r in radky]
    podily = [int(p) for p in presne]          # floor, hodnoty jsou nezáporné
    zbytek = 100 - sum(podily)
    poradi_zbytku = sorted(range(len(radky)), key=lambda i: (-(presne[i] - podily[i]), i))
    for i in poradi_zbytku[:max(0, zbytek)]:
        podily[i] += 1
    # Co se po zaokrouhlení nedostane ani na procento, se nevypisuje —
    # řádek „0 %“ na nástěnce nic neříká. Součet zůstává 100.
    return [{"nazev": radky[i][0], "podil": podily[i]}
            for i in range(len(radky)) if podily[i] > 0]


# ------------------------------------------------------------------ vzorky

def den_radek(datum: str, hodnoty: list) -> dict:
    return {
        "dimensionValues": [{"value": datum}],
        "metricValues": [{"value": str(h)} for h in hodnoty],
    }


def odpoved_dny(radky: list[dict]) -> dict:
    return {
        "dimensionHeaders": [{"name": "date"}],
        "metricHeaders": [{"name": m, "type": "TYPE_INTEGER"} for m in METRIKY],
        "rows": radky,
        "rowCount": len(radky),
        "kind": "analyticsData#runReport",
    }


def odpoved_rozmer(pary: list[tuple[str, int]]) -> dict:
    return {
        "dimensionHeaders": [{"name": "x"}],
        "metricHeaders": [{"name": "sessions", "type": "TYPE_INTEGER"}],
        "rows": [
            {"dimensionValues": [{"value": n}], "metricValues": [{"value": str(v)}]}
            for n, v in pary
        ],
        "rowCount": len(pary),
    }


KANALY = {
    "Organic Search": "Vyhledávání Google",
    "Direct": "Přímý přístup",
    "Organic Social": "Sociální sítě",
    "Referral": "Ostatní odkazy",
    "Unassigned": "Nezařazeno",
}
ZARIZENI = {"mobile": "Mobil", "desktop": "Počítač", "tablet": "Tablet"}
STRANKY = {
    "/": "Úvodní rozcestník",
    "/index.html": "Úvodní rozcestník",
    "/domacnosti.html": "Domácnosti",
    "/firmy.html": "Firemní zákazníci",
    "/kontakt.html": "Kontakt",
}

PLNY = odpoved_dny([
    den_radek("20261016", [412, 301, 1180, "182.4211", "0.4231"]),
    den_radek("20261017", [398, 290, 1102, "175.5", "0.4402"]),
    den_radek("20261018", [201, 150, 540, "160.25", "0.51"]),
    den_radek("20261019", [188, 141, 497, "151.75", "0.5299"]),
    den_radek("20261020", [430, 318, 1240, "190.0", "0.4005"]),
    den_radek("20261021", [445, 330, 1301, "188.125", "0.3999"]),
    den_radek("20261022", [460, 341, 1355, "193.6667", "0.3875"]),
])
DIRY = odpoved_dny([
    den_radek("20261018", [201, 150, 540, "160.25", "0.51"]),
    den_radek("20261021", [445, 330, 1301, "188.125", "0.3999"]),
])
PRAZDNO = {
    "dimensionHeaders": [{"name": "date"}],
    "metricHeaders": [{"name": m} for m in METRIKY],
    "rowCount": 0,
}
JINE_PORADI = {
    "dimensionHeaders": [{"name": "date"}],
    "metricHeaders": [{"name": "bounceRate"}, {"name": "sessions"}, {"name": "totalUsers"}],
    "rows": [den_radek("20261022", ["0.625", 80, 64])],
    "rowCount": 1,
}
SPATNA_DATA = odpoved_dny([
    den_radek("2026-10-22", [10, 10, 10, "1", "0.5"]),
    den_radek("20261022", [7, 5, 20, "120.5", "0.4"]),
])

VZORKY = {
    "dny": [
        {"args": [PLNY, 7, "2026-10-22", {}], "out": None},
        {"args": [PLNY, 7, "2026-10-22", {"2026-10-20": 3, "2026-10-22": 1}], "out": None},
        {"args": [DIRY, 7, "2026-10-22", {}], "out": None},
        {"args": [PRAZDNO, 3, "2026-10-22", {}], "out": None},
        {"args": [JINE_PORADI, 1, "2026-10-22", {}], "out": None},
        {"args": [SPATNA_DATA, 1, "2026-10-22", {}], "out": None},
        {"args": [PLNY, 10, "2026-10-22", {"2026-10-15": 2}], "out": None},
        {"args": [PLNY, 2, "2026-10-31", {}], "out": None},
    ],
    "rozpad": [
        {"args": [odpoved_rozmer([
            ("Organic Search", 1204), ("Direct", 612), ("Referral", 241),
            ("Organic Social", 133), ("Unassigned", 44), ("Email", 12), ("Paid Search", 3),
        ]), KANALY, 6], "out": None},
        {"args": [odpoved_rozmer([
            ("mobile", 1402), ("desktop", 731), ("tablet", 118),
        ]), ZARIZENI, 3], "out": None},
        {"args": [odpoved_rozmer([
            ("/", 820), ("/index.html", 180), ("/domacnosti.html", 420),
            ("/firmy.html", 260), ("/kontakt.html", 95), ("/en/contact.html", 40),
        ]), STRANKY, 5], "out": None},
        {"args": [odpoved_rozmer([("Direct", 7)]), KANALY, 6], "out": None},
        {"args": [odpoved_rozmer([]), KANALY, 6], "out": None},
        {"args": [odpoved_rozmer([("a", 0), ("b", 0)]), {}, 6], "out": None},
        {"args": [odpoved_rozmer([("a", 1), ("b", 1), ("c", 1)]), {}, 3], "out": None},
        {"args": [odpoved_rozmer([("a", 1), ("b", 1), ("c", 1), ("d", 1), ("e", 1), ("f", 1), ("g", 1)]), {}, 7], "out": None},
        {"args": [odpoved_rozmer([("a", 5), ("b", 5), ("c", 1)]), {}, 2], "out": None},
        {"args": [odpoved_rozmer([("mobile", 10), ("desktop", 10)]), ZARIZENI, 0], "out": None},
    ],
}


def main() -> int:
    kam = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/orakulum/ga4.json")
    hotovo = {}
    for funkce, pripady in VZORKY.items():
        ven = []
        for p in pripady:
            args = p["args"]
            out = dny(*args) if funkce == "dny" else rozpad(*args)
            ven.append({"args": args, "out": out})
        hotovo[funkce] = ven
    kam.write_text(json.dumps(hotovo, ensure_ascii=False, indent=1) + "\n", "utf8")
    print(f"{kam}: dny {len(hotovo['dny'])} vzorků, rozpad {len(hotovo['rozpad'])} vzorků")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
