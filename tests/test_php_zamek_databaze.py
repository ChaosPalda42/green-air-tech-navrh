"""Brána: úložiště počítá špatná hesla ODDĚLENĚ pro adresu a pro účet.

Nezávislý test našel, že deset špatných hesel na jméno `qa-spravce`
z deseti různých adres vyřadí správce z administrace na čtvrt hodiny —
kdo zná jeho login, drží ho venku a nic k tomu nepotřebuje. Příčina je
v dotazu: `WHERE ... AND (kdo = ? OR detail = ?)` slije pokusy na jméno
a pokusy z adresy do JEDNOHO seznamu, takže oboje narazí na týž nízký
strop.

Pravidlo:
1. `casyChybnychHesel` vrací dvě sady — `adresa` (co přišlo z té jedné
   adresy, na kohokoli) a `ucet` (co přišlo na ten jeden účet, odkudkoli).
   Rozhoduje pak Zamek, každou sadu s vlastním stropem.
2. Účet má JEDNU identitu. Přihlašovat se jde jménem i e-mailem
   (`WHERE email = ? OR jmeno = ?`); kdyby se pokusy počítaly na doslovný
   napsaný řetězec, útočník si strop snadno zdvojí a zámek se obejde
   napsáním té druhé podoby. Pokusy na existující účet se proto počítají
   pod jeho jménem z databáze, ať se útočník ptal jakkoli.
3. Co není v okně, se nepočítá — a dotaz nesmí záležet na funkcích
   MariaDB, které se nedají proměřit (hranice okna se spočítá v PHP).

Měří se nad skutečnou databází (SQLite v paměti s týmiž tabulkami), ne
nad podvrhem; podvrh by měřil jen můj odhad, co dotaz vrátí.
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

use App\Db\UlozisteDb;

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('CREATE TABLE uzivatele (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jmeno TEXT NOT NULL, email TEXT NOT NULL UNIQUE, role TEXT NOT NULL,
    heslo_hash TEXT, aktivni INTEGER NOT NULL DEFAULT 1,
    pozvanka_token TEXT, pozvanka_do TEXT,
    vytvoreno TEXT NOT NULL, posledni_prihlaseni TEXT
)');
$pdo->exec('CREATE TABLE udalosti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kdy TEXT NOT NULL, kdo TEXT NOT NULL DEFAULT "",
    akce TEXT NOT NULL, detail TEXT NOT NULL DEFAULT ""
)');
$db = new UlozisteDb($pdo);

$spravce = $db->ulozUzivatele([
    'jmeno' => 'qa-spravce', 'email' => 'spravce@greenairtech.cz', 'role' => 'spravce',
]);

$ven = [];

/* ---- 1. deset pokusů na správce z deseti různých adres ---- */
for ($i = 1; $i <= 10; $i++) {
    $db->zapisChybneHeslo('qa-spravce', '203.0.113.' . $i);
}
/* Správce se hlásí ze své adresy, na které nikdo nic nezkoušel. */
$ven['utok_zvenci'] = $db->casyChybnychHesel('qa-spravce', '198.51.100.7', 900);

/* ---- 2. deset pokusů z jedné adresy na deset různých jmen ---- */
$pdo->exec('DELETE FROM udalosti');
for ($i = 1; $i <= 10; $i++) {
    $db->zapisChybneHeslo('nekdo-' . $i, '203.0.113.200');
}
$ven['utok_z_jedne_adresy'] = $db->casyChybnychHesel('nekdo-1', '203.0.113.200', 900);

/* ---- 3. útočník střídá jméno a e-mail téhož účtu ---- */
$pdo->exec('DELETE FROM udalosti');
for ($i = 1; $i <= 5; $i++) {
    $db->zapisChybneHeslo('qa-spravce', '203.0.113.' . $i);
    $db->zapisChybneHeslo('spravce@greenairtech.cz', '203.0.113.' . $i);
}
$ven['jmeno_i_email'] = [
    'ptam_se_jmenem' => $db->casyChybnychHesel('qa-spravce', '198.51.100.7', 900),
    'ptam_se_emailem' => $db->casyChybnychHesel('spravce@greenairtech.cz', '198.51.100.7', 900),
    'velkymi_pismeny' => $db->casyChybnychHesel('QA-Spravce', '198.51.100.7', 900),
];

/* ---- 4. co je starší než okno, se nepočítá ---- */
$pdo->exec('DELETE FROM udalosti');
$db->zapisChybneHeslo('qa-spravce', '203.0.113.1');
$pdo->prepare('UPDATE udalosti SET kdy = ?')->execute([date('Y-m-d H:i:s', time() - 3600)]);
$db->zapisChybneHeslo('qa-spravce', '203.0.113.1');
$ven['stare_se_nepocita'] = $db->casyChybnychHesel('qa-spravce', '203.0.113.1', 900);

/* ---- 5. neexistující účet: pokusy se počítají na napsaný řetězec ---- */
$pdo->exec('DELETE FROM udalosti');
$db->zapisChybneHeslo('nikdo-takovy', '203.0.113.1');
$ven['neexistujici_ucet'] = $db->casyChybnychHesel('nikdo-takovy', '198.51.100.7', 900);

/* ---- 6. jinou akci v udalosti do toho nepleteme ---- */
$pdo->exec('DELETE FROM udalosti');
$db->zapisChybneHeslo('qa-spravce', '203.0.113.1');
$db->zapisUdalost('qa-spravce', 'prihlaseni', '203.0.113.1');
$ven['po_prihlaseni'] = $db->casyChybnychHesel('qa-spravce', '203.0.113.1', 900);

echo json_encode(['spravce_id' => (int) ($spravce['id'] ?? 0), 'pripady' => $ven],
    JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    program = tmp_path_factory.mktemp("zamekdb") / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:800])
    return json.loads(hotovo.stdout)


def pocty(sada: dict) -> tuple[int, int]:
    assert set(sada) == {"adresa", "ucet"}, (
        "casyChybnychHesel musí vrátit dvě pojmenované sady "
        '{"adresa": [...], "ucet": [...]}, vrátilo: ' + json.dumps(sada, ensure_ascii=False)[:200]
    )
    return len(sada["adresa"]), len(sada["ucet"])


def test_zapis_vubec_funguje(v):
    """Kdyby se nic nezapisovalo, všechny sady by byly prázdné a brána zelená."""
    assert v["spravce_id"] > 0
    adresa, ucet = pocty(v["pripady"]["utok_z_jedne_adresy"])
    assert adresa == 10, v["pripady"]["utok_z_jedne_adresy"]


def test_utok_zvenci_nespadne_na_vrub_spravcovy_adresy(v):
    """Tohle je ten nález: deset adres na jedno jméno nesmí vypadat
    jako deset pokusů z adresy, odkud se správce hlásí."""
    adresa, ucet = pocty(v["pripady"]["utok_zvenci"])
    assert adresa == 0, (
        f"pokusy z cizích adres se připsaly adrese správce ({adresa}) — "
        "tím se dá správce vyřadit z administrace"
    )
    assert ucet == 10, f"pokusy na účet se nepočítají vůbec ({ucet}) — zámek by nikdy nedržel"


def test_utok_z_jedne_adresy_se_pocita_adrese(v):
    adresa, ucet = pocty(v["pripady"]["utok_z_jedne_adresy"])
    assert adresa == 10, adresa
    assert ucet == 1, f"na účet `nekdo-1` šel jeden pokus, ne {ucet}"


def test_ucet_ma_jednu_identitu(v):
    """Jméno i e-mail vedou k témuž účtu, tak se musí počítat k sobě."""
    p = v["pripady"]["jmeno_i_email"]
    for jak, sada in p.items():
        adresa, ucet = pocty(sada)
        assert ucet == 10, (
            f"{jak}: deset pokusů na jeden účet se započítalo jako {ucet} — "
            "útočník si strop zdvojí tím, že napíše tu druhou podobu"
        )


def test_co_vypadlo_z_okna_se_nepocita(v):
    adresa, ucet = pocty(v["pripady"]["stare_se_nepocita"])
    assert adresa == 1, f"hodinu starý pokus se pořád počítá (adresa={adresa})"
    assert ucet == 1, f"hodinu starý pokus se pořád počítá (účet={ucet})"


def test_neexistujici_ucet_se_pocita_taky(v):
    """Hádání jména, které neexistuje, je pořád hádání."""
    adresa, ucet = pocty(v["pripady"]["neexistujici_ucet"])
    assert ucet == 1, ucet


def test_jina_udalost_se_nepocita(v):
    adresa, ucet = pocty(v["pripady"]["po_prihlaseni"])
    assert (adresa, ucet) == (1, 1), (
        f"úspěšné přihlášení se připsalo ke špatným heslům: {adresa}/{ucet}"
    )
