"""Brána: přihlašovací stránka administrace se nesmí dostat do Googlu.

robots.txt ji zakazuje, ale to je jen žádost pro slušné roboty a platí jen
pro ty, co si ho přečtou. Stránka si proto musí říct sama meta značkou.

Druhá strana téhož pravidla: veřejné stránky na ostrém webu noindex mít
NESMÍ. V ukázce ho mají všechny (je to nákres, ne web), takže kdyby se
podmínka spletla, zmizel by klient z vyhledávání celý.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';
$zdroj = new App\Obsah\ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$vysledek = [];
foreach (['administrace.html', 'index.html', 'en/index.html'] as $cesta) {
    foreach ([false, true] as $ukazka) {
        $html = App\Jadro\Stranka::html($cesta, $zdroj, $ukazka);
        $vysledek[$cesta][$ukazka ? 'ukazka' : 'ostry'] = $html === null
            ? null
            : (int) (bool) preg_match('~<meta name="robots" content="noindex~', $html);
    }
}
echo json_encode($vysledek);
"""


@pytest.fixture(scope="module")
def roboti():
    hotovo = subprocess.run(
        ["php", "-r", PROGRAM.replace("{KOREN}", str(KOREN))],
        capture_output=True, text=True, cwd=KOREN,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return json.loads(hotovo.stdout)


def test_administrace_na_ostrem_webu_ma_noindex(roboti):
    assert roboti["administrace.html"]["ostry"] == 1


@pytest.mark.parametrize("cesta", ["index.html", "en/index.html"])
def test_verejna_stranka_na_ostrem_webu_noindex_nema(cesta, roboti):
    assert roboti[cesta]["ostry"] == 0


@pytest.mark.parametrize("cesta", ["administrace.html", "index.html", "en/index.html"])
def test_v_ukazce_ho_ma_kazda_stranka(cesta, roboti):
    assert roboti[cesta]["ukazka"] == 1
