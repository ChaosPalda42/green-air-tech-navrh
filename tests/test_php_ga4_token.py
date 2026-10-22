"""Akceptační test C-024 — App\\Statistiky\\Ga4Token (přihlášení servisního účtu).

Dvě části, obě se dají ověřit bez internetu:

* `base64url` se srovnává se zaznamenanou tabulkou (tests/orakulum/base64url.json,
  spočítal ji Python, ne PHP — tedy nezávislý zdroj pravdy).
* `jwt` se podepisuje čerstvým klíčem a podpis se ověřuje přes openssl_verify.
  To je silnější než zaznamenaný vzorek: neporovnává se text, ale matematika.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

KOREN = Path(__file__).resolve().parents[1]
ORAKULUM = KOREN / "tests" / "orakulum" / "base64url.json"
ROZSAH = "https://www.googleapis.com/auth/analytics.readonly"
UCET = "web@greenairtech.iam.gserviceaccount.com"
CAS = 1760000000

PROGRAM = r"""
<?php
declare(strict_types=1);
require '{KOREN}/web/app/Jadro/Autoload.php';

use App\Statistiky\Ga4Token;

$ven = [];

/* --- base64url nad zaznamenanou tabulkou --- */
$orakulum = json_decode((string) file_get_contents('{ORAKULUM}'), true, 512, JSON_THROW_ON_ERROR);
$ven['base64url'] = [];
foreach ($orakulum['base64url'] as $pripad) {
    $ven['base64url'][] = Ga4Token::base64url((string) $pripad['args'][0]);
}

/* --- jwt nad čerstvým klíčem --- */
$klic = openssl_pkey_new(['private_key_bits' => 2048, 'private_key_type' => OPENSSL_KEYTYPE_RSA]);
openssl_pkey_export($klic, $pem);
$verejny = openssl_pkey_get_details($klic)['key'];

$token = Ga4Token::jwt(
    ['client_email' => '{UCET}', 'private_key' => $pem],
    '{ROZSAH}',
    {CAS}
);

$casti = explode('.', $token);
$ven['casti'] = count($casti);
$odkoduj = static fn (string $c): mixed => json_decode(
    (string) base64_decode(strtr($c, '-_', '+/') . str_repeat('=', (4 - strlen($c) % 4) % 4)),
    true
);
$ven['hlavicka'] = count($casti) > 1 ? $odkoduj($casti[0]) : null;
$ven['telo'] = count($casti) > 1 ? $odkoduj($casti[1]) : null;
$ven['bezVycpavky'] = !str_contains($token, '=') && !str_contains($token, '+') && !str_contains($token, '/');

$ven['podpisPlati'] = false;
if (count($casti) === 3) {
    $podpis = (string) base64_decode(strtr($casti[2], '-_', '+/') . str_repeat('=', (4 - strlen($casti[2]) % 4) % 4));
    $ven['podpisPlati'] = openssl_verify($casti[0] . '.' . $casti[1], $podpis, $verejny, OPENSSL_ALGO_SHA256) === 1;
}

/* --- nepoužitelný klíč se musí poznat, ne podepsat něčím náhodným --- */
try {
    Ga4Token::jwt(['client_email' => 'a@b.cz', 'private_key' => 'tohle není klíč'], '{ROZSAH}', {CAS});
    $ven['spatnyKlic'] = 'prosel';
} catch (\Throwable $e) {
    $ven['spatnyKlic'] = 'vyjimka';
}

/* --- tělo požadavku na token --- */
$ven['pozadavek'] = Ga4Token::pozadavek('PODEPSANE.TRI.CASTI');

echo json_encode($ven, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
"""


@pytest.fixture(scope="module")
def v(tmp_path_factory):
    program = tmp_path_factory.mktemp("ga4") / "program.php"
    program.write_text(
        PROGRAM.lstrip()
        .replace("{KOREN}", str(KOREN))
        .replace("{ORAKULUM}", str(ORAKULUM))
        .replace("{ROZSAH}", ROZSAH)
        .replace("{UCET}", UCET)
        .replace("{CAS}", str(CAS)),
        "utf8",
    )
    hotovo = subprocess.run(["php", str(program)], capture_output=True, text=True, timeout=60)
    if hotovo.returncode != 0:
        raise AssertionError("PHP spadlo: " + (hotovo.stderr or hotovo.stdout).strip()[:600])
    return json.loads(hotovo.stdout)


def test_base64url_se_chova_jako_zaznam(v):
    cekano = [p["out"] for p in json.loads(ORAKULUM.read_text("utf8"))["base64url"]]
    vstupy = [p["args"][0] for p in json.loads(ORAKULUM.read_text("utf8"))["base64url"]]
    neshody = [
        f"{vstupy[i]!r}: čekáno {c!r}, přišlo {v['base64url'][i]!r}"
        for i, c in enumerate(cekano)
        if v["base64url"][i] != c
    ]
    assert not neshody, "\n".join(neshody[:10])


def test_token_ma_tri_casti_bez_vycpavky(v):
    assert v["casti"] == 3, "JWT jsou tři části oddělené tečkou"
    assert v["bezVycpavky"], "base64url nesmí obsahovat '=', '+' ani '/'"


def test_hlavicka_je_presne_ta_co_google_ceka(v):
    assert v["hlavicka"] == {"alg": "RS256", "typ": "JWT"}


def test_telo_rika_kdo_co_a_na_jak_dlouho(v):
    telo = v["telo"]
    assert telo["iss"] == UCET
    assert telo["scope"] == ROZSAH
    assert telo["aud"] == "https://oauth2.googleapis.com/token"
    assert telo["iat"] == CAS
    assert telo["exp"] == CAS + 3600, "platnost hodinu, jak Google chce"
    assert set(telo) == {"iss", "scope", "aud", "iat", "exp"}, "nic víc tam nepatří"


def test_podpis_opravdu_sedi_ke_klici(v):
    assert v["podpisPlati"], "openssl_verify nad veřejným klíčem musí podpis uznat"


def test_nepouzitelny_klic_skonci_vyjimkou(v):
    assert v["spatnyKlic"] == "vyjimka"


def test_pozadavek_je_tvar_ktery_google_prijme(v):
    assert v["pozadavek"] == (
        "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
        "&assertion=PODEPSANE.TRI.CASTI"
    )
