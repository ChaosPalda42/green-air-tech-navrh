<?php
/* Vytvoří sitemap.xml a robots.txt ostrého webu.

   Adresa domény se bere z nastavení (klíč 'web'), seznam stránek z téhož
   místa jako vykreslování — takže sitemapa nemůže tvrdit něco jiného,
   než co web umí poslat.

   Použití:
     php tools/sitemap.php                    # zapíše do web/public
     php tools/sitemap.php --kam /jina/cesta
     php tools/sitemap.php --web https://www.priklad.cz

   Instalátor si tenhle soubor jen vyžádá (require) a zavolá sitemapZapis();
   při spuštění z příkazové řádky se postará sám. */

declare(strict_types=1);

/**
 * Zapíše sitemap.xml a robots.txt. Vrací ['stranek' => int, 'celkem' => int].
 *
 * @param string $web     složka web/ (vedle app/, data/, public/)
 * @param string $kam     kam soubory zapsat
 * @param string $domena  adresa webu bez lomítka na konci
 */
function sitemapZapis(string $web, string $kam, string $domena): array
{
    $kam = rtrim($kam, '/');
    $domena = rtrim($domena, '/');

    $zdroj = new App\Obsah\ZdrojJson($web . '/data', $web . '/public/assets');
    $vsechny = App\Jadro\Stranka::seznam($zdroj->site());

    $stranky = array_values(array_filter(
        $vsechny,
        static fn (string $c): bool => !str_ends_with($c, '404.html') && !str_ends_with($c, 'administrace.html')
    ));
    sort($stranky, SORT_STRING);

    $dnes = date('Y-m-d');
    $polozky = [];
    foreach ($stranky as $cesta) {
        $adresa = htmlspecialchars($domena . '/' . $cesta, ENT_XML1 | ENT_QUOTES, 'UTF-8');
        $priorita = $cesta === 'index.html' ? '1.0' : (str_contains($cesta, '/') ? '0.6' : '0.8');
        $polozky[] = "  <url>\n    <loc>{$adresa}</loc>\n    <lastmod>{$dnes}</lastmod>\n"
            . "    <priority>{$priorita}</priority>\n  </url>";
    }

    $xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        . "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        . implode("\n", $polozky) . "\n</urlset>\n";

    $robots = "User-agent: *\n"
        . "Allow: /\n"
        . "Disallow: /administrace.html\n"
        . "Disallow: /api/\n\n"
        . "Sitemap: {$domena}/sitemap.xml\n";

    if (file_put_contents($kam . '/sitemap.xml', $xml) === false) {
        throw new RuntimeException("Nepovedlo se zapsat {$kam}/sitemap.xml");
    }
    if (file_put_contents($kam . '/robots.txt', $robots) === false) {
        throw new RuntimeException("Nepovedlo se zapsat {$kam}/robots.txt");
    }

    return ['stranek' => count($stranky), 'celkem' => count($vsechny)];
}

/* --------------------------------------------- spuštění z příkazové řádky */

if (PHP_SAPI === 'cli' && isset($argv) && realpath($argv[0]) === realpath(__FILE__)) {
    $kandidati = [dirname(__DIR__) . '/web', '/var/www/greenairtech/web'];
    $web = null;
    foreach ($kandidati as $k) {
        if (is_file($k . '/app/Jadro/Autoload.php')) {
            $web = $k;
            break;
        }
    }
    if ($web === null) {
        fwrite(STDERR, "Nenašel jsem složku web/.\n");
        exit(2);
    }
    require $web . '/app/Jadro/Autoload.php';

    $volby = [];
    for ($i = 1; $i < $argc; $i++) {
        if (str_starts_with($argv[$i], '--') && isset($argv[$i + 1])) {
            $volby[substr($argv[$i], 2)] = $argv[++$i];
        }
    }

    $kam = $volby['kam'] ?? ($web . '/public');
    $domena = $volby['web'] ?? (string) App\Jadro\Config::dej('web', '');
    if ($domena === '') {
        fwrite(STDERR, "Chybí adresa webu — doplňte 'web' do config.php nebo použijte --web.\n");
        exit(2);
    }
    if (!is_dir($kam) || !is_writable($kam)) {
        fwrite(STDERR, "Do {$kam} se nedá zapisovat.\n");
        exit(2);
    }

    try {
        $pocty = sitemapZapis($web, $kam, $domena);
    } catch (Throwable $e) {
        fwrite(STDERR, $e->getMessage() . "\n");
        exit(1);
    }

    printf(
        "sitemap.xml: %d adres (z %d stránek), robots.txt: hotovo\nsložka: %s\n",
        $pocty['stranek'],
        $pocty['celkem'],
        rtrim($kam, '/')
    );
}
