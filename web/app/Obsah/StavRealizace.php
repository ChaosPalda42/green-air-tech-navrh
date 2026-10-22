<?php
/* Stav administrace — část 'realizace': přidané, změněné a smazané.
   Zrcadlí src/lib/cms-store.mjs (upsertRealizace, removeRealizace,
   mergeRealizace), aby se server choval přesně jako prohlížeč. */

declare(strict_types=1);

namespace App\Obsah;

final class StavRealizace
{
    /**
     * Přidá nebo změní jednu realizaci. Bez id se id vyrobí z názvu (slug);
     * při kolizi se připojuje -2, -3, …, dokud id neexistuje v základu,
     * přidaných ani změněných. Id ze základu jde do 'edited' (sloučeno s
     * předchozí změnou), jinak do 'added'. Základní id se z 'removed'
     * vybere — vrácená realizace už není smazaná.
     *
     * @return array CELÝ nový stav
     */
    public static function ulozRealizaci(array $stav, array $polozka, array $zaklad = []): array
    {
        $novy = self::uplny($stav);
        $realizace = $novy['realizace'];

        $zakladniId = [];
        foreach ($zaklad as $polozkaZakladu) {
            if (is_array($polozkaZakladu) && isset($polozkaZakladu['id'])) {
                $zakladniId[(string) $polozkaZakladu['id']] = true;
            }
        }
        $pridaneId = [];
        foreach ($realizace['added'] as $p) {
            if (is_array($p) && isset($p['id'])) {
                $pridaneId[(string) $p['id']] = true;
            }
        }

        $id = $polozka['id'] ?? null;
        if ($id === null || $id === '') {
            $id = Stav::slug((string) ($polozka['nazev'] ?? ''));
            $prifix = $id;
            $pripojka = 2;
            while (isset($zakladniId[$id]) || isset($pridaneId[$id]) || array_key_exists($id, $realizace['edited'])) {
                $id = $prifix . '-' . $pripojka;
                $pripojka++;
            }
        }

        if (isset($zakladniId[$id])) {
            $existujici = $realizace['edited'][$id] ?? [];
            $realizace['edited'][$id] = array_merge($existujici, $polozka);
            $realizace['removed'] = array_values(array_filter(
                $realizace['removed'],
                static fn ($smazane) => $smazane !== $id
            ));
        } else {
            $index = null;
            foreach ($realizace['added'] as $i => $p) {
                if (is_array($p) && ($p['id'] ?? null) === $id) {
                    $index = $i;
                    break;
                }
            }
            if ($index !== null) {
                $realizace['added'][$index] = array_merge($realizace['added'][$index], $polozka);
            } else {
                $nova = $polozka;
                if (($polozka['id'] ?? null) === null || $polozka['id'] === '') {
                    $nova['id'] = $id;
                }
                $realizace['added'][] = $nova;
            }
        }

        $novy['realizace'] = $realizace;

        return $novy;
    }

    /**
     * Smaže jednu realizaci. Přidaná se jen vybere z 'added' (do 'removed'
     * se nedává — nikdy nebyla v základu). Základní se přidá do 'removed'
     * (bez duplicit) a vybere se z 'edited'.
     *
     * @return array CELÝ nový stav
     */
    public static function smazRealizaci(array $stav, string $id): array
    {
        $novy = self::uplny($stav);
        $realizace = $novy['realizace'];

        $index = null;
        foreach ($realizace['added'] as $i => $p) {
            if (is_array($p) && ($p['id'] ?? null) === $id) {
                $index = $i;
                break;
            }
        }
        if ($index !== null) {
            array_splice($realizace['added'], $index, 1);
        } else {
            if (!in_array($id, $realizace['removed'], true)) {
                $realizace['removed'][] = $id;
            }
            unset($realizace['edited'][$id]);
        }

        $novy['realizace'] = $realizace;

        return $novy;
    }

    /**
     * Základ se změnami, bez smazaných, s přidanými, seřazený podle data
     * od nejnovějšího; položky bez data jsou nejstarší (úplně poslední),
     * při stejném datu přidané před základními.
     *
     * POZOR: NEVRACÍ STAV — vrací SEZNAM realizací (list, číslovaný od nuly).
     */
    public static function spojRealizace(array $stav, array $zaklad): array
    {
        $stav = self::uplny($stav);
        $realizace = $stav['realizace'];
        $smazane = [];
        foreach ($realizace['removed'] as $id) {
            $smazane[(string) $id] = true;
        }

        $vysledek = [];
        foreach ($zaklad as $polozka) {
            if (!is_array($polozka)) {
                continue;
            }
            $id = (string) ($polozka['id'] ?? '');
            if (isset($smazane[$id])) {
                continue;
            }
            $kopie = $polozka;
            if (isset($realizace['edited'][$id]) && is_array($realizace['edited'][$id])) {
                $kopie = array_merge($kopie, $realizace['edited'][$id]);
            }
            $kopie['_zdroj'] = 'zaklad';
            $vysledek[] = $kopie;
        }
        foreach ($realizace['added'] as $polozka) {
            if (!is_array($polozka)) {
                continue;
            }
            $kopie = $polozka;
            $kopie['_zdroj'] = 'pridana';
            $vysledek[] = $kopie;
        }

        usort($vysledek, static function (array $a, array $b): int {
            $da = isset($a['datum']) && $a['datum'] !== '' ? (string) $a['datum'] : '';
            $db = isset($b['datum']) && $b['datum'] !== '' ? (string) $b['datum'] : '';
            if ($da === '' && $db === '') {
                return $a['_zdroj'] === 'pridana' ? -1 : 1;
            }
            if ($da === '') {
                return 1;
            }
            if ($db === '') {
                return -1;
            }
            if ($da > $db) {
                return -1;
            }
            if ($da < $db) {
                return 1;
            }
            if ($a['_zdroj'] === 'pridana' && $b['_zdroj'] !== 'pridana') {
                return -1;
            }
            if ($a['_zdroj'] !== 'pridana' && $b['_zdroj'] === 'pridana') {
                return 1;
            }
            return 0;
        });

        foreach ($vysledek as $i => $polozka) {
            unset($vysledek[$i]['_zdroj']);
        }

        return array_values($vysledek);
    }

    /* ------------------------------------------------------------ pomocné */

    /** Doplní chybějící klíče části 'realizace'; zbytek stavu nedotýká. */
    private static function uplny(array $stav): array
    {
        if (!isset($stav['realizace']) || !is_array($stav['realizace'])) {
            $stav['realizace'] = ['added' => [], 'edited' => [], 'removed' => []];
        }
        foreach (['added' => [], 'edited' => [], 'removed' => []] as $klic => $prazdne) {
            if (!array_key_exists($klic, $stav['realizace'])) {
                $stav['realizace'][$klic] = $prazdne;
            }
        }

        return $stav;
    }
}
