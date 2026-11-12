"""Akceptace: co PHP vkládá do stránky pro admin.js (window.GAT_*).

Dvě věci, na kterých administrace stojí a žádná jiná brána je nevidí: tvar
stavu a seznam uživatelů. Obojí se našlo až klikáním v živé administraci.

Stav: prázdné mapy musí být {}, ne [].

Našlo se to až klikáním v živé administraci: PHP posílalo
`window.GAT_STAV = {"texts":[], ...}`, prohlížeč z toho udělal pole a první
uložený text se při JSON.stringify ztratil — uložil se prázdný stav.
Orákulum to vidět nemohlo: tests/phpmod.py prázdný objekt a prázdné pole
schválně srovnává na totéž.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Uloziste;
use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$stav = json_decode('{STAV}', true);

$uloziste = new class ($stav) implements Uloziste {
    public function __construct(private array $stav) {}
    public function stav(): array { return $this->stav; }
    public function ulozStav(array $s, string $kdo): void {}
    public function uzivatele(): array { return []; }
    public function ulozUzivatele(array $u): array { return $u; }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }
};

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$kam = Odkazy::rozpoznej('{CESTA}', $zdroj->site());
echo Stranka::vykresli($kam, $zdroj, false, $zdroj, $uloziste);
"""

PRAZDNY = {
    "texts": {},
    "realizace": {"added": [], "edited": {}, "removed": []},
    "portrety": {},
    "updatedAt": None,
}
S_TEXTEM = {
    "texts": {"cs": {"rozcestnik.lead": "Nový text"}},
    "realizace": {"added": [], "edited": {}, "removed": []},
    "portrety": {"radek-tyla": {"zoom": 140, "x": 0, "y": -15}},
    "updatedAt": "2026-10-22T18:07:39.000Z",
}


def vykresli(cesta: str, stav: dict) -> str:
    program = (
        PROGRAM.replace("{KOREN}", str(KOREN))
        .replace("{CESTA}", cesta)
        .replace("{STAV}", json.dumps(stav).replace("\\", "\\\\").replace("'", "\\'"))
    )
    hotovo = subprocess.run(["php", "-r", program.replace("<?php", "", 1)],
                            capture_output=True, text=True)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return hotovo.stdout


def gat_stav(html: str) -> str:
    nalez = re.search(r"window\.GAT_STAV = (.*?);window\.|window\.GAT_STAV = (.*?);</script>", html, re.S)
    assert nalez is not None, "window.GAT_STAV se ve stránce nenašel"
    return (nalez.group(1) or nalez.group(2)).strip()


@pytest.mark.parametrize("cesta", ["index.html", "administrace.html"])
def test_prazdne_mapy_jsou_objekty(cesta):
    syrovy = gat_stav(vykresli(cesta, PRAZDNY))
    assert '"texts":{}' in syrovy, f"texts musí být objekt, ne pole: {syrovy[:120]}"
    assert '"edited":{}' in syrovy, f"realizace.edited musí být objekt: {syrovy[:160]}"
    assert '"added":[]' in syrovy and '"removed":[]' in syrovy, "seznamy zůstávají poli"
    # výřezy portrétů mají stejnou past: prázdné pole by prohlížeč uložil
    # jako [] a první posun fotky by se při JSON.stringify ztratil
    assert '"portrety":{}' in syrovy, f"portrety musí být objekt, ne pole: {syrovy[:160]}"


@pytest.mark.parametrize("cesta", ["index.html", "administrace.html"])
def test_stav_s_textem_prejde_beze_zmeny(cesta):
    nactene = json.loads(gat_stav(vykresli(cesta, S_TEXTEM)))
    assert nactene == S_TEXTEM


# --- window.GAT_UZIVATELE -------------------------------------------------
# admin.js čte seznam ze stránky (serverUloziste → pamet["gat-admin-uzivatele"]).
# Když ho PHP nevloží, záložka Uživatelé je na ostrém webu vždycky prázdná.

PROGRAM_UZIVATELE = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Uloziste;
use App\Auth\Sezeni;
use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$lide = [
    ['id' => 1, 'jmeno' => 'Pavel Janda', 'email' => 'pavel@g.test', 'role' => 'spravce', 'aktivni' => 1],
    ['id' => 2, 'jmeno' => 'Martina M.', 'email' => 'martina@g.test', 'role' => 'editor', 'aktivni' => 1],
];

$uloziste = new class ($lide) implements Uloziste {
    public function __construct(private array $lide) {}
    public function stav(): array { return \App\Obsah\Stav::prazdny(); }
    public function ulozStav(array $s, string $kdo): void {}
    public function uzivatele(): array { return $this->lide; }
    public function ulozUzivatele(array $u): array { return $u; }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }
};

if ('{ROLE}' !== '') {
    Sezeni::prihlas(['id' => 1, 'jmeno' => 'Pavel Janda', 'email' => 'pavel@g.test', 'role' => '{ROLE}']);
}

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$kam = Odkazy::rozpoznej('administrace.html', $zdroj->site());
echo Stranka::vykresli($kam, $zdroj, false, $zdroj, $uloziste);
"""


def administrace_jako(role: str) -> str:
    program = PROGRAM_UZIVATELE.replace("{KOREN}", str(KOREN)).replace("{ROLE}", role)
    hotovo = subprocess.run(["php", "-d", "session.save_path=" + str(KOREN / "web" / "cache"),
                             "-r", program], capture_output=True, text=True)
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return hotovo.stdout


def vlozeny_seznam(html: str):
    nalez = re.search(r"window\.GAT_UZIVATELE = (.*?);window\.|window\.GAT_UZIVATELE = (.*?);</script>", html, re.S)
    if nalez is None:
        return None
    return json.loads((nalez.group(1) or nalez.group(2)).strip())


def test_spravce_dostane_seznam_uzivatelu():
    seznam = vlozeny_seznam(administrace_jako("spravce"))
    assert seznam is not None, "window.GAT_UZIVATELE se do stránky nevložil"
    assert [u["jmeno"] for u in seznam] == ["Pavel Janda", "Martina M."]
    assert [u["role"] for u in seznam] == ["spravce", "editor"]


def test_kdo_na_uzivatele_nesmi_seznam_nedostane():
    for role in ("editor", "autor"):
        seznam = vlozeny_seznam(administrace_jako(role))
        assert seznam in (None, []), f"role {role} nemá seznam uživatelů vidět"


def test_neprihlasenemu_se_seznam_neposila():
    assert vlozeny_seznam(administrace_jako("")) in (None, [])
