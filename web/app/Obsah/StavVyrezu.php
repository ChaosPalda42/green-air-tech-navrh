<?php
/* Stav administrace — část 'portrety': výřez fotky v kolečku týmu.
   Zrcadlí src/lib/cms-store.mjs (normalizeVyrez, jeVychoziVyrez, setVyrez,
   getVyrez, mergeVyrezy), aby server vykreslil totéž co ukázka.

   Výřez je `zoom` (přiblížení v procentech, 100 = celá fotka) a `x`/`y`
   (posun fotky v procentech šířky kolečka). Posun nesmí odkrýt okraj, takže
   ho omezuje přiblížení: při zoomu 100 se posunout nedá vůbec, při 160 je po
   každé straně navíc 30 %. Hodnoty jsou celá procenta — tentýž výřez musí
   v PHP i v JS vyjít na stejné bajty (hlídá tests/test_php_shoda_stranek.py). */

declare(strict_types=1);

namespace App\Obsah;

final class StavVyrezu
{
    public const VYCHOZI = ['zoom' => 100, 'x' => 0, 'y' => 0];
    public const MAX_ZOOM = 250;

    /** Hodnoty v mezích a na celá procenta; posun zkrácený podle přiblížení. */
    public static function normalizuj(mixed $vyrez): array
    {
        $v = is_array($vyrez) ? $vyrez : [];
        $zoom = self::zaokrouhli(self::cislo($v['zoom'] ?? null, 100));
        if ($zoom < 100) {
            $zoom = 100;
        }
        if ($zoom > self::MAX_ZOOM) {
            $zoom = self::MAX_ZOOM;
        }
        $mez = ($zoom - 100) / 2;

        return ['zoom' => $zoom, 'x' => self::omez($v['x'] ?? null, $mez), 'y' => self::omez($v['y'] ?? null, $mez)];
    }

    public static function jeVychozi(mixed $vyrez): bool
    {
        return self::normalizuj($vyrez) === self::VYCHOZI;
    }

    /** Nastaví výřez jednoho člověka; `null` záznam ze stavu SMAŽE.

       Mazat i výřez 100/0/0 by vzalo správci možnost vrátit fotku na celou:
       soubor site.json u některých lidí přiblížení vozí a stav ho jen
       přepisuje, takže smazaný záznam znamená „nech dodané", ne
       „nepřibližuj". Prázdno se proto ukládá taky. */
    public static function nastavVyrez(array $stav, string $id, mixed $vyrez): array
    {
        $novy = self::uplny($stav);
        if ($vyrez === null) {
            unset($novy['portrety'][$id]);
        } else {
            $novy['portrety'][$id] = self::normalizuj($vyrez);
        }

        return $novy;
    }

    public static function vyrez(array $stav, string $id): ?array
    {
        $ulozeny = $stav['portrety'][$id] ?? null;
        if ($ulozeny === null) {
            return null;
        }

        return self::normalizuj($ulozeny);
    }

    /**
     * Lidé ze souborů přelepení výřezy z administrace.
     *
     * @param list<array> $zaklad
     * @return list<array>
     */
    public static function spojVyrezy(array $stav, array $zaklad): array
    {
        $prepisy = is_array($stav['portrety'] ?? null) ? $stav['portrety'] : [];
        $vysledek = [];
        foreach ($zaklad as $osoba) {
            $kopie = is_array($osoba) ? $osoba : [];
            $id = (string) ($kopie['id'] ?? '');
            if (isset($prepisy[$id])) {
                $kopie['vyrez'] = self::normalizuj($prepisy[$id]);
            }
            $vysledek[] = $kopie;
        }

        return $vysledek;
    }

    /**
     * Výřez jako hodnota atributu style, nebo prázdný řetězec u výchozího.
     * Dvě desetinná místa u přiblížení proto, aby PHP a JS napsaly tytéž
     * znaky — `1.6` proti `1.60` by rozhodila bajtová shoda s ukázkou.
     */
    public static function styl(mixed $vyrez): string
    {
        if ($vyrez === null || self::jeVychozi($vyrez)) {
            return '';
        }
        $v = self::normalizuj($vyrez);

        return '--vz:' . number_format($v['zoom'] / 100, 2, '.', '')
            . ';--vx:' . $v['x'] . '%;--vy:' . $v['y'] . '%';
    }

    /* ------------------------------------------------------------ pomocné */

    /* Jako Math.round v JS: půlky nahoru, tedy i -11.5 na -11. PHP round()
       zaokrouhluje půlky od nuly (-12) a výřez by se v PHP a v JS rozešel. */
    private static function zaokrouhli(float $n): int
    {
        return (int) floor($n + 0.5);
    }

    private static function cislo(mixed $hodnota, float $vychozi): float
    {
        if (is_int($hodnota) || is_float($hodnota)) {
            return is_finite((float) $hodnota) ? (float) $hodnota : $vychozi;
        }
        if (is_string($hodnota) && is_numeric($hodnota)) {
            return (float) $hodnota;
        }

        return $vychozi;
    }

    private static function omez(mixed $hodnota, float $mez): int
    {
        $n = self::zaokrouhli(self::cislo($hodnota, 0));
        if ($n > $mez) {
            $n = (int) floor($mez);
        }
        if ($n < -$mez) {
            $n = -(int) floor($mez);
        }

        return $n;
    }

    /** Doplní 'portrety' do stavu, který ho ještě nemá. */
    private static function uplny(array $stav): array
    {
        if (!isset($stav['portrety']) || !is_array($stav['portrety'])) {
            $stav['portrety'] = [];
        }

        return $stav;
    }
}
