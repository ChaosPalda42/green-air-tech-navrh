"""Akceptační test C-022 — App\\Posta\\Odeslani (poptávka z webu na e-mail firmy).

Formulář na webu je ta nejdůležitější věc, co na stránce je: když se poptávka
nedoručí nebo přijde zmrzačená, firma o zakázku přišla. Brána proto hlídá tvar
zprávy do posledního řádku a hlavně to, že se do hlaviček nedostane nic, co
napsal cizí člověk do formuláře.

Všechna jména a adresy v testu jsou vymyšlené.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Posta\Odeslani;
use App\Posta\Prepravka;

$nastaveni = ['prijemce' => 'poptavky@greenairtech.test', 'odesilatel' => 'web@greenairtech.test'];
$slovnik = ['typy' => ['projekce' => 'Projekce', 'servis' => 'Servis a údržba'], 'predmet' => 'Poptávka z webu'];

$poptavka = [
    'typ' => 'projekce',
    'jmeno' => 'Jana Vymyšlená',
    'email' => 'jana@priklad.test',
    'telefon' => '+420 601 123 456',
    'zprava' => "Dobrý den,\npotřebujeme projekt vzduchotechniky.\nDěkuji.",
    'vetev' => 'firmy',
    'jazyk' => 'cs',
];

$prepravka = new class implements Prepravka {
    public array $poslano = [];
    public bool $vysledek = true;
    public function posli(string $komu, string $predmet, string $telo, array $hlavicky): bool {
        $this->poslano[] = ['komu' => $komu, 'predmet' => $predmet, 'telo' => $telo, 'hlavicky' => $hlavicky];
        return $this->vysledek;
    }
};

$padajici = new class implements Prepravka {
    public function posli(string $komu, string $predmet, string $telo, array $hlavicky): bool { return false; }
};

$podvrh = $poptavka;
$podvrh['jmeno'] = "Zlo\r\nBcc: kdokoli@jinde.test";
$podvrh['email'] = "zlo@priklad.test\r\nBcc: kdokoli@jinde.test";

$bezEmailu = $poptavka;
$bezEmailu['email'] = 'tohle-neni-adresa';

$holy = ['typ' => 'servis', 'jmeno' => 'Bez Kontaktu', 'zprava' => 'Dotaz.'];

echo json_encode([
    'zprava' => Odeslani::zprava($poptavka, $nastaveni, $slovnik),
    'podvrh' => Odeslani::zprava($podvrh, $nastaveni, $slovnik),
    'bez_emailu' => Odeslani::zprava($bezEmailu, $nastaveni, $slovnik),
    'holy' => Odeslani::zprava($holy, $nastaveni, $slovnik),
    'cizi_typ' => Odeslani::zprava(['typ' => 'vymyslene', 'jmeno' => 'A', 'zprava' => 'B'], $nastaveni, $slovnik),
    'odeslano' => Odeslani::posli($poptavka, $nastaveni, $slovnik, $prepravka),
    'neodeslano' => Odeslani::posli($poptavka, $nastaveni, $slovnik, $padajici),
    'prepravka_dostala' => $prepravka->poslano,
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("posta")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_zprava_jde_firme_a_predmet_rika_o_co_jde(v):
    z = v["zprava"]
    assert z["komu"] == "poptavky@greenairtech.test"
    assert "Poptávka z webu" in z["predmet"] and "Projekce" in z["predmet"], z["predmet"]
    assert v["cizi_typ"]["predmet"].endswith("vymyslene"), \
        "neznámý typ se má do předmětu opsat tak, jak přišel"


def test_telo_obsahuje_vsechno_co_clovek_napsal(v):
    telo = v["zprava"]["telo"]
    for cast in ("Jana Vymyšlená", "jana@priklad.test", "+420 601 123 456",
                 "potřebujeme projekt vzduchotechniky", "firmy", "Projekce"):
        assert cast in telo, f"v těle chybí {cast!r}\n---\n{telo}"
    assert telo.count("\n") >= 5, "tělo je slité do jednoho řádku"


def test_hlavicky_maji_spravnou_adresu_a_kodovani(v):
    h = v["zprava"]["hlavicky"]
    assert h["From"] == "web@greenairtech.test"
    assert h["Reply-To"] == "jana@priklad.test", "odpověď má jít zákazníkovi"
    assert h["MIME-Version"] == "1.0"
    assert h["Content-Type"] == 'text/plain; charset="UTF-8"'
    assert "Bcc" not in h


def test_do_hlavicek_se_nedostane_nic_z_formulare(v):
    h = v["podvrh"]["hlavicky"]
    spojene = "\n".join(f"{k}: {x}" for k, x in h.items())
    assert "Bcc" not in spojene, f"podstrčená hlavička prošla:\n{spojene}"
    for hodnota in h.values():
        assert "\r" not in hodnota and "\n" not in hodnota, f"hlavička má zlom řádku: {hodnota!r}"
    assert "\r" not in v["podvrh"]["predmet"] and "\n" not in v["podvrh"]["predmet"]
    assert "kdokoli@jinde.test" not in spojene


def test_bez_platneho_emailu_se_reply_to_vynecha(v):
    assert "Reply-To" not in v["bez_emailu"]["hlavicky"], \
        "neplatná adresa se nesmí dostat do Reply-To"
    assert "tohle-neni-adresa" in v["bez_emailu"]["telo"], \
        "co člověk napsal, má firma stejně vidět v těle"
    assert "Reply-To" not in v["holy"]["hlavicky"]


def test_chybejici_pole_nic_nerozbiji(v):
    z = v["holy"]
    assert "Bez Kontaktu" in z["telo"] and "Dotaz." in z["telo"]
    assert z["komu"] == "poptavky@greenairtech.test"


def test_posli_vrati_jak_to_dopadlo(v):
    assert v["odeslano"] is True
    assert v["neodeslano"] is False, "neúspěch přepravky se musí propsat do výsledku"
    assert len(v["prepravka_dostala"]) == 1
    assert v["prepravka_dostala"][0]["komu"] == "poptavky@greenairtech.test"
