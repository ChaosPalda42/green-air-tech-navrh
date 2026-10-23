"""Akceptační test C-031 — App\\Jadro\\Adresa (adresa návštěvníka).

Dvě místa na webu potřebují vědět, odkud návštěvník přišel: zámek
administrace (aby jeden útočník nezamkl všechny) a strop poptávek (aby
jeden robot nezablokoval formulář všem).

Pravidlo brány:
- HLAVIČKY SE VĚŘÍ JEN TEHDY, když to volající řekne. Nález kola 2 (K1):
  podle README stojí web přímo za Apache/nginx a žádná proxy hlavičku
  nepřepisuje — `X-Forwarded-For` tedy dorazí taková, jakou si ji poslal
  sám návštěvník, a strop na adresu i zámek podle adresy by se daly obejít
  jedním řádkem v požadavku. Bez nastavení proto platí jen REMOTE_ADDR.
- Když nastavení říká „jsme za proxy" (`['verit' => true]`), platí staré
  pořadí: CF-Connecting-IP, pak PRVNÍ položka X-Forwarded-For, nakonec
  REMOTE_ADDR. Zdroj, ve kterém není platná adresa, se PŘESKOČÍ — podvržená
  hlavička tak nesmaže skutečnou adresu.
- Když nastavení navíc vyjmenuje proxy (`['verit' => true, 'adresy' => […]]`),
  hlavičky se čtou jen tehdy, přišel-li požadavek od jedné z nich. Od kohokoli
  jiného platí REMOTE_ADDR, i kdyby hlavičky poslal.
- Port se odřízne (proxy píšou i „1.2.3.4:51514"), hranaté závorky u IPv6
  taky. Když platná adresa není nikde, vrátí se prázdný řetězec.
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

VERIT = {"verit": True}

# popis -> ($_SERVER, $proxy, čekaná adresa)
PRIPADY: dict[str, tuple[dict[str, str], dict, str]] = {
    # ---------------------------------------------- bez proxy (výchozí stav)
    "bez nastavení platí jen REMOTE_ADDR": (
        {CF: "198.51.100.7", XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, {}, "10.0.0.1"),
    "podvržené hlavičky bez proxy nic nezmění": (
        {XFF: "203.0.113.9", REMOTE: "192.0.2.50"}, {}, "192.0.2.50"),
    "bez proxy a bez REMOTE_ADDR není nic": ({XFF: "203.0.113.9"}, {}, ""),
    "vypnutá důvěra je totéž jako žádná": (
        {XFF: "203.0.113.9", REMOTE: "192.0.2.50"}, {"verit": False}, "192.0.2.50"),
    "prázdný seznam proxy při zapnuté důvěře věří hlavičkám": (
        {XFF: "203.0.113.9", REMOTE: "192.0.2.50"},
        {"verit": True, "adresy": []}, "203.0.113.9"),

    # ---------------------------------------------------------- za proxy
    "prázdné prostředí": ({}, VERIT, ""),
    "jen REMOTE_ADDR": ({REMOTE: "203.0.113.9"}, VERIT, "203.0.113.9"),
    "Cloudflare má přednost": (
        {CF: "198.51.100.7", XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, VERIT, "198.51.100.7"),
    "bez Cloudflare rozhoduje X-Forwarded-For": (
        {XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, VERIT, "203.0.113.9"),
    "z X-Forwarded-For platí první položka": (
        {XFF: "203.0.113.9, 70.41.3.18, 150.172.238.178", REMOTE: "10.0.0.1"},
        VERIT, "203.0.113.9"),
    "mezery kolem položek": ({XFF: "   203.0.113.9 ,10.0.0.5  "}, VERIT, "203.0.113.9"),
    "nesmysl v Cloudflare hlavičce se přeskočí": (
        {CF: "nic", XFF: "203.0.113.9", REMOTE: "10.0.0.1"}, VERIT, "203.0.113.9"),
    "nesmysl v X-Forwarded-For se přeskočí": (
        {XFF: "neco-divneho", REMOTE: "10.0.0.1"}, VERIT, "10.0.0.1"),
    # Z X-Forwarded-For platí jen PRVNÍ položka — ta je od návštěvníka.
    # Když je nesmyslná, jde se na REMOTE_ADDR, ne na druhou položku: tu už
    # psala proxy a adresa návštěvníka v ní není.
    "nesmysl v první položce nepustí druhou": (
        {XFF: "neco-divneho, 203.0.113.9", REMOTE: "10.0.0.1"}, VERIT, "10.0.0.1"),
    "prázdná hlavička se přeskočí": ({XFF: "", REMOTE: "10.0.0.1"}, VERIT, "10.0.0.1"),
    "čárky bez obsahu": ({XFF: " , , ", REMOTE: "10.0.0.1"}, VERIT, "10.0.0.1"),
    "nesmysl všude": ({CF: "x", XFF: "y", REMOTE: "z"}, VERIT, ""),
    "port se odřízne": ({REMOTE: "203.0.113.9:51514"}, VERIT, "203.0.113.9"),
    "port v X-Forwarded-For": ({XFF: "203.0.113.9:443, 10.0.0.1"}, VERIT, "203.0.113.9"),
    "IPv6": ({REMOTE: "2001:db8::1"}, VERIT, "2001:db8::1"),
    "IPv6 v hranatých závorkách": ({REMOTE: "[2001:db8::1]"}, VERIT, "2001:db8::1"),
    "IPv6 se závorkami a portem": ({REMOTE: "[2001:db8::1]:443"}, VERIT, "2001:db8::1"),
    "vnitřní síť je platná adresa": ({REMOTE: "192.168.1.14"}, VERIT, "192.168.1.14"),
    "localhost": ({REMOTE: "127.0.0.1"}, VERIT, "127.0.0.1"),
    "jen tečky": ({REMOTE: "...."}, VERIT, ""),
    "číslo, co není adresa": ({REMOTE: "999.999.999.999"}, VERIT, ""),
    "adresa s písmeny": ({REMOTE: "203.0.113.9abc"}, VERIT, ""),
    # Podvržená délka: hlavička smí být dlouhá, ale výsledek je jedna adresa.
    "dlouhý seznam": ({XFF: ", ".join(["203.0.113.9"] * 50)}, VERIT, "203.0.113.9"),
    "nečitelné znaky": ({REMOTE: "203.0.113.9\n"}, VERIT, "203.0.113.9"),

    # -------------------------------------------- jmenovitě vypsané proxy
    "od vypsané proxy se hlavičce věří": (
        {XFF: "203.0.113.9", REMOTE: "10.0.0.1"},
        {"verit": True, "adresy": ["10.0.0.1"]}, "203.0.113.9"),
    "od cizí adresy se hlavička zahodí": (
        {XFF: "203.0.113.9", REMOTE: "198.51.100.200"},
        {"verit": True, "adresy": ["10.0.0.1"]}, "198.51.100.200"),
    "proxy zadaná sítí": (
        {XFF: "203.0.113.9", REMOTE: "10.4.7.9"},
        {"verit": True, "adresy": ["10.0.0.0/8"]}, "203.0.113.9"),
    "mimo zadanou síť": (
        {XFF: "203.0.113.9", REMOTE: "11.4.7.9"},
        {"verit": True, "adresy": ["10.0.0.0/8"]}, "11.4.7.9"),
    "proxy zadaná sítí IPv6": (
        {XFF: "203.0.113.9", REMOTE: "2001:db8::55"},
        {"verit": True, "adresy": ["2001:db8::/32"]}, "203.0.113.9"),
    "víc proxy v seznamu, sedí druhá": (
        {XFF: "203.0.113.9", REMOTE: "172.16.0.3"},
        {"verit": True, "adresy": ["10.0.0.0/8", "172.16.0.0/12"]}, "203.0.113.9"),
    "nesmysl v seznamu proxy nikomu nevěří": (
        {XFF: "203.0.113.9", REMOTE: "10.0.0.1"},
        {"verit": True, "adresy": ["tohle-neni-adresa"]}, "10.0.0.1"),
    "bez REMOTE_ADDR se seznamu proxy nevyhoví": (
        {XFF: "203.0.113.9"}, {"verit": True, "adresy": ["10.0.0.0/8"]}, ""),
}

# (adresa, síť) -> čekaný výsledek
SITE: dict[str, tuple[str, str, bool]] = {
    "adresa v síti /8": ("10.4.7.9", "10.0.0.0/8", True),
    "adresa mimo síť /8": ("11.4.7.9", "10.0.0.0/8", False),
    "síť /32 je jedna adresa": ("10.0.0.1", "10.0.0.1/32", True),
    "síť /32 nikoho jiného nepustí": ("10.0.0.2", "10.0.0.1/32", False),
    "bez lomítka se adresy srovnají": ("10.0.0.1", "10.0.0.1", True),
    "bez lomítka a jiná adresa": ("10.0.0.2", "10.0.0.1", False),
    "IPv6 v síti /32": ("2001:db8::55", "2001:db8::/32", True),
    "IPv6 mimo síť /32": ("2001:db9::55", "2001:db8::/32", False),
    "IPv6 v síti /64": ("2001:db8:0:1::9", "2001:db8:0:1::/64", True),
    "IPv6 mimo síť /64": ("2001:db8:0:2::9", "2001:db8:0:1::/64", False),
    "IPv4 se do IPv6 sítě nepočítá": ("10.0.0.1", "2001:db8::/32", False),
    "IPv6 se do IPv4 sítě nepočítá": ("2001:db8::1", "10.0.0.0/8", False),
    "síť /0 pustí všechno ze své rodiny": ("203.0.113.9", "0.0.0.0/0", True),
    "nesmyslná síť nepustí nikoho": ("10.0.0.1", "tohle-neni-sit", False),
    "prázdná síť nepustí nikoho": ("10.0.0.1", "", False),
    "nesmyslná adresa neprojde": ("tohle-neni-adresa", "10.0.0.0/8", False),
    "záporná maska neprojde": ("10.0.0.1", "10.0.0.0/-1", False),
    "maska nad rozsah neprojde": ("10.0.0.1", "10.0.0.0/33", False),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Jadro\Adresa;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

$ven = ['adresy' => [], 'site' => []];
foreach ($vstup['adresy'] as $klic => $pripad) {
    $server = $pripad['server'];
    $proxy = $pripad['proxy'];
    $kopieServeru = $server;
    $kopieProxy = $proxy;
    $ven['adresy'][$klic] = [
        'adresa' => Adresa::navstevnika($server, $proxy),
        'nemutuje' => $kopieServeru === $server && $kopieProxy === $proxy,
    ];
}
foreach ($vstup['site'] as $klic => $pripad) {
    $ven['site'][$klic] = Adresa::vSiti($pripad[0], $pripad[1]);
}
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("adresa")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps({
        "adresy": {k: {"server": s, "proxy": p} for k, (s, p, _) in PRIPADY.items()},
        "site": {k: [a, s] for k, (a, s, _) in SITE.items()},
    }, ensure_ascii=False), "utf8")
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
    *_, cekana = PRIPADY[popis]
    assert v["adresy"][popis]["adresa"] == cekana, popis


@pytest.mark.parametrize("popis", list(SITE))
def test_adresa_v_siti(popis, v):
    *_, cekano = SITE[popis]
    assert v["site"][popis] is cekano, popis


def test_vstup_se_nemeni(v):
    for popis, o in v["adresy"].items():
        assert o["nemutuje"], f"{popis}: funkce přepsala pole, které jí dal volající"


def test_bez_nastaveni_se_hlavickam_neveri(v):
    """Nález K1: web podle README stojí přímo za Apache, žádná proxy hlavičku
    nepřepisuje. Kdyby se X-Forwarded-For věřilo vždycky, stačí jeden řádek
    v požadavku a strop poptávek i zámek podle adresy jsou k ničemu."""
    assert v["adresy"]["bez nastavení platí jen REMOTE_ADDR"]["adresa"] == "10.0.0.1"
    assert v["adresy"]["podvržené hlavičky bez proxy nic nezmění"]["adresa"] == "192.0.2.50"


def test_vypsana_proxy_pusti_jen_svoje_hlavicky(v):
    """Kdo si vypíše proxy, chce po ní hlavičku věřit — ale jen po ní."""
    assert v["adresy"]["od vypsané proxy se hlavičce věří"]["adresa"] == "203.0.113.9"
    assert v["adresy"]["od cizí adresy se hlavička zahodí"]["adresa"] == "198.51.100.200"


def test_podvrzena_hlavicka_nesmaze_skutecnou_adresu(v):
    """Kdyby „X-Forwarded-For: neco-divneho" vrátilo prázdno, strop na adresu
    by se dal vypnout jednou hlavičkou i za proxy."""
    assert v["adresy"]["nesmysl v X-Forwarded-For se přeskočí"]["adresa"] == "10.0.0.1"
    assert v["adresy"]["nesmysl v Cloudflare hlavičce se přeskočí"]["adresa"] == "203.0.113.9"
