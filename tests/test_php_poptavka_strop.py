"""Brána: strop poptávek platí na adresu, ne na celý web.

Nezávislý test našel, že po dvaceti odeslaných poptávkách dostane
`429 prilis-mnoho` i návštěvník z jiné adresy (měřeno s X-Forwarded-For):
kdokoli tak na deset minut zablokuje formulář všem zákazníkům. Strop sám
smysl má — dvacet zpráv za deset minut není zákazník, ale stroj — jen se
musí počítat tomu, kdo je poslal.

Pravidlo:
- Na JEDNU adresu projde nejvýš STROP_ADRESA zpráv za okno; devátá dostane
  429. Zablokovaná adresa nebrání nikomu jinému.
- Nad tím stojí globální strop (STROP_CELKEM) jako záchranná síť proti
  rozprostřenému robotovi; je mnohem vyšší, aby nebyl vypínačem formuláře.
- Počítají se jen PŘIJATÉ zprávy. Medová past a neplatný formulář kvótu
  neujídají — jinak by robot vypnul formulář nesmysly, které se nikam
  neukládají.
- Odmítnutá poptávka se neukládá do databáze a okno se posouvá: co je
  starší než okno, se nepočítá.

Měří se nad opravdovou databází (SQLite v paměti s týmiž tabulkami) a přes
skutečné App\\Jadro\\Poptavka::obsluz, ne nad podvrhem — jinak by brána
měřila jen můj odhad.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

STROP_ADRESA = 8
STROP_CELKEM = 60
OKNO = 600

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Db\UlozisteDb;
use App\Jadro\Config;
use App\Jadro\Poptavka;
use App\Obsah\ZdrojJson;

/* Hlavičkám se věří jen za proxy (nález K1) — tenhle test adresy rozlišuje
   přes X-Forwarded-For, takže si tu proxy zapne. */
Config::nastav(['posta' => ['zpusob' => 'log'], 'ukazka' => false,
    'proxy' => ['verit' => true]]);
$logPosty = '{KOREN}/web/data/posta.log';
@unlink($logPosty);

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');

function cistaDb(): UlozisteDb
{
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec('CREATE TABLE poptavky (
        id INTEGER PRIMARY KEY AUTOINCREMENT, prijato TEXT NOT NULL,
        typ TEXT NOT NULL DEFAULT "", jmeno TEXT NOT NULL DEFAULT "",
        email TEXT NOT NULL DEFAULT "", telefon TEXT NOT NULL DEFAULT "",
        zprava TEXT, vetev TEXT NOT NULL DEFAULT "", jazyk TEXT NOT NULL DEFAULT "cs",
        odeslano INTEGER NOT NULL DEFAULT 0
    )');
    $pdo->exec('CREATE TABLE udalosti (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kdy TEXT NOT NULL,
        kdo TEXT NOT NULL DEFAULT "", akce TEXT NOT NULL, detail TEXT NOT NULL DEFAULT ""
    )');
    return new UlozisteDb($pdo);
}

/** Jedno odeslání formuláře z dané adresy ('' = bez proxy, bez adresy). */
function posli(UlozisteDb $db, ZdrojJson $zdroj, string $ip, array $navic = []): int
{
    unset($_SERVER['HTTP_CF_CONNECTING_IP'], $_SERVER['HTTP_X_FORWARDED_FOR'],
        $_SERVER['REMOTE_ADDR']);
    if ($ip !== '') {
        $_SERVER['REMOTE_ADDR'] = '10.9.9.9';
        $_SERVER['HTTP_X_FORWARDED_FOR'] = $ip;
    }
    $_POST = [
        'jmeno' => 'Zákazník Zkouška',
        'email' => 'zakaznik@priklad.cz',
        'telefon' => '+420 777 123 456',
        'typ' => 'rekuperace',
        'zprava' => 'Prosím o nabídku na rekuperaci do rodinného domu.',
        'souhlas' => true,
        'jazyk' => 'cs',
    ] + $navic;
    foreach ($navic as $klic => $hodnota) {
        $_POST[$klic] = $hodnota;
    }
    $stav = 0;
    Poptavka::obsluz('POST', $zdroj, $db, static function (int $s, array $t) use (&$stav): void {
        $stav = $s;
    });
    return $stav;
}

function pocetRadku(UlozisteDb $db, string $tabulka): int
{
    $odraz = new ReflectionProperty(UlozisteDb::class, 'pdo');
    $pdo = $odraz->getValue($db);
    return (int) $pdo->query('SELECT COUNT(*) FROM ' . $tabulka)->fetchColumn();
}

/** Posune všechny záznamy o sekundy dozadu — tím se posune okno. */
function posunCas(UlozisteDb $db, int $sekund): void
{
    $odraz = new ReflectionProperty(UlozisteDb::class, 'pdo');
    $pdo = $odraz->getValue($db);
    foreach (['poptavky' => 'prijato', 'udalosti' => 'kdy'] as $tabulka => $sloupec) {
        $radky = $pdo->query('SELECT id, ' . $sloupec . ' FROM ' . $tabulka)->fetchAll();
        foreach ($radky as $r) {
            $novy = date('Y-m-d H:i:s', (int) strtotime((string) $r[$sloupec]) - $sekund);
            $pdo->prepare('UPDATE ' . $tabulka . ' SET ' . $sloupec . ' = ? WHERE id = ?')
                ->execute([$novy, $r['id']]);
        }
    }
}

$ven = [];

/* ---- jedna adresa: strop platí jí, ostatní nechává na pokoji ---- */
$db = cistaDb();
$stavy = [];
for ($i = 0; $i < 11; $i++) {
    $stavy[] = posli($db, $zdroj, '203.0.113.9');
}
$ven['jedna_adresa'] = $stavy;
$ven['jina_adresa_po_zablokovani'] = posli($db, $zdroj, '198.51.100.7');
$ven['ulozeno_po_zablokovani'] = pocetRadku($db, 'poptavky');

/* ---- okno se posouvá ---- */
$db = cistaDb();
for ($i = 0; $i < {STROP_ADRESA}; $i++) {
    posli($db, $zdroj, '203.0.113.9');
}
$ven['devata_hned'] = posli($db, $zdroj, '203.0.113.9');
posunCas($db, {OKNO} + 100);
$ven['devata_po_okne'] = posli($db, $zdroj, '203.0.113.9');

/* ---- globální strop: rozprostřený robot ---- */
$db = cistaDb();
$prijato = 0;
$odmitnuto = 0;
for ($s = 1; $s <= 20; $s++) {
    for ($i = 0; $i < {STROP_ADRESA}; $i++) {
        $stav = posli($db, $zdroj, '203.0.113.' . $s);
        if ($stav === 200) { $prijato++; } else { $odmitnuto++; }
    }
}
$ven['globalni_prijato'] = $prijato;
$ven['globalni_odmitnuto'] = $odmitnuto;
$ven['globalni_cista_adresa'] = posli($db, $zdroj, '198.51.100.7');

/* ---- medová past a neplatný formulář kvótu neujídají ---- */
$db = cistaDb();
$pastStavy = [];
for ($i = 0; $i < 20; $i++) {
    $pastStavy[] = posli($db, $zdroj, '203.0.113.9', ['vebsajt' => 'https://robot.example']);
}
$ven['past_stavy'] = array_values(array_unique($pastStavy));
$ven['past_ulozeno'] = pocetRadku($db, 'poptavky');
$ven['po_pasti'] = posli($db, $zdroj, '203.0.113.9');

$db = cistaDb();
$vadne = [];
for ($i = 0; $i < 20; $i++) {
    $vadne[] = posli($db, $zdroj, '203.0.113.9', ['jmeno' => '', 'email' => 'nic']);
}
$ven['vadne_stavy'] = array_values(array_unique($vadne));
$ven['po_vadnych'] = posli($db, $zdroj, '203.0.113.9');

/* ---- bez adresy (přímý běh bez proxy) formulář funguje dál ---- */
$db = cistaDb();
$bez = [];
for ($i = 0; $i < 3; $i++) {
    $_SERVER = [];
    $bez[] = posli($db, $zdroj, '');
}
$ven['bez_adresy'] = array_values(array_unique($bez));

@unlink($logPosty);
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    program = tmp_path_factory.mktemp("poptavka") / "program.php"
    program.write_text(
        PROGRAM.lstrip()
        .replace("{KOREN}", str(KOREN))
        .replace("{STROP_ADRESA}", str(STROP_ADRESA))
        .replace("{STROP_CELKEM}", str(STROP_CELKEM))
        .replace("{OKNO}", str(OKNO)),
        "utf8",
    )
    hotovo = subprocess.run(
        ["php", str(program)], capture_output=True, text=True, timeout=180,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[-800:])
    return json.loads(hotovo.stdout)


def test_na_jednu_adresu_plati_strop(v):
    stavy = v["jedna_adresa"]
    assert stavy[:STROP_ADRESA] == [200] * STROP_ADRESA, (
        f"prvních {STROP_ADRESA} zpráv z jedné adresy musí projít, dostal jsem {stavy}"
    )
    assert set(stavy[STROP_ADRESA:]) == {429}, (
        f"po {STROP_ADRESA} zprávách má adresa dostat 429, dostal jsem {stavy}"
    )


def test_zablokovana_adresa_nebrani_ostatnim(v):
    assert v["jina_adresa_po_zablokovani"] == 200, (
        "zákazník z jiné adresy dostal 429 jen proto, že někdo jiný poslal "
        f"{STROP_ADRESA + 3} zpráv — tím kdokoli zablokuje formulář všem"
    )


def test_odmitnuta_poptavka_se_neuklada(v):
    assert v["ulozeno_po_zablokovani"] == STROP_ADRESA + 1, (
        "v databázi je jiný počet poptávek, než kolik jich prošlo: "
        f"{v['ulozeno_po_zablokovani']}"
    )


def test_okno_se_posouva(v):
    assert v["devata_hned"] == 429
    assert v["devata_po_okne"] == 200, (
        "po uplynutí okna musí adresa zkusit znovu — jinak je strop trvalý zákaz"
    )


def test_globalni_strop_je_zachranna_sit(v):
    assert v["globalni_prijato"] == STROP_CELKEM, (
        f"globální strop má pustit {STROP_CELKEM} zpráv za okno, pustil "
        f"{v['globalni_prijato']}"
    )
    assert v["globalni_odmitnuto"] > 0, "rozprostřený robot neodešel s ničím odmítnutým"
    assert v["globalni_cista_adresa"] == 429, (
        "globální strop se nevyhodnocuje — rozprostřený robot pošle, kolik chce"
    )


def test_globalni_strop_je_vyssi_nez_na_adresu():
    assert STROP_CELKEM > STROP_ADRESA * 3, (
        "globální strop musí být mnohem vyšší než na adresu, jinak je z něj "
        "zase vypínač formuláře pro všechny"
    )


def test_medova_past_kvotu_neujida(v):
    assert v["past_stavy"] == [200], f"medová past má robotovi poděkovat: {v['past_stavy']}"
    assert v["past_ulozeno"] == 0, "zpráva z medové pasti se uložila do databáze"
    assert v["po_pasti"] == 200, (
        "dvacet zpráv z medové pasti ujedlo kvótu — robot tak vypne formulář "
        "nesmysly, které se nikam neukládají"
    )


def test_neplatny_formular_kvotu_neujida(v):
    assert v["vadne_stavy"] == [422], f"neplatný formulář má 422: {v['vadne_stavy']}"
    assert v["po_vadnych"] == 200, (
        "dvacet nevyplněných formulářů ujedlo kvótu"
    )


def test_bez_adresy_formular_funguje(v):
    assert v["bez_adresy"] == [200], (
        "bez adresy návštěvníka (přímý běh bez proxy) formulář přestal brát "
        f"zprávy: {v['bez_adresy']}"
    )
