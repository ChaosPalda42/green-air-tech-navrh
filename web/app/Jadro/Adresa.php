<?php
/* Adresa návštěvníka z hlaviček požadavku.

   Dvě místa na webu potřebují vědět, odkud návštěvník přišel: zámek
   administrace a strop poptávek. HLAVIČKY SE VĚŘÍ JEN TEHDY, když to
   řekne nastavení z config.php: ['verit' => bool, 'adresy' => list<string>].
   Bez důvěry platí JEN REMOTE_ADDR — podvržená X-Forwarded-For by jinak
   strop i zámek obešla jedním řádkem v požadavku.

   Když se věřit smí, zdroje v pořadí: CF-Connecting-IP (za Cloudflare),
   pak PRVNÍ položka X-Forwarded-For, nakonec REMOTE_ADDR. Zdroj, ve
   kterém platná adresa není, se přeskočí a zkusí se další — podvržená
   hlavička tak nesmaže skutečnou adresu.

   Když nastavení vyjmenuje proxy ('adresy'), hlavičky se čtou jen tehdy,
   přišel-li požadavek od jedné z nich (adresa nebo síť s maskou). */

declare(strict_types=1);

namespace App\Jadro;

final class Adresa
{
    /**
     * Vrátí jednu adresu jako text, nebo prázdný řetězec, když žádná
     * platná není. Pole $server se nečte z superglobálu a nemutuje se.
     */
    public static function navstevnika(array $server, array $proxy = []): string
    {
        $verit = (bool) ($proxy['verit'] ?? false);
        $hlavicky = $verit && self::odProxy($server, (array) ($proxy['adresy'] ?? []));

        if ($hlavicky) {
            foreach (['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'] as $klic) {
                $adresa = self::plna((string) ($server[$klic] ?? ''));
                if ($adresa !== '') {
                    return $adresa;
                }
            }

            return '';
        }

        return self::plna((string) ($server['REMOTE_ADDR'] ?? ''));
    }

    /**
     * Je požadavek od jedné z vypsaných proxy? Prázdný seznam znamená
     * „věřit každé proxy\" — důvěra je už zapnutá. Nesmyslná položka
     * se prostě nikomu nevyhoví.
     */
    private static function odProxy(array $server, array $adresy): bool
    {
        if ($adresy === []) {
            return true;
        }

        $adresa = self::plna((string) ($server['REMOTE_ADDR'] ?? ''));
        if ($adresa === '') {
            return false;
        }

        foreach ($adresy as $sit) {
            if (self::vSiti($adresa, (string) $sit)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Je adresa v zadané síti? 'sit' je buď jedna adresa ('10.0.0.1'),
     * nebo zápis se maskou ('10.0.0.0/8', '2001:db8::/32'). Nesmysl = false.
     */
    public static function vSiti(string $adresa, string $sit): bool
    {
        $adresa = self::plna($adresa);
        if ($adresa === '') {
            return false;
        }

        $sit = trim($sit);
        $maska = null;
        if (str_contains($sit, '/')) {
            [$sit, $maskaText] = explode('/', $sit, 2);
            /* Jen samé číslice: '8.0', '+8', ' 8' ani '' maska není. (Pozor na
               `(int) $x !== (float) $x` — int a float se nikdy nerovnají
               identicky, takže taková podmínka zahodí každou masku.) */
            if (preg_match('/^\d{1,3}$/', $maskaText) !== 1) {
                return false;
            }
            $maska = (int) $maskaText;
        }

        $sit = self::plna($sit);
        if ($sit === '') {
            return false;
        }

        $isIpv6Adresa = filter_var($adresa, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6) !== false;
        $isIpv6Site = filter_var($sit, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6) !== false;
        if ($isIpv6Adresa !== $isIpv6Site) {
            return false;
        }

        $max = $isIpv6Site ? 128 : 32;
        if ($maska === null) {
            $maska = $max;
        }
        if ($maska < 0 || $maska > $max) {
            return false;
        }

        $binAdresa = inet_pton($adresa);
        $binSit = inet_pton($sit);
        if ($binAdresa === false || $binSit === false) {
            return false;
        }
        $delka = strlen($binAdresa);
        for ($i = 0; $i < $delka; $i++) {
            $bit = $maska - $i * 8;
            if ($bit <= 0) {
                break;
            }
            $mask = $bit >= 8 ? 0xFF : (0xFF << (8 - $bit)) & 0xFF;
            if ((ord($binAdresa[$i]) & $mask) !== (ord($binSit[$i]) & $mask)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Z textu hlavičky vezme první položku (položky dělí čárka), očistí ji
     * a vrátí platnou adresu, jinak prázdný řetězec.
     */
    private static function plna(string $zdroj): string
    {
        $polozka = trim(explode(',', $zdroj, 2)[0]);
        if ($polozka === '') {
            return '';
        }

        // Hranaté závorky u IPv6, případně s portem: [2001:db8::1]:443
        if (str_starts_with($polozka, '[')) {
            $zavorka = strpos($polozka, ']');
            if ($zavorka === false) {
                return '';
            }
            $polozka = substr($polozka, 1, $zavorka - 1);
        } else {
            // Port u IPv4: 1.2.3.4:51514 (u IPv6 bez závorek port nelze
            // rozlišit od adresy, proto se řeší jen tvar s jednou tečkou
            // za posledním dvojtečkou, kde by port mohl být).
            if (substr_count($polozka, ':') === 1) {
                $polozka = substr($polozka, 0, strrpos($polozka, ':'));
            }
        }

        if ($polozka === '') {
            return '';
        }

        if (filter_var($polozka, FILTER_VALIDATE_IP) === false) {
            return '';
        }

        return $polozka;
    }
}
