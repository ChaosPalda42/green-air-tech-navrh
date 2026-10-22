<?php
/* České řazení bez rozšíření intl. Reprodukuje to, co v prohlížeči dělá
   String.prototype.localeCompare(…, 'cs'): tři celé průchody přes řetězec.

   1. průchod — abeceda: a b c č d e f g h ch i j k l m n o p q r ř s š t u v
      w x y z ž. Diakritika, která v češtině není samostatné písmeno (á, ě, ď,
      ú, ů …), spadá ke svému základnímu písmenu; č, ř, š, ž jsou písmena sama.
      Nepísmena stojí před číslicemi a ty před písmeny.
   2. průchod — přízvuk: teprve když se první průchod rovná, rozhoduje
      diakritika (a < á < ä, e < é < ě, u < ú < ů).
   3. průchod — velikost: nakonec malé před velkým (ar < Ar).

   Kdo porovnává znak po znaku a váhy mísí do jednoho klíče, dostane
   'Á' < 'Ar' místo 'Á' > 'Ar'. Proto tři pole, ne jedno. */

declare(strict_types=1);

namespace App\Obsah;

final class RazeniCs
{
    /** Pořadí písmen v české abecedě (1. průchod). */
    private const ABECEDA = [
        'a', 'b', 'c', 'č', 'd', 'e', 'f', 'g', 'h', 'ch', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 'ř', 's', 'š', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'ž',
    ];

    /** Malé písmeno => [základní písmeno abecedy, váha přízvuku]. */
    private const PISMENA = [
        'a' => ['a', 0], 'á' => ['a', 1], 'ä' => ['a', 2], 'à' => ['a', 3], 'â' => ['a', 4],
        'b' => ['b', 0],
        'c' => ['c', 0],
        'č' => ['č', 0],
        'd' => ['d', 0], 'ď' => ['d', 1],
        'e' => ['e', 0], 'é' => ['e', 1], 'ě' => ['e', 2], 'ë' => ['e', 3],
        'f' => ['f', 0],
        'g' => ['g', 0],
        'h' => ['h', 0],
        'i' => ['i', 0], 'í' => ['i', 1],
        'j' => ['j', 0],
        'k' => ['k', 0],
        'l' => ['l', 0],
        'm' => ['m', 0],
        'n' => ['n', 0], 'ň' => ['n', 1],
        'o' => ['o', 0], 'ó' => ['o', 1], 'ö' => ['o', 2], 'ô' => ['o', 3],
        'p' => ['p', 0],
        'q' => ['q', 0],
        'r' => ['r', 0],
        'ř' => ['ř', 0],
        's' => ['s', 0],
        'š' => ['š', 0],
        't' => ['t', 0], 'ť' => ['t', 1],
        'u' => ['u', 0], 'ú' => ['u', 1], 'ů' => ['u', 2], 'ü' => ['u', 3],
        'v' => ['v', 0],
        'w' => ['w', 0],
        'x' => ['x', 0],
        'y' => ['y', 0], 'ý' => ['y', 1],
        'z' => ['z', 0],
        'ž' => ['ž', 0],
    ];

    /** Velké písmeno => malé. Bez mbstring: tabulka pro naši abecedu. */
    private const MALE = [
        'A' => 'a', 'Á' => 'á', 'Ä' => 'ä', 'À' => 'à', 'Â' => 'â',
        'B' => 'b', 'C' => 'c', 'Č' => 'č', 'D' => 'd', 'Ď' => 'ď',
        'E' => 'e', 'É' => 'é', 'Ě' => 'ě', 'Ë' => 'ë', 'F' => 'f',
        'G' => 'g', 'H' => 'h', 'I' => 'i', 'Í' => 'í', 'J' => 'j',
        'K' => 'k', 'L' => 'l', 'M' => 'm', 'N' => 'n', 'Ň' => 'ň',
        'O' => 'o', 'Ó' => 'ó', 'Ö' => 'ö', 'Ô' => 'ô', 'P' => 'p',
        'Q' => 'q', 'R' => 'r', 'Ř' => 'ř', 'S' => 's', 'Š' => 'š',
        'T' => 't', 'Ť' => 'ť', 'U' => 'u', 'Ú' => 'ú', 'Ů' => 'ů',
        'Ü' => 'ü', 'V' => 'v', 'W' => 'w', 'X' => 'x', 'Y' => 'y',
        'Ý' => 'ý', 'Z' => 'z', 'Ž' => 'ž',
    ];

    /** Nepísmena, která se v názvech potkávají nejčastěji, v tomto pořadí. */
    private const NEPISMENA = [
        ' ' => 0, "\u{00a0}" => 0, '-' => 1, '–' => 2, ',' => 3, '.' => 4,
        '/' => 5, '(' => 6, ')' => 7,
    ];

    /** Pásma 1. průchodu: nepísmena < číslice < písmena. */
    private const PASMO = 2000000;

    public static function porovnej(string $a, string $b): int
    {
        $ka = self::klice($a);
        $kb = self::klice($b);

        for ($u = 0; $u < 3; $u++) {
            $vysledek = self::porovnejPole($ka[$u], $kb[$u]);
            if ($vysledek !== 0) {
                return $vysledek;
            }
        }

        return 0;
    }

    /**
     * @param list<string> $texty
     * @return list<string>
     */
    public static function seradit(array $texty): array
    {
        $kopie = array_values($texty);
        usort($kopie, [self::class, 'porovnej']);

        return $kopie;
    }

    /**
     * Tři klíče jednoho řetězce: abeceda, přízvuk, velikost.
     *
     * @return array{0: list<int>, 1: list<int>, 2: list<int>}
     */
    private static function klice(string $text): array
    {
        $poradi = array_flip(self::ABECEDA);
        $znaky = preg_split('//u', $text, -1, PREG_SPLIT_NO_EMPTY) ?: [];
        $pocet = count($znaky);

        $abeceda = [];
        $prizvuk = [];
        $velikost = [];

        for ($i = 0; $i < $pocet; $i++) {
            $znak = $znaky[$i];
            $maly = self::MALE[$znak] ?? $znak;
            $druhy = $i + 1 < $pocet ? $znaky[$i + 1] : '';
            $druhyMaly = self::MALE[$druhy] ?? $druhy;

            // ch je jedno písmeno a stojí mezi h a i
            if ($maly === 'c' && $druhyMaly === 'h') {
                $abeceda[] = self::PASMO * 3 + $poradi['ch'];
                $prizvuk[] = 0;
                $velka = isset(self::MALE[$znak]);
                $velkaDruha = isset(self::MALE[$druhy]);
                $velikost[] = $velka && $velkaDruha ? 2 : ($velka || $velkaDruha ? 1 : 0);
                $i++;
                continue;
            }

            if (isset(self::PISMENA[$maly])) {
                [$zaklad, $vaha] = self::PISMENA[$maly];
                $abeceda[] = self::PASMO * 3 + $poradi[$zaklad];
                $prizvuk[] = $vaha;
                $velikost[] = isset(self::MALE[$znak]) ? 1 : 0;
                continue;
            }

            if ($znak >= '0' && $znak <= '9') {
                $abeceda[] = self::PASMO * 2 + self::kod($znak);
                $prizvuk[] = 0;
                $velikost[] = 0;
                continue;
            }

            $abeceda[] = self::PASMO + (self::NEPISMENA[$znak] ?? 100 + self::kod($znak));
            $prizvuk[] = 0;
            $velikost[] = 0;
        }

        return [$abeceda, $prizvuk, $velikost];
    }

    /**
     * Porovnání dvou klíčů prvek po prvku. Kratší, který je předponou
     * delšího, jde první — proto se NESMÍ použít PHP operátor na polích,
     * ten porovnává nejdřív počet prvků.
     *
     * @param list<int> $a
     * @param list<int> $b
     */
    private static function porovnejPole(array $a, array $b): int
    {
        $sdilene = min(count($a), count($b));
        for ($i = 0; $i < $sdilene; $i++) {
            if ($a[$i] !== $b[$i]) {
                return $a[$i] < $b[$i] ? -1 : 1;
            }
        }

        return count($a) <=> count($b);
    }

    /** Kódový bod znaku UTF-8 bez mbstring. */
    private static function kod(string $znak): int
    {
        $bajty = unpack('C*', $znak) ?: [];
        $pocet = count($bajty);

        return match ($pocet) {
            1 => $bajty[1],
            2 => (($bajty[1] & 0x1F) << 6) | ($bajty[2] & 0x3F),
            3 => (($bajty[1] & 0x0F) << 12) | (($bajty[2] & 0x3F) << 6) | ($bajty[3] & 0x3F),
            default => (($bajty[1] & 0x07) << 18) | (($bajty[2] & 0x3F) << 12)
                | (($bajty[3] & 0x3F) << 6) | ($bajty[4] & 0x3F),
        };
    }
}
