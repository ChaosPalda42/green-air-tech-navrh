<?php
/* Vykreslí stránku ostrého webu do stdout — pro bajtový diff proti ukázce.

   Použití:
     php tools/vykresli.php index.html
     php tools/vykresli.php en/kontakt.html
     php tools/vykresli.php --seznam        # všechny adresy, jedna na řádek

   Data bere z web/data (tam je build.mjs kopíruje), hashe aktiv z out/web/assets. */

declare(strict_types=1);

$koren = dirname(__DIR__);
require $koren . '/web/app/Jadro/Autoload.php';

use App\Jadro\Stranka;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson($koren . '/web/data', $koren . '/web/public/assets');
$arg = $argv[1] ?? '';

if ($arg === '--seznam') {
    echo implode("\n", Stranka::seznam($zdroj->site())), "\n";
    exit(0);
}
if ($arg === '--vse') {
    $cil = $argv[2] ?? '';
    if ($cil === '') {
        fwrite(STDERR, "Chybí cílová složka.\n");
        exit(2);
    }
    $chyby = 0;
    foreach (Stranka::seznam($zdroj->site()) as $cesta) {
        $soubor = $cil . '/' . $cesta;
        @mkdir(dirname($soubor), 0o777, true);
        try {
            $html = Stranka::html($cesta, $zdroj, true);
            if ($html === null) {
                throw new \RuntimeException('adresa se nerozpoznala');
            }
            file_put_contents($soubor, $html);
        } catch (\Throwable $e) {
            $chyby++;
            file_put_contents($soubor . '.chyba', get_class($e) . ': ' . $e->getMessage() . "\n");
        }
    }
    fwrite(STDERR, "nevykresleno: {$chyby}\n");
    exit(0);
}
if ($arg === '') {
    fwrite(STDERR, "Chybí adresa stránky.\n");
    exit(2);
}

$html = Stranka::html($arg, $zdroj, true);
if ($html === null) {
    fwrite(STDERR, "Taková stránka není: {$arg}\n");
    exit(1);
}
echo $html;
