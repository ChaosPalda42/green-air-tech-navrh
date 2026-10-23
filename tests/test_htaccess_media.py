"""Brána: ve složce s nahranými fotkami se nesmí spustit skript.

README to tvrdí a tester to vyvrátil: v .htaccess stálo

    RewriteCond %{REQUEST_FILENAME} -f
    RewriteRule ^ - [L]            # existující soubor obslouží Apache sám

PŘED pravidlem, které v media zakazuje .php — a `[L]` další pravidla
zastaví. `media/zkouska.php` se proto vrátilo s kódem 200 a vypsalo, co
v něm bylo. Nahrání samo PHP soubor nevyrobí (všechno se překóduje na
WebP), ale je to obrana do hloubky a ta má držet.

Pravidlo: zákaz skriptů v media stojí v .htaccess PŘED zkratkou pro
existující soubory, a ve složce media leží vlastní .htaccess, který
vypne PHP i tam, kde se přepisy adres nečtou.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]
HTACCESS = KOREN / "web" / "public" / ".htaccess"
MEDIA_HTACCESS = KOREN / "web" / "public" / "media" / ".htaccess"
BALICEK = KOREN / "nasazeni" / "balicek.sh"


def test_zakaz_skriptu_stoji_pred_zkratkou_na_existujici_soubor() -> None:
    radky = HTACCESS.read_text().splitlines()
    zakaz = [i for i, r in enumerate(radky) if "media/" in r and "[F" in r]
    zkratka = [i for i, r in enumerate(radky) if "REQUEST_FILENAME" in r and "-f" in r]
    assert zakaz, ".htaccess vůbec nezakazuje skripty v media"
    assert zkratka, ".htaccess nemá zkratku pro existující soubory (změnil se?)"
    assert min(zakaz) < min(zkratka), (
        "zákaz skriptů v media je AŽ ZA zkratkou pro existující soubory — "
        "ta končí [L], takže se zákaz nikdy nevyhodnotí"
    )


def test_media_ma_vlastni_htaccess_ktery_vypne_php() -> None:
    assert MEDIA_HTACCESS.is_file(), "web/public/media/.htaccess chybí"
    text = MEDIA_HTACCESS.read_text()
    assert re.search(r"php_flag\s+engine\s+off", text, re.I), "nevypíná mod_php (php_flag engine off)"
    assert re.search(r"SetHandler\s+(None|default-handler)", text, re.I), (
        "nepřepisuje handler na None — pod php-fpm by se soubor jinak poslal interpretu"
    )


def test_balicek_ten_htaccess_zabaluje() -> None:
    """Soubor, který se nedostane do ZIPu, u klienta nic nechrání."""
    assert "media/.htaccess" in BALICEK.read_text(), (
        "nasazeni/balicek.sh nekopíruje web/public/media/.htaccess do balíčku"
    )

def test_nahrane_fotky_nejdou_do_gitu_ale_htaccess_ano() -> None:
    """Fotky klienta jsou data, ne kód — a .htaccess je naopak závora,
    která musí v repozitáři zůstat, jinak ji balíček nemá odkud vzít."""

    def ignorovan(cesta: str) -> bool:
        return subprocess.run(
            ["git", "check-ignore", "-q", cesta], cwd=KOREN
        ).returncode == 0

    assert ignorovan("web/public/media/realizace-01.webp"), (
        "nahraná fotka ve web/public/media není v .gitignore — z administrace "
        "by se fotky klienta dostaly do gitu a na GitHub"
    )
    assert not ignorovan("web/public/media/.htaccess"), (
        "web/public/media/.htaccess je ignorovaný, takže není v repozitáři "
        "a balíček ho nemá odkud zkopírovat"
    )
