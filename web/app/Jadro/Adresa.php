<?php
/* Adresa návštěvníka z hlaviček požadavku.

   Dvě místa na webu potřebují vědět, odkud návštěvník přišel: zámek
   administrace a strop poptávek. Pořadí zdrojů: CF-Connecting-IP (za
   Cloudflare), pak PRVNÍ položka X-Forwarded-For, nakonec REMOTE_ADDR.
   Zdroj, ve kterém platná adresa není, se přeskočí a zkusí se další —
   podvržená hlavička tak nesmaže skutečnou adresu. */

declare(strict_types=1);

namespace App\Jadro;

final class Adresa
{
    /**
     * Vrátí jednu adresu jako text, nebo prázdný řetězec, když žádná
     * platná není. Pole $server se nečte z superglobálu a nemutuje se.
     */
    public static function navstevnika(array $server): string
    {
        $zdroje = [
            (string) ($server['HTTP_CF_CONNECTING_IP'] ?? ''),
            (string) ($server['HTTP_X_FORWARDED_FOR'] ?? ''),
            (string) ($server['REMOTE_ADDR'] ?? ''),
        ];

        foreach ($zdroje as $zdroj) {
            $adresa = self::prvniPlatna($zdroj);
            if ($adresa !== '') {
                return $adresa;
            }
        }

        return '';
    }

    /**
     * Z textu hlavičky vezme první položku (položky dělí čárka), očistí ji
     * a vrátí platnou adresu, jinak prázdný řetězec.
     */
    private static function prvniPlatna(string $zdroj): string
    {
        $polozka = trim(explode(',', $zdroj, 2)[0]);

        return self::plna($polozka);
    }

    /**
     * Očistí jednu položku (odstraní port a hranaté závorky u IPv6) a
     * ověří, že je to platná IPv4 nebo IPv6 adresa.
     */
    private static function plna(string $polozka): string
    {
        $polozka = trim($polozka);
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
