<?php
/* Přehled realizací větve, detail realizace a šablona pro realizace
   přidané v administraci.

   Doslovný přepis odpovídající části src/templates/stranky.mjs. JSON v
   <script type="application/json"> musí vyjít stejně jako z JSON.stringify,
   proto JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES a stejné pořadí klíčů. */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Grafika;
use App\Sablony\Ikony;
use App\Sablony\Layout;

final class Realizace
{
    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function dc(string $k): string
    {
        return Casti::dc($k);
    }

    /** Totéž co JSON.stringify v prohlížeči. */
    private static function js(mixed $data): string
    {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    }

    public static function realizacePrehled(Kontext $ctx): string
    {
        $site = $ctx->site();
        $vetev = (string) $ctx->vetev;
        $seznam = $ctx->realizaceSeznam();

        // nabízíme jen obory, které se v téhle větvi opravdu vyskytují
        $pouzite = [];
        foreach ($seznam as $r) {
            foreach ($r['kategorie'] as $k) {
                $pouzite[$k] = true;
            }
        }
        $kategorie = ['vse'];
        foreach ($site['kategorieRealizaci'] as $k) {
            if (isset($pouzite[$k])) {
                $kategorie[] = $k;
            }
        }

        $chipy = '';
        foreach ($kategorie as $k) {
            $chipy .= '<button type="button" class="chip" data-kategorie="' . $k . '" aria-pressed="'
                . ($k === 'vse' ? 'true' : 'false') . '">' . $ctx->t("realizace.kategorie.{$k}") . '</button>';
        }

        $karty = '';
        $data = [];
        foreach ($seznam as $r) {
            $karty .= Casti::kartaRealizace($ctx, $r);
            $data[] = [
                'id' => $r['id'],
                'nazev' => $ctx->t("realizace.polozky.{$r['id']}.nazev"),
                'misto' => $ctx->t("realizace.polozky.{$r['id']}.misto"),
                'perex' => $ctx->t("realizace.polozky.{$r['id']}.perex"),
                'datum' => $r['datum'],
                'kategorie' => $r['kategorie'],
                'motiv' => $r['motiv'],
                'odkaz' => $ctx->odkaz('realizace', $r['id']),
            ];
        }

        $nazvyKategorii = [];
        foreach ($kategorie as $k) {
            $nazvyKategorii[$k] = $ctx->t("realizace.kategorie.{$k}");
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t("vetve.{$vetev}.nazev"),
            'titulek' => $ctx->t("vetve.{$vetev}.realizaceTitulek"),
            'lead' => $ctx->zk($ctx->t("vetve.{$vetev}.realizaceLead")),
            'drobecky' => [
                ['nazev' => $ctx->t("vetve.{$vetev}.nazev"), 'href' => $ctx->odkazVetve($vetev, 'vetev')],
                ['nazev' => $ctx->t('nav.realizace')],
            ],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="filtry" data-jen-js>
      <div class="filtry-chipy">' . $chipy . '</div>
      <div class="filtry-vpravo">
        <label class="hledani">
          <span class="vizualne-skryto">' . $ctx->t('ui.hledat') . '</span>
          ' . self::ikona('lupa') . '
          <input type="search" data-hledani placeholder="' . Layout::a($ctx->t('ui.hledat')) . '…">
        </label>
        <span class="pocet-vysledku" data-pocet aria-live="polite"></span>
      </div>
    </div>
    <div class="mrizka mrizka-3" data-vypis-realizaci>' . $karty . '</div>
    <p class="lead" data-prazdno hidden style="text-align:center;padding:3rem 0">' . $ctx->t('ui.nenalezeno') . '</p>
  </div>
</section>
<script type="application/json" data-realizace-data>' . self::js([
            'polozky' => $data,
            'kategorie' => $nazvyKategorii,
            'texty' => [
                'vice' => $ctx->t('ui.vice'),
                'nenalezeno' => $ctx->t('ui.nenalezeno'),
                'pocet' => $ctx->t('ui.filtrovat'),
            ],
            'detailSablona' => $ctx->odkaz('realizaceDetail'),
        ]) . '</script>
' . Layout::vyzva($ctx);
    }

    public static function realizaceDetail(Kontext $ctx, array $r): string
    {
        $vetev = (string) $ctx->vetev;
        $p = "realizace.polozky.{$r['id']}";

        $dalsi = '';
        $kolik = 0;
        foreach ($ctx->realizaceSeznam() as $x) {
            if ($x['id'] === $r['id'] || $kolik >= 3) {
                continue;
            }
            $dalsi .= Casti::kartaRealizace($ctx, $x);
            $kolik++;
        }

        $technologie = [];
        foreach ($ctx->klice("{$p}.technologie") as $k) {
            $technologie[] = '<span class="odznak odznak-zeleny">' . $ctx->t("{$p}.technologie.{$k}") . '</span>';
        }

        $kategorie = [];
        foreach ($r['kategorie'] as $k) {
            $kategorie[] = $ctx->t("realizace.kategorie.{$k}");
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t("vetve.{$vetev}.nazev"),
            'titulek' => $ctx->t("{$p}.nazev"),
            'lead' => $ctx->zk($ctx->t("{$p}.perex")),
            'drobecky' => [
                ['nazev' => $ctx->t("vetve.{$vetev}.nazev"), 'href' => $ctx->odkazVetve($vetev, 'vetev')],
                ['nazev' => $ctx->t('nav.realizace'), 'klic' => 'realizace'],
                ['nazev' => $ctx->t("{$p}.nazev")],
            ],
        ]) . '

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <div class="detail-nahled" data-realizace-galerie="' . $r['id'] . '">' . Grafika::motivRealizace($r['motiv'], ['popis' => $ctx->t("{$p}.nazev")]) . '</div>
        <h2>' . $ctx->t('realizace.detail.rozsah') . '</h2>
        <p' . self::dc("{$p}.zadani") . '>' . $ctx->zk($ctx->t("{$p}.zadani")) . '</p>
        ' . Casti::seznamOdskrtnuty($ctx, "{$p}.rozsah") . '
        <h2 style="margin-top:2.4rem">' . $ctx->t('realizace.detail.vysledek') . '</h2>
        <p' . self::dc("{$p}.vysledek") . '>' . $ctx->zk($ctx->t("{$p}.vysledek")) . '</p>
      </div>
      <div>
        <h3>' . $ctx->t('realizace.detail.parametry') . '</h3>
        <dl class="parametry">
          <div><dt>' . $ctx->t('realizace.detail.kraj') . '</dt><dd>' . $ctx->t("{$p}.misto") . ', ' . $r['kraj'] . '</dd></div>
          <div><dt>' . $ctx->t('realizace.detail.dokonceno') . '</dt><dd>' . $ctx->datum($r['datum'], 'mesic') . '</dd></div>
          <div><dt>' . $ctx->t('realizace.detail.plocha') . '</dt><dd>' . $r['plocha'] . '</dd></div>
          <div><dt>' . $ctx->t('realizace.detail.doba') . '</dt><dd>' . $r['doba'] . '</dd></div>
          <div><dt>' . $ctx->t('ui.kategorie') . '</dt><dd>' . implode(', ', $kategorie) . '</dd></div>
        </dl>
        <h3 style="margin-top:2rem">' . $ctx->t('realizace.detail.technologie') . '</h3>
        <div style="display:flex;flex-wrap:wrap;gap:.4rem">' . implode(' ', $technologie) . '</div>
      </div>
    </div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>' . $ctx->t('realizace.detail.dalsiRealizace') . '</h2></div>
    <div class="mrizka mrizka-3">' . $dalsi . '</div>
  </div>
</section>

' . Layout::vyzva($ctx, [
            'titulek' => $ctx->t('realizace.detail.maObdobny'),
            'lead' => $ctx->t('realizace.detail.maObdobnyLead'),
        ]);
    }

    /** Stránka pro realizace přidané v administraci (vykresluje se z JSON v prohlížeči). */
    public static function realizaceSablona(Kontext $ctx): string
    {
        $data = [];
        foreach ($ctx->realizaceSeznam() as $r) {
            $data[] = [
                'id' => $r['id'],
                'nazev' => $ctx->t("realizace.polozky.{$r['id']}.nazev"),
                'odkaz' => $ctx->odkaz('realizace', $r['id']),
            ];
        }
        $kategorie = [];
        foreach ($ctx->site()['kategorieRealizaci'] as $k) {
            $kategorie[$k] = $ctx->t("realizace.kategorie.{$k}");
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('realizace.stranka.stitek'),
            'titulek' => '<span data-sablona="nazev">' . $ctx->t('realizace.stranka.titulek') . '</span>',
            'lead' => '<span data-sablona="perex"></span>',
            'drobecky' => [
                ['nazev' => $ctx->t('nav.realizace'), 'klic' => 'realizace'],
                ['nazev' => $ctx->t('realizace.stranka.stitek')],
            ],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <div data-sablona="nahled" style="border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/10;margin-bottom:2rem">' . Grafika::motivRealizace(1) . '</div>
        <h2>' . $ctx->t('realizace.detail.rozsah') . '</h2>
        <p data-sablona="zadani"></p>
        <ul class="seznam-odskrtnuty" data-sablona="rozsah"></ul>
        <h2 style="margin-top:2.4rem">' . $ctx->t('realizace.detail.vysledek') . '</h2>
        <p data-sablona="vysledek"></p>
      </div>
      <div>
        <h3>' . $ctx->t('realizace.detail.parametry') . '</h3>
        <dl class="parametry" data-sablona="parametry"></dl>
        <h3 style="margin-top:2rem">' . $ctx->t('realizace.detail.technologie') . '</h3>
        <div data-sablona="technologie" style="display:flex;flex-wrap:wrap;gap:.4rem"></div>
        <p style="margin-top:2rem"><a class="odkaz-sip" href="' . $ctx->odkaz('realizace') . '">' . $ctx->t('ui.vsechnyRealizace') . self::ikona('sip') . '</a></p>
      </div>
    </div>
  </div>
</section>
<script type="application/json" data-sablona-data>' . self::js([
            'zakladni' => $data,
            'popisky' => [
                'kraj' => $ctx->t('realizace.detail.kraj'),
                'dokonceno' => $ctx->t('realizace.detail.dokonceno'),
                'plocha' => $ctx->t('realizace.detail.plocha'),
                'doba' => $ctx->t('realizace.detail.doba'),
                'kategorie' => $ctx->t('ui.kategorie'),
            ],
            'kategorie' => $kategorie,
        ]) . '</script>
' . Layout::vyzva($ctx);
    }
}
