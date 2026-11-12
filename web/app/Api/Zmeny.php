<?php
/* C-019 — co se v administraci změnilo a jestli to ten uživatel smí.
   Server si sám spočítá, kterých oblastí se změna týká, a teprve podle toho
   se podívá do matice práv (App\Auth\Uzivatele::smi). */

declare(strict_types=1);

namespace App\Api;

use App\Auth\Uzivatele;

final class Zmeny
{
    /**
     * Seznam oblastí, kterých se změna mezi $stary a $novy týká:
     * 'texty', 'novinky', 'realizace'. Beze změny prázdné pole;
     * každá oblast se vyskytne jen jednou.
     */
    public static function oblasti(array $stary, array $novy): array
    {
        $oblasti = [];

        // texts: jakýkoli dotčený jazyk; klíč začínající "novinky." patří novinkám,
        // ostatní texty patří oblasti 'texty'.
        $stareTexty = self::splosteTexty($stary['texts'] ?? null);
        $noveTexty = self::splosteTexty($novy['texts'] ?? null);
        foreach (array_keys($stareTexty + $noveTexty) as $kluc) {
            if (($stareTexty[$kluc] ?? null) !== ($noveTexty[$kluc] ?? null)) {
                if (str_starts_with((string) $kluc, 'novinky.')) {
                    $oblasti['novinky'] = true;
                } else {
                    $oblasti['texty'] = true;
                }
            }
        }

        // realizace: cokoli se změnilo v added/edited/removed
        foreach (['added', 'edited', 'removed'] as $cast) {
            $stara = $stary['realizace'][$cast] ?? [];
            $nova = $novy['realizace'][$cast] ?? [];
            if (!is_array($stara)) {
                $stara = [];
            }
            if (!is_array($nova)) {
                $nova = [];
            }
            if ($stara !== $nova) {
                $oblasti['realizace'] = true;
            }
        }

        /* Portréty: posun fotky v kolečku týmu je úprava vzhledu obsahu
           stránky, takže sedí do stejného práva jako přepis textů — autor
           novinek na ni nedosáhne, editor obsahu ano. */
        if (($stary['portrety'] ?? null) !== ($novy['portrety'] ?? null)) {
            $oblasti['texty'] = true;
        }

        /* Tým: přidat, upravit nebo odebrat člověka je úprava obsahu stránky
           stejně jako přepis textu — a jméno s rolí se píšou do textů, takže
           dvojí právo by bylo k ničemu. */
        foreach (['added', 'edited', 'removed'] as $cast) {
            $stara = $stary['lide'][$cast] ?? [];
            $nova = $novy['lide'][$cast] ?? [];
            if (!is_array($stara)) {
                $stara = [];
            }
            if (!is_array($nova)) {
                $nova = [];
            }
            if ($stara !== $nova) {
                $oblasti['texty'] = true;
            }
        }

        return array_keys($oblasti);
    }

    /** true, když uživatel s rolí $role smí VŠECHNY spočítané oblasti. */
    public static function smiZmenit(string $role, array $stary, array $novy): bool
    {
        foreach (self::oblasti($stary, $novy) as $oblast) {
            if (!Uzivatele::smi($role, $oblast)) {
                return false;
            }
        }
        return true;
    }

    /** texts: [jazyk => [kluc => hodnota]] splaští na [kluc => hodnota]. */
    private static function splosteTexty(mixed $texts): array
    {
        if (!is_array($texts)) {
            return [];
        }
        $vysledek = [];
        foreach ($texts as $jazyk => $polozky) {
            if (!is_array($polozky)) {
                continue;
            }
            foreach ($polozky as $kluc => $hodnota) {
                $vysledek[(string) $kluc] = $hodnota;
            }
        }
        return $vysledek;
    }
}
