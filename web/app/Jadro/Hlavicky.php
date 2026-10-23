<?php
/* Bezpečnostní hlavičky ostrého webu.

   Posílá je PHP, ne jen .htaccess: na nginxu by se pravidla z .htaccess
   nepoužila a web by jel bez nich. Apache si je pak nastaví ještě jednou
   stejně, což nevadí — header() stejnojmennou hlavičku přepíše.

   Skripty má web vložené přímo ve stránce (window.GAT_*, měření), proto
   script-src musí povolit 'unsafe-inline'. Cenu to má pořád: skript ani styl
   se nenačte odjinud než z našeho webu (a z Google Tag Manageru kvůli
   statistikám), stránka se nedá otevřít v cizím rámu a formulář nejde odeslat
   jinam. */

declare(strict_types=1);

namespace App\Jadro;

final class Hlavicky
{
    /** Odkud se smí načíst měřicí kód a kam smí odesílat. */
    private const GOOGLE_SKRIPT = 'https://www.googletagmanager.com';
    private const GOOGLE_SPOJENI = 'https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com';

    /** Půl roku. Bez `preload`, aby se dalo vrátit zpátky. */
    private const HSTS = 'max-age=15552000; includeSubDomains';

    /**
     * Hlavičky, které se mají poslat. $https = jde požadavek po HTTPS
     * (jen tehdy má smysl HSTS — po HTTP ho prohlížeč stejně zahodí).
     *
     * @return array<string,string>
     */
    public static function seznam(bool $https): array
    {
        $hlavicky = [
            'X-Content-Type-Options' => 'nosniff',
            'X-Frame-Options' => 'SAMEORIGIN',
            'Referrer-Policy' => 'strict-origin-when-cross-origin',
            'Permissions-Policy' => 'geolocation=(), microphone=(), camera=(), payment=(), usb=()',
            'Content-Security-Policy' => self::csp(),
        ];
        if ($https) {
            $hlavicky['Strict-Transport-Security'] = self::HSTS;
        }

        return $hlavicky;
    }

    public static function posli(): void
    {
        if (headers_sent()) {
            return;
        }
        foreach (self::seznam(self::pozadavekPresHttps()) as $jmeno => $hodnota) {
            header($jmeno . ': ' . $hodnota);
        }
    }

    /** Za reverzní proxy (Cloudflare, nginx) přijde pravda v X-Forwarded-Proto. */
    public static function pozadavekPresHttps(): bool
    {
        if (($_SERVER['HTTPS'] ?? '') !== '' && ($_SERVER['HTTPS'] ?? 'off') !== 'off') {
            return true;
        }

        return strtolower((string) ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '')) === 'https';
    }

    private static function csp(): string
    {
        return implode('; ', [
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'self'",
            "form-action 'self'",
            "img-src 'self' data: blob: https://*.google-analytics.com",
            "font-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline' " . self::GOOGLE_SKRIPT,
            'connect-src \'self\' ' . self::GOOGLE_SPOJENI,
        ]);
    }
}
