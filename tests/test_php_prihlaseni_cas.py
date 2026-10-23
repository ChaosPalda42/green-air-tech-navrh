"""Brána: z času odpovědi na přihlášení se nesmí poznat, že účet existuje.

Nález K3 (testovací session, kolo 2 i 3). `Uzivatele::overHeslo` sice umí
dopočítat falešný hash i pro neexistující účet, ale volající v
`web/public/index.php` ho u neznámého jména vůbec nezavolal:

    if ($uzivatel !== null && Uzivatele::overHeslo($uzivatel, …))

Zkratka `&&` je přesně ta díra: bcrypt se u známého jména počítá, u neznámého
ne. Testovací session to naměřila třemi požadavky na čisté instalaci (:8099):
známé jméno + špatné heslo 0,20 s, neznámé jméno 0,004 s. Padesátinásobek —
kdo si projede seznam jmen, pozná z časů, která v administraci existují, a
útok na heslo si zúží na účty, které opravdu jsou.

Proč tahle brána vznikla, když jedna časová brána už je: ta stará
(`tests/test_php_uzivatele.py::test_neznamy_ucet_neodpovida_rychleji`) měří
`overHeslo` přímo, a ta byla zelená i s touhle dírou — pravidlo se musí měřit
tam, kde se o přihlášení rozhoduje, tedy na HTTP požadavku. Obě zůstávají:
jedna hlídá funkci, druhá volajícího.

Jak se měří: skutečný `web/public/index.php` běží na vestavěném serveru PHP
nad SQLite (`Spojeni::nastav`), přihlašuje se opravdovým formulářem včetně
CSRF a sezení. Osm pokusů (4 známé jméno, 4 neznámé) se vejde pod zámek
`Zamek::LIMIT_ADRESA = 10`, takže měří heslo, ne zámek.

Zaznamenaný vzorek po opravě (tento stroj, PHP 8.5.10, 23. 10. 2026):
známé jméno 216,50 ms, neznámé 216,43 ms, podíl 1,000. Před opravou:
známé 219,95 ms, neznámé 1,53 ms, podíl 0,007 — brána padala na témže řádku.
"""
from __future__ import annotations

import http.cookiejar
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
VEREJNE = KOREN / "web" / "public"

JMENO = "qa-spravce"
EMAIL = "qa-spravce@greenairtech.cz"
HESLO = "Spravne-Heslo-123"
SPATNE = "Spatne-Heslo-123"
NEZNAME = "qa-takovy-tu-neni"

POKUSU = 4          # na každou variantu; 8 celkem je pod Zamek::LIMIT_ADRESA
POMER = 0.5         # neznámé jméno nesmí být rychlejší než polovina známého

PREPEND = r"""<?php
/* Podstrčené prostředí pro bránu: skutečný index.php, ale databáze SQLite
   v souboru a nastavení bez config.php (ten v repozitáři není). */
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Db\Spojeni;
use App\Db\UlozisteDb;
use App\Jadro\Config;

Config::nastav([
    'ukazka' => false,
    'posta' => ['zpusob' => 'log'],
    'domena' => 'http://127.0.0.1',
]);

$soubor = '{DB}';
$nova = !is_file($soubor) || filesize($soubor) === 0;
$pdo = new PDO('sqlite:' . $soubor, null, null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);
if ($nova) {{
    $pdo->exec('CREATE TABLE stav (
        id INTEGER PRIMARY KEY, dokument TEXT NOT NULL,
        zmeneno TEXT NOT NULL, kdo TEXT NOT NULL)');
    $pdo->exec('CREATE TABLE stav_historie (
        id INTEGER PRIMARY KEY AUTOINCREMENT, dokument TEXT NOT NULL,
        zmeneno TEXT NOT NULL, kdo TEXT NOT NULL)');
    $pdo->exec('CREATE TABLE uzivatele (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jmeno TEXT NOT NULL, email TEXT NOT NULL UNIQUE, role TEXT NOT NULL,
        heslo_hash TEXT, aktivni INTEGER NOT NULL DEFAULT 1,
        pozvanka_token TEXT, pozvanka_do TEXT,
        vytvoreno TEXT NOT NULL, posledni_prihlaseni TEXT)');
    $pdo->exec('CREATE TABLE poptavky (
        id INTEGER PRIMARY KEY AUTOINCREMENT, prijato TEXT NOT NULL,
        typ TEXT NOT NULL DEFAULT "", jmeno TEXT NOT NULL DEFAULT "",
        email TEXT NOT NULL DEFAULT "", telefon TEXT NOT NULL DEFAULT "",
        zprava TEXT, vetev TEXT NOT NULL DEFAULT "",
        jazyk TEXT NOT NULL DEFAULT "cs", odeslano INTEGER NOT NULL DEFAULT 0)');
    $pdo->exec('CREATE TABLE udalosti (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kdy TEXT NOT NULL,
        kdo TEXT NOT NULL DEFAULT "", akce TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT "")');

    $vloz = $pdo->prepare('INSERT INTO uzivatele
        (jmeno, email, role, heslo_hash, aktivni, vytvoreno)
        VALUES (?, ?, ?, ?, 1, ?)');
    $vloz->execute([
        '{JMENO}', '{EMAIL}', 'spravce',
        password_hash('{HESLO}', PASSWORD_DEFAULT),
        date('Y-m-d H:i:s'),
    ]);
}}
Spojeni::nastav($pdo);
"""


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """Vestavěný server PHP nad skutečným index.php. Vrací základ adresy."""
    dir = tmp_path_factory.mktemp("prihlaseni")
    prepend = dir / "prepend.php"
    prepend.write_text(
        PREPEND.format(KOREN=KOREN, DB=dir / "qa.sqlite", JMENO=JMENO,
                       EMAIL=EMAIL, HESLO=HESLO),
        encoding="utf-8",
    )

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        ["php", "-d", f"auto_prepend_file={prepend}",
         "-d", f"session.save_path={dir}",
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
                urllib.request.urlopen(zaklad + "/administrace.html", timeout=2).read()
                break
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
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


def _otevri(zaklad):
    """Vrátí (opener, csrf): sezení s cookie a token z přihlašovací stránky."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    html = opener.open(zaklad + "/administrace.html", timeout=10).read().decode("utf-8", "replace")
    nalez = re.search(r'name="csrf" value="([^"]+)"', html)
    assert nalez, "na přihlašovací stránce není skryté pole csrf"
    return opener, nalez.group(1)


def _zkus(opener, zaklad, csrf, jmeno, heslo):
    """Pošle přihlášení a vrátí (sekundy, stav). Přesměrování se nenásleduje."""
    data = urllib.parse.urlencode({
        "akce": "prihlasit", "csrf": csrf, "jmeno": jmeno, "heslo": heslo,
    }).encode()
    pozadavek = urllib.request.Request(zaklad + "/administrace.html", data=data)

    class BezSkoku(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    bez = urllib.request.build_opener(
        *[h for h in opener.handlers if isinstance(h, urllib.request.HTTPCookieProcessor)],
        BezSkoku(),
    )
    zacatek = time.perf_counter()
    try:
        odpoved = bez.open(pozadavek, timeout=30)
        stav = odpoved.getcode()
        odpoved.read()
    except urllib.error.HTTPError as e:
        stav = e.code
        e.read()
    return time.perf_counter() - zacatek, stav


def _stred(hodnoty):
    s = sorted(hodnoty)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


@pytest.fixture(scope="module")
def mereni(server):
    """Každý pokus z ČERSTVÉHO sezení — `Sezeni::spatneHeslo` od třetího
    pokusu v jednom sezení schválně spí (1–3 s) a to zdržení by rozdíl
    v ověřování hesla překrylo. Útočník si sezení taky zahodí."""
    casy = {"zname": [], "nezname": []}
    stavy = set()
    for _ in range(POKUSU):
        for klic, jmeno in (("zname", JMENO), ("nezname", NEZNAME)):
            opener, csrf = _otevri(server)
            cas, stav = _zkus(opener, server, csrf, jmeno, SPATNE)
            casy[klic].append(cas * 1000)
            stavy.add(stav)
    return {
        "zname": _stred(casy["zname"]),
        "nezname": _stred(casy["nezname"]),
        "stavy": stavy,
        "vsechno": casy,
    }


def test_spatne_heslo_neprihlasi(mereni):
    """Osm pokusů se špatným heslem nesmí nikoho pustit dál — kdyby některý
    prošel, časy by se měřily na jiné cestě, než si brána myslí."""
    assert mereni["stavy"] <= {200, 303}, f"nečekané stavy: {mereni['stavy']}"


def test_neznamy_ucet_neodpovida_rychleji_pres_http(mereni):
    """Nález K3: volající musí heslo ověřit i u jména, které neexistuje."""
    zname, nezname = mereni["zname"], mereni["nezname"]
    assert zname > 20, (
        f"přihlášení se známým jménem trvalo {zname:.0f} ms — na bcrypt to "
        "nevypadá a měření nemá co srovnávat (běží vůbec ověřování hesla?)"
    )
    assert nezname >= zname * POMER, (
        f"neznámé jméno odpovědělo za {nezname:.0f} ms, známé za {zname:.0f} ms "
        f"(podíl {nezname / zname:.3f}) — z času jde poznat, který účet "
        "v administraci existuje"
    )
