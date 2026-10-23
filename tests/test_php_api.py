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
        if ($jmeno === 'obri.png') { throw new \App\Fotky\MocVelka('nevejde se do pameti'); }
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

// Pozor: všechny požadavky jdou přes JEDNO úložiště a v řadě za sebou, takže
// úspěšný zápis zůstane dalšímu požadavku pod rukama. Každý další zápis proto
// musí být SKUTEČNÁ změna proti tomu, co tam zbylo — jinak by se z otázky
// „smí autor měnit texty?" stalo „co se stane, když autor nepošle změnu?"
// a brána by měřila něco jiného, než co tvrdí.
$stavAutorem = $prazdnyStav;
$stavAutorem['texts']['cs'] = ['nav.sluzby' => 'Co umíme (autor)'];
$stavSNovinkou = $prazdnyStav;
$stavSNovinkou['texts']['cs'] = [
    'nav.sluzby' => 'Co umíme',
    'novinky.polozky.prvni.titulek' => 'Titulek',
];
$stavEditorem = $prazdnyStav;
$stavEditorem['texts']['cs'] = [
    'nav.sluzby' => 'Co umíme (editor)',
    'novinky.polozky.prvni.titulek' => 'Titulek',
];

$sady = [
    'stav_cteni' => ['metoda' => 'GET', 'cesta' => 'stav'],
    'stav_cteni_neprihlaseny' => ['metoda' => 'GET', 'cesta' => 'stav', 'uzivatel' => null],
    'stav_zapis' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem)],
    'stav_zapis_bez_csrf' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'csrf_ok' => false],
    'stav_zapis_neprihlaseny' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSTextem), 'uzivatel' => null],
    'stav_zapis_autorem' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavAutorem), 'uzivatel' => $autor],
    'stav_zapis_autorem_novinka' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavSNovinkou), 'uzivatel' => $autor],
    'stav_zapis_editorem' => ['metoda' => 'PUT', 'cesta' => 'stav', 'telo' => json_encode($stavEditorem), 'uzivatel' => $editor],
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
    /* Okraje nahrávání. Když soubor přeteče upload_max_filesize, PHP ho
       zahodí a nechá jen číslo chyby — bez něj administrace tvrdila „vyberte
       soubor" člověku, který soubor vybral. */
    'fotka_moc_velka' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor' => ['tmp_name' => '/tmp/x', 'name' => 'obri.png']],
    'fotka_pres_upload_limit' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor_chyba' => UPLOAD_ERR_INI_SIZE],
    'fotka_pres_limit_formulare' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor_chyba' => UPLOAD_ERR_FORM_SIZE],
    'fotka_pres_post_limit' => ['metoda' => 'POST', 'cesta' => 'fotka', 'telo_velke' => true],
    'fotka_preruseno' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor_chyba' => UPLOAD_ERR_PARTIAL],
    'fotka_nevybrana' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor_chyba' => UPLOAD_ERR_NO_FILE],
    'fotka_server_nema_tmp' => ['metoda' => 'POST', 'cesta' => 'fotka',
        'soubor_chyba' => UPLOAD_ERR_NO_TMP_DIR],
    /* Velký soubor nesmí otevřít zadní vrátka: práva se ptají dřív. */
    'fotka_moc_velka_autorem' => ['metoda' => 'POST', 'cesta' => 'fotka', 'uzivatel' => $autor,
        'soubor_chyba' => UPLOAD_ERR_INI_SIZE],
    'fotka_moc_velka_bez_csrf' => ['metoda' => 'POST', 'cesta' => 'fotka', 'csrf_ok' => false,
        'soubor_chyba' => UPLOAD_ERR_INI_SIZE],
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
    "fotka_moc_velka": (413, "fotka-moc-velka"),
    "fotka_pres_upload_limit": (413, "soubor-moc-velky"),
    "fotka_pres_limit_formulare": (413, "soubor-moc-velky"),
    "fotka_pres_post_limit": (413, "soubor-moc-velky"),
    "fotka_preruseno": (400, "nahrani-preruseno"),
    "fotka_nevybrana": (400, "chybi-soubor"),
    "fotka_server_nema_tmp": (503, "fotky-nejsou"),
    "fotka_moc_velka_autorem": (403, "nesmis"),
    "fotka_moc_velka_bez_csrf": (403, "csrf"),
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

# ======================================================================
# Hesla a pozvánky — druhá polovina C-020.
#
# Akceptační test C-020 (druhá polovina) — hesla a pozvánky přes API.
#
# Nezávislý test našel, že nově založený uživatel se do administrace nikdy
# nedostane a nikdo si nezmění heslo: `POST /api/uzivatele` uložilo
# `heslo_hash NULL, pozvanka_token NULL`, přihlášení tím účtem skončilo
# chybou a Router ani administrace žádnou cestu k heslu nenabízely. Správce
# si tak nezmění ani vlastní heslo z instalace, ačkoli administrace slibuje
# „zadejte e-mail a heslo, které jste dostali v pozvánce“ a „zapomenuté
# heslo vám obnoví správce webu“.
#
# Pravidla, která tahle brána drží:
#
# 1. Zakládání uživatele VYROBÍ pozvánku (token + platnost), uloží ji a vrátí
#    tomu, kdo zakládá — on ji předá kolegovi. Heslo se přes API neposílá ani
#    nevrací NIKDY; správce cizí heslo nenastavuje.
# 2. `POST pozvanka` vystaví pozvánku znovu (ztratila se, propadla, kolega
#    heslo zapomněl) a zároveň staré heslo zruší — jinak by platily dvě cesty
#    do účtu. Sám sobě ji správce vystavit nemůže: zrušil by si heslo a do
#    administrace by ho musel pustit někdo jiný.
# 3. `POST heslo` mění VLASTNÍ heslo: bez správného starého to nejde, nové
#    musí projít kontrolou síly a cizí účet se tudy měnit nedá.
# 4. Pořadí kontrol je jako u ostatních cílů: CSRF, přihlášení, práva,
#    metoda, data. Odmítnutý požadavek na úložiště nesáhne.
#
# Na vlastní heslo se právo „uzivatele“ nežádá — to má jen správce a heslo si
# musí umět změnit každý.
# ======================================================================


PROGRAM_HESLA = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Router;
use App\Api\Uloziste;
use App\Auth\Uzivatele;

/* Podvrh úložiště: pamatuje si, na co se Router ptal a co zapsal. Hesla jsou
   skutečné hashe, aby se dalo měřit i ověření starého hesla. */
$uloziste = new class implements Uloziste {
    public array $sahnuto = [];
    public array $zapisy = [];

    public function stav(): array { $this->sahnuto[] = 'stav'; return []; }
    public function ulozStav(array $stav, string $kdo): void { $this->sahnuto[] = 'ulozStav'; }

    public function uzivatele(): array
    {
        $this->sahnuto[] = 'uzivatele';
        return [
            ['id' => 1, 'jmeno' => 'pavel', 'email' => 'pavel@g.cz', 'role' => 'spravce', 'aktivni' => 1],
            ['id' => 2, 'jmeno' => 'eva', 'email' => 'eva@g.cz', 'role' => 'editor', 'aktivni' => 1],
        ];
    }

    public function ulozUzivatele(array $u): array
    {
        $this->sahnuto[] = 'ulozUzivatele';
        $this->zapisy[] = $u;
        return $u + ['id' => (int) ($u['id'] ?? 7)];
    }

    public function smazUzivatele(int $id): void { $this->sahnuto[] = 'smazUzivatele'; }

    public function uzivatelPodleJmena(string $j): ?array
    {
        $this->sahnuto[] = 'uzivatelPodleJmena';
        if ($j === 'pavel') {
            return ['id' => 1, 'jmeno' => 'pavel', 'email' => 'pavel@g.cz', 'role' => 'spravce',
                'aktivni' => 1, 'heslo_hash' => Uzivatele::hash('StareHeslo123')];
        }
        if ($j === 'tonda') {
            return ['id' => 3, 'jmeno' => 'tonda', 'email' => 'tonda@g.cz', 'role' => 'autor',
                'aktivni' => 1, 'heslo_hash' => Uzivatele::hash('StareHeslo123')];
        }
        return null;
    }
};

$spravce = ['id' => 1, 'jmeno' => 'pavel', 'role' => 'spravce'];
$autor = ['id' => 3, 'jmeno' => 'tonda', 'role' => 'autor'];

function volej(array $zmeny, Uloziste $u): array
{
    return Router::obsluz($zmeny + [
        'metoda' => 'POST', 'cesta' => 'heslo', 'dotaz' => [], 'soubor' => null,
        'csrf_ok' => true, 'uzivatel' => null, 'telo' => '',
    ], $u, null, null);
}

$ven = [];

/* ---- zakládání uživatele vyrobí pozvánku ---- */
$ven['zalozeni'] = volej([
    'cesta' => 'uzivatele', 'uzivatel' => $spravce,
    'telo' => json_encode(['jmeno' => 'Nová Kolegyně', 'email' => 'nova@g.cz', 'role' => 'editor']),
], $uloziste);
$ven['co_se_ulozilo'] = $uloziste->zapisy[0] ?? [];

/* ---- vlastní heslo ---- */
$uloziste->zapisy = [];
$ven['heslo_spravne'] = volej([
    'uzivatel' => $spravce,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'NoveHeslo12345']),
], $uloziste);
$zapis = $uloziste->zapisy[0] ?? [];
$ven['zmena_hesla_zapis'] = [
    'id' => (int) ($zapis['id'] ?? 0),
    'je_to_hash_noveho' => is_string($zapis['heslo_hash'] ?? null)
        && password_verify('NoveHeslo12345', (string) $zapis['heslo_hash']),
    'v_zapisu_neni_cisty_text' => !str_contains(json_encode($zapis), 'NoveHeslo12345'),
    'klice' => array_keys($zapis),
];

$ven['heslo_spatne_stare'] = volej([
    'uzivatel' => $spravce,
    'telo' => json_encode(['stare' => 'uplne-jine', 'nove' => 'NoveHeslo12345']),
], $uloziste);

$ven['heslo_kratke_nove'] = volej([
    'uzivatel' => $spravce,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'Kratke1']),
], $uloziste);

$ven['heslo_prazdne_nove'] = volej([
    'uzivatel' => $spravce,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => '   ']),
], $uloziste);

$ven['heslo_bez_prihlaseni'] = volej(['uzivatel' => null,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'NoveHeslo12345'])], $uloziste);
$ven['heslo_bez_csrf'] = volej(['uzivatel' => $spravce, 'csrf_ok' => false,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'NoveHeslo12345'])], $uloziste);
$ven['heslo_get'] = volej(['uzivatel' => $spravce, 'metoda' => 'GET'], $uloziste);

/* Autor nemá právo na uživatele, ale vlastní heslo si změnit smí. */
$uloziste->zapisy = [];
$ven['heslo_autor'] = volej(['uzivatel' => $autor,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'NoveHeslo12345'])], $uloziste);
$ven['autor_menil_sve_id'] = (int) ($uloziste->zapisy[0]['id'] ?? 0);

/* Cizí účet tudy nikdo nepřepíše, i kdyby ho v těle vyjmenoval. */
$uloziste->zapisy = [];
$ven['heslo_ciziho'] = volej([
    'uzivatel' => $spravce,
    'telo' => json_encode(['stare' => 'StareHeslo123', 'nove' => 'NoveHeslo12345',
        'id' => 2, 'jmeno' => 'eva', 'email' => 'eva@g.cz']),
], $uloziste);
$ven['komu_se_zmenilo'] = array_map(fn ($z) => (int) ($z['id'] ?? 0), $uloziste->zapisy);

/* ---- pozvánka znovu ---- */
$uloziste->zapisy = [];
$ven['pozvanka_znovu'] = volej([
    'cesta' => 'pozvanka', 'uzivatel' => $spravce, 'telo' => json_encode(['id' => 2]),
], $uloziste);
$ven['pozvanka_zapis'] = $uloziste->zapisy[0] ?? [];

$ven['pozvanka_bez_id'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $spravce,
    'telo' => json_encode([])], $uloziste);
$ven['pozvanka_nesmysl_id'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $spravce,
    'telo' => json_encode(['id' => 'abc'])], $uloziste);
$ven['pozvanka_neznamy'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $spravce,
    'telo' => json_encode(['id' => 99])], $uloziste);
$ven['pozvanka_sam_sobe'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $spravce,
    'telo' => json_encode(['id' => 1])], $uloziste);
$ven['pozvanka_bez_prava'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $autor,
    'telo' => json_encode(['id' => 2])], $uloziste);
$ven['pozvanka_bez_prihlaseni'] = volej(['cesta' => 'pozvanka', 'uzivatel' => null,
    'telo' => json_encode(['id' => 2])], $uloziste);
$ven['pozvanka_bez_csrf'] = volej(['cesta' => 'pozvanka', 'uzivatel' => $spravce,
    'csrf_ok' => false, 'telo' => json_encode(['id' => 2])], $uloziste);
$ven['pozvanka_get'] = volej(['cesta' => 'pozvanka', 'metoda' => 'GET', 'uzivatel' => $spravce], $uloziste);

/* Odmítnutý požadavek nesmí na úložiště sáhnout. */
$uloziste->sahnuto = [];
volej(['cesta' => 'pozvanka', 'uzivatel' => $autor, 'telo' => json_encode(['id' => 2])], $uloziste);
volej(['cesta' => 'heslo', 'uzivatel' => null, 'telo' => json_encode(['stare' => 'x', 'nove' => 'y'])], $uloziste);
volej(['cesta' => 'heslo', 'uzivatel' => $spravce, 'csrf_ok' => false, 'telo' => '{}'], $uloziste);
volej(['cesta' => 'heslo', 'uzivatel' => $spravce, 'metoda' => 'DELETE'], $uloziste);
$ven['sahnuto_po_odmitnutych'] = $uloziste->sahnuto;

echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def h(tmp_path_factory):
    program = tmp_path_factory.mktemp("hesla") / "program.php"
    program.write_text(PROGRAM_HESLA.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:900])
    return json.loads(hotovo.stdout)


# ---------------------------------------------------------- zakládání

def test_zalozeni_vyrobi_pozvanku(h):
    o = h["zalozeni"]
    assert o["stav"] == 200, o
    pozvanka = o["telo"].get("pozvanka")
    assert isinstance(pozvanka, dict), (
        "odpověď neobsahuje pozvánku, takže správce nemá co předat kolegovi: "
        + json.dumps(o["telo"], ensure_ascii=False)[:300]
    )
    assert len(str(pozvanka.get("token", ""))) == 64, pozvanka
    assert str(pozvanka.get("do", "")) != "", pozvanka


def test_pozvanka_se_i_ulozila(h):
    """Token v odpovědi, který není v databázi, by se nedal uplatnit."""
    u = h["co_se_ulozilo"]
    assert u.get("pozvanka_token") == h["zalozeni"]["telo"]["pozvanka"]["token"], u
    assert u.get("pozvanka_do") == h["zalozeni"]["telo"]["pozvanka"]["do"], u
    assert u.get("aktivni") == 1, u


def test_zalozeni_nikdy_nenastavuje_heslo(h):
    u = h["co_se_ulozilo"]
    assert not any(k in u and u[k] for k in ("heslo", "heslo_hash")), (
        "zakládání uživatele nastavuje heslo — správce cizí heslo nastavovat nemá: "
        + json.dumps(u, ensure_ascii=False)
    )


# ------------------------------------------------------------- heslo

def test_vlastni_heslo_se_zmeni(h):
    o = h["heslo_spravne"]
    assert o["stav"] == 200, o
    assert o["telo"].get("ok") is True, o
    z = h["zmena_hesla_zapis"]
    assert z["id"] == 1, f"změna se zapsala na cizí id: {z}"
    assert z["je_to_hash_noveho"], f"neuložil se hash nového hesla: {z}"
    assert z["v_zapisu_neni_cisty_text"], "heslo se ukládá v čitelné podobě"


def test_zmena_hesla_zrusi_starou_pozvanku(h):
    """Kdo zná heslo, nemá potřebovat pozvánku — a dvě cesty do účtu
    znamenají, že stará pozvánka platí dál, i když se heslo změnilo."""
    z = h["zmena_hesla_zapis"]
    assert "pozvanka_token" in z["klice"], (
        "změna hesla nechává pozvánku v platnosti: " + json.dumps(z["klice"])
    )


def test_bez_spravneho_stareho_hesla_to_nejde(h):
    o = h["heslo_spatne_stare"]
    assert o["stav"] == 403, f"špatné staré heslo dalo {o['stav']} místo 403: {o}"
    assert o["telo"]["chyba"] == "spatne-stare-heslo", o["telo"]


def test_slabe_nove_heslo_se_odmitne(h):
    for klic, duvod in (("heslo_kratke_nove", "kratke"), ("heslo_prazdne_nove", "prazdne")):
        o = h[klic]
        assert o["stav"] == 400, f"{klic}: {o}"
        assert o["telo"]["chyba"] == "vadne-heslo", o["telo"]
        assert o["telo"].get("duvod") == duvod, o["telo"]


def test_heslo_jen_prihlasenemu_a_s_csrf(h):
    assert h["heslo_bez_prihlaseni"]["stav"] == 401, h["heslo_bez_prihlaseni"]
    assert h["heslo_bez_csrf"]["stav"] == 403, h["heslo_bez_csrf"]
    assert h["heslo_bez_csrf"]["telo"]["chyba"] == "csrf", h["heslo_bez_csrf"]
    assert h["heslo_get"]["stav"] == 405, h["heslo_get"]


def test_na_vlastni_heslo_nepotrebuje_pravo_na_uzivatele(h):
    """Autor nesmí do uživatelů, ale vlastní heslo si změnit musí."""
    o = h["heslo_autor"]
    assert o["stav"] == 200, (
        "autor si nemůže změnit vlastní heslo — pak ho nezmění nikdo kromě správce: "
        + json.dumps(o, ensure_ascii=False)
    )
    assert h["autor_menil_sve_id"] == 3, h["autor_menil_sve_id"]


def test_cizi_heslo_se_tudy_zmenit_neda(h):
    assert h["heslo_ciziho"]["stav"] == 200, h["heslo_ciziho"]
    assert h["komu_se_zmenilo"] == [1], (
        "tělo s cizím id/jménem přesměrovalo zápis na jiný účet: "
        + json.dumps(h["komu_se_zmenilo"])
    )


# ---------------------------------------------------------- pozvánka

def test_pozvanku_lze_vystavit_znovu(h):
    o = h["pozvanka_znovu"]
    assert o["stav"] == 200, o
    token = o["telo"]["pozvanka"]["token"]
    assert len(token) == 64, o["telo"]
    z = h["pozvanka_zapis"]
    assert (int) (z.get("id", 0)) == 2, z
    assert z.get("pozvanka_token") == token, z
    assert z.get("pozvanka_do"), z


def test_nova_pozvanka_zrusi_stare_heslo(h):
    """Pozvánka se vystavuje i tomu, kdo heslo zapomněl. Kdyby staré heslo
    zůstalo, znal by ho pořád ten, kdo ho případně odkoukal."""
    z = h["pozvanka_zapis"]
    assert "heslo_hash" in z and z["heslo_hash"] is None, (
        "nová pozvánka nechala staré heslo v platnosti: " + json.dumps(z, ensure_ascii=False)
    )


def test_pozvanka_sam_sobe_se_odmitne(h):
    o = h["pozvanka_sam_sobe"]
    assert o["stav"] == 409, (
        f"správce si vystavil pozvánku sám sobě ({o['stav']}) — zrušil by si tím "
        "heslo a do administrace by ho musel pustit někdo jiný"
    )
    assert o["telo"]["chyba"] == "nelze-sam-sebe", o["telo"]


def test_pozvanka_hlasi_chyby(h):
    assert h["pozvanka_bez_id"]["stav"] == 400, h["pozvanka_bez_id"]
    assert h["pozvanka_bez_id"]["telo"]["chyba"] == "chybi-id", h["pozvanka_bez_id"]
    assert h["pozvanka_nesmysl_id"]["stav"] == 400, h["pozvanka_nesmysl_id"]
    assert h["pozvanka_neznamy"]["stav"] == 404, h["pozvanka_neznamy"]
    assert h["pozvanka_neznamy"]["telo"]["chyba"] == "neznamy-uzivatel", h["pozvanka_neznamy"]
    assert h["pozvanka_bez_prava"]["stav"] == 403, h["pozvanka_bez_prava"]
    assert h["pozvanka_bez_prava"]["telo"]["chyba"] == "nesmis", h["pozvanka_bez_prava"]
    assert h["pozvanka_bez_prihlaseni"]["stav"] == 401, h["pozvanka_bez_prihlaseni"]
    assert h["pozvanka_bez_csrf"]["stav"] == 403, h["pozvanka_bez_csrf"]
    assert h["pozvanka_bez_csrf"]["telo"]["chyba"] == "csrf", h["pozvanka_bez_csrf"]
    assert h["pozvanka_get"]["stav"] == 405, h["pozvanka_get"]


def test_odmitnuty_pozadavek_na_uloziste_nesahne(h):
    assert h["sahnuto_po_odmitnutych"] == [], (
        "odmítnutý požadavek se ptal úložiště: " + json.dumps(h["sahnuto_po_odmitnutych"])
    )


def test_velky_soubor_nemluvi_o_chybejicim_souboru(v):
    """Tester dostal na 12MB souboru `chybi-soubor`. Správce soubor vybral a
    hláška ho posílá vybrat ho znovu — a znovu."""
    for jmeno in ("fotka_pres_upload_limit", "fotka_pres_post_limit",
                  "fotka_pres_limit_formulare"):
        o = v["odpovedi"][jmeno]
        assert o["telo"]["chyba"] != "chybi-soubor", (
            f"{jmeno}: odpověď tvrdí, že soubor chybí, přitom byl jen moc velký"
        )
        assert o["stav"] == 413, f"{jmeno}: čekán 413, přišlo {o['stav']}"

