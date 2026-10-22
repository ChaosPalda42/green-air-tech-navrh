"""Spojka mezi zaznamenaným orákulem (JS) a PHP implementací.

Vzorky v tests/orakulum/*.json vznikly spuštěním knihoven z ukázky nad
skutečnými daty webu (tools/orakulum-knihovny.mjs). Pravidlo, které brána
vynucuje, je v nich — ne v PHP kódu, na který se ptáme.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]
ZNACKA_UNDEF = "\0undefined"


def _srovnej(hodnota):
    """JS a PHP se liší ve dvou věcech, které pro nás nic neznamenají:
    `undefined` proti `null` a prázdný objekt proti prázdnému polí."""
    if hodnota == ZNACKA_UNDEF:
        return None
    if isinstance(hodnota, dict):
        if not hodnota:
            return []
        return {k: _srovnej(v) for k, v in hodnota.items()}
    if isinstance(hodnota, list):
        if not hodnota:
            return []
        return [_srovnej(v) for v in hodnota]
    return hodnota


def ocekavane(jmeno: str) -> dict[str, list]:
    data = json.loads((KOREN / "tests" / "orakulum" / f"{jmeno}.json").read_text("utf8"))
    return {f: [_srovnej(p["out"]) for p in pripady] for f, pripady in data.items()}


def vstupy(jmeno: str) -> dict[str, list]:
    data = json.loads((KOREN / "tests" / "orakulum" / f"{jmeno}.json").read_text("utf8"))
    return {f: [p["args"] for p in pripady] for f, pripady in data.items()}


def z_php(jmeno: str) -> dict[str, list]:
    hotovo = subprocess.run(
        ["php", str(KOREN / "tools" / "orakulum.php"), jmeno],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if hotovo.returncode != 0:
        raise AssertionError(f"orakulum.php {jmeno} spadlo: {hotovo.stderr.strip()[:400]}")
    data = json.loads(hotovo.stdout)
    vysledek = {}
    for funkce, pripady in data.items():
        vysledek[funkce] = [
            p["chyba"] if "chyba" in p else _srovnej(p["out"]) for p in pripady
        ]
    return vysledek


def zkratka(hodnota, limit: int = 220) -> str:
    text = json.dumps(hodnota, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit] + "…"


def rozdily(jmeno: str, vysledky: dict[str, list], jen: set[str] | None = None) -> list[str]:
    """Seznam neshod proti zaznamenanému orákulu, v pořadí vzorků.

    `jen` zúží srovnání na vyjmenované funkce — jedno orákulum pak může sloužit
    dvěma branám, každá za svůj kus (viz Stav a StavRealizace)."""
    ocek = ocekavane(jmeno)
    args = vstupy(jmeno)
    out: list[str] = []
    for funkce, cekane in ocek.items():
        if jen is not None and funkce not in jen:
            continue
        mam = vysledky.get(funkce)
        if mam is None:
            out.append(f"{funkce}: PHP nevrátilo nic")
            continue
        if len(mam) != len(cekane):
            out.append(f"{funkce}: {len(mam)} výsledků proti {len(cekane)} vzorkům")
            continue
        for i, (o, m) in enumerate(zip(cekane, mam)):
            if o != m:
                out.append(
                    f"{funkce}[{i}] vstup {zkratka(args[funkce][i], 160)}\n"
                    f"    čekáno: {zkratka(o)}\n"
                    f"    přišlo: {zkratka(m)}"
                )
    return out
