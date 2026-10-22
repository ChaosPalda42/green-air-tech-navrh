<?php
/* Jedno spojení do MariaDB na celý požadavek. Údaje jsou v config/config.php,
   který vznikne při instalaci. */

declare(strict_types=1);

namespace App\Db;

use App\Jadro\Config;

final class Spojeni
{
    private static ?\PDO $pdo = null;

    public static function dej(): \PDO
    {
        if (self::$pdo instanceof \PDO) {
            return self::$pdo;
        }
        $d = Config::dej('databaze', []);
        $dsn = sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
            (string) ($d['host'] ?? 'localhost'),
            (int) ($d['port'] ?? 3306),
            (string) ($d['jmeno'] ?? ''),
        );
        self::$pdo = new \PDO($dsn, (string) ($d['uzivatel'] ?? ''), (string) ($d['heslo'] ?? ''), [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            \PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        return self::$pdo;
    }

    /** Pro testy a instalátor: podstrčí hotové spojení. */
    public static function nastav(?\PDO $pdo): void
    {
        self::$pdo = $pdo;
    }

    /** Jsou tabulky na svém místě? */
    public static function pripraveno(): bool
    {
        try {
            self::dej()->query('SELECT 1 FROM uzivatele LIMIT 1');
            return true;
        } catch (\Throwable) {
            return false;
        }
    }

    /** Přehraje schema.sql; nic nepřepíše, jen doplní, co chybí. */
    public static function migruj(?string $soubor = null): void
    {
        $soubor ??= dirname(__DIR__, 2) . '/databaze/schema.sql';
        if (!is_file($soubor)) {
            // Tiché nic by se projevilo až jako „tabulka uzivatele neexistuje“
            // kdesi dál — a hledalo by se to špatně.
            throw new \RuntimeException('Chybí schéma databáze: ' . $soubor);
        }
        $radky = explode("\n", (string) file_get_contents($soubor));
        // poznámky pryč nejdřív, jinak by zakomentovaný řádek spolkl příkaz za sebou
        $cisty = implode("\n", array_filter(
            $radky,
            static fn (string $r): bool => !str_starts_with(trim($r), '--'),
        ));
        $pdo = self::dej();
        foreach (explode(';', $cisty) as $prikaz) {
            $prikaz = trim($prikaz);
            if ($prikaz !== '') {
                $pdo->exec($prikaz);
            }
        }
    }
}
