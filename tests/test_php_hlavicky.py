"""Brána: jaké bezpečnostní hlavičky ostrý web posílá.

Hlavičky posílá PHP (ne jen .htaccess), aby platily i na nginxu. Tenhle test
se ptá na jejich obsah — jestli opravdu odcházejí, se ověřuje na nasazené
instalaci curl -D.

Pravidlo:
- CSP nesmí povolit načtení skriptu odjinud než z našeho webu a z Google Tag
  Manageru (měření); stránka se nesmí dát vložit do cizího rámu a formulář
  se nesmí dát odeslat jinam.
- HSTS se posílá JEN po HTTPS. Po HTTP by ho prohlížeč zahodil a na webu bez
  certifikátu by se tím dal web zamknout.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
echo json_encode([
    'http' => \App\Jadro\Hlavicky::seznam(false),
    'https' => \App\Jadro\Hlavicky::seznam(true),
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
"""


@pytest.fixture(scope="module")
def hlavicky():
    hotovo = subprocess.run(
        ["php", "-r", PROGRAM.replace("{KOREN}", str(KOREN))],
        capture_output=True, text=True,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return json.loads(hotovo.stdout)


def test_hsts_jen_pres_https(hlavicky):
    assert "Strict-Transport-Security" not in hlavicky["http"]
    assert "max-age=" in hlavicky["https"]["Strict-Transport-Security"]
    assert "preload" not in hlavicky["https"]["Strict-Transport-Security"]


@pytest.mark.parametrize("jmeno", [
    "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy",
    "Permissions-Policy", "Content-Security-Policy",
])
def test_hlavicka_je_v_obou_pripadech(jmeno, hlavicky):
    assert jmeno in hlavicky["http"] and jmeno in hlavicky["https"]


def csp(hlavicky) -> dict[str, str]:
    radky = [c.strip() for c in hlavicky["https"]["Content-Security-Policy"].split(";") if c.strip()]
    return {r.split(" ", 1)[0]: r for r in radky}


def test_csp_pousti_skripty_jen_z_naseho_webu_a_od_googlu(hlavicky):
    smerovky = csp(hlavicky)
    assert smerovky["script-src"] == "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com"
    assert smerovky["default-src"] == "default-src 'self'"
    assert smerovky["object-src"] == "object-src 'none'"


def test_csp_zakazuje_cizi_ram_a_cizi_cil_formulare(hlavicky):
    smerovky = csp(hlavicky)
    assert smerovky["frame-ancestors"] == "frame-ancestors 'self'"
    assert smerovky["form-action"] == "form-action 'self'"
    assert smerovky["base-uri"] == "base-uri 'self'"


def test_csp_pousti_obrazky_z_administrace(hlavicky):
    """Náhled nahrané fotky je blob:/data: URL — bez nich by administrace
    ukazovala prázdná místa."""
    obrazky = csp(hlavicky)["img-src"]
    assert "data:" in obrazky and "blob:" in obrazky
