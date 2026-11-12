"""Brána: každá adresa obrázku ve vykreslené stránce nese verzi svého obsahu.

Nález (12. 11. 2026). Klient si stěžoval na ořez dvou portrétů v kontaktech.
Opravené fotky by ale nikdo neuviděl: `web/public/.htaccess` posílá obrázky
s `Cache-Control: public, max-age=31536000, immutable` a zdůvodňuje to
komentářem „jména aktiv nesou hash obsahu, proto natrvalo". U stylů a skriptů
to platí — `Kontext::asset()` jim z `Zdroj::verzeAktiv()` přidá `?v=<hash>`.
U obrázků ne; ty šly bez verze. `immutable` znamená, že prohlížeč cache ani
neověřuje, takže kdo si starou fotku jednou stáhl, drží si ji rok a nová
fotka na témže jméně se k němu nedostane.

Proč brána takhle: měří se adresy ve **vykreslené stránce**, tedy přesně to,
co prohlížeč dostane a podle čeho si cache drží — ne to, že se někde v šabloně
volá `asset()`. A verze se porovnává s obsahem souboru na disku, aby „nějaké
?v=" neprošlo jako verze; jinak by brána hlídala jen tvar, ne účel.

Ukázka na GitHub Pages má verze taky (staví je build.mjs ze stejného
manifestu), a že se čísla shodují bajt na bajt, hlídá
tests/test_php_shoda_stranek.py.

Zaznamenaný vzorek (tento stroj, PHP 8.5.10, 12. 11. 2026; 139 vykreslených
stránek, 50 různých souborů v assets/img):
  PŘED opravou: 1187 výskytů adres obrázků, z toho bez ?v= 1187, s ověřenou
                verzí 0
  PO opravě:    1187 výskytů, bez ?v= 0, s ověřenou verzí 1187
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
IMG = KOREN / "web" / "public" / "assets" / "img"

# Adresa obrázku z podstránky vede o patro výš: ../assets/img/…
ADRESA = re.compile(r"^(?:\.\./)*assets/img/([^?]+)\?v=([0-9a-f]{8})$")
BEZ_VERZE = re.compile(r"^(?:\.\./)*assets/img/([^?]+)$")

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Config;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$site = $zdroj->site();

/* Posbírá adresy obrázků ze všech míst, kde se v hlavě i těle objevují:
   src, href (favicon), content (og:image) a každý kus srcsetu. */
function adresyObrazku(string $html): array
{
    preg_match_all('~(?:src|href|content)="((?:\.\./)*assets/img/[^"]*)"~i', $html, $m);
    $vse = $m[1];
    preg_match_all('~srcset="([^"]*)"~i', $html, $s);
    foreach ($s[1] as $set) {
        foreach (explode(',', $set) as $kus) {
            $adresa = trim(explode(' ', trim($kus))[0]);
            if (str_contains($adresa, 'assets/img/')) {
                $vse[] = $adresa;
            }
        }
    }
    return $vse;
}

$vysledek = [];
foreach (array_unique(Stranka::seznam($site)) as $cesta) {
    Config::nastav(['web' => 'https://www.greenairtech.cz']);
    $html = Stranka::html($cesta, $zdroj, false);
    if ($html === null) {
        continue;
    }
    $vysledek[$cesta] = adresyObrazku($html);
}
echo json_encode($vysledek);
"""


@pytest.fixture(scope="module")
def adresy():
    program = PROGRAM.replace("{KOREN}", str(KOREN))
    hotovo = subprocess.run(
        ["php", "-r", program], capture_output=True, text=True, cwd=KOREN,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    data = json.loads(hotovo.stdout)
    assert len(data) > 100, f"vykreslilo se jen {len(data)} stránek, čekáme celý web"
    return data


@pytest.fixture(scope="module")
def vsechny(adresy):
    return [u for seznam in adresy.values() for u in seznam]


def test_web_opravdu_vklada_obrazky(vsechny):
    """Kontrola samotné brány: kdyby se adresy přestaly hledat, projde prázdno."""
    assert len(vsechny) > 500, f"našlo se jen {len(vsechny)} adres obrázků"


def test_zadna_adresa_obrazku_neni_bez_verze(adresy):
    """Bez ?v= si prohlížeč podle `immutable` nechá starou fotku rok."""
    bez = {}
    for cesta, seznam in adresy.items():
        chybne = sorted({u for u in seznam if BEZ_VERZE.match(u)})
        if chybne:
            bez[cesta] = chybne[:3]
    assert bez == {}, (
        f"{len(bez)} stránek vkládá obrázek bez verze v adrese "
        f"(např. {dict(list(bez.items())[:3])})"
    )


def test_verze_odpovida_obsahu_souboru(vsechny):
    """Verze musí být otisk obsahu — jinak hlídáme tvar, ne účel."""
    spatne = {}
    for u in sorted(set(vsechny)):
        m = ADRESA.match(u)
        if m is None:
            spatne[u] = "adresa nemá ?v=<8 znaků sha1>"
            continue
        soubor = IMG / m.group(1)
        if not soubor.is_file():
            spatne[u] = "soubor na disku není"
            continue
        cekame = hashlib.sha1(soubor.read_bytes()).hexdigest()[:8]
        if m.group(2) != cekame:
            spatne[u] = f"verze {m.group(2)}, obsah má {cekame}"
    assert spatne == {}, f"verze nesouhlasí s obsahem: {dict(list(spatne.items())[:5])}"


def test_stejny_soubor_ma_vsude_stejnou_verzi(vsechny):
    """Jedna fotka = jedna adresa; jinak si ji prohlížeč stahuje víckrát."""
    podle_souboru: dict[str, set[str]] = {}
    for u in set(vsechny):
        m = ADRESA.match(u) or BEZ_VERZE.match(u)
        if m is None:
            continue
        podle_souboru.setdefault(m.group(1), set()).add(u.split("assets/img/")[-1])
    vice = {s: sorted(v) for s, v in podle_souboru.items() if len(v) > 1}
    assert vice == {}, f"týž soubor má víc verzí: {vice}"
