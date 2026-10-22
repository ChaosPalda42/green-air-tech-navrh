<?php
/* Přehled služeb větve a detail jedné služby.

   Doslovný přepis odpovídající části src/templates/stranky.mjs. */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Ikony;
use App\Sablony\Layout;

final class Sluzby
{
    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function dc(string $k): string
    {
        return Casti::dc($k);
    }

    public static function sluzbyPrehled(Kontext $ctx): string
    {
        $vetev = (string) $ctx->vetev;
        $karty = '';
        foreach ($ctx->sluzbyVetve($vetev) as $s) {
            $karty .= Casti::kartaSluzby($ctx, $s);
        }
        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t("vetve.{$vetev}.nazev"),
            'titulek' => $ctx->t("vetve.{$vetev}.sluzbyTitulek"),
            'lead' => $ctx->zk($ctx->t("vetve.{$vetev}.sluzbyLead")),
            'drobecky' => [
                ['nazev' => $ctx->t("vetve.{$vetev}.nazev"), 'href' => $ctx->odkazVetve($vetev, 'vetev')],
                ['nazev' => $ctx->t('nav.sluzby')],
            ],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">' . $karty . '</div>
  </div>
</section>
' . self::krokySekce($ctx) . '
' . Layout::vyzva($ctx);
    }

    private static function krokySekce(Kontext $ctx): string
    {
        return '<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek">' . $ctx->t('home.postup.stitek') . '</span>
      <h2>' . $ctx->t('home.postup.titulek') . '</h2>
    </div>
    ' . Casti::kroky($ctx, 'home.postup.kroky') . '
  </div>
</section>';
    }

    public static function sluzbaDetail(Kontext $ctx, array $s): string
    {
        $vetev = (string) $ctx->vetev;
        $p = "sluzby.polozky.{$s['id']}";
        $maKroky = $ctx->klice("{$p}.kroky") !== [];

        $souvisi = '';
        $kolik = 0;
        foreach ($ctx->sluzbyVetve($vetev) as $x) {
            if ($x['id'] === $s['id'] || $kolik >= 3) {
                continue;
            }
            $souvisi .= Casti::kartaSluzby($ctx, $x);
            $kolik++;
        }

        $doplnky = '';
        foreach (['upozorneni', 'refit', 'dispecink', 'servis'] as $k) {
            if (!$ctx->existuje("{$p}.{$k}.titulek")) {
                continue;
            }
            $doplnky .= '<div class="panel-info' . ($k === 'upozorneni' ? ' varovny' : '') . '" style="margin-top:1.6rem">
        <h3' . self::dc("{$p}.{$k}.titulek") . '>' . $ctx->t("{$p}.{$k}.titulek") . '</h3>
        <p' . self::dc("{$p}.{$k}.popis") . '>' . $ctx->zk($ctx->t("{$p}.{$k}.popis")) . '</p>
      </div>';
        }

        $sekceKroky = $maKroky
            ? '<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>' . $ctx->t('sluzby.spolecne.jakProbiha') . '</h2></div>
    ' . Casti::kroky($ctx, "{$p}.kroky") . '
  </div>
</section>'
            : '';

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t("vetve.{$vetev}.nazev"),
            'titulek' => $ctx->t("{$p}.titulek"),
            'lead' => $ctx->zk($ctx->t("{$p}.lead")),
            'drobecky' => [
                ['nazev' => $ctx->t("vetve.{$vetev}.nazev"), 'href' => $ctx->odkazVetve($vetev, 'vetev')],
                ['nazev' => $ctx->t('nav.sluzby'), 'klic' => 'sluzby'],
                ['nazev' => $ctx->t("{$p}.nazev")],
            ],
        ]) . '

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2' . self::dc("{$p}.nazev") . '>' . $ctx->t("{$p}.nazev") . '</h2>
        <p class="lead"' . self::dc("{$p}.popis") . '>' . $ctx->zk($ctx->t("{$p}.popis")) . '</p>
        <h3 style="margin-top:2.2rem">' . $ctx->t('sluzby.spolecne.coZahrnuje') . '</h3>
        ' . Casti::seznamOdskrtnuty($ctx, "{$p}.body") . '
        ' . $doplnky . '
      </div>
      <div>
        ' . $ctx->obrazek($s['foto'], ['alt' => $ctx->t("{$p}.nazev"), 'sirky' => '(min-width: 940px) 40vw, 92vw', 'trida' => 'dvojsloupec-obraz']) . '
        <p class="popiska">' . $ctx->t('ui.ilustracniGrafika') . ' · ' . $ctx->t("{$p}.nazev") . '</p>
      </div>
    </div>
  </div>
</section>

' . $sekceKroky . '

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>' . $ctx->t('sluzby.spolecne.souvisi') . '</h2></div>
    <div class="mrizka mrizka-3">' . $souvisi . '</div>
  </div>
</section>

' . Layout::vyzva($ctx, [
            'titulek' => $ctx->t('sluzby.spolecne.zajimaVas'),
            'lead' => $ctx->t('sluzby.spolecne.zajimaVasLead'),
        ]);
    }
}
