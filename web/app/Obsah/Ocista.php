<?php
/* Očista textů, které přišly z administrace. Texty se na webu vypisují jako
   HTML (aby fungovalo <br>), takže se musí očistit na jednom místě — při
   ukládání, než se text dostane do databáze.

   Povolené jsou jen značky br, b, strong, i, em bez atributů; vše ostatní
   (včetně povolené značky s atributem) se vypíše jako text. Ampersand se
   nepřepisuje — očista je idempotentní a dvojí uložení text nerozpadne. */

declare(strict_types=1);

namespace App\Obsah;

final class Ocista
{
    /** Povolená značka bez atributů; srovná se na malá písmena a `<br>`. */
    private const VZOR = '/(<\\s*\\/?\\s*(?:br|b|strong|i|em)\\s*\\/?\\s*>)/i';

    /**
     * Vrátí text, ve kterém zůstaly jen povolené HTML značky; ostatní `<` a
     * `>` jsou zapsané jako `&lt;` a `&gt;`.
     */
    public static function text(string $text): string
    {
        // 1. Rozdělíme text na části podle povolených značek.
        // PREG_SPLIT_DELIM_CAPTURE zajistí, že samotné značky budou součástí pole.
        $parts = preg_split(self::VZOR, $text, -1, PREG_SPLIT_DELIM_CAPTURE);

        if ($parts === false) {
            // Stát by se to nemělo (vzor je pevný), ale kdyby ano, je lepší
            // vrátit text celý escapovaný než o něj přijít.
            return str_replace(['<', '>'], ['&lt;', '&gt;'], $text);
        }

        $ven = '';
        foreach ($parts as $index => $part) {
            // Pokud je index sudý, jde o text mezi značkami.
            // Pokud je index lichý, jde o samotnou značku (díky PREG_SPLIT_DELIM_CAPTURE).
            if ($index % 2 === 0) {
                // Text mezi značkami: musíme ošetřit všechny < a >.
                $ven .= str_replace(['<', '>'], ['&lt;', '&gt;'], $part);
            } else {
                // Povolená značka: normalizujeme ji.
                $ven .= self::normalizeTag($part);
            }
        }

        return $ven;
    }

    /**
     * Normalizuje povolenou značku na malá písmena a odstraní zbytečné mezery/samozavřírky.
     * Např. <BR>, <br/>, <br /> -> <br>
     */
    private static function normalizeTag(string $tag): string
    {
        // Odstraníme všechno kolem značky, abychom zjistili typ.
        // Regex pro extrakci: (slash?)(tagname)(slash?)
        if (preg_match('/<\\s*(\\/?)\\s*(br|b|strong|i|em)\\s*(\\/?)\\s*>/i', $tag, $m)) {
            $slash = $m[1];
            $name = strtolower($m[2]);
            // Pro br (void element) se v testech očekává vždy <br> bez /
            if ($name === 'br') {
                return '<br>';
            }
            // Pro ostatní značky (b, strong, i, em) zachováme slash pokud tam je.
            // Testy neukazují explicitně jak má vypadat </B>, ale standardně by to mělo být </b>.
            return '<' . $slash . $name . '>';
        }
        return ''; // Should not happen if VZOR matched
    }

    /**
     * Projde dokument rekurzivně a na KAŽDÝ řetězec (klíče i hodnoty) použije
     * text(). Čísla, logické hodnoty a null zůstávají; struktura a pořadí
     * klíčů se nemění.
     */
    public static function stav(array $stav): array
    {
        $ven = [];
        foreach ($stav as $klic => $hodnota) {
            $ven[self::text((string) $klic)] = self::hodnota($hodnota);
        }

        return $ven;
    }

    private static function hodnota(mixed $hodnota): mixed
    {
        if (is_string($hodnota)) {
            return self::text($hodnota);
        }
        if (is_array($hodnota)) {
            return self::stav($hodnota);
        }

        return $hodnota;
    }
}
