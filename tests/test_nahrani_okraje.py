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
INSTALATOR = KOREN / "nasazeni" / "balicek" / "install.php"
README = KOREN / "nasazeni" / "balicek" / "README-NASAZENI.md"
INI_PRO_KLIENTA = KOREN / "nasazeni" / "balicek" / "greenairtech.ini"
BALICEK = KOREN / "nasazeni" / "balicek.sh"
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


def test_server_prijme_vsechno_co_administrace_pusti() -> None:
    """Dvě hranice na dvou stranách drátu: administrace odmítne soubor sama
    (src/lib/fotky.mjs) a php.ini ho odmítne na serveru. Kdyby byla serverová
    nižší, správce by dostal chybu na soubor, který mu administrace pustila."""
    mjs = (KOREN / "src" / "lib" / "fotky.mjs").read_text()
    nalez = re.search(r"velikost\s*>\s*(\d+)\s*\*\s*1024\s*\*\s*1024", mjs)
    assert nalez, "v src/lib/fotky.mjs se nenašel limit velikosti souboru"
    v_prohlizeci = int(nalez.group(1)) * 1024 ** 2

    text = PHP_INI.read_text()
    soubor = velikost(text, "upload_max_filesize")
    telo = velikost(text, "post_max_size")
    assert soubor >= v_prohlizeci, (
        f"upload_max_filesize {soubor // 1024 ** 2}M je pod limitem "
        f"administrace ({v_prohlizeci // 1024 ** 2}M): soubor, který "
        "administrace pustí, server odmítne"
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


# ---------------------------------------------------- co dostane klient

def test_balicek_vozi_ini_pro_klienta() -> None:
    """Náš php.ini je pro náš Docker. Klient instaluje na svůj Debian, kde
    výchozí upload_max_filesize je 2 MB — fotku by nenahrál vůbec. V balíčku
    proto musí být soubor, který si zkopíruje k sobě."""
    assert INI_PRO_KLIENTA.is_file(), (
        "nasazeni/balicek/greenairtech.ini chybí — klient nemá co zkopírovat "
        "do /etc/php/8.5/apache2/conf.d/"
    )
    text = INI_PRO_KLIENTA.read_text()
    nas = PHP_INI.read_text()
    for klic in ("memory_limit", "upload_max_filesize", "post_max_size"):
        assert velikost(text, klic) >= velikost(nas, klic), (
            f"{klic} pro klienta je nižší než v našem php.ini — u klienta by "
            "nahrávání fotek dopadlo jinak než na zkoušce"
        )
    assert "balicek/greenairtech.ini" in BALICEK.read_text(), (
        "nasazeni/balicek.sh ten soubor do ZIPu nekopíruje"
    )


# Jak instalátor mluví o limitech, hlídá tests/test_balicek_verze_php.py —
# tam se stránka opravdu vykreslí (s limity čistého Debianu i s dostatečnými).
# Čtení zdrojáku, které tu stálo dřív, projde i podmínce, co se nikdy
# nevykreslí (nález K4 od testovací session).


def test_readme_mluvi_o_limitech_php() -> None:
    text = README.read_text()
    assert "greenairtech.ini" in text, (
        "README neříká, že se má zkopírovat greenairtech.ini — klient nainstaluje "
        "podle něj a fotky mu nepůjdou nahrát"
    )

