"""Akceptační test C-031 — App\\Jadro\\Adresa (adresa návštěvníka).

Dvě místa na webu potřebují vědět, odkud návštěvník přišel: zámek
administrace (aby jeden útočník nezamkl všechny) a strop poptávek (aby
jeden robot nezablokoval formulář všem). Dosud si adresu každé z nich
luštilo samo a jen z dvou hlaviček — a nezávislý test našel, že strop
poptávek adresu nerozlišuje vůbec.

Pravidlo brány:
- Pořadí zdrojů: CF-Connecting-IP (za Cloudflare), pak PRVNÍ položka
  X-Forwarded-For, nakonec REMOTE_ADDR.
- Zdroj, ve kterém není platná adresa, se PŘESKOČÍ a zkusí se další.
  Podvržená hlavička tak nesmaže skutečnou adresu — jinak by stačilo
  poslat „X-Forwarded-For: nic" a strop na adresu by přestal platit.
- Port se odřízne (proxy píšou i „1.2.3.4:51514"), hranaté závorky u IPv6
  taky.
- Když platná adresa není nikde, vrátí se prázdný řetězec. Volající pak
  ví, že podle adresy nic rozhodnout nemůže.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

CF = "HTTP_CF_CONNECTING_IP"
XFF = "HTTP_X_FORWARDED_FOR"
REMOTE = "REMOTE_ADDR"

# popis -> ($_SERVER, čekaná adresa)
PRIPADY: dict[str, tuple[dict[str, str], str]] = {
    "prázdné prostředí": ({}, ""),
    "jen REMOTE_ADDR": ({REMOTE: "203.0.113.9"}, "203.0.113.9"),
    "Cloudflare má přednost": (
        {CF: "198.51.100.7", XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, "198.51.100.7"),
    "bez Cloudflare rozhoduje X-Forwarded-For": (
        {XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, "203.0.113.9"),
    "z X-Forwarded-For platí první položka": (
        {XFF: "203.0.113.9, 70.41.3.18, 150.172.238.178", REMOTE: "10.0.0.1"}, "203.0.113.9"),
    "mezery kolem položek": ({XFF: "   203.0.113.9 ,10.0.0.5  "}, "203.0.113.9"),
    "nesmysl v Cloudflare hlavičce se přeskočí": (
        {CF: "nic", XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, "203.0.113.9"),
    "nesmysl v X-Forwarded-For se přeskočí": (
        {XFF: "neco-divneho", REMOTE: "10.0.0.1"}, "10.0.0.1"),
    "prázdná hlavička se přeskočí": ({XFF: "", REMOTE: "10.0.0.1"}, "10.0.0.1"),
    "čárky bez obsahu": ({XFF: " , , ", REMOTE: "10.0.0.1"}, "10.0.0.1"),
    "nesmysl všude": ({CF: "x", XFF: "y", REMOTE: "z"}, ""),
    "port se odřízne": ({REMOTE: "203.0.113.9:51514"}, "203.0.113.9"),
    "port v X-Forwarded-For": ({XFF: "203.0.113.9:443, 10.0.0.1"}, "203.0.113.9"),
    "IPv6": ({REMOTE: "2001:db8::1"}, "2001:db8::1"),
    "IPv6 v hranatých závorkách": ({REMOTE: "[2001:db8::1]"}, "2001:db8::1"),
    "IPv6 se závorkami a portem": ({REMOTE: "[2001:db8::1]:443"}, "2001:db8::1"),
    "vnitřní síť je platná adresa": ({REMOTE: "192.168.1.14"}, "192.168.1.14"),
    "localhost": ({REMOTE: "127.0.0.1"}, "127.0.0.1"),
    "jen tečky": ({REMOTE: "...."}, ""),
    "číslo, co není adresa": ({REMOTE: "999.999.999.999"}, ""),
    "adresa s písmeny": ({REMOTE: "203.0.113.9abc"}, ""),
    # Podvržená délka: hlavička smí být dlouhá, ale výsledek je jedna adresa.
    "dlouhý seznam": ({XFF: ", ".join(["203.0.113.9"] * 50)}, "203.0.113.9"),
    "nečitelné znaky": ({REMOTE: "203.0.113.9\n"}, "203.0.113.9"),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Adresa;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

$ven = [];
foreach ($vstup as $klic => $server) {
    $kopie = $server;
    $ven[$klic] = [
        'adresa' => Adresa::navstevnika($server),
        'nemutuje' => $kopie === $server,
    ];
}
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("adresa")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps({k: s for k, (s, _) in PRIPADY.items()}, ensure_ascii=False), "utf8")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(vstup)], capture_output=True, text=True, timeout=60,
    )
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


@pytest.mark.parametrize("popis", list(PRIPADY))
def test_adresa_navstevnika(popis, v):
    _, cekana = PRIPADY[popis]
    assert v[popis]["adresa"] == cekana, popis


def test_vstup_se_nemeni(v):
    for popis, o in v.items():
        assert o["nemutuje"], f"{popis}: funkce přepsala pole, které jí dal volající"


def test_podvrzena_hlavicka_nesmaze_skutecnou_adresu(v):
    """Kdyby „X-Forwarded-For: neco-divneho" vrátilo prázdno, strop na adresu
    by se dal vypnout jednou hlavičkou."""
    assert v["nesmysl v X-Forwarded-For se přeskočí"]["adresa"] == "10.0.0.1"
    assert v["nesmysl v Cloudflare hlavičce se přeskočí"]["adresa"] == "203.0.113.9"
