<?php
/* C-015 — serverová validace poptávkového formuláře.
   Chová se stejně jako ukázková knihovna src/lib/form-validate.mjs. */

declare(strict_types=1);

namespace App\Formular;

final class Validace
{
    public static function isEmail(mixed $hodnota): bool
    {
        if (!is_string($hodnota) || $hodnota === '') {
            return false;
        }
        if (preg_match('/\s/u', $hodnota) === 1) {
            return false;
        }
        if (str_contains($hodnota, '..')) {
            return false;
        }
        $at = strpos($hodnota, '@');
        if ($at === false || $at !== strrpos($hodnota, '@')) {
            return false;
        }
        $local = substr($hodnota, 0, $at);
        $domena = substr($hodnota, $at + 1);
        if ($local === '' || $domena === '') {
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
        $tld = end($casti);
        if (strlen($tld) < 2 || preg_match('/^[A-Za-z]{2,}$/', $tld) !== 1) {
            return false;
        }
        return true;
    }

    public static function normalizePhone(mixed $hodnota): string
    {
        if (!is_string($hodnota)) {
            return '';
        }
        $cist = preg_replace('/[\s()\-\x{00A0}\x{2010}\x{2011}\x{2012}\x{2013}\x{2014}\x{2015}\x{2212}]/u', '', $hodnota) ?? '';
        if (preg_match('/^00\d{9,15}$/', $cist) === 1) {
            return '+' . substr($cist, 2);
        }
        if (preg_match('/^420\d{9}$/', $cist) === 1) {
            return '+' . $cist;
        }
        if (preg_match('/^\d{9}$/', $cist) === 1) {
            return '+420' . $cist;
        }
        return $cist;
    }

    public static function isPhoneCz(mixed $hodnota): bool
    {
        if (!is_string($hodnota) || $hodnota === '') {
            return false;
        }
        return preg_match('/^\+420[2-79]\d{8}$/', self::normalizePhone($hodnota)) === 1;
    }

    public static function isPhone(mixed $hodnota): bool
    {
        if (!is_string($hodnota) || $hodnota === '') {
            return false;
        }
        $v = self::normalizePhone($hodnota);
        if (str_starts_with($v, '+420')) {
            return self::isPhoneCz($hodnota);
        }
        return preg_match('/^\+[1-9]\d{8,14}$/', $v) === 1;
    }

    public static function validateContact(array $hodnoty, array $zpravy = []): array
    {
        $chyby = [];

        $typ = is_string($hodnoty['typ'] ?? null) ? trim($hodnoty['typ']) : '';
        if ($typ === '') {
            $chyby['typ'] = 'required';
        }

        $jmeno = is_string($hodnoty['jmeno'] ?? null) ? trim($hodnoty['jmeno']) : '';
        if ($jmeno === '') {
            $chyby['jmeno'] = 'required';
        }

        $email = is_string($hodnoty['email'] ?? null) ? trim($hodnoty['email']) : '';
        if ($email !== '' && !self::isEmail($email)) {
            $chyby['email'] = 'email';
        }

        $telefon = is_string($hodnoty['telefon'] ?? null) ? trim($hodnoty['telefon']) : '';
        if ($telefon !== '' && !self::isPhone($telefon)) {
            $chyby['telefon'] = 'telefon';
        }

        if ($telefon === '' && $email === '') {
            $chyby['kontakt'] = 'kontakt';
        }

        $zprava = is_string($hodnoty['zprava'] ?? null) ? trim($hodnoty['zprava']) : '';
        if ($zprava !== '' && mb_strlen($zprava) < 10) {
            $chyby['zprava'] = 'zprava-kratka';
        }

        if (($hodnoty['souhlas'] ?? null) !== true) {
            $chyby['souhlas'] = 'souhlas';
        }

        $texty = [];
        foreach (array_keys($chyby) as $pole) {
            $kod = $chyby[$pole];
            if (array_key_exists($pole, $zpravy)) {
                $texty[$pole] = $zpravy[$pole];
            } elseif (array_key_exists($kod, $zpravy)) {
                $texty[$pole] = $zpravy[$kod];
            } else {
                $texty[$pole] = $kod;
            }
        }

        return [
            'ok' => $chyby === [],
            'errors' => $chyby,
            'messages' => $texty,
        ];
    }
}
