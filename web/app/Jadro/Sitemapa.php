<?php
/* Sitemap.xml a robots.txt ostrého webu.

   Sitemapu dřív budoval nástroj při instalaci ze souborů v data/; stránka
   přidaná v administraci se do ní nedostala. Teď ji skládáme z téhož seznamu
   adres, jaký web umí poslat (Stranka::seznam), a index.php ji vydává přímo.
   Chybová stránka a administrace do sitemapy nepatří. */

declare(strict_types=1);

namespace App\Jadro;

final class Sitemapa
{
    /**
     * Celý obsah sitemap.xml pro adresy, které web umí poslat.
     *
     * @param array $site dokument site (jazyky, větve, služby, realizace, novinky)
     */
    public static function xml(array $site, string $domena, string $dnes): string
    {
        $koren = rtrim($domena, '/');
        $ven = '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
            . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
        foreach (array_unique(Stranka::seznam($site)) as $cesta) {
            if (str_ends_with($cesta, '404.html') || str_ends_with($cesta, 'administrace.html')) {
                continue;
            }
            $ven .= '  <url>' . "\n"
                . '    <loc>' . htmlspecialchars($koren . '/' . $cesta, ENT_XML1 | ENT_QUOTES) . '</loc>' . "\n"
                . '    <lastmod>' . htmlspecialchars($dnes, ENT_XML1 | ENT_QUOTES) . '</lastmod>' . "\n"
                . '  </url>' . "\n";
        }
        return $ven . '</urlset>' . "\n";
    }

    /** Celý obsah robots.txt. */
    public static function robots(string $domena): string
    {
        $koren = rtrim($domena, '/');
        return "User-agent: *\n"
            . "Allow: /\n"
            . "Disallow: /administrace.html\n"
            . "Disallow: /api/\n"
            . "Sitemap: {$koren}/sitemap.xml\n";
    }
}
