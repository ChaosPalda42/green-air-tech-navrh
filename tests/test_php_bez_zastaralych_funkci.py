"""Akceptace: ostrý web běží na PHP 8.5, a ten už hlásí zastaralé funkce.

Klient má Debian 13 s PHP 8.5.12. Když kód volá funkci, kterou PHP 8.5
označilo za zastaralou, zapíše se při každém požadavku E_DEPRECATED do
logu serveru — našlo se to při první skutečné odpovědi z GA4:
"Function curl_close() is deprecated since 8.5" pětkrát za jedno čtení
statistik.

Brána proto hlídá, že v PHP kódu žádná taková funkce nezůstane.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

KOREN = Path(__file__).resolve().parents[1]

# Funkce, které v PHP 8.5 nic nedělají a jen hlásí E_DEPRECATED.
ZASTARALE = (
    "curl_close", "curl_multi_close", "curl_share_close",
    # imagedestroy() se našlo při nahrání fotky na testovací instalaci:
    # „Function imagedestroy() is deprecated since 8.5, as it has no effect
    # since PHP 8.0" — čtyřikrát za jedno nahrání.
    "imagedestroy",
    # Tytéž „zavírače", které od PHP 8.0 nic nedělají; ať se nepřidají znovu.
    "finfo_close", "xml_parser_free", "shmop_close",
)

SLOZKY = ("web/app", "web/public", "tools", "nasazeni/balicek")


def php_soubory() -> list[Path]:
    soubory: list[Path] = []
    for slozka in SLOZKY:
        soubory.extend(sorted((KOREN / slozka).rglob("*.php")))
    return soubory


def test_slozky_existuji() -> None:
    """Kdyby se složka přejmenovala, brána by mlčky hlídala prázdno."""
    for slozka in SLOZKY:
        assert (KOREN / slozka).is_dir(), slozka


# Hledá se tokenizérem samotného PHP, ne v textu: jméno funkce zmíněné
# v komentáři nebo v řetězci není volání a bránu spouštět nesmí.
HLEDAC = r"""
$zastarale = array_flip(json_decode($argv[1], true));
$nalezy = [];
foreach (array_slice($argv, 2) as $soubor) {
    $tokeny = token_get_all((string) file_get_contents($soubor));
    $pocet = count($tokeny);
    foreach ($tokeny as $i => $token) {
        if (!is_array($token) || $token[0] !== T_STRING) {
            continue;
        }
        if (!isset($zastarale[$token[1]])) {
            continue;
        }
        /* Předchozí významný token: -> nebo :: nebo function znamená
           metodu či vlastní definici, ne volání funkce PHP. */
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
        $nalezy[] = $soubor . ':' . $token[2] . ' ' . $token[1] . '()';
    }
}
echo json_encode($nalezy);
"""


def test_zadne_zastarale_volani() -> None:
    soubory = [str(s) for s in php_soubory()]
    assert soubory, "nenašel jsem žádný PHP soubor"
    hotovo = subprocess.run(
        ["php", "-r", HLEDAC, "--", json.dumps(list(ZASTARALE)), *soubory],
        capture_output=True,
        text=True,
        check=True,
    )
    nalezy = [n.replace(str(KOREN) + "/", "") for n in json.loads(hotovo.stdout)]
    assert nalezy == [], "zastaralá volání: " + ", ".join(nalezy)
