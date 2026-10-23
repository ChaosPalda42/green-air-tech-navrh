"""Akceptační test C-021 — App\\Fotky\\Zpracovani (nahraná fotka na serveru).

Ukázka nahrané fotky zmenšovala v prohlížeči a držela je v localStorage. Na
ostrém webu to musí udělat server: zmenšit na rozumnou hranu, překlopit do
webp a uložit pod jménem, které se nedá uhodnout ani podstrčit. Cizí soubor
(text, prázdný soubor, obrázek s příponou .jpg) se nesmí dostat na disk.
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
echo json_encode(['vysledek' => $vysledek, 'soubory' => $soubory],
    JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("fotky")
    kam = dir / "media"
    kam.mkdir()
    tmp = dir / "nahrane"
    tmp.mkdir()
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(kam), str(tmp)],
        capture_output=True, text=True, timeout=120,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


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
