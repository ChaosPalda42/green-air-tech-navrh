<?php
/* Meze týmu ve stavu administrace. Řekne, jestli to, co administrace posílá
   v klíči `lide`, smí projít. Čisté PHP: žádný stav, žádná síť, žádná
   databáze, žádný echo, žádné superglobály. Pole podá volající.

   Stav se vkládá do KAŽDÉ stránky webu, takže tady platí stejný důvod jako
   u realizací (nález K2): bez mezí by se web nafoukl o cokoli, co někdo pošle.

   Fotka je jen cesta do `media/` — soubor tam uložil server z /api/fotka.
   Data URL se NEPUSTÍ: obrázek v textu stavu by rostl do každé stránky. */

declare(strict_types=1);

namespace App\Obsah;

final class MezeLidi
{
    /** Kolik lidí smí administrace přidat a kolik odebrat. */
    public const MAX_PRIDANYCH = StavLidi::MAX_PRIDANYCH;
    public const MAX_ODEBRANYCH = 100;

    /** Nejdelší hodnota každého pole ve znacích. */
    private const DELKY = [
        'jmeno' => 120,
        'telefon' => 40,
        'telefonHref' => 40,
        'email' => 190,
        'inicialy' => 4,
        'fotka' => 160,
    ];

    /** Id do adresy: malá písmena, číslice a pomlčky, bez pomlček na krajích. */
    private const RE_ID = '/^[a-z0-9]+(?:-[a-z0-9]+)*$/';

    /** Jméno souboru ve složce media. Tečka smí, dvě za sebou se hlídají zvlášť. */
    private const RE_JMENO = '/^[A-Za-z0-9._-]{1,120}$/';

    /**
     * Dostane obsah klíče 'lide' ze stavu administrace:
     * ['added' => list<array>, 'edited' => map<id, array>, 'removed' => list<id>].
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}
     */
    public static function zkontroluj(array $lide): array
    {
        foreach (array_keys($lide) as $klic) {
            if (!in_array($klic, ['added', 'edited', 'removed'], true)) {
                return self::chyba('nezname-pole', (string) $klic);
            }
        }
        foreach (['added', 'edited', 'removed'] as $klic) {
            if (array_key_exists($klic, $lide) && !is_array($lide[$klic])) {
                return self::chyba('vadna-hodnota', $klic);
            }
        }

        $added = $lide['added'] ?? [];
        if (count($added) > self::MAX_PRIDANYCH) {
            return self::chyba('moc-dat', 'added');
        }
        $videna = [];
        foreach ($added as $osoba) {
            if (!is_array($osoba)) {
                return self::chyba('vadny-clovek', 'added');
            }
            $id = $osoba['id'] ?? null;
            if (!is_string($id) || preg_match(self::RE_ID, $id) !== 1) {
                return self::chyba('vadne-id', 'added');
            }
            if (isset($videna[$id])) {
                return self::chyba('dvakrat-id', $id);
            }
            $videna[$id] = true;
            /* Člověk bez jména by se na stránce ukázal jako prázdné kolečko
               a nešel by poznat ani v administraci. */
            $jmeno = $osoba['jmeno'] ?? null;
            if (!is_string($jmeno) || trim($jmeno) === '') {
                return self::chyba('vadny-clovek', $id);
            }
            $chyba = self::zkontrolujPole($osoba, $id);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        $edited = $lide['edited'] ?? [];
        if (count($edited) > self::MAX_PRIDANYCH + self::MAX_ODEBRANYCH) {
            return self::chyba('moc-dat', 'edited');
        }
        foreach ($edited as $id => $osoba) {
            if (!is_string($id) || preg_match(self::RE_ID, $id) !== 1) {
                return self::chyba('vadne-id', 'edited');
            }
            if (!is_array($osoba)) {
                return self::chyba('vadny-clovek', $id);
            }
            /* Změna je dílčí (jen to, co dialog poslal), takže jméno povinné
               není — ale když přijde, nesmí být prázdné. */
            if (array_key_exists('jmeno', $osoba)
                && (!is_string($osoba['jmeno']) || trim($osoba['jmeno']) === '')) {
                return self::chyba('vadny-clovek', $id);
            }
            $chyba = self::zkontrolujPole($osoba, $id);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        $removed = $lide['removed'] ?? [];
        if (count($removed) > self::MAX_ODEBRANYCH) {
            return self::chyba('moc-dat', 'removed');
        }
        foreach ($removed as $id) {
            if (!is_string($id) || preg_match(self::RE_ID, $id) !== 1) {
                return self::chyba('vadne-id', 'removed');
            }
        }

        return ['ok' => true, 'chyba' => null, 'detail' => null];
    }

    /* ------------------------------------------------------------ pomocné */

    /** @return array{ok: bool, chyba: ?string, detail: ?string}|null null = v pořádku */
    private static function zkontrolujPole(array $osoba, string $id): ?array
    {
        foreach (array_keys($osoba) as $pole) {
            if (!in_array((string) $pole, StavLidi::POLE, true)) {
                return self::chyba('nezname-pole', (string) $pole);
            }
        }
        foreach ($osoba as $pole => $hodnota) {
            if ($pole === 'id') {
                continue;
            }
            if (!is_string($hodnota)) {
                return self::chyba('vadna-hodnota', (string) $pole);
            }
            $mez = self::DELKY[(string) $pole] ?? 0;
            if (mb_strlen($hodnota, 'UTF-8') > $mez) {
                return self::chyba('dlouhy-text', (string) $pole);
            }
        }
        if (array_key_exists('fotka', $osoba) && $osoba['fotka'] !== '') {
            $cesta = (string) $osoba['fotka'];
            if (!str_starts_with($cesta, 'media/')) {
                return self::chyba('vadna-fotka', $id);
            }
            $jmeno = substr($cesta, strlen('media/'));
            if (str_contains($jmeno, '..') || preg_match(self::RE_JMENO, $jmeno) !== 1) {
                return self::chyba('vadna-fotka', $id);
            }
        }

        return null;
    }

    /** @return array{ok: bool, chyba: string, detail: string} */
    private static function chyba(string $kod, string $detail): array
    {
        return ['ok' => false, 'chyba' => $kod, 'detail' => $detail];
    }
}
