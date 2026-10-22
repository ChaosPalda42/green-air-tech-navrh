"""Akceptační test C-020 — App\\Api\\Router (co administrace smí po serveru chtít).

Router je jediná cesta, kterou se do webu dostanou změny z prohlížeče. Brána
proto popisuje KAŽDOU odpověď: co se vrátí nepřihlášenému, co bez CSRF, co
uživateli bez práv, co při nesmyslných datech. Ukládání, statistiky i fotky
jsou v testu podvržené (anonymní třídy), takže se měří jen rozhodování.
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

use App\Api\Router;
use App\Api\Uloziste;
use App\Fotky\Ulozny;
use App\Statistiky\Poskytovatel;

$prazdnyStav = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []]];

$uloziste = new class ($prazdnyStav) implements Uloziste {
    public array $zapsano = [];
    public array $smazano = [];
    public function __construct(private array $stav) {}
    public function stav(): array { return $this->stav; }
    public function ulozStav(array $stav, string $kdo): void { $this->zapsano[] = [$kdo, $stav]; $this->stav = $stav; }
    public function uzivatele(): array {
        return [['id' => 1, 'jmeno' => 'pavel', 'email' => 'pavel@g.cz', 'role' => 'spravce', 'aktivni' => 1]];
    }
    public function ulozUzivatele(array $u): array { $this->zapsano[] = ['uzivatel', $u]; return $u + ['id' => 7]; }
    public function smazUzivatele(int $id): void { $this->smazano[] = $id; }
    public function uzivatelPodleJmena(string $j): ?array { return $j === 'pavel' ? ['id' => 1, 'jmeno' => 'pavel'] : null; }
};

$statistiky = new class implements Poskytovatel {
    public array $dotazy = [];
    public function prehled(int $dni): array {
        $this->dotazy[] = $dni;
        return ['dny' => [['datum' => '2026-10-01', 'navstevy' => 10, 'uzivatele' => 8,
            'zobrazeni' => 30, 'poptavky' => 1, 'cas' => 120.0, 'opusteni' => 40.0]],
            'rozpady' => ['zdroje' => [['nazev' => 'Hledání', 'podil' => 100]]]];
    }
};

$fotky = new class implements Ulozny {
    public function uloz(string $tmp, string $jmeno): array {
        if ($jmeno === 'spatna.txt') { throw new \RuntimeException('neni obrazek'); }
        return ['id' => 'f1', 'nazev' => $jmeno, 'typ' => 'image/webp', 'sirka' => 1600,
            'vyska' => 900, 'bajty' => 12345, 'soubor' => 'media/f1.webp'];
    }
};

$spravce = ['jmeno' => 'pavel', 'role' => 'spravce'];
$editor = ['jmeno' => 'martina', 'role' => 'editor'];
$autor = ['jmeno' => 'honza', 'role' => 'autor'];

$pozadavek = static function (array $p) use ($spravce): array {
    return array_merge([
        'metoda' => 'GET', 'cesta' => 'stav', 'telo' => '', 'dotaz' => [],
        'uzivatel' => $spravce, 'csrf_ok' => true, 'soubor' => null,
    ], $p);
};

$stavSTextem = $prazdnyStav;
$stavSTextem['texts']['cs'] = ['nav.sluzby' => 'Co umíme'];
$stavSNovinkou = $prazdnyStav;
$stavSNovinkou['texts']['cs'] = ['novinky.polozky.prvni.titulek' => 'Titulek'];

$sady = [
    'stav_cteni' => ['metoda' => 'GET', 'cesta' => 'stav'],
    'stav_cteni_neprihlaseny' => ['metoda' => 'GET', 'cesta' => 'stav', 'uzivatel' => null],
    'stav_zapis' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem)],
    'stav_zapis_bez_csrf' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'csrf_ok' => false],
    'stav_zapis_neprihlaseny' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'uzivatel' => null],
    'stav_zapis_autorem' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'uzivatel' => $autor],
    'stav_zapis_autorem_novinka' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSNovinkou), 'uzivatel' => $autor],
    'stav_zapis_editorem' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'uzivatel' => $editor],
    'stav_zapis_nesmysl' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => 'tohle neni json'],
    'stav_zapis_pole' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => '[1,2,3]'],
    'stav_zapis_prazdne_telo' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => ''],
    'stav_spatna_metoda' => ['metoda' => 'DELETE', 'cesta' => 'stav'],
    'uzivatele_cteni' => ['metoda' => 'GET', 'cesta' => 'uzivatele'],
    'uzivatele_cteni_editorem' => ['metoda' => 'GET', 'cesta' => 'uzivatele', 'uzivatel' => $editor],
    'uzivatele_zapis' => ['metoda' => 'POST', 'cesta' => 'uzivatele',
        'telo' => json_encode(['jmeno' => 'Nová Kolegyně', 'email' => 'nova@greenairtech.cz', 'role' => 'editor'])],
    'uzivatele_zapis_vadny' => ['metoda' => 'POST', 'cesta' => 'uzivatele',
        'telo' => json_encode(['jmeno' => '', 'email' => 'spatne', 'role' => 'kral'])],
    'uzivatele_zapis_editorem' => ['metoda' => 'POST', 'cesta' => 'uzivatele', 'uzivatel' => $editor,
        'telo' => json_encode(['jmeno' => 'X', 'email' => 'x@g.cz', 'role' => 'editor'])],
    'uzivatele_smazani' => ['metoda' => 'DELETE', 'cesta' => 'uzivatele', 'dotaz' => ['id' => '2']],
    'uzivatele_smazani_sebe' => ['metoda' => 'DELETE', 'cesta' => 'uzivatele', 'dotaz' => ['id' => '1']],
    'uzivatele_smazani_bez_id' => ['metoda' => 'DELETE', 'cesta' => 'uzivatele'],
    'statistiky' => ['metoda' => 'GET', 'cesta' => 'statistiky', 'dotaz' => ['dni' => '30']],
    'statistiky_bez_dni' => ['metoda' => 'GET', 'cesta' => 'statistiky'],
    'statistiky_divne_dni' => ['metoda' => 'GET', 'cesta' => 'statistiky', 'dotaz' => ['dni' => '5000']],
    'statistiky_editorem' => ['metoda' => 'GET', 'cesta' => 'statistiky', 'dotaz' => ['dni' => '30'], 'uzivatel' => $editor],
    'fotka' => ['metoda' => 'POST', 'cesta' => 'fotka', 'soubor' => ['tmp_name' => '/tmp/x', 'name' => 'hala.jpg']],
    'fotka_bez_souboru' => ['metoda' => 'POST', 'cesta' => 'fotka'],
    'fotka_vadna' => ['metoda' => 'POST', 'cesta' => 'fotka', 'soubor' => ['tmp_name' => '/tmp/x', 'name' => 'spatna.txt']],
    'fotka_autorem' => ['metoda' => 'POST', 'cesta' => 'fotka', 'uzivatel' => $autor,
        'soubor' => ['tmp_name' => '/tmp/x', 'name' => 'hala.jpg']],
    'neznamy_cil' => ['metoda' => 'GET', 'cesta' => 'vymyslene'],
    'prazdny_cil' => ['metoda' => 'GET', 'cesta' => ''],
];

$odpovedi = [];
foreach ($sady as $jmeno => $p) {
    $odpovedi[$jmeno] = Router::obsluz($pozadavek($p), $uloziste, $statistiky, $fotky);
}
$bezStatistik = Router::obsluz($pozadavek(['cesta' => 'statistiky', 'dotaz' => ['dni' => '30']]), $uloziste, null, $fotky);
$bezFotek = Router::obsluz($pozadavek(['metoda' => 'POST', 'cesta' => 'fotka',
    'soubor' => ['tmp_name' => '/tmp/x', 'name' => 'hala.jpg']]), $uloziste, $statistiky, null);

echo json_encode([
    'odpovedi' => $odpovedi,
    'bez_statistik' => $bezStatistik,
    'bez_fotek' => $bezFotek,
    'zapsano' => array_map(static fn (array $z): string => (string) $z[0], $uloziste->zapsano),
    'smazano' => $uloziste->smazano,
    'dotazy_statistik' => $statistiky->dotazy,
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""

# Co má router odpovědět. Čísla jsou HTTP stavy, 'chyba' je klíč v těle odpovědi.
CEKANO = {
    "stav_cteni": (200, None),
    "stav_cteni_neprihlaseny": (401, "neprihlaseno"),
    "stav_zapis": (200, None),
    "stav_zapis_bez_csrf": (403, "csrf"),
    "stav_zapis_neprihlaseny": (401, "neprihlaseno"),
    "stav_zapis_autorem": (403, "nesmis"),
    "stav_zapis_autorem_novinka": (200, None),
    "stav_zapis_editorem": (200, None),
    "stav_zapis_nesmysl": (400, "nesmyslny-stav"),
    "stav_zapis_pole": (400, "nesmyslny-stav"),
    "stav_zapis_prazdne_telo": (400, "nesmyslny-stav"),
    "stav_spatna_metoda": (405, "spatna-metoda"),
    "uzivatele_cteni": (200, None),
    "uzivatele_cteni_editorem": (403, "nesmis"),
    "uzivatele_zapis": (200, None),
    "uzivatele_zapis_vadny": (400, "vadna-data"),
    "uzivatele_zapis_editorem": (403, "nesmis"),
    "uzivatele_smazani": (200, None),
    "uzivatele_smazani_sebe": (409, "nelze-sam-sebe"),
    "uzivatele_smazani_bez_id": (400, "chybi-id"),
    "statistiky": (200, None),
    "statistiky_bez_dni": (200, None),
    "statistiky_divne_dni": (400, "spatne-dni"),
    "statistiky_editorem": (403, "nesmis"),
    "fotka": (200, None),
    "fotka_bez_souboru": (400, "chybi-soubor"),
    "fotka_vadna": (400, "fotka-nesla"),
    "fotka_autorem": (403, "nesmis"),
    "neznamy_cil": (404, "neznamy-cil"),
    "prazdny_cil": (404, "neznamy-cil"),
}


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("api")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_kazdy_pozadavek_dostane_cekanou_odpoved(v):
    spatne = []
    for jmeno, (stav, chyba) in CEKANO.items():
        o = v["odpovedi"][jmeno]
        if o["stav"] != stav:
            spatne.append(f"{jmeno}: stav {o['stav']} místo {stav} (tělo {json.dumps(o['telo'], ensure_ascii=False)[:120]})")
            continue
        mam = o["telo"].get("chyba")
        if chyba is None and mam is not None:
            spatne.append(f"{jmeno}: čekán úspěch, přišla chyba {mam!r}")
        elif chyba is not None and mam != chyba:
            spatne.append(f"{jmeno}: chyba {mam!r} místo {chyba!r}")
    assert not spatne, "\n".join(spatne)


def test_odpovedi_nesou_data(v):
    o = v["odpovedi"]
    assert "stav" in o["stav_cteni"]["telo"], "čtení stavu nevrátilo stav"
    assert o["stav_zapis"]["telo"]["stav"]["texts"]["cs"]["nav.sluzby"] == "Co umíme"
    assert len(o["uzivatele_cteni"]["telo"]["uzivatele"]) == 1
    assert o["uzivatele_zapis"]["telo"]["uzivatel"]["id"] == 7
    assert o["uzivatele_zapis_vadny"]["telo"]["pole"], "u vadných dat chybí seznam vadných polí"
    assert o["statistiky"]["telo"]["dny"][0]["navstevy"] == 10
    assert o["statistiky"]["telo"]["rozpady"]["zdroje"][0]["podil"] == 100
    assert o["fotka"]["telo"]["fotka"]["soubor"] == "media/f1.webp"


def test_odmitnuty_pozadavek_nic_neulozi(v):
    # uložit se smělo jen při třech úspěšných zápisech stavu a jednom uživateli
    assert v["zapsano"] == ["pavel", "honza", "martina", "uzivatel"], v["zapsano"]
    assert v["smazano"] == [2], "smazal se někdo jiný, než se mělo"


def test_statistiky_bez_dni_berou_vychozich_30(v):
    # dotaz se smí dostat k poskytovateli jen dvakrát: jednou s 30, jednou bez
    # (odmítnutý rozsah ani editor bez práv se ho nesmí vůbec zeptat)
    assert v["dotazy_statistik"] == [30, 30], v["dotazy_statistik"]


def test_bez_poskytovatele_to_rekne_a_nespadne(v):
    assert v["bez_statistik"]["stav"] == 503
    assert v["bez_statistik"]["telo"]["chyba"] == "statistiky-nejsou"
    assert v["bez_fotek"]["stav"] == 503
    assert v["bez_fotek"]["telo"]["chyba"] == "fotky-nejsou"
