"""Akceptační test C-021 — App\\Fotky\\Zpracovani (nahraná fotka na serveru).

Ukázka nahrané fotky zmenšovala v prohlížeči a držela je v localStorage. Na
ostrém webu to musí udělat server: zmenšit na rozumnou hranu, překlopit do
webp a uložit pod jménem, které se nedá uhodnout ani podstrčit. Cizí soubor
(text, prázdný soubor, obrázek s příponou .jpg) se nesmí dostat na disk.

Nezávislý test našel, že 7000×7000 PNG (160 kB na disku!) skončí jako
`500 chyba-serveru`: GD drží obrázek nekomprimovaný, 4 bajty na pixel, a PHP
na memory_limit umře fatální chybou. Tu nejde odchytit — zákazník dostane
prázdnou odpověď a správce nemá v administraci co říct. Rozhodnout se proto
musí z HLAVIČKY souboru, dřív než se obrázek rozbalí do paměti, a odmítnutí
je obyčejná výjimka (App\\Fotky\\MocVelka), ze které Router udělá 413.

Měří se dvěma běhy s různým memory_limit: pravidlo je „vejde se to do paměti,
kterou server dal", ne magický počet pixelů. Obrázky s ohromnou hlavičkou jsou
podvrh o pár stech bajtech — pravý takový obrázek by se do testu nevešel a
nemusí: právě o to jde.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
MAX_HRANA = 1600

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

$kam = $argv[1];
$tmp = $argv[2];

/* Vstupy: dva skutečné obrázky, text s obrázkovou příponou a prázdný soubor. */
$velky = imagecreatetruecolor(2400, 1200);
imagefill($velky, 0, 0, imagecolorallocate($velky, 40, 120, 80));
imagejpeg($velky, $tmp . '/velky.jpg', 90);

$maly = imagecreatetruecolor(800, 600);
imagefill($maly, 0, 0, imagecolorallocate($maly, 200, 40, 40));
imagepng($maly, $tmp . '/maly.png');

$vysoky = imagecreatetruecolor(500, 2000);
imagefill($vysoky, 0, 0, imagecolorallocate($vysoky, 10, 10, 200));
imagepng($vysoky, $tmp . '/vysoky.png');

/* Obrázek s paletou (ne truecolor) — takový vyleze z úsporného PNG i ze
   skenu. imagewebp() ho bez převodu „uloží" jako nula bajtů a vrátí true. */
$seda = imagecreate(900, 700);
imagecolorallocate($seda, 255, 255, 255);
imagefill($seda, 0, 0, imagecolorallocate($seda, 90, 90, 90));
imagepng($seda, $tmp . '/seda.png');

file_put_contents($tmp . '/podvrh.jpg', "tohle je text, ne obrazek\n");
file_put_contents($tmp . '/prazdny.jpg', '');

$zpracovani = new App\Fotky\Zpracovani($kam, 'media');

$zkus = static function (callable $co): array {
    try {
        return ['ok' => true, 'v' => $co()];
    } catch (\Throwable $e) {
        return ['ok' => false, 'trida' => get_class($e)];
    }
};

$vysledek = [
    'velky' => $zkus(static fn () => $zpracovani->uloz($tmp . '/velky.jpg', 'Hala Říčany.JPG')),
    'maly' => $zkus(static fn () => $zpracovani->uloz($tmp . '/maly.png', 'maly.png')),
    'vysoky' => $zkus(static fn () => $zpracovani->uloz($tmp . '/vysoky.png', 'vysoky.png')),
    'seda' => $zkus(static fn () => $zpracovani->uloz($tmp . '/seda.png', 'seda.png')),
    'podvrh' => $zkus(static fn () => $zpracovani->uloz($tmp . '/podvrh.jpg', 'podvrh.jpg')),
    'prazdny' => $zkus(static fn () => $zpracovani->uloz($tmp . '/prazdny.jpg', 'prazdny.jpg')),
    'chybi' => $zkus(static fn () => $zpracovani->uloz($tmp . '/neexistuje.jpg', 'x.jpg')),
];
/* Tentýž obrázek podruhé: nesmí vzniknout druhý soubor s jiným jménem. */
$vysledek['velky_znovu'] = $zkus(static fn () => $zpracovani->uloz($tmp . '/velky.jpg', 'jinak.jpg'));

/* PNG, ve kterém je jen hlavička s rozměry a za ní nesmysl. getimagesize()
   čte jen hlavičku, takže rozměry vidí — a právě podle nich se musí rozhodnout
   DŘÍV, než se obrázek rozbalí. */
$hlavickaPng = static function (int $sirka, int $vyska) use ($tmp): string {
    $ihdr = pack('N2C5', $sirka, $vyska, 8, 2, 0, 0, 0);
    $idat = 'IDAT' . str_repeat('x', 8);
    $soubor = "\x89PNG\r\n\x1a\n"
        . pack('N', strlen($ihdr)) . 'IHDR' . $ihdr . pack('N', crc32('IHDR' . $ihdr))
        . pack('N', 8) . $idat . pack('N', crc32($idat));
    $cesta = $tmp . '/hlavicka-' . $sirka . 'x' . $vyska . '.png';
    file_put_contents($cesta, $soubor);
    return $cesta;
};

$vysledek['obri'] = $zkus(static fn () => $zpracovani->uloz($hlavickaPng(20000, 20000), 'obri.png'));
$vysledek['bezne'] = $zkus(static fn () => $zpracovani->uloz($hlavickaPng(6000, 4000), 'bezne.png'));
$vysledek['male'] = $zkus(static fn () => $zpracovani->uloz($hlavickaPng(1200, 800), 'male.png'));

$soubory = [];
foreach (glob($kam . '/*') ?: [] as $cesta) {
    $rozmer = @getimagesize($cesta);
    $soubory[basename($cesta)] = [
        'bajtu' => filesize($cesta),
        'sirka' => $rozmer[0] ?? null,
        'vyska' => $rozmer[1] ?? null,
        'typ' => $rozmer['mime'] ?? null,
    ];
}
echo json_encode([
    'vysledek' => $vysledek,
    'soubory' => $soubory,
    'limit' => ini_get('memory_limit'),
    'vrchol' => memory_get_peak_usage(true),
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


def beh(tmp_path_factory, limit: str) -> dict:
    dir = tmp_path_factory.mktemp("fotky")
    kam = dir / "media"
    kam.mkdir()
    tmp = dir / "nahrane"
    tmp.mkdir()
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(
        # display_errors do stderr: varování z GD by jinak v CLI spadlo do
        # stdout a rozbilo JSON, který brána čte.
        ["php", "-d", "memory_limit=" + limit, "-d", "display_errors=stderr",
         str(program), str(kam), str(tmp)],
        capture_output=True, text=True, timeout=120,
    )
    if hotovo.returncode != 0:
        raise AssertionError(
            f"PHP spadlo při memory_limit={limit} (fatální chyba z paměti se "
            "nedá odchytit, zákazník dostane 500): "
            + (hotovo.stderr or hotovo.stdout).strip()[-600:]
        )
    return json.loads(hotovo.stdout)


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    """Běh s pamětí, do které se vejde i velká fotka z mobilu."""
    return beh(tmp_path_factory, "1024M")


@pytest.fixture(scope="module")
def malo_pameti(tmp_path_factory):
    """Běh na serveru s úspornou pamětí — 24 Mpx se tam rozbalit nedá."""
    return beh(tmp_path_factory, "128M")


def test_velka_fotka_se_zmensi_a_prevede_na_webp(v):
    o = v["vysledek"]["velky"]
    assert o["ok"], f"zpracování spadlo: {o}"
    f = o["v"]
    assert f["sirka"] == MAX_HRANA, f"delší hrana se nezmenšila na {MAX_HRANA}: {f['sirka']}"
    assert f["vyska"] == MAX_HRANA // 2, f"poměr stran se nezachoval: {f}"
    assert f["typ"] == "image/webp", f"čekán webp, přišlo {f['typ']}"
    assert f["soubor"].startswith("media/") and f["soubor"].endswith(".webp"), f["soubor"]
    assert f["nazev"] == "Hala Říčany.JPG", "původní jméno se má zachovat pro člověka"
    assert f["bajty"] > 0
    disk = v["soubory"][f["soubor"].split("/")[-1]]
    assert disk["bajtu"] == f["bajty"], "bajty v popisu nesouhlasí se souborem na disku"
    assert disk["sirka"] == MAX_HRANA


def test_vysoky_obrazek_se_meri_podle_delsi_hrany(v):
    f = v["vysledek"]["vysoky"]["v"]
    assert f["vyska"] == MAX_HRANA, f
    assert f["sirka"] == 400, f


def test_mala_fotka_se_nezvetsuje(v):
    f = v["vysledek"]["maly"]["v"]
    assert (f["sirka"], f["vyska"]) == (800, 600), f


def test_jmeno_souboru_vychazi_z_obsahu(v):
    jmeno = v["vysledek"]["velky"]["v"]["soubor"].split("/")[-1]
    assert len(jmeno.split(".")[0]) >= 16, f"jméno se dá uhodnout: {jmeno}"
    assert all(c in "0123456789abcdef" for c in jmeno.split(".")[0]), jmeno
    assert v["vysledek"]["velky_znovu"]["v"]["soubor"].split("/")[-1] == jmeno, \
        "tentýž obrázek podruhé dal jiné jméno"
    assert len(v["soubory"]) == 4, f"na disku je {len(v['soubory'])} souborů místo čtyř: {list(v['soubory'])}"


def test_obrazek_s_paletou_skonci_na_disku_neprazdny(v):
    o = v["vysledek"]["seda"]
    assert o["ok"], f"obrázek s paletou neprošel: {o}"
    f = o["v"]
    assert f["bajty"] > 0, "fotka se uložila jako prázdný soubor"
    disk = v["soubory"][f["soubor"].split("/")[-1]]
    assert disk["bajtu"] == f["bajty"], "bajty v popisu nesouhlasí se souborem na disku"
    assert disk["typ"] == "image/webp", f"čekán webp, na disku je {disk['typ']}"
    assert (disk["sirka"], disk["vyska"]) == (900, 700), disk


def test_cizi_soubor_se_odmitne_a_nic_neulozi(v):
    for jmeno in ("podvrh", "prazdny", "chybi"):
        o = v["vysledek"][jmeno]
        assert not o["ok"], f"{jmeno}: soubor prošel, přitom to není obrázek"
        assert o["trida"] in ("RuntimeException", "InvalidArgumentException"), o
    pripony = {s.split(".")[-1] for s in v["soubory"]}
    assert pripony == {"webp"}, f"na disku skončilo něco jiného než webp: {pripony}"


def test_obri_rozmery_se_odmitnou_misto_fatalni_chyby(v):
    """400 Mpx je 1,6 GB v paměti. To se nevejde nikam a musí to být
    odmítnutí, ne smrt procesu."""
    o = v["vysledek"]["obri"]
    assert not o["ok"], "obrázek 20000×20000 prošel — tolik paměti server nemá"
    assert o["trida"] == "App\\Fotky\\MocVelka", (
        "odmítnutí se nedá odlišit od „tohle není obrázek\": Router pak pošle "
        f"400 fotka-nesla a správce netuší, že má fotku zmenšit. Přišlo {o}"
    )


def test_bezna_fotka_z_mobilu_v_dostatku_pameti_projde(v):
    """6000×4000 je dnes běžná fotka z telefonu. Při 1 GB paměti ji nesmí
    odmítnout strop — tam ji zastaví až rozbitá data v podvrhu."""
    o = v["vysledek"]["bezne"]
    assert o["trida"] != "App\\Fotky\\MocVelka", (
        "běžná fotka z mobilu odmítnuta jako příliš velká, přitom se do paměti "
        "vejde — strop se nesmí počítat z magického počtu pixelů"
    )


def test_pri_male_pameti_se_vetsi_fotka_odmitne(malo_pameti):
    o = malo_pameti["vysledek"]["bezne"]
    assert not o["ok"], "6000×4000 při 128M paměti prošlo — to skončí fatální chybou"
    assert o["trida"] == "App\\Fotky\\MocVelka", (
        f"čekáno odmítnutí kvůli paměti, přišlo {o}"
    )
    male = malo_pameti["vysledek"]["male"]
    assert male["trida"] != "App\\Fotky\\MocVelka", (
        "1200×800 se vejde i do 128M — tohle už není strop, ale vypnuté "
        "nahrávání fotek"
    )


def test_odmitnuta_fotka_se_vubec_nerozbaluje(malo_pameti):
    """Kdyby se rozměry jen „zkusily", vrchol paměti by vyletěl — a to je
    přesně ta fatální chyba, kterou brána hlídá."""
    assert malo_pameti["vrchol"] < 100 * 1024 * 1024, (
        f"vrchol paměti {malo_pameti['vrchol']} B při limitu 128M: obrázek se "
        "začal rozbalovat, než se o něm rozhodlo"
    )
