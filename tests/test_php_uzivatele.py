"""Akceptační test C-018 — App\\Auth\\Uzivatele (kdo se dostane do administrace a co smí).

Pravidlo, které brána vynucuje, je OPSANÉ z toho, co ukázka slibuje klientovi
(data/content/cs.json → admin.uzivatele):
  Správce       … „Všechno včetně uživatelů a statistik“
  Editor obsahu … „Texty, realizace a novinky“
  Autor článků  … „Jen novinky a články“
a z poznámky „na ostré verzi se každému pošle pozvánka a heslo si nastaví sám“.

Test se nikdy neptá kódu, jestli je výsledek v pořádku — matice práv je tady.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

OBLASTI = ["texty", "realizace", "novinky", "uzivatele", "statistiky"]
MATICE = {
    "spravce": {"texty", "realizace", "novinky", "uzivatele", "statistiky"},
    "editor": {"texty", "realizace", "novinky"},
    "autor": {"novinky"},
}

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Auth\Uzivatele;

$matice = [];
foreach (['spravce', 'editor', 'autor', 'neznama', ''] as $role) {
    foreach (['texty', 'realizace', 'novinky', 'uzivatele', 'statistiky', 'vymyslene'] as $oblast) {
        $matice[$role . '|' . $oblast] = Uzivatele::smi($role, $oblast);
    }
}

$hash = Uzivatele::hash('Tajne-Heslo-123');
$hash2 = Uzivatele::hash('Tajne-Heslo-123');
$uz = ['jmeno' => 'pavel', 'heslo_hash' => $hash, 'role' => 'spravce', 'aktivni' => 1];

$poz1 = Uzivatele::pozvanka();
$poz2 = Uzivatele::pozvanka();

echo json_encode([
    'oblasti' => Uzivatele::OBLASTI,
    'role' => array_keys(Uzivatele::ROLE),
    'matice' => $matice,
    'hash_neni_heslo' => $hash !== 'Tajne-Heslo-123',
    'hash_je_jiny' => $hash !== $hash2,
    'hash_delka' => strlen($hash) >= 50,
    'overi_spravne' => Uzivatele::overHeslo($uz, 'Tajne-Heslo-123'),
    'odmitne_spatne' => Uzivatele::overHeslo($uz, 'tajne-heslo-123'),
    'odmitne_prazdne' => Uzivatele::overHeslo($uz, ''),
    'odmitne_bez_hashe' => Uzivatele::overHeslo(['jmeno' => 'x'], 'cokoli'),
    'odmitne_neaktivniho' => Uzivatele::overHeslo(['heslo_hash' => $hash, 'aktivni' => 0], 'Tajne-Heslo-123'),
    'sila' => [
        'dobre' => Uzivatele::zkontrolujHeslo('Tajne-Heslo-123'),
        'kratke' => Uzivatele::zkontrolujHeslo('Krat1'),
        'prazdne' => Uzivatele::zkontrolujHeslo(''),
        'mezery' => Uzivatele::zkontrolujHeslo('            '),
        'dlouhe_ale_jen_pismena' => Uzivatele::zkontrolujHeslo('obyceajneheslo'),
        'ohromne' => Uzivatele::zkontrolujHeslo(str_repeat('a1B', 200)),
        /* Hranice je 12 znaků — tolik slibuje instalátor i administrace.
           Tester našel, že kód pouštěl osmiznakové a hláska mluvila o 12. */
        'jedenact' => Uzivatele::zkontrolujHeslo('Abcdefghij1'),
        'dvanact' => Uzivatele::zkontrolujHeslo('Abcdefghij12'),
        'osm' => Uzivatele::zkontrolujHeslo('Abcdefg1'),
    ],
    'zapis' => [
        'dobry' => Uzivatele::zkontroluj(['jmeno' => 'Pavel Janda', 'email' => 'pavel@greenairtech.cz', 'role' => 'editor']),
        'bez_jmena' => Uzivatele::zkontroluj(['jmeno' => '  ', 'email' => 'pavel@greenairtech.cz', 'role' => 'editor']),
        'spatny_email' => Uzivatele::zkontroluj(['jmeno' => 'Pavel', 'email' => 'pavel@', 'role' => 'editor']),
        'bez_emailu' => Uzivatele::zkontroluj(['jmeno' => 'Pavel', 'email' => '', 'role' => 'editor']),
        'cizi_role' => Uzivatele::zkontroluj(['jmeno' => 'Pavel', 'email' => 'p@g.cz', 'role' => 'kral']),
        'prazdne' => Uzivatele::zkontroluj([]),
    ],
    'pozvanka' => [
        'token1' => $poz1['token'],
        'token2' => $poz2['token'],
        'do1' => $poz1['do'],
    ],
    'odmitne_neznamy_ucet' => Uzivatele::overHeslo(null, 'Tajne-Heslo-123'),
    /* Časy ověření hesla. Měří se střední hodnota z několika pokusů, aby
       jedno zdržení stroje nerozhodovalo. Pravidlo je v akceptaci (Pythonu):
       neznámý účet nesmí odpovědět výrazně rychleji než známý — jinak se dá
       z času poznat, která jména v administraci existují. */
    'casy' => (static function () use ($hash): array {
        $uz = ['jmeno' => 'pavel', 'heslo_hash' => $hash, 'aktivni' => 1];
        $pripady = [
            'znamy_ucet_spatne_heslo' => static fn (): bool => Uzivatele::overHeslo($uz, 'spatne-heslo-123'),
            'neznamy_ucet' => static fn (): bool => Uzivatele::overHeslo(null, 'spatne-heslo-123'),
            'ucet_bez_hashe' => static fn (): bool => Uzivatele::overHeslo(['jmeno' => 'x'], 'spatne-heslo-123'),
            'neaktivni_ucet' => static fn (): bool => Uzivatele::overHeslo(
                ['heslo_hash' => $hash, 'aktivni' => 0], 'spatne-heslo-123'),
        ];
        $ven = [];
        foreach ($pripady as $klic => $volani) {
            $mereni = [];
            for ($i = 0; $i < 5; $i++) {
                $zacatek = hrtime(true);
                $volani();
                $mereni[] = (hrtime(true) - $zacatek) / 1e6;
            }
            sort($mereni);
            $ven[$klic] = $mereni[2];   // prostřední z pěti
        }
        return $ven;
    })(),
    'pozvanka_plati' => Uzivatele::pozvankaPlati($poz1),
    'pozvanka_propadla' => Uzivatele::pozvankaPlati(['token' => $poz1['token'], 'do' => '2020-01-01 00:00:00']),
    'pozvanka_bez_tokenu' => Uzivatele::pozvankaPlati(['do' => $poz1['do']]),
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    dir = tmp_path_factory.mktemp("uzivatele")
    program = dir / "program.php"
    program.write_text(PROGRAM.lstrip().replace("{KOREN}", str(KOREN)), "utf8")
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_role_a_oblasti_jsou_ty_ze_zadani(v):
    assert sorted(v["oblasti"]) == sorted(OBLASTI)
    assert sorted(v["role"]) == ["autor", "editor", "spravce"]


def test_matice_prav_odpovida_tomu_co_ukazka_slibuje(v):
    spatne = []
    for role, smi in MATICE.items():
        for oblast in OBLASTI:
            cekano = oblast in smi
            mam = v["matice"][f"{role}|{oblast}"]
            if mam is not cekano:
                spatne.append(f"{role} + {oblast}: čekáno {cekano}, přišlo {mam}")
    assert not spatne, "\n".join(spatne)


def test_neznama_role_nebo_oblast_nesmi_nic(v):
    for role in ("neznama", ""):
        for oblast in OBLASTI:
            assert v["matice"][f"{role}|{oblast}"] is False, f"{role} smí {oblast}"
    for role in MATICE:
        assert v["matice"][f"{role}|vymyslene"] is False, f"{role} smí vymyšlenou oblast"


def test_hesla_se_ukladaji_jako_hash(v):
    assert v["hash_neni_heslo"] is True, "heslo se ukládá v čitelné podobě"
    assert v["hash_je_jiny"] is True, "dvakrát totéž heslo dalo tentýž hash — chybí sůl"
    assert v["hash_delka"] is True
    assert v["overi_spravne"] is True
    assert v["odmitne_spatne"] is False
    assert v["odmitne_prazdne"] is False
    assert v["odmitne_bez_hashe"] is False
    assert v["odmitne_neaktivniho"] is False, "odhlášený/neaktivní uživatel se nesmí přihlásit"


def test_sila_hesla(v):
    s = v["sila"]
    assert s["dobre"] is None, "dost dlouhé heslo bylo odmítnuto"
    assert s["ohromne"] is None
    assert s["kratke"], "krátké heslo prošlo"
    assert s["prazdne"], "prázdné heslo prošlo"
    assert s["mezery"], "heslo z mezer prošlo"
    assert s["dlouhe_ale_jen_pismena"] is None, "pravidlo nemá nutit číslice, jen délku"
    assert s["dvanact"] is None, "dvanáct znaků je ta slíbená hranice a musí projít"
    assert s["jedenact"], "jedenáct znaků prošlo, ačkoli slibujeme aspoň dvanáct"
    assert s["osm"], "osmiznakové heslo prošlo (instalátor přitom slibuje dvanáct)"


def test_zapis_uzivatele(v):
    z = v["zapis"]
    assert z["dobry"] == [], f"platný zápis byl odmítnut: {z['dobry']}"
    assert "jmeno" in z["bez_jmena"]
    assert "email" in z["spatny_email"]
    assert "email" in z["bez_emailu"]
    assert "role" in z["cizi_role"]
    assert set(z["prazdne"]) >= {"jmeno", "email", "role"}


def test_pozvanka_je_nahodna_a_casove_omezena(v):
    p = v["pozvanka"]
    assert len(p["token1"]) == 64 and all(c in "0123456789abcdef" for c in p["token1"])
    assert p["token1"] != p["token2"], "dvě pozvánky dostaly tentýž token"
    assert p["do1"][:2] == "20" and len(p["do1"]) == 19, f"čekán tvar YYYY-MM-DD HH:MM:SS, přišlo {p['do1']}"
    assert v["pozvanka_plati"] is True
    assert v["pozvanka_propadla"] is False, "propadlá pozvánka pořád platí"
    assert v["pozvanka_bez_tokenu"] is False


def test_neznamy_ucet_neodpovida_rychleji(v):
    """Nález K3 z kola 2: existující účet ~0,20 s, neznámé jméno ~0,01 s —
    z času jde poznat, která jména v administraci existují. Heslo se proto
    musí ověřit i tam, kde není co ověřovat (proti falešnému hashi)."""
    assert v["odmitne_neznamy_ucet"] is False, "neznámý účet (null) musí vrátit false"

    c = v["casy"]
    znamy = c["znamy_ucet_spatne_heslo"]
    assert znamy > 5, (
        f"ověření hesla u známého účtu trvalo {znamy:.2f} ms — to na bcrypt "
        "nevypadá a měření nemá co srovnávat"
    )
    for klic in ("neznamy_ucet", "ucet_bez_hashe", "neaktivni_ucet"):
        assert c[klic] >= znamy * 0.5, (
            f"{klic} odpověděl za {c[klic]:.2f} ms, známý účet za {znamy:.2f} ms — "
            "z rozdílu se dá vyčíst, který účet existuje"
        )
