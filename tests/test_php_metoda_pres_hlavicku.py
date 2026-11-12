"""Brána: administrace musí uložit i tam, kde hosting nepustí PUT a DELETE.

Nález z ostrého webu (12. 11. 2026). Správce v administraci posunul fotku a
dostal „Na tuhle změnu nemáte právo." Právo měl — požadavek se k PHP vůbec
nedostal: hosting u klienta odmítá metody PUT a DELETE na úrovni Apache,
takže 403 vrátil web server dřív, než se spustil index.php. Administrace
ukládá všechno PUTem a maže DELETE, takže tam nešlo uložit NIC; a protože
odpověď byla HTML, prohlížeč z ní přečetl jen stavový kód 403 a ukázal
hlášku o právech.

Oprava: prohlížeč posílá POST a skutečnou metodu připíše do hlavičky
`X-HTTP-Method-Override`; `App\\Jadro\\Metoda` ji na serveru přečte zpátky.
Bere se jen hlavička a jen u POSTu — tu cizí stránka nenastaví (prohlížeč by
si vyžádal CORS preflight), kdežto formulářové pole `_method` jde odeslat
odkudkoli.

Zaznamenaný vzorek skutečného provozu:

  ostrý web https://www.greenairtech.cz (12. 11. 2026, před opravou):
    GET    /api/stav  401  application/json  {"chyba":"neprihlaseno"}
    POST   /api/stav  405  application/json  {"chyba":"spatna-metoda"}
    PUT    /api/stav  403  text/html         199 B od Apache
    DELETE /api/stav  403  text/html         199 B od Apache

  zkušební nasazení (Docker, PHP 8.5.12, přihlášený správce, po opravě):
    POST /api/stav bez hlavičky                405  {"chyba":"spatna-metoda"}
    POST /api/stav + X-HTTP-Method-Override: PUT      200, uloženy 3 výřezy,
         radek-tyla = {"zoom":120,"x":0,"y":-8}
    POST /api/stav + X-HTTP-Method-Override: SMAZAT   405  {"chyba":"spatna-metoda"}
    načtení /administrace.html znovu            ve stavu 3 výřezy
    načtení /kontakt.html                       --vz:1.20;--vx:0%;--vy:-8%
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
VEREJNE = KOREN / "web" / "public"
INDEX = VEREJNE / "index.php"
ADMIN_JS = VEREJNE / "assets" / "admin.js"

PROGRAM = r"""
require 'KOREN/web/app/Jadro/Autoload.php';

use App\Jadro\Metoda;

$pripady = json_decode(file_get_contents('php://stdin'), true);
$ven = [];
foreach ($pripady as $p) {
    $server = [];
    if ($p['hlavicka'] !== null) {
        $server['HTTP_X_HTTP_METHOD_OVERRIDE'] = $p['hlavicka'];
    }
    $ven[] = Metoda::skutecna($p['metoda'], $server);
}
echo json_encode($ven);
"""

# metoda požadavku, hodnota hlavičky (None = hlavička chybí), co má vyjít
PRIPADY = [
    ("POST", "PUT", "PUT"),
    ("POST", "DELETE", "DELETE"),
    ("POST", "put", "PUT"),
    ("POST", "  PUT  ", "PUT"),
    ("POST", None, "POST"),
    ("POST", "", "POST"),
    ("POST", "GET", "POST"),
    ("POST", "POST", "POST"),
    ("POST", "SMAZAT", "POST"),
    ("POST", "PUT, DELETE", "POST"),
    # mimo POST hlavička nerozhoduje: GET se nesmí dát přestrojit na mazání
    ("GET", "DELETE", "GET"),
    ("PUT", "DELETE", "PUT"),
    ("DELETE", "PUT", "DELETE"),
    ("get", None, "GET"),
]


def test_metoda_z_hlavicky():
    """Hlavička platí jen u POSTu a jen pro PUT a DELETE."""
    vstup = json.dumps([{"metoda": m, "hlavicka": h} for m, h, _ in PRIPADY])
    hotovo = subprocess.run(
        ["php", "-r", PROGRAM.replace("KOREN", str(KOREN))],
        input=vstup, capture_output=True, text=True,
    )
    assert hotovo.returncode == 0, hotovo.stderr[:800]
    dostali = json.loads(hotovo.stdout)
    cekali = [c for _, _, c in PRIPADY]
    rozdily = [
        f"{m} + {h!r} → {d}, čekáno {c}"
        for (m, h, c), d in zip(PRIPADY, dostali)
        if d != c
    ]
    assert rozdily == [], "; ".join(rozdily)


def test_index_preklada_metodu_v_api():
    """index.php se na skutečnou metodu ptá uvnitř API, a to před Routerem.

    Pořadí rozhoduje: nad poptávkou by hlavička přestrojila i veřejný
    formulář, pod Routerem by se nestihla uplatnit.
    """
    zdroj = INDEX.read_text("utf-8")
    assert "Metoda::skutecna($metoda, $_SERVER)" in zdroj, (
        "index.php se neptá App\\Jadro\\Metoda na skutečnou metodu — "
        "POST s hlavičkou se k Routeru dostane pořád jako POST"
    )
    kde_api = zdroj.index("str_starts_with($cesta, 'api/')")
    kde_poptavka = zdroj.index("Poptavka::obsluz(")
    kde_preklad = zdroj.index("Metoda::skutecna($metoda, $_SERVER)")
    kde_router = zdroj.index("Router::obsluz(")
    assert kde_api < kde_poptavka < kde_preklad < kde_router, (
        f"špatné pořadí v index.php: api={kde_api} poptavka={kde_poptavka} "
        f"překlad={kde_preklad} router={kde_router}"
    )


def test_administrace_posila_prestrojenou_metodu():
    """Sbalený skript administrace posílá POST a metodu v hlavičce."""
    skript = ADMIN_JS.read_text("utf-8")
    assert '"X-HTTP-Method-Override"' in skript, (
        "admin.js hlavičku neposílá — na hostingu bez PUT se neuloží nic"
    )
    assert 'method: prestrojena ? "POST" : metoda' in skript, (
        "admin.js pořád posílá PUT/DELETE natvrdo"
    )


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """Vestavěný server PHP nad skutečným index.php. Vrací základ adresy."""
    dir = tmp_path_factory.mktemp("metoda")
    prepend = dir / "prepend.php"
    prepend.write_text(
        "<?php\nrequire '%s/web/app/Jadro/Autoload.php';\n"
        "\\App\\Jadro\\Config::nastav(['web' => 'https://www.greenairtech.cz', 'ukazka' => false]);\n"
        % KOREN,
        encoding="utf-8",
    )

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
                pytest.fail("php -S skončil hned: " + proc.communicate()[1].decode()[:800])
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


def posli(zaklad: str, metoda: str, cesta: str, hlavicky: dict, telo: bytes | None = None):
    zadost = urllib.request.Request(zaklad + cesta, data=telo, method=metoda)
    for k, v in hlavicky.items():
        zadost.add_header(k, v)
    trida = urllib.request.HTTPRedirectHandler

    class BezPresmerovani(trida):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(BezPresmerovani)
    try:
        with opener.open(zadost, timeout=10) as o:
            return o.getcode()
    except urllib.error.HTTPError as e:
        return e.code


def test_hlavicka_nevleze_mimo_api(server):
    """Přihlašovací POST na administraci zůstává POSTem i s hlavičkou.

    Kdyby se překlad udělal nad celým požadavkem, hlavička by přihlášení i
    odhlášení proměnila v PUT a formulář by přestal fungovat.
    """
    bez = posli(server, "POST", "/administrace.html",
                {"Content-Type": "application/x-www-form-urlencoded"}, b"akce=odhlasit")
    s_hlavickou = posli(server, "POST", "/administrace.html",
                        {"Content-Type": "application/x-www-form-urlencoded",
                         "X-HTTP-Method-Override": "PUT"}, b"akce=odhlasit")
    assert bez == 303, f"odhlášení nevrací 303, ale {bez}"
    assert s_hlavickou == 303, (
        f"hlavička změnila i požadavek mimo API: {s_hlavickou} místo 303"
    )
