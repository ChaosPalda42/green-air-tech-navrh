<?php
/* Odkud šablony berou obsah. Dvě implementace: ZdrojJson (soubory, jako
   v ukázce) a ZdrojDb (MariaDB, ostrý web). Díky tomuhle řezu se dá celý
   web vykreslit a porovnat s ukázkou bez databáze. */

declare(strict_types=1);

namespace App\Obsah;

interface Zdroj
{
    /** Struktura webu: firma, jazyky, větve, služby, realizace, novinky. */
    public function site(): array;

    /** Překlady jednoho jazyka ve vnořeném tvaru. */
    public function dict(string $jazyk): array;

    /** Zkratky pro vysvětlivky: abbr => ['full' => …, 'popis' => …]. */
    public function slovnik(string $jazyk): array;

    /** Manifest obrázků z optimize_images.py. */
    public function obrazky(): array;

    /** Otisky aktiv pro ?v=… (jméno souboru => prvních 8 znaků sha1). */
    public function verzeAktiv(): array;
}
