<?php

declare(strict_types=1);

namespace App\Fotky;

use RuntimeException;

final class Zpracovani implements Ulozny
{
    /** Delší hrana, na kterou se fotka zmenšuje. */
    private const int MAX_HRANA = 1600;

    /** Kolik paměti (v bajtech) si necháme na PHP samotné a na zbytek procesu. */
    private const int REZERVA = 64 * 1024 * 1024;

    public function __construct(
        private readonly string $kamNaDisk,
        private readonly string $verejnaCesta
    ) {
    }

    public function uloz(string $docasnySoubor, string $puvodniJmeno): array
    {
        if (!is_file($docasnySoubor) || filesize($docasnySoubor) === 0) {
            throw new RuntimeException('Soubor neexistuje nebo je prázdný.');
        }

        // Rozměry čteme jen z hlavičky — obrázek se ještě nerozbaluje.
        $info = @getimagesize($docasnySoubor);
        if ($info === false) {
            throw new RuntimeException('Soubor není platný obrázek.');
        }

        [$sirka, $vyska] = $info;

        // Rozhodnutí o velikosti se dělá DŘÍV, než se obrázek rozbalí do
        // paměti. GD drží obrázek nekomprimovaný (4 bajty na pixel), takže
        // 20000×20000 je 1,6 GB a PHP na memory_limit umře fatální chybou,
        // kterou nejde odchytit. Pravidlo: vejde se to do paměti, kterou
        // server dal — ne magický strop v pixelech.
        $potrebne = $sirka * $vyska * 4;
        $limit = $this->limitPameti();
        if ($limit > 0 && $potrebne > $limit - self::REZERVA) {
            throw new MocVelka('Fotka je příliš velká, zmenšete ji prosím.');
        }

        $zdroj = imagecreatefromstring((string) file_get_contents($docasnySoubor));
        if ($zdroj === false) {
            throw new RuntimeException('Nepodařilo se načíst obrázek.');
        }

        // Úsporné PNG a skeny přijdou s paletou. imagewebp() takový obrázek
        // „uloží“ jako nula bajtů a vrátí true — převod na truecolor je
        // jediné, co tomu zabrání.
        if (!imageistruecolor($zdroj)) {
            imagepalettetotruecolor($zdroj);
        }

        // Zmenšení: delší hrana na MAX_HRANA, poměr stran se zachová.
        // Menší fotky se nezvětšují.
        $novaSirka = $sirka;
        $novaVyska = $vyska;
        if ($sirka > self::MAX_HRANA || $vyska > self::MAX_HRANA) {
            $poměr = min(self::MAX_HRANA / $sirka, self::MAX_HRANA / $vyska);
            $novaSirka = max(1, (int) round($sirka * $poměr));
            $novaVyska = max(1, (int) round($vyska * $poměr));
            $novy = imagecreatetruecolor($novaSirka, $novaVyska);
            imagecopyresampled($novy, $zdroj, 0, 0, 0, 0, $novaSirka, $novaVyska, $sirka, $vyska);
            unset($zdroj);
            $obraz = $novy;
        } else {
            $obraz = $zdroj;
        }

        // Bezpečné jméno: hash obsahu původního souboru. Nedá se uhodnout ani
        // podstrčit a tentýž obrázek podruhé dostane stejné jméno.
        $id = hash('sha256', (string) file_get_contents($docasnySoubor));
        $souborJmeno = $id . '.webp';
        $cestaNaDisk = rtrim($this->kamNaDisk, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $souborJmeno;

        // Selhání (třeba nezapisovatelná složka) hlásí výjimka níž; varování by
        // se vytisklo do těla odpovědi a rozbilo JSON i hlavičky.
        if (!@imagewebp($obraz, $cestaNaDisk, 85)) {
            throw new RuntimeException('Nepodařilo se uložit WebP.');
        }

        unset($obraz);

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
            'sirka' => $novaSirka,
            'vyska' => $novaVyska,
            'bajty' => $bajty,
            'soubor' => rtrim($this->verejnaCesta, '/') . '/' . $souborJmeno,
        ];
    }

    /**
     * Aktuální limit paměti v bajtech; 0 znamená „bez omezení“.
     */
    private function limitPameti(): int
    {
        $limit = ini_get('memory_limit');
        if ($limit === false || $limit === '' || $limit === '-1') {
            return 0;
        }

        $limit = trim((string) $limit);
        $mnozitel = 1;
        $posledni = strtolower(substr($limit, -1));
        if ($posledni === 'g') {
            $mnozitel = 1024 ** 3;
            $limit = substr($limit, 0, -1);
        } elseif ($posledni === 'm') {
            $mnozitel = 1024 ** 2;
            $limit = substr($limit, 0, -1);
        } elseif ($posledni === 'k') {
            $mnozitel = 1024;
            $limit = substr($limit, 0, -1);
        }

        return (int) ((float) $limit * $mnozitel);
    }
}
