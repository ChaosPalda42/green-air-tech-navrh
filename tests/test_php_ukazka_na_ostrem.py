"""Brána: slovník ukázky se nesmí objevit na ostrém webu.

Nález Michaelův (4. 11. 2026, snímek kontaktní stránky). Nad každým
kontaktním formulářem svítí infobox „V téhle ukázce se zpráva nikam
neodesílá — na ostrém webu dorazí na info@greenairtech.cz." Jenže
`Casti::formular` ho vykresloval **vždycky**, bez ohledu na `$ctx->ukazka`,
takže ho měl i ostrý web — tam, kde formulář doopravdy odesílá. Návštěvník
tak čte, že jeho poptávka nikam nejde, a neodešle ji.

Změřeno na současné verzi (ukazka=false, všech 139 stránek): hláška je na
15 veřejných stránkách — index, domácnosti, firemní zákazníci, kariéra a
kontakt v každém ze tří jazyků. Druhý nález z téhož měření: stránka
ochrana-osobnich-udaju.html ukazuje i na ostrém webu poznámku „Tento text
je ukázkový a před spuštěním webu ho doporučujeme nechat zkontrolovat."
To je vzkaz pro klienta, ne pro návštěvníka.

Proč brána takhle: měří se vykreslená stránka v režimu ostrého webu, tedy
tam, kde se o zobrazení rozhoduje, ne přítomnost klíče v obsahu. Klíče v
obsahu zůstávají — ukázka na GitHub Pages je potřebuje a klient je vidí v
administraci.

`administrace.html` se sem nepočítá: svoje „tohle je ukázka" si hlídá sama
přes `$ctx->ukazka` (Administrace.php:99) a slovník ukázky má legitimně ve
svém skriptu — administrace ty texty umí editovat.

Zaznamenaný vzorek (tento stroj, PHP 8.5.10, 4. 11. 2026; 138 stránek bez
administrace, součty přes celý web):
  PŘED opravou  ostrý:  hlaska=15 poznamka=1 volné nálezy=16
  PO opravě     ostrý:  hlaska=0  poznamka=0 volné nálezy=0
                ukázka: hlaska=15 poznamka=3 volné nálezy=200
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

# Volná síť na cokoli, co by slovník ukázky přinesl příště. „demo" s hranicí
# slova, aby neplatila demontáž; `nákres` je naše slovo pro ukázkovou část.
# Česky se skloňuje („v téhle ukázce"), proto i kmen `ukázc`.
VOLNY_VZOR = r"~ukázk|ukázc|\bdemo\b|nákres~ui"

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$site = $zdroj->site();

/* Přesné texty ukázky z obsahu — brána se neptá na slova, ale na tyhle
   konkrétní věty v každém jazyce. */
$hlasky = [];
$poznamky = [];
foreach (['cs', 'en', 'de'] as $jazyk) {
    $d = json_decode(file_get_contents('{KOREN}/web/data/content/' . $jazyk . '.json'), true);
    $hlasky[$jazyk] = $d['kontakt']['formular']['odeslanoDemo'];
    $poznamky[$jazyk] = $d['gdpr']['poznamka'];
}

function viditelny(string $html): string
{
    $bez = preg_replace('~<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>~is', '', $html);
    return trim(preg_replace('~\s+~u', ' ', strip_tags($bez)));
}

function jazykCesty(string $cesta): string
{
    if (str_starts_with($cesta, 'en/')) { return 'en'; }
    if (str_starts_with($cesta, 'de/')) { return 'de'; }
    return 'cs';
}

$vysledek = [];
foreach (array_unique(Stranka::seznam($site)) as $cesta) {
    if ($cesta === 'administrace.html') { continue; }
    $jazyk = jazykCesty($cesta);
    $zaznam = [];
    foreach ([false, true] as $ukazka) {
        $html = Stranka::html($cesta, $zdroj, $ukazka);
        if ($html === null) { continue 2; }
        $text = viditelny($html);
        $zaznam[$ukazka ? 'ukazka' : 'ostry'] = [
            'hlaska' => (int) (bool) str_contains($text, $hlasky[$jazyk]),
            'poznamka' => (int) (bool) str_contains($text, $poznamky[$jazyk]),
            'volne' => preg_match_all('{VOLNY_VZOR}', $text),
        ];
    }
    $vysledek[$cesta] = $zaznam;
}
echo json_encode($vysledek);
"""


@pytest.fixture(scope="module")
def stranky():
    program = (PROGRAM
               .replace("{KOREN}", str(KOREN))
               .replace("{VOLNY_VZOR}", VOLNY_VZOR))
    hotovo = subprocess.run(
        ["php", "-r", program], capture_output=True, text=True, cwd=KOREN,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    data = json.loads(hotovo.stdout)
    assert len(data) > 100, f"vykreslilo se jen {len(data)} stránek, čekáme celý web"
    return data


def test_ostry_web_nerika_ze_formular_neodesila(stranky):
    """Hláška ukázky nad kontaktním formulářem na ostrém webu nemá co dělat."""
    kde = [c for c, z in stranky.items() if z["ostry"]["hlaska"]]
    assert kde == [], (
        f"{len(kde)} stránek ostrého webu tvrdí, že formulář nikam neodesílá "
        f"(např. {kde[:5]}) — návštěvník to čte nad formulářem, který odesílá"
    )


def test_ostry_web_neukazuje_poznamku_ze_je_text_ukazkovy(stranky):
    """Vzkaz „tenhle text si nechte zkontrolovat" patří klientovi, ne návštěvníkovi."""
    kde = [c for c, z in stranky.items() if z["ostry"]["poznamka"]]
    assert kde == [], f"poznámka o ukázkovém textu je na ostrém webu: {kde}"


def test_na_ostrem_webu_nezbylo_nic_z_ukazky(stranky):
    """Volná síť: žádné „ukázka", „demo" ani „nákres" ve viditelném textu."""
    kde = {c: z["ostry"]["volne"] for c, z in stranky.items() if z["ostry"]["volne"]}
    assert kde == {}, f"slovník ukázky zůstal na ostrém webu: {kde}"


def test_v_ukazce_hlaska_zustava(stranky):
    """Druhá strana pravidla: v ukázce se hláška ukazovat MUSÍ, jinak by se
    stačilo splést v podmínce a zmizela by i z nákresu na GitHub Pages."""
    kde = [c for c, z in stranky.items() if z["ukazka"]["hlaska"]]
    assert len(kde) >= 10, f"v ukázce hláška zbyla jen na {len(kde)} stránkách: {kde}"
