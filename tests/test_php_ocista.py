"""Akceptační test C-027 — App\\Obsah\\Ocista (očista textů z administrace).

Texty z administrace se na webu vypisují JAKO HTML, aby v nich fungovalo
`<br>` (jediná značka, kterou výchozí obsah používá). Vypisuje je server
i prohlížeč (app.js: `el.innerHTML = prepisy[klic]`), takže se musí očistit
na JEDNOM místě — při ukládání, než se text dostane do databáze.

Pravidlo: ze značek projdou jen `br`, `b`, `strong`, `i`, `em` bez atributů;
všechno ostatní se vypíše jako text. Ampersand se nepřepisuje — funkce je
tím pádem idempotentní a dvojí uložení text nerozpadne.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

# vstup → co má vyjít
PRIPADY = [
    # projde beze změny
    ("Obyčejný text", "Obyčejný text"),
    ("Dva řádky<br>pod sebou", "Dva řádky<br>pod sebou"),
    ("Tlustě <b>tady</b> a <strong>tady</strong>", "Tlustě <b>tady</b> a <strong>tady</strong>"),
    ("Kurzíva <i>tady</i> a <em>tady</em>", "Kurzíva <i>tady</i> a <em>tady</em>"),
    ("Značky se srovnají: <BR> <br/> <br />", "Značky se srovnají: <br> <br> <br>"),
    ("Firma & syn, 5 > 3", "Firma & syn, 5 > 3".replace(">", "&gt;")),
    # zavřít skript nejde
    ("Konec </script><script>window.UTEK=1</script>",
     "Konec &lt;/script&gt;&lt;script&gt;window.UTEK=1&lt;/script&gt;"),
    # obrázek s obsluhou chyby je nejkratší cesta ke krádeži sezení
    ('<img src=x onerror="fetch(1)">', '&lt;img src=x onerror="fetch(1)"&gt;'),
    ("<svg/onload=alert(1)>", "&lt;svg/onload=alert(1)&gt;"),
    ("<iframe src=//zlo.test></iframe>", "&lt;iframe src=//zlo.test&gt;&lt;/iframe&gt;"),
    # povolená značka s atributem povolená není
    ('<br onfocus="x" autofocus>', '&lt;br onfocus="x" autofocus&gt;'),
    ('<b class="zlo">text</b>', '&lt;b class="zlo"&gt;text</b>'),
    # komentář, kterým by se taky dal ukončit skript
    ("<!-- skryto --> dál", "&lt;!-- skryto --&gt; dál"),
    ("", ""),
]

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
$vstup = json_decode(file_get_contents('{VSTUP}'), true);
$ven = [];
foreach ($vstup['texty'] as $t) { $ven['texty'][] = \App\Obsah\Ocista::text($t); }
$ven['stav'] = \App\Obsah\Ocista::stav($vstup['stav']);
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""

STAV = {
    "texts": {
        "cs": {"rozcestnik.titulek": "<img src=x onerror=1> a <br> dál"},
        "<script>zly.klic</script>": {"a.b": "x"},
    },
    "realizace": {
        "added": [{"id": "nova", "kraj": "<b>Praha</b>", "motiv": 3, "hotovo": True}],
        "edited": {"logisticke-centrum-d1": {"kraj": "<iframe>"}},
        "removed": ["<i>id</i>"],
    },
    "updatedAt": "2026-10-23T10:00:00.000Z",
}

CEKA_STAV = {
    "texts": {
        "cs": {"rozcestnik.titulek": "&lt;img src=x onerror=1&gt; a <br> dál"},
        "&lt;script&gt;zly.klic&lt;/script&gt;": {"a.b": "x"},
    },
    "realizace": {
        "added": [{"id": "nova", "kraj": "<b>Praha</b>", "motiv": 3, "hotovo": True}],
        "edited": {"logisticke-centrum-d1": {"kraj": "&lt;iframe&gt;"}},
        "removed": ["<i>id</i>"],
    },
    "updatedAt": "2026-10-23T10:00:00.000Z",
}


@pytest.fixture(scope="module")
def vysledek(tmp_path_factory):
    vstup = tmp_path_factory.mktemp("ocista") / "vstup.json"
    vstup.write_text(
        json.dumps({"texty": [v for v, _ in PRIPADY], "stav": STAV}, ensure_ascii=False), "utf8"
    )
    program = PROGRAM.replace("{KOREN}", str(KOREN)).replace("{VSTUP}", str(vstup))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return json.loads(hotovo.stdout)


@pytest.mark.parametrize("vstup,ceka", PRIPADY, ids=[p[0][:28] or "prazdny" for p in PRIPADY])
def test_text(vstup, ceka, vysledek):
    i = [v for v, _ in PRIPADY].index(vstup)
    assert vysledek["texty"][i] == ceka


def test_stav_se_ocisti_celý_a_tvar_zustane(vysledek):
    assert vysledek["stav"] == CEKA_STAV


def test_ocista_je_idempotentni(tmp_path):
    """Administrace uložený text znovu načte a znovu uloží — po druhém průchodu
    se nesmí nic změnit, jinak by z `&lt;` postupně vznikalo `&amp;lt;`."""
    jednou = [c for _, c in PRIPADY]
    vstup = tmp_path / "vstup.json"
    vstup.write_text(json.dumps({"texty": jednou, "stav": CEKA_STAV}, ensure_ascii=False), "utf8")
    program = PROGRAM.replace("{KOREN}", str(KOREN)).replace("{VSTUP}", str(vstup))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    podruhe = json.loads(hotovo.stdout)
    assert podruhe["texty"] == jednou
    assert podruhe["stav"] == CEKA_STAV


def test_vychozi_obsah_webu_projde_beze_zmeny(tmp_path):
    """Kdyby očista měnila texty ze souborů, rozpadla by se ukázka — a hlavně
    by se při prvním uložení v administraci přepsal celý web."""
    texty = []

    def sber(uzel):
        if isinstance(uzel, str):
            texty.append(uzel)
        elif isinstance(uzel, dict):
            for k, v in uzel.items():
                if str(k).startswith("_"):
                    continue  # _comment v datových souborech se nikam nevypisuje
                sber(v)
        elif isinstance(uzel, list):
            for v in uzel:
                sber(v)

    for soubor in sorted((KOREN / "web" / "data").rglob("*.json")):
        sber(json.loads(soubor.read_text("utf8")))
    assert len(texty) > 500, f"výchozí obsah se nenačetl (jen {len(texty)} řetězců)"

    vstup = tmp_path / "vstup.json"
    vstup.write_text(json.dumps({"texty": texty, "stav": {}}, ensure_ascii=False), "utf8")
    program = PROGRAM.replace("{KOREN}", str(KOREN)).replace("{VSTUP}", str(vstup))
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    ven = json.loads(hotovo.stdout)["texty"]
    zmenene = [(a, b) for a, b in zip(texty, ven) if a != b]
    assert zmenene == [], f"očista změnila výchozí obsah: {zmenene[:3]}"
