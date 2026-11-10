"""Brána: web má jednu adresu — https://www.greenairtech.cz.

Nález při kontrole ostrého webu (10. 11. 2026). Web odpovídal kódem 200 na
všech čtyřech adresách — `http://greenairtech.cz`, `http://www.greenairtech.cz`,
`https://greenairtech.cz`, `https://www.greenairtech.cz` — a ani jedna
nepřesměrovala na druhou. Pro vyhledávač to byly čtyři weby se stejným
obsahem. Kanonická adresa v hlavě stránky (test_php_kanonicka_adresa.py) je
jen žádost, kterou vyhledávač může přejít; odpověď serveru je 301.

Druhá polovina: po čistém HTTP se web obsluhoval celý, včetně přihlášení do
administrace. HSTS se posílá jen po HTTPS (a správně — po HTTP by ho prohlížeč
zahodil), takže návštěvníka na HTTP nic na HTTPS nepřevedlo.

Proč brána takhle: pravidlo je v `.htaccess`, tedy v konfiguraci Apache —
jediný způsob, jak ho změřit, je spustit Apache a zeptat se ho. Test tedy
rozběhne `/usr/sbin/httpd` nad `web/public` s `AllowOverride All`, bez PHP,
a ptá se na stavový kód a hlavičku Location. Čtení souboru očima by změřilo
jen to, že tam text je — ne že Apache podle něj rozhoduje (stačí špatně
pořadí nebo chybějící `[L]`).

Co brána hlídá i obráceně: cizí hostitel (localhost, IP, testovací adresa)
se přesměrovat NESMÍ, jinak by se tím rozbil vývoj a případná testovací
instalace. A `/.well-known/` musí projít i po HTTP, jinak by se obnova
certifikátu zacyklila na našem vlastním přesměrování.

Zaznamenaný vzorek (tento stroj, Apache 2.4.67, 10. 11. 2026):
  PŘED opravou  Host greenairtech.cz, http   → 200 (žádné Location)
                Host www.greenairtech.cz, http → 200
                Host localhost                 → 200
  PO opravě     Host greenairtech.cz, http   → 301 https://www.greenairtech.cz/kontakt.html
                Host www.greenairtech.cz, http → 301 https://www.greenairtech.cz/kontakt.html
                Host greenairtech.cz, X-Forwarded-Proto: https → 301 (na www, jeden skok)
                Host www.greenairtech.cz, X-Forwarded-Proto: https → 200
                Host localhost                 → 200 (vývoj se nepřesměrovává)
                /.well-known/acme-challenge/x po HTTP → 200
"""
from __future__ import annotations

import http.client
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
VEREJNE = KOREN / "web" / "public"
HTTPD = "/usr/sbin/httpd"
MODULY = Path("/usr/libexec/apache2")

KONFIGURACE = """
ServerName zkouska.local
Listen 127.0.0.1:{PORT}
PidFile "{DIR}/httpd.pid"
ErrorLog "{DIR}/error.log"
LoadModule mpm_prefork_module {MODULY}/mod_mpm_prefork.so
LoadModule authz_core_module {MODULY}/mod_authz_core.so
LoadModule unixd_module {MODULY}/mod_unixd.so
LoadModule dir_module {MODULY}/mod_dir.so
LoadModule mime_module {MODULY}/mod_mime.so
LoadModule headers_module {MODULY}/mod_headers.so
LoadModule setenvif_module {MODULY}/mod_setenvif.so
LoadModule rewrite_module {MODULY}/mod_rewrite.so
DocumentRoot "{KOREN}"
<Directory "{KOREN}">
    AllowOverride All
    Require all granted
</Directory>
"""


@pytest.fixture(scope="module")
def apache(tmp_path_factory):
    """Skutečný Apache nad web/public, aby šlo změřit, jak rozhoduje.

    PHP se nenahrává — index.php se tedy pošle jako text. Nám jde o stavový
    kód a Location, ne o vykreslenou stránku."""
    if not Path(HTTPD).is_file():
        pytest.skip(f"{HTTPD} na tomhle stroji není")

    dir = tmp_path_factory.mktemp("apache")
    # Apache chce čitelnou cestu až ke kořeni; tmp od pytestu to splňuje.
    koren = dir / "web"
    shutil.copytree(VEREJNE, koren)

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    conf = dir / "httpd.conf"
    conf.write_text(KONFIGURACE.format(
        PORT=port, DIR=dir, KOREN=koren, MODULY=MODULY,
    ), encoding="utf-8")

    hotovo = subprocess.run([HTTPD, "-f", str(conf), "-t"],
                            capture_output=True, text=True)
    assert hotovo.returncode == 0, f"konfigurace Apache neprošla: {hotovo.stderr[-800:]}"

    # Vlastní skupina procesů a zahozený výstup: httpd si forkuje potomky a
    # bez toho si na sebe pytest a Apache posílají signály.
    proc = subprocess.Popen([HTTPD, "-f", str(conf), "-D", "FOREGROUND"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    try:
        for _ in range(100):
            if proc.poll() is not None:
                chyba = (dir / "error.log").read_text(encoding="utf-8", errors="replace")
                pytest.fail(f"httpd skončil hned: {chyba[-800:]}")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            pytest.fail("Apache se nerozběhl")
        # Složka pro ACME; po HTTP musí projít i bez PHP.
        acme = koren / ".well-known" / "acme-challenge"
        acme.mkdir(parents=True, exist_ok=True)
        (acme / "zkouska").write_text("ok", encoding="utf-8")
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def zeptej(port: int, cesta: str, host: str, hlavicky: dict | None = None):
    """Vrátí (stavový kód, Location)."""
    spoj = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        spoj.request("GET", cesta, headers={"Host": host, **(hlavicky or {})})
        o = spoj.getresponse()
        o.read()
        return o.status, o.getheader("Location")
    finally:
        spoj.close()


CIL = "https://www.greenairtech.cz"


@pytest.mark.parametrize("host", ["greenairtech.cz", "www.greenairtech.cz"])
def test_cisty_http_jde_na_https_s_www(apache, host):
    """Po HTTP se web vůbec obsluhovat nemá — a to jedním skokem na www."""
    kod, kam = zeptej(apache, "/kontakt.html", host)
    assert kod == 301, f"Host {host} po HTTP odpovědělo {kod}, čekáme 301"
    assert kam == f"{CIL}/kontakt.html", f"Host {host} míří na {kam}"


def test_adresa_bez_www_jde_na_www_i_kdyz_uz_je_https(apache):
    """HTTPS bez www je ta druhá polovina duplicity."""
    kod, kam = zeptej(apache, "/kontakt.html", "greenairtech.cz",
                      {"X-Forwarded-Proto": "https"})
    assert kod == 301 and kam == f"{CIL}/kontakt.html", f"kód {kod}, Location {kam}"


def test_hlavni_adresa_se_neprresmerovava(apache):
    """Druhá strana pravidla: na správné adrese se web obsluhuje. Kdyby se
    přesměrovával i tady, zacyklí se a web je nedostupný."""
    kod, kam = zeptej(apache, "/kontakt.html", "www.greenairtech.cz",
                      {"X-Forwarded-Proto": "https"})
    assert kod == 200, f"hlavní adresa odpověděla {kod} (Location {kam}) — hrozí smyčka"


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "zkouska.local"])
def test_cizi_hostitel_se_neprresmerovava(apache, host):
    """Vývoj a testovací instalace nesmí skončit na ostré adrese klienta."""
    kod, kam = zeptej(apache, "/kontakt.html", host)
    assert kod == 200, f"Host {host} se přesměroval ({kod} → {kam})"


def test_dotaz_zustava_v_adrese(apache):
    """Bez query stringu by se ztratily parametry, třeba ?chyba=1 u přihlášení."""
    kod, kam = zeptej(apache, "/administrace.html?chyba=1", "greenairtech.cz")
    assert kod == 301
    assert kam == f"{CIL}/administrace.html?chyba=1", f"Location {kam}"


def test_overeni_certifikatu_projde_i_po_http(apache):
    """Kdyby se ACME přesměrovalo na HTTPS, obnova certifikátu by se zacyklila
    právě ve chvíli, kdy certifikát propadl."""
    kod, kam = zeptej(apache, "/.well-known/acme-challenge/zkouska",
                      "www.greenairtech.cz")
    assert kod == 200, f"ACME po HTTP odpovědělo {kod} (Location {kam})"


def test_zakaz_skriptu_v_media_plati_i_po_http(apache):
    """Obrana do hloubky se přesměrováním nesmí obejít — 403, ne 301."""
    kod, kam = zeptej(apache, "/media/zkouska.php", "greenairtech.cz")
    assert kod == 403, f"media/zkouska.php odpovědělo {kod} (Location {kam})"
