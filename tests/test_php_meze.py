"""Akceptační test C-032 — App\\Obsah\\Meze (co administrace smí uložit).

Nález kola 2 (K2): PUT /api/stav vzal cokoli. Dvě stě tisíc znaků pod
vymyšleným klíčem se uložilo a stav administrace se vkládá do KAŽDÉ stránky
webu (`window.GAT_STAV`) — z 971 bajtů se stalo 200 kB na každé stránce.
Vložený text se nevykreslí (klíč nikdo nezná) a je escapovaný, takže to není
díra; je to ale způsob, jak omylem (vložením celého dokumentu do pole) nebo
schválně zpomalit celý web.

Tahle brána hlídá první polovinu: velikost, nejvyšší úroveň a texty.
Realizace a fotky má na starost App\\Obsah\\MezeRealizaci (C-033, brána
tests/test_php_meze_realizaci.py) — Meze se jí musí zeptat, ne si pravidla
opisovat.

Pravidlo:
- Projde jen to, co administrace opravdu posílá: jazyky cs/en/de a klíče ze
  seznamu `admin-klice.json` plus dynamické klíče nových realizací.
- Hodnota textu nejvýš MAX_HODNOTA znaků, celý stav nejvýš MAX_CELKEM bajtů.
- Nic se nezahazuje potichu: každé porušení vrátí ['ok' => false] s krátkým
  kódem, aby administrace mohla říct, co se nepovedlo.
- Prázdný seznam klíčů znamená „seznam nemám" — pak se klíče nehlídají (aby
  chybějící soubor s klíči neshodil celou administraci), limity platí dál.
- Na žádný vstup se nesmí zhroutit: ani na stav, který nejde do JSONu.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

MAX_HODNOTA = 20000
MAX_CELKEM = 1048576

KLICE = [
    "kontakt.formular.titulek",
    "home.duvody.titulek",
    "realizace.polozky.poliklinika-pisek.nazev",
]

PLATNA_FOTKA = {
    "id": "f1",
    "nazev": "kotelna.jpg",
    "typ": "image/webp",
    "sirka": 1600,
    "vyska": 1067,
    "bajty": 180000,
    "dataUrl": "media/3f2a9c.webp",
}

PRAZDNE_REALIZACE = {"added": [], "edited": {}, "removed": []}


def stav(texts=None, realizace=None, **navic) -> dict:
    s = {
        "texts": texts if texts is not None else {},
        "realizace": realizace if realizace is not None else dict(PRAZDNE_REALIZACE),
        "updatedAt": "2026-10-23T18:30:00.000Z",
    }
    s.update(navic)
    return s


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


# popis -> (stav, klíče, čekaný kód chyby nebo None = projde)
PRIPADY: dict[str, tuple[object, list[str], str | None]] = {
    # ------------------------------------------------------------ projde
    "prázdný stav": (stav(), KLICE, None),
    "stav bez klíčů vůbec": ({}, KLICE, None),
    "jen texty, nic jiného": (
        {"texts": {"cs": {"kontakt.formular.titulek": "Napište nám"}}}, KLICE, None),
    "známý klíč ve třech jazycích": (stav({
        "cs": {"kontakt.formular.titulek": "Napište nám"},
        "en": {"kontakt.formular.titulek": "Write to us"},
        "de": {"kontakt.formular.titulek": "Schreiben Sie uns"},
    }), KLICE, None),
    "dynamický klíč nové realizace": (stav({
        "cs": {"realizace.polozky.nova-kotelna-pisek.nazev": "Nová kotelna"},
    }), KLICE, None),
    "dynamický klíč ve všech pěti polích": (stav({
        "cs": {
            "realizace.polozky.nova-kotelna-pisek.misto": "Písek",
            "realizace.polozky.nova-kotelna-pisek.perex": "Perex.",
            "realizace.polozky.nova-kotelna-pisek.zadani": "Zadání.",
            "realizace.polozky.nova-kotelna-pisek.vysledek": "Výsledek.",
        },
    }), KLICE, None),
    "dynamický klíč s číslovaným podklíčem": (stav({
        "cs": {
            "realizace.polozky.nova-kotelna-pisek.rozsah.r1": "Demontáž",
            "realizace.polozky.nova-kotelna-pisek.technologie.t12": "Čerpadlo",
        },
    }), KLICE, None),
    "hodnota na hranici délky": (
        stav({"cs": {"kontakt.formular.titulek": "@@HODNOTA_PRESNE@@"}}), KLICE, None),
    "prázdný seznam klíčů klíče nehlídá": (
        stav({"cs": {"vymysleny.klic": "cokoli"}}), [], None),
    "prázdný text smí (maže klíč)": (
        stav({"cs": {"kontakt.formular.titulek": ""}}), KLICE, None),
    "updatedAt smí být null": (stav(updatedAt=None), KLICE, None),
    "celá nová realizace projde dál": (
        stav(realizace={"added": [polozka()], "edited": {}, "removed": []}), KLICE, None),

    # ------------------------------------------------------- neprojde
    "neznámý klíč": (
        stav({"cs": {"vymysleny.klic": "cokoli"}}), KLICE, "neznamy-klic"),
    "neznámý klíč pod tvarem realizace": (
        stav({"cs": {"realizace.polozky.nova.vymyslene": "cokoli"}}), KLICE, "neznamy-klic"),
    "dynamický klíč bez pole": (
        stav({"cs": {"realizace.polozky.nova": "cokoli"}}), KLICE, "neznamy-klic"),
    "dynamický podklíč s tečkou": (
        stav({"cs": {"realizace.polozky.nova.rozsah.r1.a": "x"}}), KLICE, "neznamy-klic"),
    "id realizace v klíči s velkými písmeny": (
        stav({"cs": {"realizace.polozky.Nova-Kotelna.nazev": "x"}}), KLICE, "neznamy-klic"),
    "id realizace v klíči s tečkou": (
        stav({"cs": {"realizace.polozky.nova.kotelna.nazev": "x"}}), KLICE, "neznamy-klic"),
    "id realizace v klíči s lomítkem": (
        stav({"cs": {"realizace.polozky.a/b.nazev": "x"}}), KLICE, "neznamy-klic"),
    "neznámý jazyk": (
        stav({"fr": {"kontakt.formular.titulek": "Bonjour"}}), KLICE, "neznamy-jazyk"),
    "jazyk s velkým písmenem": (
        stav({"CS": {"kontakt.formular.titulek": "Ahoj"}}), KLICE, "neznamy-jazyk"),
    "texty jazyka nejsou pole": (
        stav({"cs": "Napište nám"}), KLICE, "vadna-hodnota"),
    "texty nejsou pole": (stav(texts="nic"), KLICE, "vadna-hodnota"),
    "hodnota není text": (
        stav({"cs": {"kontakt.formular.titulek": {"a": 1}}}), KLICE, "vadna-hodnota"),
    "hodnota je číslo": (
        stav({"cs": {"kontakt.formular.titulek": 42}}), KLICE, "vadna-hodnota"),
    "hodnota je null": (
        stav({"cs": {"kontakt.formular.titulek": None}}), KLICE, "vadna-hodnota"),
    "hodnota o znak delší": (
        stav({"cs": {"kontakt.formular.titulek": "@@HODNOTA_DLOUHA@@"}}), KLICE, "dlouhy-text"),
    "celý stav je moc velký": ("@@VELKY_STAV@@", KLICE, "moc-dat"),
    "stav, který nejde do JSONu": ("@@SPATNE_UTF8@@", KLICE, "vadna-hodnota"),
    "cizí klíč na nejvyšší úrovni": (
        stav(novinky={"cs": {}}), KLICE, "nezname-pole"),
    "updatedAt není text": (stav(updatedAt=["ted"]), KLICE, "vadna-hodnota"),
    "updatedAt je román": (stav(updatedAt="x" * 65), KLICE, "vadna-hodnota"),

    # ----- tohle nerozhoduje Meze sama, ptá se MezeRealizaci (C-033) -----
    "cizí pole u realizace (přes MezeRealizaci)": (
        stav(realizace={"added": [polozka(skript="<img src=x>")], "edited": {}, "removed": []}),
        KLICE, "nezname-pole"),
    "fotka jako data URL (přes MezeRealizaci)": (
        stav(realizace={"added": [polozka(fotky=[dict(
            PLATNA_FOTKA, dataUrl="data:image/jpeg;base64,/9j/4AAQSkZJRg==")])],
            "edited": {}, "removed": []}), KLICE, "vadna-fotka"),
    "vadné id realizace (přes MezeRealizaci)": (
        stav(realizace={"added": [polozka(id="../../etc/passwd")], "edited": {},
                        "removed": []}), KLICE, "vadne-id"),
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Obsah\Meze;

$vstup = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);

/* Velké a nehezké vstupy se nevozí v JSONu, vyrobí se tady — jinak by
   akceptace tahala megabajt textu v souboru. */
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

$velkyStav = static function (): array {
    $texty = [];
    for ($i = 0; $i < 80; $i++) {
        $texty['klic' . $i] = str_repeat('b', 19000);
    }
    return [
        'texts' => ['cs' => $texty],
        'realizace' => ['added' => [], 'edited' => [], 'removed' => []],
        'updatedAt' => '2026-10-23T18:30:00.000Z',
    ];
};

$ven = [];
foreach ($vstup as $klic => $pripad) {
    if ($pripad['stav'] === '@@VELKY_STAV@@') {
        $stav = $velkyStav();
    } elseif ($pripad['stav'] === '@@SPATNE_UTF8@@') {
        // Bajt, který v UTF-8 nemá co dělat: json_encode na něm selže a
        // strlen(false) by pod strict_types byla rovnou TypeError.
        $stav = ['texts' => ['cs' => ['kontakt.formular.titulek' => "ahoj \xff\xfe"]]];
    } else {
        $stav = $dosad($pripad['stav']);
    }
    $kopie = $stav;
    $klice = $pripad['klice'];
    $kopieKlicu = $klice;
    $vysledek = Meze::stav($stav, $klice);
    $ven[$klic] = [
        'ok' => $vysledek['ok'] ?? null,
        'chyba' => $vysledek['chyba'] ?? null,
        'detail' => $vysledek['detail'] ?? null,
        'nemutuje' => $kopie === $stav && $kopieKlicu === $klice,
    ];
}
$ven['__meze'] = ['hodnota' => Meze::MAX_HODNOTA, 'celkem' => Meze::MAX_CELKEM];
echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("meze")
    vstup = dir / "vstup.json"
    vstup.write_text(json.dumps(
        {k: {"stav": s, "klice": kl} for k, (s, kl, _) in PRIPADY.items()},
        ensure_ascii=False), "utf8")
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
def test_meze_stavu(popis, v):
    *_, cekano = PRIPADY[popis]
    o = v[popis]
    if cekano is None:
        assert o["ok"] is True, (
            f"{popis}: stav, který administrace opravdu posílá, byl odmítnut "
            f"({o['chyba']}, {o['detail']})"
        )
    else:
        assert o["ok"] is False, f"{popis}: prošlo to, co projít nemělo"
        assert o["chyba"] == cekano, f"{popis}: čekán kód {cekano}, přišlo {o['chyba']}"


def test_vstup_se_nemeni(v):
    for popis, o in v.items():
        if popis == "__meze":
            continue
        assert o["nemutuje"], f"{popis}: Meze přepsaly pole, které jim dal volající"


def test_meze_jsou_ty_ze_zadani(v):
    assert v["__meze"]["hodnota"] == MAX_HODNOTA
    assert v["__meze"]["celkem"] == MAX_CELKEM


def test_odmitnuti_rekne_cim(v):
    """Administrace musí mít co ukázat člověku — jinak jen „něco se nepovedlo"."""
    assert "vymysleny.klic" in str(v["neznámý klíč"]["detail"]), (
        "u neznámého klíče detail ten klíč nejmenuje"
    )
    assert "novinky" in str(v["cizí klíč na nejvyšší úrovni"]["detail"]), (
        "u cizího pole detail to pole nejmenuje"
    )
    assert "fr" in str(v["neznámý jazyk"]["detail"]), (
        "u neznámého jazyka detail ten jazyk nejmenuje"
    )


def test_realizace_rozhoduje_meze_realizaci(v):
    """Meze si pravidla realizací neopisují — zeptají se C-033. Kdyby na
    realizace nekoukaly vůbec, prošla by data URL fotky a tím to, kvůli čemu
    celý nález K2 je."""
    for popis in ("cizí pole u realizace (přes MezeRealizaci)",
                  "fotka jako data URL (přes MezeRealizaci)",
                  "vadné id realizace (přes MezeRealizaci)"):
        assert v[popis]["ok"] is False, f"{popis}: Meze realizace vůbec nekontrolují"
    assert v["celá nová realizace projde dál"]["ok"] is True, (
        "běžná nová realizace neprošla — administrace by nepřidala realizaci"
    )


def test_dve_sta_tisic_znaku_z_nalezu_neprojde(v):
    """Přesně to, co našel nezávislý test: dlouhý text pod cizím klíčem."""
    assert v["neznámý klíč"]["ok"] is False
    assert v["hodnota o znak delší"]["ok"] is False
    assert v["celý stav je moc velký"]["chyba"] == "moc-dat"
