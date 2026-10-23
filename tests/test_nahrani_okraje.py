"""Brána: okraje nahrávání fotek (nález 10, druhá půlka).

Nezávislý test zjistil, že soubor nad `upload_max_filesize` vrátí
`chybi-soubor`. Správce soubor vybral — a hláška ho posílá vybrat ho znovu.
PHP v takovém případě soubor zahodí a nechá jen číslo chyby v `$_FILES`;
když ho index.php nepředá, Router o něm nemůže vědět.

Rozhodování patří Routeru (C-020) a zmenšování Zpracování (C-021). Tahle
brána hlídá to, co není ani v jednom z nich: že se číslo chyby z PHP vůbec
dostane až k rozhodnutí, že limity v balíčku dávají dohromady smysl a že
administrace má pro ty odpovědi českou hlášku.
"""
from __future__ import annotations

import re
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]
PHP_INI = KOREN / "nasazeni" / "php.ini"
INDEX = KOREN / "web" / "public" / "index.php"
ADMIN_JS = KOREN / "src" / "assets" / "admin.js"
ADMIN_JS_WEB = KOREN / "web" / "public" / "assets" / "admin.js"


def velikost(text: str, klic: str) -> int:
    """Hodnotu z php.ini v bajtech ('512M' -> 536870912)."""
    nalez = re.search(rf"^\s*{re.escape(klic)}\s*=\s*(\d+)([KMG]?)", text, re.M | re.I)
    assert nalez, f"v nasazeni/php.ini chybí {klic}"
    nasobek = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[nalez.group(2).upper()]
    return int(nalez.group(1)) * nasobek


def test_pamet_staci_na_fotku_z_mobilu() -> None:
    """Fotka z dnešního telefonu má 24 až 50 Mpx; GD jí dá 4 bajty na pixel,
    tedy 96 až 200 MB, a vedle toho drží zmenšenou kopii. S 256 MB se větší
    fotka odmítne jako příliš velká — správně, ale zbytečně."""
    pamet = velikost(PHP_INI.read_text(), "memory_limit")
    assert pamet >= 512 * 1024 ** 2, (
        f"memory_limit {pamet // 1024 ** 2}M: běžná fotka z mobilu se nerozbalí "
        "a administrace ji odmítne"
    )


def test_limity_nahrani_jsou_vzajemne_konzistentni() -> None:
    text = PHP_INI.read_text()
    soubor = velikost(text, "upload_max_filesize")
    telo = velikost(text, "post_max_size")
    assert soubor >= 24 * 1024 ** 2, (
        f"upload_max_filesize {soubor // 1024 ** 2}M: fotka přímo z telefonu "
        "se nenahraje vůbec"
    )
    assert telo > soubor, (
        "post_max_size není větší než upload_max_filesize — PHP pak zahodí celý "
        "požadavek včetně čísla chyby a administrace neví, co se stalo"
    )


def test_index_predava_cislo_chyby_z_php() -> None:
    text = INDEX.read_text()
    assert "soubor_chyba" in text, (
        "index.php nepředává Routeru $_FILES['fotka']['error'] — bez něj se "
        "z „soubor je moc velký\" nikdy nestane nic jiného než „chybí soubor\""
    )
    assert "telo_velke" in text and "CONTENT_LENGTH" in text, (
        "při překročení post_max_size je $_FILES prázdné a zbyde jen délka "
        "požadavku; index.php ji Routeru nepředává"
    )


def test_administrace_umi_rict_ze_je_fotka_velka() -> None:
    for cesta in (ADMIN_JS, ADMIN_JS_WEB):
        text = cesta.read_text()
        for kod in ("soubor-moc-velky", "fotka-moc-velka"):
            assert kod in text, (
                f"{cesta.name} nezná odpověď {kod} — správce uvidí obecné "
                "„Fotku se nepovedlo nahrát\" a nedozví se, že ji má zmenšit"
            )
