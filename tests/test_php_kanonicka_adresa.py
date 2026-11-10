"""Brána: každá veřejná stránka ostrého webu říká svou kanonickou adresu.

Nález při celkové kontrole ostrého webu (10. 11. 2026). Web odpovídá na
`greenairtech.cz` i `www.greenairtech.cz` a ani jedna adresa nepřesměruje na
druhou. Stránky přitom neměly `<link rel="canonical">`, takže vyhledávač vidí
každou stránku dvakrát a sílu odkazů si rozdělí mezi dvě adresy. Michael
rozhodl 10. 11. 2026: hlavní je `https://www.greenairtech.cz`.

Druhý nález z téhož měření: `hreflang` měl **relativní** adresy
(`href="en/kontakt.html"`) a **chyběl odkaz sám na sebe** — stránka v češtině
uváděla jen `en` a `de`. Obojí je podle Googlu neplatné: relativní adresy
ignoruje a skupinu bez odkazu na sebe zahodí celou, takže tři jazykové verze
spolu nesouvisely.

Proč brána takhle: měří se vykreslená hlava stránky v obou režimech, tedy
tam, kde se o značkách rozhoduje, ne přítomnost volání v šabloně. Adresa webu
se podstrčí přes `Config::nastav` — ostrý web ji má z `config/config.php`,
který v repozitáři není.

Ukázka na GitHub Pages se staví do podsložky, je celá `noindex` a plnou adresu
nezná; tam musí hlava zůstat **přesně** jako dosud, jinak se rozbije bajtový
diff proti nákresu (tests/test_php_shoda_stranek.py). Chybová stránka a
přihlášení do administrace se neindexují, kanonická adresa jim nepatří.

Zaznamenaný vzorek (tento stroj, PHP 8.5.10, 10. 11. 2026; 139 vykreslených
stránek, z toho 135 indexovaných — 404 a administrace ve třech jazycích ven):
  PŘED opravou  ostrý:  canonical 0/135  hreflang relativních 270  se sebou 0
  PO opravě     ostrý:  canonical 135/135  hreflang relativních 0  se sebou 135
                ukázka: canonical 0  hreflang relativních 270  se sebou 0
                        (nákres beze změny — v obou měřeních stejná čísla)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

DOMENA = "https://www.greenairtech.cz"
# 404 a administrace mají noindex, do sitemapy ani do canonical nepatří.
BEZ_ADRESY = ("404.html", "administrace.html")

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Config;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$site = $zdroj->site();

function hlava(string $html): array
{
    preg_match('~<head\b[^>]*>(.*?)</head>~is', $html, $m);
    $head = $m[1] ?? '';
    preg_match_all('~<link\s+rel="canonical"\s+href="([^"]*)"~i', $head, $k);
    preg_match_all('~<link\s+rel="alternate"\s+hreflang="([^"]*)"\s+href="([^"]*)"~i', $head, $h);
    return [
        'canonical' => $k[1],
        'hreflang' => array_map(null, $h[1], $h[2]),
    ];
}

$vysledek = [];
foreach (array_unique(Stranka::seznam($site)) as $cesta) {
    $zaznam = [];
    foreach ([false, true] as $ukazka) {
        /* Ostrý web zná svou adresu z nastavení, ukázka ne. */
        Config::nastav($ukazka ? [] : ['web' => '{DOMENA}']);
        $html = Stranka::html($cesta, $zdroj, $ukazka);
        if ($html === null) { continue 2; }
        $zaznam[$ukazka ? 'ukazka' : 'ostry'] = hlava($html);
    }
    $vysledek[$cesta] = $zaznam;
}
echo json_encode($vysledek);
"""


@pytest.fixture(scope="module")
def hlavy():
    program = PROGRAM.replace("{KOREN}", str(KOREN)).replace("{DOMENA}", DOMENA)
    hotovo = subprocess.run(
        ["php", "-r", program], capture_output=True, text=True, cwd=KOREN,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    data = json.loads(hotovo.stdout)
    assert len(data) > 100, f"vykreslilo se jen {len(data)} stránek, čekáme celý web"
    return data


def indexovane(hlavy):
    return {c: z for c, z in hlavy.items() if not c.endswith(BEZ_ADRESY)}


def test_kazda_indexovana_stranka_ma_prave_jednu_kanonickou_adresu(hlavy):
    """Bez canonical si vyhledávač indexuje www i bez www jako dva weby."""
    chybne = {c: z["ostry"]["canonical"] for c, z in indexovane(hlavy).items()
              if len(z["ostry"]["canonical"]) != 1}
    assert chybne == {}, (
        f"{len(chybne)} stránek ostrého webu nemá právě jednu kanonickou adresu "
        f"(např. {dict(list(chybne.items())[:5])})"
    )


def test_kanonicka_adresa_ukazuje_na_sebe_pod_hlavni_domenou(hlavy):
    """Canonical musí být plná adresa té samé stránky, ne jiné a ne relativní."""
    spatne = {}
    for cesta, z in indexovane(hlavy).items():
        cekame = f"{DOMENA}/{cesta}"
        if z["ostry"]["canonical"] != [cekame]:
            spatne[cesta] = z["ostry"]["canonical"]
    assert spatne == {}, f"kanonická adresa nesouhlasí se stránkou: {dict(list(spatne.items())[:5])}"


def test_neindexovane_stranky_kanonickou_adresu_nemaji(hlavy):
    """404 a přihlášení do administrace mají noindex; canonical by si odporoval."""
    zbytek = {c: z["ostry"]["canonical"] for c, z in hlavy.items()
              if c.endswith(BEZ_ADRESY) and z["ostry"]["canonical"]}
    assert zbytek == {}, f"noindex stránka má kanonickou adresu: {zbytek}"


def test_hreflang_ma_plne_adresy(hlavy):
    """Relativní hreflang Google ignoruje — musí to být absolutní adresa."""
    spatne = {}
    for cesta, z in indexovane(hlavy).items():
        relativni = [h for h in z["ostry"]["hreflang"] if not h[1].startswith(DOMENA + "/")]
        if relativni:
            spatne[cesta] = relativni
    assert spatne == {}, f"hreflang není plná adresa: {dict(list(spatne.items())[:3])}"


def test_hreflang_uvadi_i_sebe_a_vsechny_jazyky(hlavy):
    """Bez odkazu sám na sebe Google celou jazykovou skupinu zahodí."""
    spatne = {}
    for cesta, z in indexovane(hlavy).items():
        kody = sorted(h[0] for h in z["ostry"]["hreflang"])
        if kody != ["cs", "de", "en", "x-default"]:
            spatne[cesta] = kody
    assert spatne == {}, (
        f"hreflang neuvádí všechny tři jazyky, sebe a x-default: "
        f"{dict(list(spatne.items())[:3])}"
    )


def test_hreflang_vede_na_tutez_stranku_v_jinem_jazyce(hlavy):
    """Skupina musí být souvislá: co stránka uvádí jako svou verzi v cizím
    jazyce, to musí tu stránku uvádět zpátky — jinak si Google skupinu
    nespáruje. Kontroluje se přes kanonickou adresu té druhé stránky."""
    kanonicke = {z["ostry"]["canonical"][0]: c
                 for c, z in indexovane(hlavy).items() if z["ostry"]["canonical"]}
    rozpad = {}
    for cesta, z in indexovane(hlavy).items():
        for kod, adresa in z["ostry"]["hreflang"]:
            if kod == "x-default":
                continue
            soused = kanonicke.get(adresa)
            if soused is None:
                rozpad.setdefault(cesta, []).append(f"{kod} → neznámá adresa {adresa}")
                continue
            zpatky = {a for _, a in hlavy[soused]["ostry"]["hreflang"]}
            if f"{DOMENA}/{cesta}" not in zpatky:
                rozpad.setdefault(cesta, []).append(f"{kod} → {soused} se nevrací")
    assert rozpad == {}, f"jazyková skupina není souvislá: {dict(list(rozpad.items())[:3])}"


def test_ukazka_zustava_bez_kanonicke_adresy(hlavy):
    """Nákres na GitHub Pages svou adresu nezná a je celý noindex. Kdyby se mu
    canonical vložil, ukazoval by na ostrý web a bajtový diff proti ukázce
    (test_php_shoda_stranek.py) by spadl."""
    kde = [c for c, z in hlavy.items() if z["ukazka"]["canonical"]]
    assert kde == [], f"ukázka dostala kanonickou adresu: {kde[:5]}"


def test_v_ukazce_zustava_hreflang_jak_byl(hlavy):
    """Druhá strana pravidla: v ukázce zůstávají relativní odkazy na dva cizí
    jazyky — přesně jak je má nákres."""
    spatne = {}
    for cesta, z in hlavy.items():
        kody = sorted(h[0] for h in z["ukazka"]["hreflang"])
        plne = [h for h in z["ukazka"]["hreflang"] if h[1].startswith("http")]
        if len(kody) != 2 or plne:
            spatne[cesta] = z["ukazka"]["hreflang"]
    assert spatne == {}, f"ukázce se změnil hreflang: {dict(list(spatne.items())[:3])}"
