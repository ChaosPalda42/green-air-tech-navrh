<?php
/* Přihlášení servisního účtu Googlu: podepsaný JWT (RS256) a tělo požadavku
   na https://oauth2.googleapis.com/token. */

declare(strict_types=1);

namespace App\Statistiky;

final class Ga4Token
{
    /** base64 bez výcpávky '=' a s '-' místo '+' a '_' místo '/'. */
    public static function base64url(string $data): string
    {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }

    /**
     * Podepsaný JWT pro servisní účet Googlu.
     *
     * @param array{client_email?:string,private_key?:string} $ucet rozkódovaný JSON klíče
     * @throws \RuntimeException když klíč nejde načíst
     */
    public static function jwt(array $ucet, string $rozsah, int $cas): string
    {
        $klic = @openssl_pkey_get_private((string) ($ucet['private_key'] ?? ''));
        if ($klic === false) {
            throw new \RuntimeException('Privátní klíč servisního účtu nejde načíst.');
        }

        $hlavicka = self::base64url((string) json_encode(
            ['alg' => 'RS256', 'typ' => 'JWT'],
            JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
        ));
        $telo = self::base64url((string) json_encode(
            [
                'iss' => (string) ($ucet['client_email'] ?? ''),
                'scope' => $rozsah,
                'aud' => 'https://oauth2.googleapis.com/token',
                'iat' => $cas,
                'exp' => $cas + 3600,
            ],
            JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
        ));

        $podpis = '';
        if (!openssl_sign($hlavicka . '.' . $telo, $podpis, $klic, OPENSSL_ALGO_SHA256)) {
            throw new \RuntimeException('Podpis JWT se nepodařilo vytvořit.');
        }

        return $hlavicka . '.' . $telo . '.' . self::base64url($podpis);
    }

    /** Tělo POSTu na https://oauth2.googleapis.com/token. */
    public static function pozadavek(string $jwt): string
    {
        return http_build_query([
            'grant_type' => 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion' => $jwt,
        ]);
    }
}
