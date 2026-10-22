<?php
/* C-015 — serverová validace poptávkového formuláře.
   Chová se stejně jako ukázková knihovna src/lib/form-validate.mjs. */

declare(strict_types=1);

namespace App\Formular;

final class Validace
{
    public static function isEmail(mixed $hodnota): bool
    {
        if (!is_string($hodnota)) {
            return false;
        }
        $v = $hodnota;
        if ($v === '' || str_contains($v, ' ')) {
            return false;
        }
        if (substr_count($v, '@') !== 1) {
            return false;
        }
        [$local, $domena] = explode('@', $v);
        if ($local === '') {
            return false;
        }
        $casti = explode('.', $domena);
        if (count($casti) < 2) {
            return false;
        }
        foreach ($casti as $cast) {
            if ($cast === '') {
                return false;
            }
        }
        if (!preg_match('/^[A-Za-z]{2,}$/', end($casti))) {
            return false;
        }
        return true;
    }

    public static function normalizePhone(mixed $hodnota): string
    {
        if (!is_string($hodnota)) {
            return '';
        }
        $v = preg_replace('/[\s()\-\x{00A0}\x{2010}\x{2011}\x{2012}\x{2013}\x{2014}\x{2015}\x{2212}]/u', '', $hodnota) ?? '';
        if (str_starts_with($v, '00420') && strlen($v) === 14) {
            $v = '+420' . substr($v, 5);
        } elseif (str_starts_with($v, '420') && strlen($v) === 12) {
            $v = '+420' . substr($v, 3);
        } elseif (preg_match('/^\d{9}$/', $v)) {
            $v = '+420' . $v;
        }
        return $v;
    }

    public static function isPhoneCz(mixed $hodnota): bool
    {
        if (!is_string($hodnota) || $hodnota === '') {
            return false;
        }
        $v = self::normalizePhone($hodnota);
        if (!preg_match('/^\+420(\d{9})$/', $v, $m)) {
            return false;
        }
        return in_array($m[1][0], ['6', '7', '2', '3', '5', '9'], true);
    }

    public static function validateContact(array $hodnoty, array $zpravy = []): array
    {
        $chyby = [];

        if (!is_string($hodnoty['typ'] ?? null) || trim($hodnoty['typ']) === '') {
            $chyby['typ'] = 'required';
        }
        if (!is_string($hodnoty['jmeno'] ?? null) || trim($hodnoty['jmeno']) === '') {
            $chyby['jmeno'] = 'required';
        }

        $email = is_string($hodnoty['email'] ?? null) ? $hodnoty['email'] : '';
        $telefon = is_string($hodnoty['telefon'] ?? null) ? $hodnoty['telefon'] : '';

        if ($email !== '' && !self::isEmail($email)) {
            $chyby['email'] = 'email';
        }
        if ($telefon !== '' && !self::isPhoneCz($telefon)) {
            $chyby['telefon'] = 'telefon';
        }
        if (trim($email) === '' && trim($telefon) === '') {
            $chyby['kontakt'] = 'kontakt';
        }

        $zprava = is_string($hodnoty['zprava'] ?? null) ? $hodnoty['zprava'] : '';
        $zpravaTrim = trim($zprava);
        if ($zpravaTrim !== '' && mb_strlen($zpravaTrim) < 10) {
            $chyby['zprava'] = 'zprava-kratka';
        }

        if (($hodnoty['souhlas'] ?? null) !== true) {
            $chyby['souhlas'] = 'souhlas';
        }

        $texty = [];
        foreach (array_keys($chyby) as $pole) {
            $kod = $chyby[$pole];
            $texty[$pole] = $zpravy[$pole] ?? $zpravy[$kod] ?? $kod;
        }

        return [
            'ok' => $chyby === [],
            'errors' => $chyby,
            'messages' => $texty,
        ];
    }
}
