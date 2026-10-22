<?php
/* Nastavení webu. Soubor config/config.php vytváří instalátor; v repozitáři
   není, protože obsahuje přístup k databázi. config/config.vzor.php je vzor. */

declare(strict_types=1);

namespace App\Jadro;

final class Config
{
    private static ?array $data = null;

    /** @return array<string,mixed> */
    public static function vse(): array
    {
        if (self::$data === null) {
            $cesta = dirname(__DIR__, 2) . '/config/config.php';
            $data = is_file($cesta) ? require $cesta : [];
            self::$data = is_array($data) ? $data : [];
        }
        return self::$data;
    }

    public static function dej(string $klic, mixed $vychozi = null): mixed
    {
        $kus = self::vse();
        foreach (explode('.', $klic) as $k) {
            if (!is_array($kus) || !array_key_exists($k, $kus)) {
                return $vychozi;
            }
            $kus = $kus[$k];
        }
        return $kus;
    }

    /** Jen pro testy: podstrčí nastavení bez souboru. */
    public static function nastav(?array $data): void
    {
        self::$data = $data;
    }

    /** Ukázkový režim: noindex a demo cedulky. Ostrý web má false. */
    public static function ukazka(): bool
    {
        return (bool) self::dej('ukazka', false);
    }
}
