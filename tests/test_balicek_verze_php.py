"""Brána nasazení: balíček musí klienta poslat na BEZPEČNOU verzi PHP.

Nález kola 2, dodatek K6: 21. 10. 2026 vyšly mimořádné opravy dvou
kritických děr v PHP, které umožňují spuštění cizího kódu bez přihlášení
(CVE-2026-109618 a CVE-2026-109619, CVSS 9.2) — opravené jsou 8.5.12,
8.4.27, 8.3.36 a 8.2.35. 23. 10. k tomu přibyla CVE-2026-115560, pro kterou
oprava ještě není; php.net radí vypnout `session.upload_progress`.
Balíček přitom psal jen „testováno na 8.5.12" a nastavení PHP o tom mlčelo.

Pravidlo:
- README jmenuje minimální verze v obou podporovaných řadách a ukáže, jak
  si je klient ověří (`php -v`), a říká, že se aktualizace PHP sledují.
- greenairtech.ini vypíná session.upload_progress a na 8.5 i
  fatal_error_backtraces — to jsou doporučení z php.net, která pokrývají i
  tu neopravenou díru.
- Instalátor verzi porovná a když je starší než opravená, NAPÍŠE TO. Tenhle
  Mac má PHP 8.5.10, tedy starší — brána to tedy neověřuje čtením kódu,
  ale skutečným renderem stránky instalátoru.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
INI = KOREN / "nasazeni/balicek/greenairtech.ini"
INSTALATOR = KOREN / "nasazeni/balicek/install.php"
README = KOREN / "nasazeni/balicek/README-NASAZENI.md"

# řada PHP -> první opravená verze (php.net, 21. 10. 2026)
OPRAVENE = {"8.5": "8.5.12", "8.4": "8.4.27", "8.3": "8.3.36", "8.2": "8.2.35"}


def hodnota(ini: str, klic: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(klic)}\s*=\s*(\S+)", ini, re.M)
    return m.group(1) if m else None


def test_ini_vypina_upload_progress_a_backtraces() -> None:
    ini = INI.read_text()
    assert hodnota(ini, "session.upload_progress.enabled") in ("0", "Off", "off"), (
        "greenairtech.ini nevypíná session.upload_progress — to je doporučené "
        "opatření php.net ke CVE-2026-115560, pro kterou oprava ještě není, "
        "a web upload progress vůbec nepoužívá"
    )
    assert hodnota(ini, "fatal_error_backtraces") in ("0", "Off", "off"), (
        "greenairtech.ini nevypíná fatal_error_backtraces (na 8.5 druhá "
        "polovina téhož doporučení php.net)"
    )


def test_readme_rika_minimalni_verzi_php() -> None:
    text = README.read_text()
    for rada, verze in (("8.5", OPRAVENE["8.5"]), ("8.4", OPRAVENE["8.4"])):
        assert verze in text, (
            f"README nejmenuje {verze} — klient nainstaluje PHP {rada} s "
            "kritickou dírou a bude si myslet, že nasadil podle návodu"
        )
    assert "php -v" in text, "README neukáže, jak si klient verzi ověří"
    assert re.search(r"apt\s+(upgrade|update)", text), (
        "README neříká, že se aktualizace PHP sledují a instalují"
    )


def instalator_vykresli(prepinace: tuple[str, ...] = ()) -> str:
    """Vykreslí install.php tak, jak ho uvidí klient: ve stromu, kde vedle
    `public/` leží `app/`, `config/` a `data/` jako v balíčku. Čtení
    zdrojáku by neověřilo nic — podmínka může být napsaná a nikdy se
    nevykreslit."""
    with tempfile.TemporaryDirectory() as docasne:
        koren = Path(docasne)
        (koren / "public").mkdir()
        for jmeno in ("app", "data"):
            (koren / jmeno).symlink_to(KOREN / "web" / jmeno)
        (koren / "config").mkdir()  # prázdný: web ještě není nastavený
        (koren / "public" / "media").mkdir()
        shutil.copy(INSTALATOR, koren / "public" / "install.php")
        hotovo = subprocess.run(
            ["php", *prepinace, "install.php"],
            capture_output=True, text=True, timeout=60,
            cwd=str(koren / "public"),
        )
        assert hotovo.returncode == 0, (hotovo.stderr or hotovo.stdout)[-800:]
        return hotovo.stdout


def test_instalator_rekne_starou_verzi_php() -> None:
    """Tenhle stroj má PHP 8.5.10 — tedy přesně ten případ, kdy má
    instalátor varovat."""
    html = instalator_vykresli()
    bezi = subprocess.run(["php", "-r", "echo PHP_VERSION;"],
                          capture_output=True, text=True, timeout=30).stdout.strip()
    rada = ".".join(bezi.split(".")[:2])
    opravena = OPRAVENE.get(rada)
    if opravena is None:
        pytest.skip(f"PHP {bezi} není v řadě, kterou balíček popisuje")
    stara = tuple(int(x) for x in bezi.split(".")[:3]) < tuple(
        int(x) for x in opravena.split("."))
    assert opravena in html, (
        f"instalátor běží na PHP {bezi} a opravenou verzi {opravena} nikde "
        "nejmenuje — podle takové stránky se nedá poznat, jestli je server "
        "v pořádku"
    )
    if stara:
        assert re.search(r"apt\s+(upgrade|update|install)", html), (
            "instalátor řekne, že je PHP staré, ale neporadí, jak ho spravit"
        )
        assert "kritick" in html.lower(), (
            "ze stránky není poznat, že jde o kritickou chybu, ne o kosmetiku"
        )


def test_instalator_rekne_kdyz_limity_nestaci() -> None:
    """Zpřísněný nález K4: dřív se tahle brána ptala jen na text zdrojáku.
    Teď se instalátor vykreslí s limity čistého Debianu a hláška musí být
    na stránce — a s dostatečnými limity tam naopak být nesmí."""
    male = instalator_vykresli((
        "-d", "upload_max_filesize=2M", "-d", "post_max_size=8M",
        "-d", "memory_limit=128M",
    ))
    assert "Fotky se do administrace nenahrají" in male, (
        "instalátor na limitech čistého Debianu (2M upload, 128M paměti) "
        "mlčí — klient nasadí web, na který se nedá nahrát fotka"
    )
    for klic in ("upload_max_filesize", "post_max_size", "memory_limit"):
        assert klic in male, f"hláška nejmenuje {klic}, takže není co spravit"
    assert "greenairtech.ini" in male, (
        "instalátor neporadí, co s tím: v balíčku je hotové nastavení"
    )

    dost = instalator_vykresli((
        "-d", "upload_max_filesize=12M", "-d", "post_max_size=16M",
        "-d", "memory_limit=512M",
    ))
    assert "Fotky se do administrace nenahrají" not in dost, (
        "instalátor straší i na serveru, kde jsou limity v pořádku"
    )
