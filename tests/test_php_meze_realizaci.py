"""Akceptační test C-033 — App\\Obsah\\MezeRealizaci (co smí přijít v realizacích).

Druhá polovina nálezu K2. `App\\Obsah\\Meze` (C-032) hlídá velikost a texty,
tohle hlídá to, co administrace posílá v klíči `realizace`: nové položky,
změny základních položek, smazané položky a galerie fotek.

Pravidlo:
- Projde jen to, co dialog administrace opravdu skládá (src/assets/admin.js:
  vetev, nazev, misto, datum, plocha, doba, perex, zadani, vysledek, rozsah,
  technologie, kategorie, fotky, id — a motiv, který mají základní položky).
- Fotka je jen záznam o souboru v `media/`. ŽÁDNÁ data URL: na ostrém webu
  se obrázek nahrává zvlášť přes /api/fotka a do stavu patří jen cesta.
  Kdyby sem šly data URL, stav (a tím každá stránka webu) by nabobtnal o
  celé fotky — to je přesně ten nález.
- Stejná pravidla platí pro položku v `added` i pro změnu v `edited`. Kdyby
  se `edited` nekontrolovalo, stačí poslat fotku jako změnu a je to zpátky.
- Každé odmítnutí má kód a detail, který jmenuje provinilé pole nebo id.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

MAX_HODNOTA = 20000
MAX_FOTEK = 8

PLATNA_FOTKA = {
    "id": "f1",
    "nazev": "kotelna.jpg",
    "typ": "image/webp",
    "sirka": 1600,
    "vyska": 1067,
    "bajty": 180000,
    "dataUrl": "media/3f2a9c.webp",
}


def polozka(**navic) -> dict:
    p = {
        "id": "nova-kotelna-pisek",
        "vetev": "firmy",
        "nazev": "Nová kotelna",
        "misto": "Písek",
        "datum": "2026-09-01",
        "plocha": "900 m²",
        "doba": "3 měsíce",
        "perex": "Výměna kotelny v areálu.",
        "zadani": "Zadání.",
        "vysledek": "Výsledek.",
        "rozsah": ["Demontáž", "Montáž"],
        "technologie": ["Tepelné čerpadlo"],
        "kategorie": ["vytapeni"],
        "motiv": 2,
        "fotky": [dict(PLATNA_FOTKA)],
    }
    p.update(navic)
    return p


def pridana(**navic) -> dict:
    return {"added": [polozka(**navic)], "edited": {}, "removed": []}


def zmenena(**navic) -> dict:
    return {"added": [], "edited": {"poliklinika-pisek": navic}, "removed": []}


def fotka(**navic) -> dict:
    f = dict(PLATNA_FOTKA)
    f.update(navic)
    return f


# popis -> (realizace, čekaný kód chyby nebo None = projde)
PRIPADY: dict[str, tuple[object, str | None]] = {
    # ------------------------------------------------------------ projde
    "prázdné realizace": ({"added": [], "edited": {}, "removed": []}, None),
    "realizace bez klíčů vůbec": ({}, None),
    "celá nová položka": (pridana(), None),
    "nová položka bez fotek": (pridana(fotky=[]), None),
    "osm fotek": (pridana(fotky=[fotka(id=f"f{i}") for i in range(8)]), None),
    "změna jednoho pole": (zmenena(plocha="1 200 m²"), None),
    "změna fotek u základní položky": (
        {"added": [], "edited": {"poliklinika-pisek": {"fotky": [fotka()]}},
         "removed": []}, None),
    "smazaná položka": ({"added": [], "edited": {}, "removed": ["poliklinika-pisek"]}, None),
    "text na hranici délky": (pridana(perex="@@HODNOTA_PRESNE@@"), None),
    "prázdné texty v položce": (pridana(perex="", misto=""), None),
    "motiv jako text z JSONu": (pridana(motiv="3"), None),
    "prázdné seznamy": (pridana(rozsah=[], technologie=[], kategorie=[]), None),

    # ------------------------------------------------ cizí a vadná pole
    "cizí pole v nové položce": (pridana(skript="<img src=x>"), "nezname-pole"),
    "cizí pole ve změně": (zmenena(cokoli=1), "nezname-pole"),
    "cizí klíč v realizacích": (
        {"added": [], "edited": {}, "removed": [], "navic": []}, "nezname-pole"),
    "added není seznam": ({"added": {"a": 1}, "edited": {}, "removed": []}, "nezname-pole"),
    "added je seznam s dírou": (
        {"added": {1: polozka()}, "edited": {}, "removed": []}, "nezname-pole"),
    "položka v added není pole": (
        {"added": ["nic"], "edited": {}, "removed": []}, "nezname-pole"),
    "edited není pole": ({"added": [], "edited": "nic", "removed": []}, "nezname-pole"),
    "změna není pole": (
        {"added": [], "edited": {"poliklinika-pisek": "nic"}, "removed": []}, "nezname-pole"),
    "removed není seznam": (
        {"added": [], "edited": {}, "removed": {"a": "b"}}, "nezname-pole"),

    # ------------------------------------------------------------- id
    "položka bez id": (pridana(id=""), "vadne-id"),
    "položka s cestou v id": (pridana(id="../../etc/passwd"), "vadne-id"),
    "id s velkými písmeny": (pridana(id="Nova-Kotelna"), "vadne-id"),
    "id s mezerou": (pridana(id="nova kotelna"), "vadne-id"),
    "id s tečkou": (pridana(id="nova.kotelna"), "vadne-id"),
    "id s pomlčkou na konci": (pridana(id="nova-"), "vadne-id"),
    "id není text": (pridana(id=7), "vadne-id"),
    "klíč změny není slug": (
        {"added": [], "edited": {"Velké ID": {"plocha": "1 m²"}}, "removed": []}, "vadne-id"),
    "smazané id není slug": (
        {"added": [], "edited": {}, "removed": ["../../etc"]}, "vadne-id"),
    "smazané id není text": ({"added": [], "edited": {}, "removed": [7]}, "vadne-id"),

    # -------------------------------------------------------- hodnoty
    "text není text": (pridana(perex=["a"]), "vadna-hodnota"),
    "text je null": (pridana(perex=None), "vadna-hodnota"),
    "dlouhý název": (pridana(nazev="@@HODNOTA_DLOUHA@@"), "dlouhy-text"),
    "dlouhý perex ve změně": (zmenena(perex="@@HODNOTA_DLOUHA@@"), "dlouhy-text"),
    "rozsah není seznam": (pridana(rozsah="Demontáž"), "vadna-hodnota"),
    "položka rozsahu není text": (pridana(rozsah=[["a"]]), "vadna-hodnota"),
    "dlouhá položka rozsahu": (pridana(rozsah=["@@HODNOTA_DLOUHA@@"]), "dlouhy-text"),
    "sto jedna položek rozsahu": (pridana(rozsah=["x"] * 101), "vadna-hodnota"),
    "kategorie není seznam": (pridana(kategorie={"a": 1}), "vadna-hodnota"),
    "motiv není číslo": (pridana(motiv="modry"), "vadna-hodnota"),
    "motiv je pole": (pridana(motiv=[1]), "vadna-hodnota"),

    # ---------------------------------------------------------- fotky
    "devět fotek": (pridana(fotky=[fotka(id=f"f{i}") for i in range(9)]), "moc-fotek"),
    "devět fotek ve změně": (
        {"added": [], "edited": {"poliklinika-pisek": {
            "fotky": [fotka(id=f"f{i}") for i in range(9)]}}, "removed": []}, "moc-fotek"),
    "fotky nejsou seznam": (pridana(fotky={"a": 1}), "vadna-fotka"),
    "fotka není pole": (pridana(fotky=["media/a.webp"]), "vadna-fotka"),
    "fotka jako data URL": (
        pridana(fotky=[fotka(dataUrl="data:image/jpeg;base64,/9j/4AAQSkZJRg==")]),
        "vadna-fotka"),
    "data URL ve změně": (
        {"added": [], "edited": {"poliklinika-pisek": {"fotky": [
            fotka(dataUrl="data:image/png;base64,iVBORw0KGgo=")]}}, "removed": []},
        "vadna-fotka"),
    "fotka mimo media": (pridana(fotky=[fotka(dataUrl="/etc/passwd")]), "vadna-fotka"),
    "fotka s cestou nahoru": (
        pridana(fotky=[fotka(dataUrl="media/../config/config.php")]), "vadna-fotka"),
    "fotka z cizího webu": (
        pridana(fotky=[fotka(dataUrl="https://cizi.example/x.webp")]), "vadna-fotka"),
    "fotka bez dataUrl": (
        pridana(fotky=[{k: v for k, v in PLATNA_FOTKA.items() if k != "dataUrl"}]),
        "vadna-fotka"),
    "fotka s prázdným dataUrl": (pridana(fotky=[fotka(dataUrl="")]), "vadna-fotka"),
    "fotka s cizím polem": (pridana(fotky=[fotka(skript="x")]), "vadna-fotka"),
    "fotka bez id": (pridana(fotky=[fotka(id="")]), "vadna-fotka"),
    "rozměr fotky není číslo": (pridana(fotky=[fotka(sirka="široká")]), "vadna-fotka"),
    "záporné bajty": (pridana(fotky=[fotka(bajty=-1)]), "vadna-fotka"),
    "dlouhý název fotky": (pridana(fotky=[fotka(nazev="n" * 201)]), "vadna-fotka"),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Obsah\MezeRealizaci;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

$dosad = static function (mixed $co) use (&$dosad): mixed {
    if (is_array($co)) {
        $ven = [];
        foreach ($co as $k => $v) {
            $ven[$k] = $dosad($v);
        }
        return $ven;
    }
    if ($co === '@@HODNOTA_PRESNE@@') {
        return str_repeat('a', {MAX_HODNOTA});
    }
    if ($co === '@@HODNOTA_DLOUHA@@') {
        return str_repeat('a', {MAX_HODNOTA} + 1);
    }
    return $co;
};

$ven = [];
foreach ($vstup as $klic => $pripad) {
    $realizace = $dosad($pripad);
    /* JSON nemá pole s dírou: 'added' se tu přepíše na klíč 1, aby se dalo
       ověřit, že seznam s dírou neprojde. */
    if ($klic === 'added je seznam s dírou') {
        $realizace['added'] = [1 => $realizace['added'][1] ?? $realizace['added'][0]];
    }
    $kopie = $realizace;
    $vysledek = MezeRealizaci::zkontroluj($realizace);
    $ven[$klic] = [
        'ok' => $vysledek['ok'] ?? null,
        'chyba' => $vysledek['chyba'] ?? null,
        'detail' => $vysledek['detail'] ?? null,
        'nemutuje' => $kopie === $realizace,
    ];
}
$ven['__meze'] = ['hodnota' => MezeRealizaci::MAX_HODNOTA, 'fotek' => MezeRealizaci::MAX_FOTEK];
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("meze-realizaci")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps(
        {k: r for k, (r, _) in PRIPADY.items()}, ensure_ascii=False), "utf8")
    program = dir / "program.php"
    program.write_text(
        PROGRAM.lstrip().replace("{KOREN}", str(KOREN)).replace("{MAX_HODNOTA}", str(MAX_HODNOTA)),
        "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(vstup)], capture_output=True, text=True, timeout=120)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


@pytest.mark.parametrize("popis", list(PRIPADY))
def test_meze_realizaci(popis, v):
    _, cekano = PRIPADY[popis]
    o = v[popis]
    if cekano is None:
        assert o["ok"] is True, (
            f"{popis}: to, co administrace opravdu posílá, bylo odmítnuto "
            f"({o['chyba']}, {o['detail']})"
        )
    else:
        assert o["ok"] is False, f"{popis}: prošlo to, co projít nemělo"
        assert o["chyba"] == cekano, f"{popis}: čekán kód {cekano}, přišlo {o['chyba']}"


def test_vstup_se_nemeni(v):
    for popis, o in v.items():
        if popis == "__meze":
            continue
        assert o["nemutuje"], f"{popis}: MezeRealizaci přepsaly vstupní pole"


def test_meze_jsou_ty_ze_zadani(v):
    assert v["__meze"]["hodnota"] == MAX_HODNOTA
    assert v["__meze"]["fotek"] == MAX_FOTEK


def test_odmitnuti_rekne_cim(v):
    assert "skript" in str(v["cizí pole v nové položce"]["detail"]), (
        "detail nejmenuje cizí pole, administrace nemá co ukázat"
    )
    assert "navic" in str(v["cizí klíč v realizacích"]["detail"])
    assert "fotky" in str(v["devět fotek"]["detail"]) or "8" in str(v["devět fotek"]["detail"])


def test_edited_se_kontroluje_stejne_jako_added(v):
    """Nejlacinější obchvat: poslat fotku jako změnu základní položky."""
    assert v["data URL ve změně"]["ok"] is False
    assert v["devět fotek ve změně"]["ok"] is False
    assert v["cizí pole ve změně"]["ok"] is False
    assert v["dlouhý perex ve změně"]["ok"] is False
