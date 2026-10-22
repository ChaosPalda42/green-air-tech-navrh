<?php

declare(strict_types=1);

namespace App\Obsah;

final class RealizaceFiltr
{
    /**
     * Text pro porovnávání: malá písmena, bez diakritiky, okrajové mezery pryč.
     * Diakritiku řeš vlastní tabulkou, ne iconv ani intl.
     */
    public static function normalizeText(mixed $hodnota): string
    {
        if ($hodnota === null) {
            return 'null';
        }
        if (!is_string($hodnota)) {
            return (string)$hodnota;
        }

        $text = $hodnota;
        $text = mb_strtolower($text, 'UTF-8');

        $map = [
            'á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u', 'ý' => 'y', 'č' => 'c', 'ď' => 'd', 'ě' => 'e', 'ň' => 'n', 'ř' => 'r', 'š' => 's', 'ť' => 't', 'ů' => 'u', 'ž' => 'z',
            'à' => 'a', 'è' => 'e', 'ì' => 'i', 'ò' => 'o', 'ù' => 'u', 'â' => 'a', 'ê' => 'e', 'î' => 'i', 'ô' => 'o', 'û' => 'u', 'ä' => 'a', 'ë' => 'e', 'ï' => 'i', 'ö' => 'o', 'ü' => 'u',
        ];

        return strtr($text, $map);
    }

    /**
     * Volby: 'kategorie', 'dotaz', 'rok'. Prázdné nebo chybějící volby nefiltrují.
     * 'rok' přijímá číslo i řetězec. Vrací seznam (klíče 0..n-1), ne řídké pole —
     * po array_filter vždy array_values.
     *
     * Pozor na tři věci, ve kterých se ukázka chová jinak, než by člověk hádal:
     * 'kategorie' je JEDEN řetězec (a 'vse' nefiltruje), 'rok' se porovnává
     * začátkem datumu, ne číslem, a 'dotaz' se trhá na slova — musí se najít
     * všechna, a hledá se i v perexu.
     */
    public static function filterItems(array $polozky, array $volby = []): array
    {
        $kategorie = $volby['kategorie'] ?? null;
        $dotaz = $volby['dotaz'] ?? null;
        $rok = $volby['rok'] ?? null;

        $vybrane = [];

        foreach ($polozky as $polozka) {
            // --- kategorie ---
            if ($kategorie !== null && $kategorie !== '' && $kategorie !== 'vse') {
                $vlastni = $polozka['kategorie'] ?? null;
                if (!is_array($vlastni) || !in_array($kategorie, $vlastni, true)) {
                    continue;
                }
            }

            // --- rok ---
            if ($rok !== null && $rok !== '') {
                $datum = (string) ($polozka['datum'] ?? '');
                if (!str_starts_with($datum, (string) $rok)) {
                    continue;
                }
            }

            // --- dotaz ---
            if (is_string($dotaz) && trim($dotaz) !== '') {
                $slova = preg_split('/\s+/', trim($dotaz)) ?: [];
                $casti = [
                    $polozka['nazev'] ?? null,
                    $polozka['misto'] ?? null,
                    $polozka['perex'] ?? null,
                ];
                foreach (($polozka['kategorie'] ?? []) as $kat) {
                    $casti[] = $kat;
                }
                $casti = array_filter($casti, static fn ($v): bool => $v !== null);
                $vse = self::normalizeText(implode(' ', $casti));

                $vsechna = true;
                foreach ($slova as $slovo) {
                    if (!str_contains($vse, self::normalizeText($slovo))) {
                        $vsechna = false;
                        break;
                    }
                }
                if (!$vsechna) {
                    continue;
                }
            }

            $vybrane[] = $polozka;
        }

        return $vybrane;
    }

    /**
     * Seznam polí ['id' => …, 'count' => N] seřazený count sestupně a při shodě
     * id vzestupně přes RazeniCs::porovnej.
     */
    public static function collectKategorie(array $polozky): array
    {
        $counts = [];
        foreach ($polozky as $item) {
            if (isset($item['kategorie']) && is_array($item['kategorie'])) {
                foreach ($item['kategorie'] as $kat) {
                    if (!isset($counts[$kat])) {
                        $counts[$kat] = ['id' => $kat, 'count' => 0];
                    }
                    $counts[$kat]['count']++;
                }
            }
        }

        $result = array_values($counts);

        usort($result, function ($a, $b) {
            if ($a['count'] !== $b['count']) {
                return $b['count'] <=> $a['count'];
            }
            return RazeniCs::porovnej((string)$a['id'], (string)$b['id']);
        });

        return $result;
    }

    /**
     * Seznam roků (čísla) sestupně, bez duplicit.
     */
    public static function collectRoky(array $polozky): array
    {
        $rokys = [];
        foreach ($polozky as $item) {
            if (isset($item['datum']) && is_string($item['datum'])) {
                $rok = (int)substr($item['datum'], 0, 4);
                if ($rok > 0) {
                    $rokys[] = $rok;
                }
            }
        }

        $rokys = array_unique($rokys);
        rsort($rokys);

        return array_values($rokys);
    }

    /**
     * Režimy 'nejstarsi' (datum vzestupně), 'nazev' (RazeniCs::porovnej nad 'nazev'),
     * cokoli jiného = datum sestupně. Položka bez data jde vždy na konec.
     */
    public static function sortItems(array $polozky, string $rezim): array
    {
        usort($polozky, function ($a, $b) use ($rezim) {
            if ($rezim === 'nazev') {
                return RazeniCs::porovnej((string)($a['nazev'] ?? ''), (string)($b['nazev'] ?? ''));
            }

            $aDatum = $a['datum'] ?? null;
            $bDatum = $b['datum'] ?? null;

            if ($aDatum === null && $bDatum === null) {
                return 0;
            }
            if ($aDatum === null) {
                return 1;
            }
            if ($bDatum === null) {
                return -1;
            }

            if ($rezim === 'nejstarsi') {
                return strcmp((string)$aDatum, (string)$bDatum);
            } else {
                return strcmp((string)$bDatum, (string)$aDatum);
            }
        });

        return $polozky;
    }

    /**
     * Vrací ['items' => […], 'page' => N, 'pages' => N, 'total' => N]; 'pages' je
     * nejméně 1 a 'page' se zarovná do rozsahu 1..pages.
     */
    public static function paginate(array $polozky, int $stranka, int $naStranku): array
    {
        $total = count($polozky);
        
        if ($naStranku <= 0) {
            return [
                'items' => [],
                'page' => 1,
                'pages' => null,
                'total' => $total,
            ];
        }

        $pages = (int)ceil($total / $naStranku);
        if ($pages < 1) {
            $pages = 1;
        }

        if ($stranka < 1) {
            $stranka = 1;
        }
        if ($stranka > $pages) {
            $stranka = $pages;
        }

        $offset = ($stranka - 1) * $naStranku;
        $items = array_slice($polozky, $offset, $naStranku);

        return [
            'items' => $items,
            'page' => $stranka,
            'pages' => $pages,
            'total' => $total,
        ];
    }
}
