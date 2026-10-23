"""Brána: co kód potřebuje z PHP, to musí instalátor hlídat a README nainstalovat.

Nezávislý test balíčku na čistém Debianu 13 skončil HTTP 500: apt řádek
z README nenainstaloval php8.5-mbstring ani php8.5-curl, všechny kontroly
v instalátoru svítily zeleně a první POST spadl na

    PHP Fatal error: Call to undefined function App\\Auth\\mb_strlen()

a config.php vůbec nevznikl. Náš Docker na to přijít nemohl — oficiální
obraz php:8.5-apache má mbstring i curl zakompilované, Debian je má
v samostatných balíčcích.

Brána proto nečte seznam rozšíření ze zdroje pravdy, který by někdo mohl
zapomenout doplnit — vyčte si ho z KÓDU (tokenizérem PHP, ne hledáním
v textu) a pak se ptá dvou míst, která o tom musí vědět:

1. `install.php` musí každé rozšíření kontrolovat tvrdě (červeně), ať se
   instalace zastaví na kontrole a ne uprostřed zápisu do databáze.
2. apt řádek v README musí nainstalovat balíček, ve kterém to rozšíření
   na Debianu je — pokud takový balíček existuje (openssl a ctype jsou
   v jádře PHP, pro ně žádný není).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]

SLOZKY = ("web/app", "web/public", "tools", "nasazeni/balicek")
INSTALATOR = KOREN / "nasazeni" / "balicek" / "install.php"
README = KOREN / "nasazeni" / "balicek" / "README-NASAZENI.md"

# Předpona volané funkce → rozšíření a balíček na Debianu (None = je v jádře
# PHP, samostatný balíček pro něj neexistuje, takže ho apt řádek mít nemůže).
PODLE_PREDPONY: tuple[tuple[str, str, str | None], ...] = (
    ("mb_", "mbstring", "php8.5-mbstring"),
    ("curl_", "curl", "php8.5-curl"),
    ("image", "gd", "php8.5-gd"),
    ("openssl_", "openssl", None),
    ("iconv", "iconv", None),
    ("ctype_", "ctype", None),
    ("intl", "intl", "php8.5-intl"),
    ("simplexml_", "simplexml", "php8.5-xml"),
    ("finfo_", "fileinfo", None),
    ("exif_", "exif", None),
    ("zip_", "zip", "php8.5-zip"),
    ("bcadd", "bcmath", "php8.5-bcmath"),
    ("gmp_", "gmp", "php8.5-gmp"),
    ("sodium_", "sodium", None),
    ("mysqli_", "mysqli", "php8.5-mysql"),
    ("pg_", "pgsql", "php8.5-pgsql"),
)

# PDO se nevolá funkcí, ale `new PDO(...)`; ovladač je pro MariaDB pdo_mysql.
PDO = ("pdo_mysql", "php8.5-mysql")

# Tokenizérem PHP: jméno funkce v komentáři ani v řetězci není volání.
HLEDAC = r"""
$nalezy = [];
foreach (array_slice($argv, 1) as $soubor) {
    $tokeny = token_get_all((string) file_get_contents($soubor));
    $pocet = count($tokeny);
    foreach ($tokeny as $i => $token) {
        if (!is_array($token)) {
            continue;
        }
        if ($token[0] === T_STRING && strtolower($token[1]) === 'pdo') {
            $nalezy['new PDO'] = true;
            continue;
        }
        if ($token[0] !== T_STRING) {
            continue;
        }
        for ($p = $i - 1; $p >= 0; $p--) {
            if (is_array($tokeny[$p]) && $tokeny[$p][0] === T_WHITESPACE) {
                continue;
            }
            break;
        }
        $pred = $p >= 0 ? $tokeny[$p] : null;
        if (is_array($pred) && in_array($pred[0], [T_OBJECT_OPERATOR, T_DOUBLE_COLON, T_FUNCTION, T_NEW], true)) {
            continue;
        }
        for ($n = $i + 1; $n < $pocet; $n++) {
            if (is_array($tokeny[$n]) && $tokeny[$n][0] === T_WHITESPACE) {
                continue;
            }
            break;
        }
        if (($tokeny[$n] ?? null) !== '(') {
            continue;
        }
        $nalezy[strtolower($token[1])] = true;
    }
}
echo json_encode(array_keys($nalezy));
"""


def php_soubory() -> list[str]:
    soubory: list[str] = []
    for slozka in SLOZKY:
        soubory.extend(str(s) for s in sorted((KOREN / slozka).rglob("*.php")))
    return soubory


def potrebna_rozsireni() -> dict[str, str | None]:
    """{rozšíření: balíček na Debianu nebo None} vyčtené z volání v kódu."""
    soubory = php_soubory()
    assert soubory, "nenašel jsem žádný PHP soubor"
    hotovo = subprocess.run(
        ["php", "-r", HLEDAC, "--", *soubory],
        capture_output=True, text=True, check=True,
    )
    volani = set(json.loads(hotovo.stdout))
    potreba: dict[str, str | None] = {}
    for predpona, rozsireni, balicek in PODLE_PREDPONY:
        if any(v.startswith(predpona) for v in volani):
            potreba[rozsireni] = balicek
    if "new PDO" in volani:
        potreba[PDO[0]] = PDO[1]
    return potreba


def test_kod_opravdu_neco_potrebuje() -> None:
    """Kdyby se tokenizér rozbil, brána by zeleně hlídala prázdný seznam."""
    potreba = potrebna_rozsireni()
    for musi in ("mbstring", "curl", "gd", "pdo_mysql"):
        assert musi in potreba, f"{musi} se v kódu volá, a brána ho nenašla: {sorted(potreba)}"


def test_instalator_kontroluje_kazde_rozsireni() -> None:
    text = INSTALATOR.read_text()
    kontrolovane = set(re.findall(r"extension_loaded\(\s*'([a-z_0-9]+)'", text))
    chybi = sorted(set(potrebna_rozsireni()) - kontrolovane)
    assert not chybi, (
        "instalátor nekontroluje rozšíření, bez kterých web spadne: "
        + ", ".join(chybi)
        + " — kontrola musí být tvrdá (červená), ne poznámka"
    )


def test_apt_radek_v_readme_je_nainstaluje() -> None:
    radky = [r for r in README.read_text().splitlines() if "apt install" in r and "php8.5" in r]
    assert radky, "v README není apt řádek s PHP"
    apt = " ".join(radky)
    chybi = sorted(
        balicek
        for balicek in potrebna_rozsireni().values()
        if balicek is not None and balicek not in apt
    )
    assert not chybi, "apt řádek v README nenainstaluje: " + ", ".join(chybi)
