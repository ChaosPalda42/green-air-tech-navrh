<?php
/* Přihlášení do administrace: sezení, token proti podstrčeným požadavkům
   (CSRF) a zdržení po špatném heslu. Nic víc — kdo co smí, řeší
   App\Auth\Uzivatele. */

declare(strict_types=1);

namespace App\Auth;

final class Sezeni
{
    private const KLIC_UZIVATEL = 'gat_uzivatel';
    private const KLIC_CSRF = 'gat_csrf';
    private const KLIC_POKUSY = 'gat_pokusy';

    public static function zacni(): void
    {
        if (session_status() === PHP_SESSION_ACTIVE) {
            return;
        }
        session_name('GATADMIN');
        session_set_cookie_params([
            'lifetime' => 0,
            'path' => '/',
            'httponly' => true,
            'samesite' => 'Lax',
            // za HTTPS se cookie nesmí posílat nešifrovaně; na http (zkoušení) by
            // ji prohlížeč zahodil, proto se to pozná z požadavku
            'secure' => (($_SERVER['HTTPS'] ?? '') !== '')
                || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https'),
        ]);
        session_start();
    }

    /** Přihlášený uživatel ['id','jmeno','email','role'], nebo null. */
    public static function uzivatel(): ?array
    {
        self::zacni();
        $u = $_SESSION[self::KLIC_UZIVATEL] ?? null;
        return is_array($u) ? $u : null;
    }

    public static function prihlas(array $uzivatel): void
    {
        self::zacni();
        session_regenerate_id(true);
        $_SESSION[self::KLIC_UZIVATEL] = [
            'id' => (int) ($uzivatel['id'] ?? 0),
            'jmeno' => (string) ($uzivatel['jmeno'] ?? ''),
            'email' => (string) ($uzivatel['email'] ?? ''),
            'role' => (string) ($uzivatel['role'] ?? ''),
        ];
        unset($_SESSION[self::KLIC_POKUSY]);
    }

    public static function odhlas(): void
    {
        self::zacni();
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $p = session_get_cookie_params();
            setcookie(session_name(), '', [
                'expires' => time() - 42000, 'path' => $p['path'], 'domain' => $p['domain'],
                'secure' => $p['secure'], 'httponly' => $p['httponly'], 'samesite' => 'Lax',
            ]);
        }
        session_destroy();
    }

    public static function csrf(): string
    {
        self::zacni();
        if (!is_string($_SESSION[self::KLIC_CSRF] ?? null) || $_SESSION[self::KLIC_CSRF] === '') {
            $_SESSION[self::KLIC_CSRF] = bin2hex(random_bytes(32));
        }
        return $_SESSION[self::KLIC_CSRF];
    }

    public static function csrfPlati(?string $token): bool
    {
        self::zacni();
        $ulozeny = $_SESSION[self::KLIC_CSRF] ?? null;
        return is_string($ulozeny) && is_string($token) && $token !== ''
            && hash_equals($ulozeny, $token);
    }

    /** Po třetím špatném heslu se každý další pokus zdrží. */
    public static function pocetPokusu(): int
    {
        self::zacni();
        return (int) ($_SESSION[self::KLIC_POKUSY] ?? 0);
    }

    public static function spatneHeslo(): void
    {
        self::zacni();
        $_SESSION[self::KLIC_POKUSY] = self::pocetPokusu() + 1;
        $zdrzeni = min(3, max(0, self::pocetPokusu() - 2));
        if ($zdrzeni > 0) {
            sleep($zdrzeni);
        }
    }
}
