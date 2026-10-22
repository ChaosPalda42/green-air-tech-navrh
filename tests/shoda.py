"""Bajtový diff ostrého PHP webu proti vygenerované ukázce.

Ukázka v out/web je ORÁKULUM: 139 hotových stránek, které člověk viděl a
schválil. Přepis šablon do PHP je hotový přesně tehdy, když vyrobí tytéž
bajty. Proto se tu nic neporovnává "zhruba" — buď se soubory rovnají, nebo ne.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile

KOREN = pathlib.Path(__file__).resolve().parent.parent
UKAZKA = KOREN / "out" / "web"

_cache: dict[str, pathlib.Path] = {}


def vykresleno() -> pathlib.Path:
    """Vykreslí celý web PHP verzí (jednou za běh pytestu) a vrátí složku."""
    if "cesta" not in _cache:
        cil = pathlib.Path(tempfile.mkdtemp(prefix="gat-php-"))
        subprocess.run(
            ["php", str(KOREN / "tools" / "vykresli.php"), "--vse", str(cil)],
            cwd=KOREN,
            check=True,
            capture_output=True,
            text=True,
        )
        _cache["cesta"] = cil
    return _cache["cesta"]


def stranky() -> list[str]:
    hotovo = subprocess.run(
        ["php", str(KOREN / "tools" / "vykresli.php"), "--seznam"],
        cwd=KOREN,
        check=True,
        capture_output=True,
        text=True,
    )
    return [r for r in hotovo.stdout.splitlines() if r]


def rozdil(cesta: str) -> str | None:
    """None když se stránka shoduje s ukázkou, jinak popis prvního rozdílu."""
    kde = vykresleno() / cesta
    chyba = kde.with_name(kde.name + ".chyba")
    if chyba.exists():
        return f"{cesta}: PHP stránku nevykreslilo — {chyba.read_text().strip()}"
    if not kde.exists():
        return f"{cesta}: PHP nevyrobilo soubor"
    vzor_soubor = UKAZKA / cesta
    if not vzor_soubor.exists():
        return f"{cesta}: v ukázce taková stránka není (out/web je zastaralé?)"
    vzor = vzor_soubor.read_bytes()
    nase = kde.read_bytes()
    if vzor == nase:
        return None

    # první odlišný bajt + okolí, ať je vidět, o co jde
    i = next((n for n, (a, b) in enumerate(zip(vzor, nase)) if a != b), min(len(vzor), len(nase)))
    od = max(0, i - 90)
    return (
        f"{cesta}: rozdíl na bajtu {i} (ukázka {len(vzor)} B, PHP {len(nase)} B)\n"
        f"  ukázka: …{vzor[od:i + 90].decode('utf-8', 'replace')!r}\n"
        f"  PHP:    …{nase[od:i + 90].decode('utf-8', 'replace')!r}"
    )


def rozdily(cesty: list[str]) -> list[str]:
    return [r for r in (rozdil(c) for c in cesty) if r is not None]
