<?php
/* Kam si administrace ukládá, co člověk změnil. Jedna implementace sahá do
   MariaDB (App\Db\UlozisteDb), druhá je pole v testu — díky tomu se dá celé
   rozhodování o právech proměřit bez databáze. */

declare(strict_types=1);

namespace App\Api;

interface Uloziste
{
    /** Stav administrace (tvar z src/lib/cms-store.mjs); prázdné pole, když se ještě nic neuložilo. */
    public function stav(): array;

    /** Uloží stav; $kdo je jméno přihlášeného uživatele (jde do historie změn). */
    public function ulozStav(array $stav, string $kdo): void;

    /** Uživatelé administrace BEZ hashů hesel. */
    public function uzivatele(): array;

    /** Založí nebo přepíše uživatele; vrací uloženého (s id). */
    public function ulozUzivatele(array $uzivatel): array;

    public function smazUzivatele(int $id): void;

    /** Uživatel včetně hashe hesla — jen pro přihlášení. */
    public function uzivatelPodleJmena(string $jmeno): ?array;
}
