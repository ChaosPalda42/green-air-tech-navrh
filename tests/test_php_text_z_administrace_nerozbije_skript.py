"""Akceptace: text z administrace nesmí ukončit <script> ve stránce.

PHP vkládá stav administrace do stránky jako inline JSON
(`window.GAT_STAV = {…}` a `<script type="application/json">` u realizací).
Prohlížeč ale ukončí skript na PRVNÍM `</script` v jeho obsahu — i když je
uvnitř řetězce. Text uložený v administraci, ve kterém je `</b>` nebo
`</script>`, tak rozseká stránku: `window.GAT_API` a `GAT_KOREN` zůstanou
`undefined`, konzole hlásí SyntaxError a cokoli za tím místem se vykoná
jako skript.

Našlo se to klikáním v živé administraci na testovací instalaci: po uložení
titulku s `<img …>` byl `window.GAT_STAV` na index.html `undefined`.

Pravidlo: `</`, `<!--` a `-->` se do inline skriptu musí zapsat tak, aby ho
neukončily — stránka pak má pořád stejný počet skriptů a vložený JSON dojde
celý a nezměněný.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

# Co by člověk mohl do administrace napsat a čím by to shořelo.
ZLY_TEXT = 'Konec </script><script>window.UTEK=1</script> a <!-- skryto --> plus </b>'
HODNY_TEXT = "Obyčejný text bez značek"


def stav(text: str) -> dict:
    return {
        "texts": {
            "cs": {
                "rozcestnik.titulek": text,
                "rozcestnik.lead": text,
                # jde do bloku <script type="application/json"> na přehledu realizací
                "realizace.polozky.logisticke-centrum-d1.nazev": text,
            }
        },
        "realizace": {
            "added": [],
            "edited": {"logisticke-centrum-d1": {"kraj": text}},
            "removed": [],
        },
        "portrety": {"zdenek-bauska": {"zoom": 115, "x": 0, "y": 0}},
        "lide": {"added": [], "edited": {}, "removed": []},
        "updatedAt": "2026-10-23T10:00:00.000Z",
    }


PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Uloziste;
use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojDb;

$stav = json_decode(file_get_contents('{STAV}'), true);

$uloziste = new class ($stav) implements Uloziste {
    public function __construct(private array $stav) {}
    public function stav(): array { return $this->stav; }
    public function ulozStav(array $s, string $kdo): void {}
    public function uzivatele(): array { return []; }
    public function ulozUzivatele(array $u): array { return $u; }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }
};

// Stejně jako ostrý web ve web/public/index.php: obsah ze souborů přepsaný
// stavem z administrace.
$zdroj = new ZdrojDb('{KOREN}/web/data', '{KOREN}/web/public/assets', $stav);
$kam = Odkazy::rozpoznej('{CESTA}', $zdroj->site());
echo Stranka::vykresli($kam, $zdroj, false, $zdroj, $uloziste);
"""

STRANKY = ["index.html", "administrace.html", "firmy-realizace.html"]

# Poslední glob na stránce: když se skript ukončí dřív, do obsahu nedojde.
POSLEDNI_GLOB = {
    "index.html": "window.GAT_TEXTY_SERVER",
    "administrace.html": "window.GAT_UZIVATELE",
    "firmy-realizace.html": "window.GAT_TEXTY_SERVER",
}


def vykresli(cesta: str, text: str, tmp_path: Path) -> str:
    soubor = tmp_path / "stav.json"
    soubor.write_text(json.dumps(stav(text), ensure_ascii=False), "utf8")
    program = (
        PROGRAM.replace("{KOREN}", str(KOREN))
        .replace("{CESTA}", cesta)
        .replace("{STAV}", str(soubor))
    )
    hotovo = subprocess.run(
        ["php", "-d", "session.save_path=" + str(KOREN / "web" / "cache"), "-r", program],
        capture_output=True,
        text=True,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return hotovo.stdout


def inline_skripty(html: str) -> list[tuple[str, str]]:
    """Skripty tak, jak je uvidí prohlížeč: (otevírací značka, obsah do
    prvního `</script`)."""
    ven, i = [], 0
    while True:
        zacatek = html.find("<script", i)
        if zacatek < 0:
            return ven
        po_znacce = html.find(">", zacatek) + 1
        konec = html.find("</script", po_znacce)
        assert konec > 0, "neuzavřený <script> ve stránce"
        ven.append((html[zacatek:po_znacce], html[po_znacce:konec]))
        i = konec + 1


@pytest.mark.parametrize("cesta", STRANKY)
def test_vlozeny_stav_dojde_do_skriptu_cely(cesta, tmp_path):
    html = vykresli(cesta, ZLY_TEXT, tmp_path)
    nasledek = [obsah for _, obsah in inline_skripty(html) if "window.GAT_STAV" in obsah]
    assert nasledek, f"{cesta}: skript s window.GAT_STAV se ve stránce nenašel"
    obsah = nasledek[0]
    assert POSLEDNI_GLOB[cesta] in obsah, (
        f"{cesta}: skript skončil dřív než u {POSLEDNI_GLOB[cesta]} — "
        f"text z administrace ho ukončil: …{obsah[-200:]}…"
    )
    nalez = re.search(r"window\.GAT_STAV = (\{.*?\});window\.", obsah, re.S)
    assert nalez is not None, f"{cesta}: window.GAT_STAV ve skriptu není celý"
    assert json.loads(nalez.group(1)) == stav(ZLY_TEXT), f"{cesta}: stav se po cestě změnil"


def test_vlozena_data_realizaci_jsou_platny_json(tmp_path):
    html = vykresli("firmy-realizace.html", ZLY_TEXT, tmp_path)
    bloky = [obsah for znacka, obsah in inline_skripty(html) if "application/json" in znacka]
    assert bloky, "blok s daty realizací se ve stránce nenašel"
    for blok in bloky:
        json.loads(blok)
