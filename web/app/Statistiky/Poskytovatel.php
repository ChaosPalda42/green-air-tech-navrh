<?php
/* Odkud nástěnka bere čísla. Na ostrém webu Google Analytics (App\Statistiky\Ga4),
   v ukázce je generoval prohlížeč (src/lib/statistiky.mjs). Tvar je stejný, aby
   nástěnka nepoznala rozdíl. */

declare(strict_types=1);

namespace App\Statistiky;

interface Poskytovatel
{
    /**
     * Přehled za posledních $dni dní.
     *
     * @return array{
     *   dny: list<array{datum:string,navstevy:int,uzivatele:int,zobrazeni:int,poptavky:int,cas:float,opusteni:float}>,
     *   rozpady: array<string, list<array{nazev:string,podil:int}>>
     * }
     */
    public function prehled(int $dni): array;
}
