"""Akceptace: stránka administrace s pozvánkou v adrese.

Nezávislý test balíčku našel, že uživatel založený v administraci se nikdy
nepřihlásí — heslo si nemá kde nastavit. Rozhodování o pozvánce dělá
App\\Auth\\Pozvanka (C-030), tenhle soubor hlídá to druhé: že stránka
`administrace.html?pozvanka=<token>` opravdu ukáže formulář na nastavení
hesla a že se v ní neukáže nic, co se ukázat nesmí.

Pravidlo:
- S platným tokenem stránka vykreslí formulář `akce=pozvanka` s tokenem,
  dvěma poli na heslo a CSRF — a NE přihlašovací formulář, aby člověk
  neklepal heslo do něčeho, co ho nepustí.
- S propadlým nebo cizím tokenem je to naopak: přihlášení ano, formulář na
  heslo ne, a stránka to řekne (jedna hláška pro všechny důvody).
- Hash hesla ani token z účtu se do stránky nedostanou jinak než jako
  token, který už návštěvník poslal, a vždycky escapovaný do atributu.
- Chyba z odmítnutého hesla (?chyba=kratke) nesmí zapnout hlášku
  „přihlášení se nepovedlo" — to by člověka posílalo opravovat jméno.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]

TOKEN = "c" * 64
ZLY_TOKEN = '"><script>window.UTEK=1</script>'

PROGRAM = r"""
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Api\Uloziste;
use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

/* Falešné úložiště: šest metod rozhraní a navíc podleTokenu(), kterou má
   na ostrém webu UlozisteDb. Rozhraní se kvůli pozvánce nerozšiřuje. */
$uloziste = new class implements Uloziste {
    public function stav(): array { return \App\Obsah\Stav::prazdny(); }
    public function ulozStav(array $s, string $kdo): void {}
    public function uzivatele(): array { return []; }
    public function ulozUzivatele(array $u): array { return $u; }
    public function smazUzivatele(int $id): void {}
    public function uzivatelPodleJmena(string $j): ?array { return null; }

    public function podleTokenu(string $token): ?array
    {
        $ulozeny = '{ULOZENY}';
        if ($ulozeny === '' || $token !== $ulozeny) {
            return null;
        }
        return [
            'id' => '7',
            'jmeno' => 'Editor Test',
            'email' => 'editor@priklad.cz',
            'role' => 'editor',
            'aktivni' => '1',
            'heslo_hash' => null,
            'pozvanka_token' => $ulozeny,
            'pozvanka_do' => date('Y-m-d H:i:s', time() + {ZBYVA}),
        ];
    }
};

$_GET = json_decode('{DOTAZ}', true, 512, JSON_THROW_ON_ERROR);

$zdroj = new ZdrojJson('{KOREN}/web/data', '{KOREN}/web/public/assets');
$kam = Odkazy::rozpoznej('administrace.html', $zdroj->site());
echo Stranka::vykresli($kam, $zdroj, false, $zdroj, $uloziste);
"""


def stranka(dotaz: dict, ulozeny: str = TOKEN, zbyva: int = 3 * 86400) -> str:
    import json as _json
    program = (
        PROGRAM.replace("{KOREN}", str(KOREN))
        .replace("{ULOZENY}", ulozeny.replace("\\", "\\\\").replace("'", "\\'"))
        .replace("{ZBYVA}", str(zbyva))
        .replace("{DOTAZ}", _json.dumps(dotaz).replace("\\", "\\\\").replace("'", "\\'"))
    )
    hotovo = subprocess.run(["php", "-r", program], capture_output=True, text=True, timeout=60)
    assert hotovo.returncode == 0, (hotovo.stderr or hotovo.stdout)[-2000:]
    return hotovo.stdout


def formular_pozvanky(html: str) -> str | None:
    """Vrátí formulář, který posílá akce=pozvanka — nebo None."""
    for kus in re.findall(r"<form\b.*?</form>", html, re.S):
        if re.search(r'name="akce"\s+value="pozvanka"', kus):
            return kus
    return None


@pytest.fixture(scope="module")
def s_pozvankou():
    return stranka({"pozvanka": TOKEN})


@pytest.fixture(scope="module")
def propadla():
    return stranka({"pozvanka": TOKEN}, zbyva=-60)


@pytest.fixture(scope="module")
def bez_pozvanky():
    return stranka({})


def test_platna_pozvanka_ukaze_formular_na_heslo(s_pozvankou):
    form = formular_pozvanky(s_pozvankou)
    assert form is not None, (
        "stránka s platnou pozvánkou nemá formulář akce=pozvanka — nový uživatel "
        "si heslo nenastaví a nikdy se nepřihlásí"
    )
    assert 'method="post"' in form.lower()
    assert f'name="token" value="{TOKEN}"' in form, "formulář musí poslat token zpátky"
    assert re.search(r'name="heslo"[^>]*type="password"|type="password"[^>]*name="heslo"', form), \
        "chybí pole na heslo"
    assert re.search(r'name="heslo2"', form), "chybí druhé pole na opsání hesla"
    assert re.search(r'name="csrf"\s+value="[^"]+"', form), "formulář bez CSRF tokenu"
    assert "Editor Test" in s_pozvankou, "stránka má říct, pro koho ta pozvánka je"


def test_platna_pozvanka_neukaze_prihlaseni(s_pozvankou):
    assert 'value="prihlasit"' not in s_pozvankou, (
        "vedle formuláře na nové heslo svítí i přihlášení — člověk zadá heslo, "
        "které ještě neexistuje, a dostane „přihlášení se nepovedlo\""
    )


def test_propadla_pozvanka_posle_na_prihlaseni(propadla):
    assert formular_pozvanky(propadla) is None, (
        "propadlá pozvánka pořád nabízí nastavení hesla"
    )
    assert 'value="prihlasit"' in propadla, "propadlá pozvánka musí nechat přihlášení"
    assert "data-pozvanka-propadla" in propadla, (
        "stránka mlčí o tom, že pozvánka propadla — člověk nepozná, proč tam "
        "formulář není"
    )


def test_cizi_token_se_chova_stejne_jako_propadly():
    cizi = stranka({"pozvanka": "d" * 64})
    assert formular_pozvanky(cizi) is None
    assert "data-pozvanka-propadla" in cizi, (
        "neznámý token musí dostat tutéž hlášku jako propadlý — jinak se dá "
        "z odpovědi vyčíst, který token v databázi existuje"
    )


def test_bez_pozvanky_se_nic_nemeni(bez_pozvanky):
    assert formular_pozvanky(bez_pozvanky) is None
    assert 'value="prihlasit"' in bez_pozvanky
    assert "data-pozvanka-propadla" not in bez_pozvanky, (
        "kdo přišel na administraci bez pozvánky, nemá co řešit propadlou pozvánku"
    )


def test_chyba_hesla_neposila_opravovat_jmeno():
    html = stranka({"pozvanka": TOKEN, "chyba": "kratke"})
    assert formular_pozvanky(html) is not None, (
        "po odmítnutém hesle musí formulář na stránce zůstat"
    )
    assert "data-chyba-pozvanky" in html, "stránka neřekne, co bylo s heslem špatně"
    assert "data-chyba-prihlaseni" not in html, (
        "krátké heslo z pozvánky zapnulo hlášku „přihlášení se nepovedlo\" — "
        "to posílá člověka opravovat jméno a heslo, které ještě nemá"
    )


def test_hash_hesla_ani_cizi_token_do_stranky_nejdou():
    html = stranka({"pozvanka": TOKEN})
    assert "$2y$" not in html, "do stránky se dostal hash hesla"
    jiny = stranka({"pozvanka": "e" * 64})
    assert TOKEN not in jiny, (
        "stránka vypsala token uložený u účtu, i když návštěvník poslal jiný"
    )


def test_token_se_escapuje_do_atributu():
    """Token se sice vždycky rovná tomu z databáze, ale do atributu patří
    escapovaný — jinak by stačil jeden divný řádek v databázi."""
    html = stranka({"pozvanka": ZLY_TOKEN}, ulozeny=ZLY_TOKEN)
    assert ZLY_TOKEN not in html, (
        "token z databáze se do stránky dostal doslova — uzavřel atribut a dál "
        "je z něj skript. (Vevnitř JSON bloku se `</` escapuje zvlášť, takže "
        "doslovný výskyt tohohle tokenu kdekoli ve stránce je vada.)"
    )
    assert formular_pozvanky(html) is not None, "formulář se vykreslit má, jen escapovaně"
