<?php
/* Co se stane, když něco spadne. Na ostrém webu nesmí z odpovědi vypadnout
   ani hláska PHP: varování rozbije JSON (a hlavičky, protože se tiskne dřív
   než ony) a výpis zásobníku prozradí cesty na serveru. Všechno proto jde do
   logu a návštěvník dostane krátkou 500. */

declare(strict_types=1);

namespace App\Jadro;

final class Chyby
{
    private static bool $odpovezeno = false;

    public static function nastav(): void
    {
        error_reporting(E_ALL);
        ini_set('display_errors', '0');
        ini_set('display_startup_errors', '0');
        ini_set('log_errors', '1');

        set_error_handler(static function (int $druh, string $zprava, string $soubor, int $radek): bool {
            error_log(sprintf('[%s] %s v %s:%d', self::jmenoDruhu($druh), $zprava, $soubor, $radek));

            // Varování web nepoloží, jen se zapíše. Chyba ano.
            if (in_array($druh, [E_ERROR, E_USER_ERROR, E_RECOVERABLE_ERROR], true)) {
                self::odpoved();
                exit(1);
            }

            return true;
        });

        set_exception_handler(static function (\Throwable $vyjimka): void {
            error_log(sprintf(
                'neodchycená %s: %s v %s:%d',
                $vyjimka::class,
                $vyjimka->getMessage(),
                $vyjimka->getFile(),
                $vyjimka->getLine()
            ));
            self::odpoved();
        });

        register_shutdown_function(static function (): void {
            $posledni = error_get_last();
            if ($posledni === null) {
                return;
            }
            if (!in_array($posledni['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
                return;
            }
            error_log(sprintf(
                'fatální: %s v %s:%d',
                $posledni['message'],
                $posledni['file'],
                $posledni['line']
            ));
            self::odpoved();
        });
    }

    /** Krátká 500 — JSON pro API, jinak stránka. Nikdy nic z té chyby. */
    private static function odpoved(): void
    {
        if (self::$odpovezeno) {
            return;
        }
        self::$odpovezeno = true;

        // Co se už vytisklo, ještě můžeme zahodit — jinak by to zůstalo v těle.
        while (ob_get_level() > 0) {
            @ob_end_clean();
        }

        if (headers_sent()) {
            return;
        }

        http_response_code(500);

        if (self::jeApi()) {
            header('Content-Type: application/json; charset=utf-8');
            echo '{"chyba":"chyba-serveru"}';
            return;
        }

        header('Content-Type: text/html; charset=utf-8');
        echo "<!doctype html>\n<html lang=\"cs\"><meta charset=\"utf-8\">"
            . "<title>Nepovedlo se</title>"
            . "<style>body{font:16px/1.5 system-ui,sans-serif;margin:4rem auto;max-width:30rem;padding:0 1rem}</style>"
            . "<h1>Něco se nepovedlo</h1>"
            . "<p>Stránku se teď nepodařilo připravit. Zkuste to prosím za chvíli znovu.</p>\n";
    }

    private static function jeApi(): bool
    {
        $cesta = (string) ($_SERVER['REQUEST_URI'] ?? '');
        $cesta = (string) parse_url($cesta, PHP_URL_PATH);

        return str_starts_with($cesta, '/api/');
    }

    private static function jmenoDruhu(int $druh): string
    {
        return match ($druh) {
            E_ERROR, E_USER_ERROR => 'chyba',
            E_WARNING, E_USER_WARNING => 'varování',
            E_NOTICE, E_USER_NOTICE => 'poznámka',
            E_DEPRECATED, E_USER_DEPRECATED => 'zastaralé',
            E_RECOVERABLE_ERROR => 'zachytitelná chyba',
            default => 'hlášení ' . $druh,
        };
    }
}
