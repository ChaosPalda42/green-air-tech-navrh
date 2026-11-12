"""Brána — App\\Obsah\\MezeLidi: co smí přijít z administrace v klíči `lide`.

Tým se dá v administraci doplnit, upravit i zkrátit, a stav se vkládá do
KAŽDÉ stránky webu. Platí tu proto totéž co u realizací (nález K2): bez
mezí by stránky nafoukl kdokoli, kdo pošle vlastní tělo požadavku.

Měří se to, co dialog administrace skutečně skládá (jméno, telefon, e-mail,
zkratka, cesta k fotce), a hlavně to, co se dá poslat místo toho:
- fotka jako data URL — obrázek v textu stavu, tedy v každé stránce,
- cesta mimo `media/` nebo s `..` — čtení odkudkoli ze serveru,
- cizí pole, dvakrát stejné id, prázdné jméno, stovky lidí.

Změna (`edited`) se kontroluje stejně jako přidání (`added`); kdyby ne,
stačí poslat fotku jako změnu základního člověka a pravidlo je k ničemu.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

MAX_PRIDANYCH = 30
MAX_ODEBRANYCH = 100


def osoba(**navic) -> dict:
    o = {
        "id": "zofie-novakova",
        "jmeno": "Žofie Nováková",
        "telefon": "+420 123 456 789",
        "telefonHref": "+420123456789",
        "email": "novakova@greenairtech.cz",
        "inicialy": "ŽN",
        "fotka": "media/zofie-novakova-3f2a9c.webp",
    }
    o.update(navic)
    return o


def pridany(**navic) -> dict:
    return {"added": [osoba(**navic)], "edited": {}, "removed": []}


def zmeneny(**navic) -> dict:
    return {"added": [], "edited": {"jan-bauska": navic}, "removed": []}


# popis -> (lide, čekaný kód chyby nebo None = projde)
PRIPADY: dict[str, tuple[object, str | None]] = {
    # ------------------------------------------------------------ projde
    "prázdný tým": ({"added": [], "edited": {}, "removed": []}, None),
    "žádné klíče vůbec": ({}, None),
    "celý nový člověk": (pridany(), None),
    "nový člověk bez fotky": (pridany(fotka=""), None),
    "nový člověk jen se jménem": ({"added": [{"id": "a-b", "jmeno": "A B"}],
                                   "edited": {}, "removed": []}, None),
    "třicet přidaných": ({"added": [osoba(id=f"clovek-{i}") for i in range(MAX_PRIDANYCH)],
                          "edited": {}, "removed": []}, None),
    "změna telefonu": (zmeneny(telefon="+420 777 111 222"), None),
    "změna jen fotky": (zmeneny(fotka="media/jan-bauska-99aa11.webp"), None),
    "odebraný člověk": ({"added": [], "edited": {}, "removed": ["jan-bauska"]}, None),
    "sto odebraných": ({"added": [], "edited": {},
                        "removed": [f"clovek-{i}" for i in range(MAX_ODEBRANYCH)]}, None),
    "jméno na hranici délky": (pridany(jmeno="@@JMENO_PRESNE@@"), None),

    # ------------------------------------------------ cizí a vadná pole
    "cizí klíč v týmu": ({"added": [], "edited": {}, "removed": [], "navic": []},
                         "nezname-pole"),
    "cizí pole u nového člověka": (pridany(role="Jednatel"), "nezname-pole"),
    "cizí pole ve změně": (zmeneny(skript="<img src=x>"), "nezname-pole"),
    "added není seznam": ({"added": "nic", "edited": {}, "removed": []}, "vadna-hodnota"),
    "edited není pole": ({"added": [], "edited": "nic", "removed": []}, "vadna-hodnota"),
    "removed není seznam": ({"added": [], "edited": {}, "removed": "nic"}, "vadna-hodnota"),
    "člověk v added není pole": ({"added": ["Žofie"], "edited": {}, "removed": []},
                                 "vadny-clovek"),
    "změna není pole": ({"added": [], "edited": {"jan-bauska": "nic"}, "removed": []},
                        "vadny-clovek"),

    # ------------------------------------------------------------- id
    "člověk bez id": (pridany(id=""), "vadne-id"),
    "id s cestou": (pridany(id="../../etc/passwd"), "vadne-id"),
    "id s velkými písmeny": (pridany(id="Zofie-Novakova"), "vadne-id"),
    "id s mezerou": (pridany(id="zofie novakova"), "vadne-id"),
    "id s tečkou": (pridany(id="zofie.novakova"), "vadne-id"),
    "id s pomlčkou na konci": (pridany(id="zofie-"), "vadne-id"),
    "id není text": (pridany(id=7), "vadne-id"),
    "dvakrát stejné id": ({"added": [osoba(), osoba()], "edited": {}, "removed": []},
                          "dvakrat-id"),
    "klíč změny není slug": ({"added": [], "edited": {"Velké ID": {"telefon": "1"}},
                              "removed": []}, "vadne-id"),
    "odebrané id není slug": ({"added": [], "edited": {}, "removed": ["../../etc"]},
                              "vadne-id"),
    "odebrané id není text": ({"added": [], "edited": {}, "removed": [7]}, "vadne-id"),

    # ------------------------------------------------------------ jméno
    "nový člověk bez jména": ({"added": [{"id": "a-b"}], "edited": {}, "removed": []},
                              "vadny-clovek"),
    "prázdné jméno": (pridany(jmeno=""), "vadny-clovek"),
    "jméno jen z mezer": (pridany(jmeno="   "), "vadny-clovek"),
    "prázdné jméno ve změně": (zmeneny(jmeno=""), "vadny-clovek"),
    "jméno není text": (pridany(jmeno=["Žofie"]), "vadne-jmeno-nebo-hodnota"),

    # ---------------------------------------------------------- hodnoty
    "telefon není text": (pridany(telefon=420123456789), "vadna-hodnota"),
    "e-mail je null": (pridany(email=None), "vadna-hodnota"),
    "dlouhé jméno": (pridany(jmeno="@@JMENO_DLOUHE@@"), "dlouhy-text"),
    "dlouhý e-mail": (pridany(email="e" * 191), "dlouhy-text"),
    "dlouhá zkratka": (pridany(inicialy="ABCDE"), "dlouhy-text"),
    "dlouhý e-mail ve změně": (zmeneny(email="e" * 191), "dlouhy-text"),

    # ------------------------------------------------------------ fotka
    "fotka jako data URL": (pridany(fotka="data:image/jpeg;base64,/9j/4AAQSkZJRg=="),
                            "vadna-fotka"),
    "data URL ve změně": (zmeneny(fotka="data:image/png;base64,iVBORw0KGgo="),
                          "vadna-fotka"),
    "fotka mimo media": (pridany(fotka="/etc/passwd"), "vadna-fotka"),
    "fotka s cestou nahoru": (pridany(fotka="media/../config/config.php"), "vadna-fotka"),
    "fotka v podsložce": (pridany(fotka="media/tajne/x.webp"), "vadna-fotka"),
    "fotka z cizího webu": (pridany(fotka="https://cizi.example/x.webp"), "vadna-fotka"),
    "fotka jen media/": (pridany(fotka="media/"), "vadna-fotka"),

    # -------------------------------------------------------- množství
    "třicet jeden přidaných": (
        {"added": [osoba(id=f"clovek-{i}") for i in range(MAX_PRIDANYCH + 1)],
         "edited": {}, "removed": []}, "moc-dat"),
    "sto jeden odebraných": (
        {"added": [], "edited": {},
         "removed": [f"clovek-{i}" for i in range(MAX_ODEBRANYCH + 1)]}, "moc-dat"),
    "moc změn": (
        {"added": [], "edited": {f"clovek-{i}": {"telefon": "1"}
                                 for i in range(MAX_PRIDANYCH + MAX_ODEBRANYCH + 1)},
         "removed": []}, "moc-dat"),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require 'KOREN/web/app/Jadro/Autoload.php';

use App\Obsah\MezeLidi;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

$dosad = static function (mixed $co) use (&$dosad): mixed {
    if (is_array($co)) {
        $ven = [];
        foreach ($co as $k => $v) {
            $ven[$k] = $dosad($v);
        }
        return $ven;
    }
    if ($co === '@@JMENO_PRESNE@@') {
        return str_repeat('a', 120);
    }
    if ($co === '@@JMENO_DLOUHE@@') {
        return str_repeat('a', 121);
    }
    return $co;
};

$ven = [];
foreach ($vstup as $klic => $pripad) {
    $lide = $dosad($pripad);
    $kopie = $lide;
    $vysledek = MezeLidi::zkontroluj($lide);
    $ven[$klic] = [
        'ok' => $vysledek['ok'] ?? null,
        'chyba' => $vysledek['chyba'] ?? null,
        'detail' => $vysledek['detail'] ?? null,
        'nemutuje' => $kopie === $lide,
    ];
}
$ven['__meze'] = [
    'pridanych' => MezeLidi::MAX_PRIDANYCH,
    'odebranych' => MezeLidi::MAX_ODEBRANYCH,
];
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("meze-lidi")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps(
        {k: r for k, (r, _) in PRIPADY.items()}, ensure_ascii=False), "utf8")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("KOREN", str(KOREN)), "utf8")
    hotovo = subprocess.run(
        ["php", str(program), str(vstup)], capture_output=True, text=True, timeout=120)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


@pytest.mark.parametrize("popis", list(PRIPADY))
def test_meze_lidi(popis, v):
    _, cekano = PRIPADY[popis]
    o = v[popis]
    if cekano is None:
        assert o["ok"] is True, (
            f"{popis}: to, co administrace opravdu posílá, bylo odmítnuto "
            f"({o['chyba']}, {o['detail']})"
        )
    elif cekano == "vadne-jmeno-nebo-hodnota":
        # jméno, které není text, může spadnout na jménu i na typu hodnoty
        assert o["ok"] is False, f"{popis}: prošlo to, co projít nemělo"
        assert o["chyba"] in ("vadny-clovek", "vadna-hodnota"), o["chyba"]
    else:
        assert o["ok"] is False, f"{popis}: prošlo to, co projít nemělo"
        assert o["chyba"] == cekano, f"{popis}: čekán kód {cekano}, přišlo {o['chyba']}"


def test_vstup_se_nemeni(v):
    for popis, o in v.items():
        if popis == "__meze":
            continue
        assert o["nemutuje"], f"{popis}: MezeLidi přepsaly vstupní pole"


def test_meze_jsou_ty_ze_zadani(v):
    assert v["__meze"]["pridanych"] == MAX_PRIDANYCH
    assert v["__meze"]["odebranych"] == MAX_ODEBRANYCH


def test_odmitnuti_rekne_cim(v):
    assert "role" in str(v["cizí pole u nového člověka"]["detail"])
    assert "navic" in str(v["cizí klíč v týmu"]["detail"])
    assert "zofie-novakova" in str(v["dvakrát stejné id"]["detail"])


def test_zmena_se_kontroluje_stejne_jako_pridani(v):
    """Nejlacinější obchvat: poslat fotku jako změnu základního člověka."""
    assert v["data URL ve změně"]["ok"] is False
    assert v["cizí pole ve změně"]["ok"] is False
    assert v["dlouhý e-mail ve změně"]["ok"] is False
    assert v["prázdné jméno ve změně"]["ok"] is False
