<?php
/* Co se stane s nahranou fotkou. Ostrý web ji zmenší a uloží do
   public/media (App\Fotky\Zpracovani); v testu stačí pole. */

declare(strict_types=1);

namespace App\Fotky;

interface Ulozny
{
    /**
     * Zpracuje nahraný soubor a vrátí popis fotky pro stav administrace.
     *
     * @return array{id:string,nazev:string,typ:string,sirka:int,vyska:int,bajty:int,soubor:string}
     * @throws \RuntimeException když soubor není obrázek nebo se nedá zpracovat
     */
    public function uloz(string $docasnySoubor, string $puvodniJmeno): array;
}
