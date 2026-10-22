<?php
/* Data pro administraci: seznam editovatelných klíčů, slovníky jazyků,
   realizace a kategorie.

   Seznam editovatelných klíčů se v ukázce sbíral z vykreslených stránek
   (každé `data-cms="…"`). Tady se dělá totéž, ale výsledek se ukládá do
   web/data/admin-klice.json — vykreslit kvůli jednomu otevření administrace
   celý web by bylo zbytečné. Soubor se dá předgenerovat:
   `php tools/klice.php`. */

declare(strict_types=1);

namespace App\Jadro;

use App\Obsah\I18n;
use App\Obsah\Zdroj;

final class Administrace
{
    public static function data(Kontext $ctx, Zdroj $zdroj, ?string $cacheKlicu = null): array
    {
        $site = $zdroj->site();

        $slovniky = [];
        foreach ($site['jazyky'] as $j) {
            $slovniky[$j['kod']] = I18n::flatten($zdroj->dict($j['kod']));
        }

        $realizace = [];
        foreach ($site['realizace'] as $r) {
            $p = "realizace.polozky.{$r['id']}";
            $rozsah = [];
            foreach ($ctx->klice("{$p}.rozsah") as $k) {
                $rozsah[] = $ctx->t("{$p}.rozsah.{$k}");
            }
            $technologie = [];
            foreach ($ctx->klice("{$p}.technologie") as $k) {
                $technologie[] = $ctx->t("{$p}.technologie.{$k}");
            }
            $realizace[] = [
                'id' => $r['id'],
                'motiv' => $r['motiv'],
                'datum' => $r['datum'],
                'kategorie' => $r['kategorie'],
                'plocha' => $r['plocha'],
                'doba' => $r['doba'],
                'vetev' => $r['vetev'],
                'nazev' => $ctx->t("{$p}.nazev"),
                'misto' => $ctx->t("{$p}.misto"),
                'perex' => $ctx->t("{$p}.perex"),
                'zadani' => $ctx->t("{$p}.zadani"),
                'vysledek' => $ctx->t("{$p}.vysledek"),
                'rozsah' => $rozsah,
                'technologie' => $technologie,
            ];
        }

        $kategorie = [];
        foreach ($site['kategorieRealizaci'] as $k) {
            $kategorie[$k] = $ctx->t("realizace.kategorie.{$k}");
        }
        $vetve = [];
        foreach ($site['vetve'] as $v) {
            $vetve[] = ['id' => $v['id'], 'nazev' => $ctx->t("vetve.{$v['id']}.nazev")];
        }

        return [
            'klice' => self::klice($zdroj, $cacheKlicu),
            'slovniky' => $slovniky,
            'realizace' => $realizace,
            'kategorie' => $kategorie,
            'vetve' => $vetve,
        ];
    }

    /** Editovatelné klíče: z cache, nebo spočítané ze všech stránek. */
    public static function klice(Zdroj $zdroj, ?string $cache = null): array
    {
        if ($cache !== null && is_file($cache)) {
            $data = json_decode((string) file_get_contents($cache), true);
            if (is_array($data) && $data !== []) {
                return $data;
            }
        }
        $klice = self::spocitejKlice($zdroj);
        if ($cache !== null) {
            @file_put_contents($cache, json_encode($klice, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        }
        return $klice;
    }

    /** Projde všechny stránky a vybere z nich `data-cms="…"`. */
    public static function spocitejKlice(Zdroj $zdroj): array
    {
        $site = $zdroj->site();
        $nalezene = [];
        foreach (Stranka::seznam($site) as $cesta) {
            if ($cesta === Odkazy::SOUBORY['administrace']) {
                continue;
            }
            $html = Stranka::html($cesta, $zdroj, true);
            if ($html === null) {
                continue;
            }
            if (preg_match_all('~data-cms="([^"]+)"~', $html, $m) > 0) {
                foreach ($m[1] as $klic) {
                    $nalezene[$klic] = true;
                }
            }
        }
        $klice = array_keys($nalezene);
        sort($klice, SORT_STRING);
        return $klice;
    }
}
