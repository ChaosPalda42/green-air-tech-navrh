<?php
/* C-030 — první heslo z pozvánky: rozhoduje, co se smí stát, když někdo
   přijde na administraci s tokenem pozvánky. Čisté PHP: žádný stav, žádná
   síť, žádná databáze, žádný echo. Účet i token podá volající, zápis do
   databáze udělá volající. Vstupní pole se nemutují. */

declare(strict_types=1);

namespace App\Auth;

final class Pozvanka
{
    /**
     * Co dostane stránka s formulářem na nastavení hesla.
     * Neplatná pozvánka (viz plati()) → PRÁZDNÉ pole.
     * Platná → přesně ['token', 'jmeno', 'email'] a nic víc.
     */
    public static function proStranku(?array $ucet, string $token): array
    {
        if (!self::plati($ucet, $token)) {
            return [];
        }
        return [
            'token' => $token,
            'jmeno' => (string) $ucet['jmeno'],
            'email' => (string) $ucet['email'],
        ];
    }

    /**
     * Rozhodnutí o uplatnění pozvánky.
     *   ['stav' => 'propadla']
     *   ['stav' => 'vadne-heslo', 'duvod' => 'prazdne'|'kratke']
     *   ['stav' => 'nesouhlasi']
     *   ['stav' => 'ok', 'zapis' => ['id' => int, 'heslo_hash' => string,
     *                                'pozvanka_token' => null, 'pozvanka_do' => null]]
     * Pořadí: nejdřív platnost pozvánky, pak síla hesla, pak shoda.
     */
    public static function prijmi(?array $ucet, string $token, string $heslo, string $heslo2): array
    {
        if (!self::plati($ucet, $token)) {
            return ['stav' => 'propadla'];
        }

        $vada = Uzivatele::zkontrolujHeslo($heslo);
        if ($vada !== null) {
            return ['stav' => 'vadne-heslo', 'duvod' => $vada];
        }

        if ($heslo !== $heslo2) {
            return ['stav' => 'nesouhlasi'];
        }

        return [
            'stav' => 'ok',
            'zapis' => [
                'id' => (int) $ucet['id'],
                'heslo_hash' => Uzivatele::hash($heslo),
                'pozvanka_token' => null,
                'pozvanka_do' => null,
            ],
        ];
    }

    /**
     * Pozvánka platí jen tehdy, když se token DOSLOVA rovná tomu, co má účet
     * v databázi, ještě neuplynula platnost a účet je aktivní. Cokoli
     * jiného je propadlá pozvánka — a mlčí stejně, aby se z odpovědi nedalo
     * vyčíst, který token existuje.
     */
    private static function plati(?array $ucet, string $token): bool
    {
        if ($ucet === null || $token === '') {
            return false;
        }

        if (($ucet['aktivni'] ?? 0) != 1) {
            return false;
        }

        $ukladany = $ucet['pozvanka_token'] ?? null;
        if (!is_string($ukladany) || $ukladany === '' || $ukladany !== $token) {
            return false;
        }

        return Uzivatele::pozvankaPlati([
            'token' => $ukladany,
            'do' => $ucet['pozvanka_do'] ?? null,
        ]);
    }
}
