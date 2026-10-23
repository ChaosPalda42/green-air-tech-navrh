"""Brána: druhý uživatel se stejným e-mailem je konflikt, ne spadlý server.

Tester poslal dvakrát `POST /api/uzivatele` se stejnou adresou a dostal
`{"chyba":"chyba-serveru"}` s kódem 500 — UNIQUE KEY email v databázi
vyhodil PDOException a ta prolétla až do obecné obsluhy chyb. Správce
tak neví, co udělal špatně, a v logu zůstane hlášená „chyba serveru“,
která žádnou chybou serveru není.

Pravidlo má dvě poloviny a obě se měří:

1. Úložiště překládá porušení jednoznačnosti na doménovou výjimku
   App\\Api\\Konflikt — a NEPŘEKLÁDÁ na ni cokoli jiného, aby se pod
   „obsazený e-mail" neschovala rozbitá databáze.
2. Router na Konflikt odpovídá 409 s důvodem v těle, ne 500.

První polovina běží nad opravdovou databází (SQLite v paměti s týmž
UNIQUE), ne nad podvrhem — jinak by brána měřila jen můj odhad, jak se
ovladač zachová.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Konflikt;
use App\Api\Router;
use App\Api\Uloziste;
use App\Db\UlozisteDb;

/* ---------- 1. úložiště nad skutečnou databází ---------- */

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('CREATE TABLE uzivatele (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jmeno TEXT NOT NULL, email TEXT NOT NULL UNIQUE, role TEXT NOT NULL,
    heslo_hash TEXT, aktivni INTEGER NOT NULL DEFAULT 1,
    pozvanka_token TEXT, pozvanka_do TEXT,
    vytvoreno TEXT NOT NULL, posledni_prihlaseni TEXT
)');
$db = new UlozisteDb($pdo);

$novy = ['jmeno' => 'Nová Kolegyně', 'email' => 'nova@greenairtech.cz', 'role' => 'editor'];
$prvni = $db->ulozUzivatele($novy);

$druhy = ['stav' => 'proslo'];
try {
    $db->ulozUzivatele(['jmeno' => 'Někdo Jiný'] + $novy);
} catch (Konflikt $e) {
    $druhy = ['stav' => 'konflikt', 'duvod' => $e->getMessage()];
} catch (\Throwable $e) {
    $druhy = ['stav' => 'vybuch', 'trida' => get_class($e)];
}

/* Jiná závada databáze se za „obsazený e-mail" vydávat nesmí. */
$pdo->exec('DROP TABLE uzivatele');
$rozbite = ['stav' => 'proslo'];
try {
    $db->ulozUzivatele($novy);
} catch (Konflikt $e) {
    $rozbite = ['stav' => 'konflikt', 'duvod' => $e->getMessage()];
} catch (\Throwable $e) {
    $rozbite = ['stav' => 'vybuch', 'trida' => get_class($e)];
}

/* ---------- 2. co na to Router ---------- */

$uloziste = new class implements Uloziste {
    public function stav(): array { return []; }
    public function ulozStav(array $stav, string $kdo): void {}
    public function uzivatele(): array { return []; }
    public function ulozUzivatele(array $u): array { throw new Konflikt('email-obsazeny'); }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }
};

$odpoved = ['stav' => 'vybuch'];
try {
    $odpoved = Router::obsluz([
        'metoda' => 'POST', 'cesta' => 'uzivatele', 'dotaz' => [], 'soubor' => null,
        'csrf_ok' => true, 'uzivatel' => ['id' => 1, 'jmeno' => 'pavel', 'role' => 'spravce'],
        'telo' => json_encode($novy),
    ], $uloziste, null, null);
} catch (\Throwable $e) {
    $odpoved = ['stav' => 'vybuch', 'trida' => get_class($e)];
}

echo json_encode([
    'prvni_zapis' => ['email' => $prvni['email'] ?? null, 'id' => (int) ($prvni['id'] ?? 0)],
    'druhy_zapis' => $druhy,
    'rozbita_databaze' => $rozbite,
    'router' => $odpoved,
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    program = tmp_path_factory.mktemp("dupl") / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:800])
    return json.loads(hotovo.stdout)


def test_prvni_uzivatel_se_ulozi(v):
    """Kdyby se nezapsal ani první, druhý by na konflikt narazit nemohl."""
    assert v["prvni_zapis"]["id"] > 0, v["prvni_zapis"]
    assert v["prvni_zapis"]["email"] == "nova@greenairtech.cz"


def test_druhy_stejny_email_je_konflikt(v):
    d = v["druhy_zapis"]
    assert d["stav"] == "konflikt", (
        "druhý zápis se stejným e-mailem nedal konflikt, ale "
        + json.dumps(d, ensure_ascii=False)
    )
    assert d["duvod"] == "email-obsazeny", d


def test_rozbita_databaze_se_za_obsazeny_email_nevydava(v):
    r = v["rozbita_databaze"]
    assert r["stav"] == "vybuch", (
        "chybějící tabulku úložiště vydalo za konflikt e-mailů: "
        + json.dumps(r, ensure_ascii=False)
    )


def test_router_odpovi_409_a_ne_500(v):
    o = v["router"]
    assert o.get("stav") == 409, f"router odpověděl {o.get('stav')} místo 409: {o}"
    assert o["telo"]["chyba"] == "email-obsazeny", o["telo"]
