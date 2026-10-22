<?php
/* Vysvětlivky zkratek. Zdroj pravdy je src/lib/glossary.mjs z ukázky — tohle
   je totéž v PHP, aby server vysázel stejné bajty jako prohlížeč.

   annotate() prochází HTML znak po znaku a přepíná mezi stavem „uvnitř značky“
   a „text“. Značky se kopírují, jak přišly (nic se nestrhává!), v textu se
   zkratky obalují. Do už existujícího <abbr>…</abbr> se nesahá. */

declare(strict_types=1);

namespace App\Obsah;

final class Slovnik
{
    /** Znaky, které v ukázce platí za pokračování slova (hranice slova). */
    private const SLOVNI = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        . 'áàâäãåāăąěèéêëēęíìîïīįñòóôöõōőřùúûüůūűýÿźçşđň'
        . 'ÁÀÂÄÃÅĀĂĄĚÈÉÊËĒĘÍÌÎÏĪĮÑÒÓÔÖÕŌŐŘÙÚÛÜŮŪŰÝŸŹÇŞĐŇ';

    /** Malé => velké, aby se seskupovalo podle skutečného písmene bez mbstring. */
    private const VELKE = [
        'a' => 'A', 'á' => 'Á', 'ä' => 'Ä', 'b' => 'B', 'c' => 'C', 'č' => 'Č',
        'd' => 'D', 'ď' => 'Ď', 'e' => 'E', 'é' => 'É', 'ě' => 'Ě', 'f' => 'F',
        'g' => 'G', 'h' => 'H', 'i' => 'I', 'í' => 'Í', 'j' => 'J', 'k' => 'K',
        'l' => 'L', 'm' => 'M', 'n' => 'N', 'ň' => 'Ň', 'o' => 'O', 'ó' => 'Ó',
        'ö' => 'Ö', 'p' => 'P', 'q' => 'Q', 'r' => 'R', 'ř' => 'Ř', 's' => 'S',
        'š' => 'Š', 't' => 'T', 'ť' => 'Ť', 'u' => 'U', 'ú' => 'Ú', 'ů' => 'Ů',
        'ü' => 'Ü', 'v' => 'V', 'w' => 'W', 'x' => 'X', 'y' => 'Y', 'ý' => 'Ý',
        'z' => 'Z', 'ž' => 'Ž',
    ];

    /**
     * @param list<array{abbr:string,full:string,popis?:string}> $terminy
     * @param array{once?:bool} $volby
     */
    public static function annotate(string $html, array $terminy, array $volby = []): string
    {
        if ($html === '' || $terminy === []) {
            return $html;
        }

        $jenPrvni = ($volby['once'] ?? false) === true;

        // delší zkratky vyhrávají (TUV před TU), řazení je stabilní
        $podleDelky = $terminy;
        usort($podleDelky, static fn (array $a, array $b): int
            => strlen((string) $b['abbr']) <=> strlen((string) $a['abbr']));

        $pouzite = [];
        $znaky = preg_split('//u', $html, -1, PREG_SPLIT_NO_EMPTY) ?: [];
        $pocet = count($znaky);
        $ven = '';
        $i = 0;

        while ($i < $pocet) {
            if ($znaky[$i] === '<') {
                // existující <abbr …>…</abbr> se přeskočí celý
                if (self::jeAbbr($znaky, $i)) {
                    $konec = self::konecAbbr($znaky, $i);
                    if ($konec !== null) {
                        $ven .= implode('', array_slice($znaky, $i, $konec - $i));
                        $i = $konec;
                        continue;
                    }
                }

                // běžná značka: opsat až po '>' včetně
                $j = $i + 1;
                while ($j < $pocet && $znaky[$j] !== '>') {
                    $j++;
                }
                $ven .= implode('', array_slice($znaky, $i, $j - $i + 1));
                $i = $j + 1;
                continue;
            }

            $nalez = null;
            $nalezDelka = 0;
            foreach ($podleDelky as $termin) {
                $zkratka = (string) $termin['abbr'];
                $delka = self::delka($zkratka);
                if ($delka <= $nalezDelka || $delka === 0) {
                    continue;
                }
                if (implode('', array_slice($znaky, $i, $delka)) !== $zkratka) {
                    continue;
                }
                $predOk = $i === 0 || !self::slovni($znaky[$i - 1]);
                $poOk = $i + $delka >= $pocet || !self::slovni($znaky[$i + $delka]);
                if ($predOk && $poOk) {
                    $nalez = $termin;
                    $nalezDelka = $delka;
                }
            }

            if ($nalez !== null) {
                $zkratka = (string) $nalez['abbr'];
                if ($jenPrvni && isset($pouzite[$zkratka])) {
                    $ven .= $znaky[$i];
                    $i++;
                    continue;
                }
                $pouzite[$zkratka] = true;
                $ven .= '<abbr class="zkratka" tabindex="0" data-abbr="' . $zkratka . '">'
                    . $zkratka . '</abbr>';
                $i += $nalezDelka;
                continue;
            }

            $ven .= $znaky[$i];
            $i++;
        }

        return $ven;
    }

    /**
     * Termín podle zkratky; velikost písmen NEROZHODUJE ('tzb' najde 'TZB').
     *
     * @param list<array{abbr:string,full:string,popis?:string}> $terminy
     * @return array{abbr:string,full:string,popis?:string}|null
     */
    public static function findTerm(array $terminy, string $abbr): ?array
    {
        $hledane = strtolower($abbr);
        foreach ($terminy as $termin) {
            if (strtolower((string) $termin['abbr']) === $hledane) {
                return $termin;
            }
        }

        return null;
    }

    /**
     * @param list<array{abbr:string,full:string,popis?:string}> $terminy
     * @return list<array{abbr:string,full:string,popis?:string}>
     */
    public static function sortTerms(array $terminy): array
    {
        $kopie = array_values($terminy);
        usort($kopie, static fn (array $a, array $b): int
            => RazeniCs::porovnej((string) $a['abbr'], (string) $b['abbr']));

        return $kopie;
    }

    /**
     * Seřazené termíny nakrájené podle prvního písmene velkým. Diakritika se
     * NESTRHÁVÁ: 'ČSN' patří do skupiny 'Č'. Skupina se uzavře vždy, když se
     * písmeno liší od předchozího — můžou se tedy opakovat ('A','Á','A','Á').
     *
     * @param list<array{abbr:string,full:string,popis?:string}> $terminy
     * @return list<array{letter:string,items:list<array{abbr:string,full:string,popis?:string}>}>
     */
    public static function groupTerms(array $terminy): array
    {
        $skupiny = [];
        $pismeno = '';
        $polozky = [];

        foreach (self::sortTerms($terminy) as $termin) {
            $prvni = self::prvniVelke((string) $termin['abbr']);
            if ($prvni !== $pismeno) {
                if ($polozky !== []) {
                    $skupiny[] = ['letter' => $pismeno, 'items' => $polozky];
                }
                $pismeno = $prvni;
                $polozky = [$termin];
            } else {
                $polozky[] = $termin;
            }
        }

        if ($polozky !== []) {
            $skupiny[] = ['letter' => $pismeno, 'items' => $polozky];
        }

        return $skupiny;
    }

    /* ------------------------------------------------------------ pomocné */

    private static function delka(string $text): int
    {
        return count(preg_split('//u', $text, -1, PREG_SPLIT_NO_EMPTY) ?: []);
    }

    private static function slovni(string $znak): bool
    {
        if ($znak >= '0' && $znak <= '9') {
            return true;
        }
        if ($znak === '_' || $znak === '-') {
            return true;
        }

        return str_contains(self::SLOVNI, $znak);
    }

    /** @param list<string> $znaky */
    private static function jeAbbr(array $znaky, int $i): bool
    {
        $jmeno = strtolower(implode('', array_slice($znaky, $i + 1, 4)));
        if ($jmeno !== 'abbr') {
            return false;
        }
        $za = $znaky[$i + 5] ?? '';

        return $za === '>' || $za === ' ' || $za === "\t" || $za === "\n" || $za === "\r";
    }

    /**
     * Pozice za nejbližším </abbr> od $i, nebo null.
     *
     * @param list<string> $znaky
     */
    private static function konecAbbr(array $znaky, int $i): ?int
    {
        $pocet = count($znaky);
        for ($j = $i; $j + 6 < $pocet; $j++) {
            if ($znaky[$j] === '<' && $znaky[$j + 1] === '/'
                && strtolower(implode('', array_slice($znaky, $j + 2, 4))) === 'abbr'
                && $znaky[$j + 6] === '>') {
                return $j + 7;
            }
        }

        return null;
    }

    private static function prvniVelke(string $text): string
    {
        $znaky = preg_split('//u', $text, -1, PREG_SPLIT_NO_EMPTY) ?: [];
        if ($znaky === []) {
            return '';
        }
        $prvni = $znaky[0];

        return self::VELKE[$prvni] ?? strtoupper($prvni);
    }
}
