<?php

declare(strict_types=1);

namespace App\Fotky;

use RuntimeException;

final class Zpracovani implements Ulozny
{
    public function __construct(
        private readonly string $kamNaDisk,
        private readonly string $verejnaCesta
    ) {
    }

    public function uloz(string $docasnySoubor, string $puvodniJmeno): array
    {
        if (!file_exists($docasnySoubor) || filesize($docasnySoubor) === 0) {
            throw new RuntimeException('Soubor neexistuje nebo je prázdný.');
        }

        $info = @getimagesize($docasnySoubor);
        if ($info === false) {
            throw new RuntimeException('Soubor není platný obrázek.');
        }

        [$sirka, $vyska, $typ] = $info;

        // Zmenšení (resize)
        $maxHrana = 1600;
        if ($sirka > $maxHrana || $vyska > $maxHrana) {
            $poměr = $sirka / $vyska;
            if ($sirka > $vyska) {
                $novaSirka = $maxHrana;
                $novaVyska = (int)round($maxHrana / $poměr);
            } else {
                $novaVyska = $maxHrana;
                $novaSirka = (int)round($maxHrana * $poměr);
            }
            
            $zdroj = imagecreatefromstring(file_get_contents($docasnySoubor));
            if ($zdroj === false) {
                throw new RuntimeException('Nepodařilo se načíst obrázek.');
            }

            $novyObraz = imagecreatetruecolor($novaSirka, $novaVyska);
            
            // Zachování průhlednosti pro PNG/WebP
            imagealphablending($novyObraz, false);
            imagesavealpha($novyObraz, true);
            
            imagecopyresampled($novyObraz, $zdroj, 0, 0, 0, 0, $novaSirka, $novaVyska, $sirka, $vyska);
            
            @imagedestroy($zdroj);
            
            $obraz = $novyObraz;
            $sirka = $novaSirka;
            $vyska = $novaVyska;
        } else {
            $obraz = imagecreatefromstring(file_get_contents($docasnySoubor));
            if ($obraz === false) {
                throw new RuntimeException('Nepodařilo se načíst obrázek.');
            }

            // Úsporné PNG a skeny přijdou s paletou. imagewebp() takový obrázek
            // „uloží" jako nula bajtů a vrátí true — převod na truecolor je
            // jediné, co tomu zabrání. (Zmenšená cesta výš kreslí do
            // imagecreatetruecolor, té se to netýká.)
            if (!imageistruecolor($obraz)) {
                imagepalettetotruecolor($obraz);
            }
        }

        // Bezpečné jméno (hash obsahu původního souboru pro deterministické jméno)
        $id = hash('sha256', file_get_contents($docasnySoubor));
        $souborJmeno = $id . '.webp';
        $cestaNaDisk = rtrim($this->kamNaDisk, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $souborJmeno;

        // Převod na WebP
        // Selhání (třeba nezapisovatelná složka) hlásí výjimka níž; varování by
        // se vytisklo do těla odpovědi a rozbilo JSON i hlavičky.
        if (!@imagewebp($obraz, $cestaNaDisk, 85)) {
            @imagedestroy($obraz);
            throw new RuntimeException('Nepodařilo se uložit WebP.');
        }

        @imagedestroy($obraz);

        // imagewebp() umí vrátit true a zapsat nic. Prázdný soubor by se na
        // webu ukázal jako rozbitý obrázek, tak ho rovnou smažeme a řekneme to.
        clearstatcache(true, $cestaNaDisk);
        $bajty = (int) @filesize($cestaNaDisk);
        if ($bajty <= 0) {
            @unlink($cestaNaDisk);
            throw new RuntimeException('Nepodařilo se uložit WebP.');
        }

        return [
            'id' => $id,
            'nazev' => $puvodniJmeno,
            'typ' => 'image/webp',
            'sirka' => $sirka,
            'vyska' => $vyska,
            'bajty' => $bajty,
            'soubor' => rtrim($this->verejnaCesta, '/') . '/' . $souborJmeno,
        ];
    }
}
