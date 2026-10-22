<?php
/* Formátování datumů bez IntlDateFormatter ani setlocale — názvy měsíců
   jsou vypsané tabulkou, takže výsledek nezávisí na ICU na serveru. */

declare(strict_types=1);

namespace App\Obsah;

final class Datum
{
    /** Měsíce v 1. pádě (tvar 'mesic'), index 1–12. */
    private const MESICE_1 = [
        'cs' => ['', 'leden', 'únor', 'březen', 'duben', 'květen', 'červen', 'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec'],
        'en' => ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'de' => ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
    ];

    /** Měsíce v 2. pádě (český tvar 'plny'), index 1–12. */
    private const MESICE_2 = [
        'cs' => ['', 'ledna', 'února', 'března', 'dubna', 'května', 'června', 'července', 'srpna', 'září', 'října', 'listopadu', 'prosince'],
    ];

    public static function format(string $jazyk, string $iso, string $tvar = 'plny'): string
    {
        if (!preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $iso, $m)) {
            return '';
        }
        $rok = (int) $m[1];
        $mesic = (int) $m[2];
        $den = (int) $m[3];
        if ($mesic < 1 || $mesic > 12 || $den < 1 || $den > self::dnuVMesici($rok, $mesic)) {
            return '';
        }

        $jazyk = in_array($jazyk, ['cs', 'en', 'de'], true) ? $jazyk : 'cs';
        $nazev = self::MESICE_1[$jazyk][$mesic];

        if ($tvar === 'mesic') {
            return $nazev . ' ' . $rok;
        }

        if ($jazyk === 'cs') {
            return $den . '. ' . self::MESICE_2['cs'][$mesic] . ' ' . $rok;
        }
        if ($jazyk === 'de') {
            return $den . '. ' . $nazev . ' ' . $rok;
        }
        return $den . ' ' . $nazev . ' ' . $rok;
    }

    private static function dnuVMesici(int $rok, int $mesic): int
    {
        return [31, self::leap($rok) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][$mesic - 1];
    }

    private static function leap(int $rok): bool
    {
        return ($rok % 4 === 0 && $rok % 100 !== 0) || $rok % 400 === 0;
    }
}
