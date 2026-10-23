"""Brána: co administrace uloží, je už očištěné.

App\\Obsah\\Ocista (C-027) umí texty očistit, Router je jediné místo, kudy
se do databáze dostanou. Tenhle test hlídá, že se tam očista opravdu volá —
sama o sobě by jinak ležela v repozitáři bez užitku.

Pravidlo: do úložiště nesmí dojít nic, co by v HTML stránky otevřelo značku,
a v odpovědi dostane prohlížeč přesně to, co se uložilo.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

ZLY = 'Konec <img src=x onerror=alert(1)> a </script> a <br> dál'
CISTY = 'Konec &lt;img src=x onerror=alert(1)&gt; a &lt;/script&gt; a <br> dál'

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Router;
use App\Api\Uloziste;

$prazdny = ['texts' => [], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []]];

$uloziste = new class ($prazdny) implements Uloziste {
    public array $zapsano = [];
    public function __construct(private array $stav) {}
    public function stav(): array { return $this->stav; }
    public function ulozStav(array $stav, string $kdo): void { $this->zapsano[] = $stav; $this->stav = $stav; }
    public function uzivatele(): array { return []; }
    public function ulozUzivatele(array $u): array { return $u; }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }
};

$telo = file_get_contents('{TELO}');
$odpoved = Router::obsluz([
    'metoda' => 'PUT', 'cesta' => 'stav', 'telo' => $telo, 'dotaz' => [],
    'uzivatel' => ['jmeno' => 'pavel', 'role' => 'spravce'], 'csrf_ok' => true, 'soubor' => null,
], $uloziste, null, null);

echo json_encode([
    'stav' => $odpoved['stav'],
    'ulozeno' => $uloziste->zapsano,
    'odpoved' => $odpoved['telo'],
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
"""


@pytest.fixture(scope="module")
def vysledek(tmp_path_factory):
    telo = tmp_path_factory.mktemp("api") / "telo.json"
    telo.write_text(json.dumps({
        "texts": {"cs": {"rozcestnik.titulek": ZLY}},
        "realizace": {
            # `misto` je skutečné pole realizace — od nálezu K2 hlídá
            # App\Obsah\MezeRealizaci, že nic jiného do stavu nepřijde,
            # takže vymyšlené pole už by neprošlo přes meze a očista by
            # se vůbec nedostala ke slovu.
            "added": [{"id": "nova", "misto": ZLY, "datum": "2026-10-01", "motiv": 1, "vetev": "firmy"}],
            "edited": {},
            "removed": [],
        },
        "updatedAt": "2026-10-23T12:00:00.000Z",
    }, ensure_ascii=False), "utf8")
    hotovo = subprocess.run(
        ["php", "-r", PROGRAM.replace("{KOREN}", str(KOREN)).replace("{TELO}", str(telo))],
        capture_output=True, text=True,
    )
    assert hotovo.returncode == 0, hotovo.stderr[-2000:]
    return json.loads(hotovo.stdout)


def test_ulozeni_projde(vysledek):
    assert vysledek["stav"] == 200, vysledek


def test_do_uloziste_dojde_ocisteny_text(vysledek):
    assert len(vysledek["ulozeno"]) == 1, "stav se neuložil (nebo víckrát)"
    ulozeno = vysledek["ulozeno"][0]
    assert ulozeno["texts"]["cs"]["rozcestnik.titulek"] == CISTY
    assert ulozeno["realizace"]["added"][0]["misto"] == CISTY


def test_prohlizec_dostane_zpatky_totez(vysledek):
    """Administrace si odpovědí přepisuje svůj stav — kdyby dostala neočištěný
    text, ukazovala by něco jiného, než co na webu je."""
    vracene = vysledek["odpoved"]["stav"]["texts"]["cs"]["rozcestnik.titulek"]
    assert vracene == CISTY
