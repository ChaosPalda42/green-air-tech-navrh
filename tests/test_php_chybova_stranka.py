"""Brána: chybová stránka odpovídá kódem 404 a neindexuje se.

Nález při kontrole ostrého webu po nasazení canonical (10. 11. 2026). Neznámá
adresa vrací 404 správně, ale **přímý požadavek na `/404.html` vracel 200 OK**,
protože `Odkazy::rozpoznej` tu adresu zná jako běžnou stránku. Pro vyhledávač
to byla plnohodnotná stránka, navíc bez kanonické adresy a bez `noindex` —
chybová stránka se tedy mohla objevit ve výsledcích hledání. Totéž ve všech
třech jazycích (`/en/404.html`, `/de/404.html`).

Proč brána takhle: ptá se vestavěného serveru PHP nad skutečným `index.php`,
tedy tam, kde se o stavovém kódu rozhoduje. Na vykresleném HTML by se stavový
kód změřit nedal.

Nastavení se podstrčí přes `auto_prepend_file` (adresa webu, aby mělo smysl se
ptát na canonical) — `config/config.php` v repozitáři není.

Zaznamenaný vzorek (tento stroj, PHP 8.5.10, 10. 11. 2026, vestavěný server
nad web/public/index.php; „canonical" je počet značek v hlavě):
  PŘED opravou  /404.html                      200  noindex NE  canonical 0
                /en/404.html                   200  noindex NE  canonical 0
                /de/404.html                   200  noindex NE  canonical 0
                /takova-stranka-neexistuje     404  noindex NE  canonical 0
                /index.html                    200  noindex NE  canonical 1
  PO opravě     /404.html                      404  noindex ANO canonical 0
                /en/404.html                   404  noindex ANO canonical 0
                /de/404.html                   404  noindex ANO canonical 0
                /takova-stranka-neexistuje     404  noindex ANO canonical 0
                /index.html                    200  noindex NE  canonical 1
"""
from __future__ import annotations

import re
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
VEREJNE = KOREN / "web" / "public"
DOMENA = "https://www.greenairtech.cz"

PREPEND = """<?php
require '{KOREN}/web/app/Jadro/Autoload.php';
/* Ostrý web zná svou adresu z config/config.php, který v repozitáři není. */
\\App\\Jadro\\Config::nastav(['web' => '{DOMENA}', 'ukazka' => false]);
"""


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """Vestavěný server PHP nad skutečným index.php. Vrací základ adresy."""
    dir = tmp_path_factory.mktemp("chyba404")
    prepend = dir / "prepend.php"
    prepend.write_text(PREPEND.format(KOREN=KOREN, DOMENA=DOMENA), encoding="utf-8")

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        ["php", "-d", f"auto_prepend_file={prepend}",
         "-S", f"127.0.0.1:{port}", "-t", str(VEREJNE), str(VEREJNE / "index.php")],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    zaklad = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if proc.poll() is not None:
                chyba = proc.communicate()[1].decode("utf-8", "replace")
                pytest.fail(f"php -S skončil hned: {chyba[:800]}")
            try:
                urllib.request.urlopen(zaklad + "/index.html", timeout=2).read()
                break
            except urllib.error.HTTPError:
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.1)
        else:
            pytest.fail("vestavěný server PHP se nerozběhl")
        yield zaklad
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def odpoved(zaklad: str, cesta: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(zaklad + cesta, timeout=10) as o:
            return o.status, o.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def hlava(html: str) -> str:
    nalez = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.S | re.I)
    return nalez.group(1) if nalez else ""


@pytest.mark.parametrize("cesta", ["/404.html", "/en/404.html", "/de/404.html"])
def test_chybova_stranka_vraci_404_i_na_vlastni_adrese(server, cesta):
    """Jako 200 OK je to pro vyhledávač běžná stránka, kterou si zaindexuje."""
    kod, _ = odpoved(server, cesta)
    assert kod == 404, f"{cesta} odpovědělo {kod}, čekáme 404"


@pytest.mark.parametrize("cesta", ["/404.html", "/en/404.html", "/de/404.html"])
def test_chybova_stranka_se_neindexuje(server, cesta):
    h = hlava(odpoved(server, cesta)[1])
    assert "noindex" in h, f"{cesta} nemá noindex"
    assert 'rel="canonical"' not in h, f"{cesta} má kanonickou adresu, ale neindexuje se"


def test_neznama_adresa_vraci_404(server):
    kod, html = odpoved(server, "/takova-stranka-neexistuje.html")
    assert kod == 404
    assert "noindex" in hlava(html)


def test_bezna_stranka_vraci_200_a_indexuje_se(server):
    """Druhá strana pravidla: aby se 404 nerozlilo na celý web."""
    kod, html = odpoved(server, "/index.html")
    assert kod == 200
    h = hlava(html)
    assert "noindex" not in h, "veřejná stránka má noindex"
    assert f'<link rel="canonical" href="{DOMENA}/index.html">' in h
