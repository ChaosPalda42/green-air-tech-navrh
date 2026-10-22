<?php
/* O nás, novinky a kariéra.

   Doslovný přepis odpovídající části src/templates/stranky.mjs. */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Grafika;
use App\Sablony\Ikony;
use App\Sablony\Layout;

final class Firma
{
    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function dc(string $k): string
    {
        return Casti::dc($k);
    }

    public static function oNas(Kontext $ctx): string
    {
        $site = $ctx->site();

        $hodnoty = '';
        $i = 0;
        foreach ($ctx->klice('onas.hodnoty.polozky') as $k) {
            $ikony = ['list', 'lide', 'stit', 'dokument'];
            $hodnoty .= '<div class="karta-sluzba" style="cursor:default">
      <span class="karta-ikona">' . self::ikona($ikony[$i % 4]) . '</span>
      <h3' . self::dc("onas.hodnoty.polozky.{$k}.titulek") . '>' . $ctx->t("onas.hodnoty.polozky.{$k}.titulek") . '</h3>
      <p' . self::dc("onas.hodnoty.polozky.{$k}.popis") . '>' . $ctx->zk($ctx->t("onas.hodnoty.polozky.{$k}.popis")) . '</p>
    </div>';
            $i++;
        }

        $divize = '';
        foreach ($ctx->klice('onas.divize.polozky') as $k) {
            $divize .= '<div class="krok">
      <h3' . self::dc("onas.divize.polozky.{$k}.titulek") . '>' . $ctx->t("onas.divize.polozky.{$k}.titulek") . '</h3>
      <p' . self::dc("onas.divize.polozky.{$k}.popis") . '>' . $ctx->zk($ctx->t("onas.divize.polozky.{$k}.popis")) . '</p>
    </div>';
        }

        $lide = '';
        foreach ($site['lide'] as $o) {
            $lide .= Casti::kartaClovek($ctx, $o);
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('onas.stitek'),
            'titulek' => $ctx->t('onas.titulek'),
            'lead' => $ctx->zk($ctx->t('onas.lead')),
            'drobecky' => [['nazev' => $ctx->t('nav.onas')]],
        ]) . '

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <h2' . self::dc('onas.pribeh.titulek') . '>' . $ctx->t('onas.pribeh.titulek') . '</h2>
        <p' . self::dc('onas.pribeh.p1') . '>' . $ctx->zk($ctx->t('onas.pribeh.p1')) . '</p>
        <p' . self::dc('onas.pribeh.p2') . '>' . $ctx->zk($ctx->t('onas.pribeh.p2')) . '</p>
        <p' . self::dc('onas.pribeh.p3') . '>' . $ctx->zk($ctx->t('onas.pribeh.p3')) . '</p>
      </div>
      <div>
        ' . $ctx->obrazek('foto-strojovna', ['alt' => 'Strojovna s rozvody', 'sirky' => '(min-width: 940px) 40vw, 92vw', 'trida' => 'dvojsloupec-obraz']) . '
        <div class="panel-info" style="margin-top:1.4rem;display:flex;gap:1rem;align-items:center">
          <img src="' . $ctx->asset('img/odznak-spolehliva-firma.png') . '" alt="" width="300" height="300" loading="lazy" style="width:72px;height:72px;background:none;flex:none">
          <div>
            <h3 style="margin-bottom:.25rem"' . self::dc('onas.odznak.titulek') . '>' . $ctx->t('onas.odznak.titulek') . '</h3>
            <p style="font-size:.9rem"' . self::dc('onas.odznak.popis') . '>' . $ctx->t('onas.odznak.popis') . '</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sekce sekce-tmava">
  <canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>
  <div class="obal">
    <div class="hlavicka-sekce"><h2' . self::dc('onas.divize.titulek') . '>' . $ctx->t('onas.divize.titulek') . '</h2></div>
    <div class="postup" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">' . $divize . '</div>
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce"><h2' . self::dc('onas.hodnoty.titulek') . '>' . $ctx->t('onas.hodnoty.titulek') . '</h2></div>
    <div class="mrizka mrizka-4">' . $hodnoty . '</div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <h2' . self::dc('onas.tym.titulek') . '>' . $ctx->t('onas.tym.titulek') . '</h2>
      <p class="lead"' . self::dc('onas.tym.lead') . '>' . $ctx->t('onas.tym.lead') . '</p>
    </div>
    <div class="mrizka mrizka-3">' . $lide . '</div>
  </div>
</section>

' . Layout::vyzva($ctx);
    }

    public static function novinkyPrehled(Kontext $ctx): string
    {
        $karty = '';
        foreach ($ctx->novinkySeznam() as $n) {
            $karty .= Casti::kartaNovinky($ctx, $n);
        }
        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('novinky.stranka.stitek'),
            'titulek' => $ctx->t('novinky.stranka.titulek'),
            'lead' => $ctx->t('novinky.stranka.lead'),
            'drobecky' => [['nazev' => $ctx->t('nav.novinky')]],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">' . $karty . '</div>
  </div>
</section>
' . Layout::vyzva($ctx);
    }

    public static function novinkaDetail(Kontext $ctx, array $n): string
    {
        $p = "novinky.polozky.{$n['id']}";

        $dalsi = '';
        $kolik = 0;
        foreach ($ctx->novinkySeznam() as $x) {
            if ($x['id'] === $n['id'] || $kolik >= 3) {
                continue;
            }
            $dalsi .= Casti::kartaNovinky($ctx, $x);
            $kolik++;
        }

        $externi = ($n['odkaz'] ?? '') !== ''
            ? '<p><a class="tl tl-obrys tl-mala" href="' . $n['odkaz'] . '" target="_blank" rel="noopener">'
                . self::ikona('externi') . $ctx->t('ui.externiClanek') . '</a></p>'
            : '';

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('ui.publikovano') . ' ' . $ctx->datum($n['datum']),
            'titulek' => $ctx->t("{$p}.nazev"),
            'lead' => $ctx->zk($ctx->t("{$p}.perex")),
            'drobecky' => [
                ['nazev' => $ctx->t('nav.novinky'), 'klic' => 'novinky'],
                ['nazev' => $ctx->t("{$p}.nazev")],
            ],
        ]) . '
<section class="sekce">
  <div class="obal obal-uzky">
    <div style="border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/9;margin-bottom:2.2rem">' . Grafika::motivRealizace($n['motiv']) . '</div>
    <div class="text-blok" style="max-width:none">
      <p class="lead"' . self::dc("{$p}.perex") . '>' . $ctx->zk($ctx->t("{$p}.perex")) . '</p>
      <p' . self::dc("{$p}.text") . '>' . $ctx->zk($ctx->t("{$p}.text")) . '</p>
      ' . $externi . '
      <p style="margin-top:2rem"><a class="odkaz-sip" href="' . $ctx->odkaz('novinky') . '">' . $ctx->t('ui.vsechnyNovinky') . self::ikona('sip') . '</a></p>
    </div>
  </div>
</section>
<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>' . $ctx->t('ui.vsechnyNovinky') . '</h2></div>
    <div class="mrizka mrizka-3">' . $dalsi . '</div>
  </div>
</section>';
    }

    public static function kariera(Kontext $ctx): string
    {
        $site = $ctx->site();

        $nabidka = '';
        $i = 0;
        foreach ($ctx->klice('kariera.nabizime.polozky') as $k) {
            $ikony = ['montaz', 'dokument', 'lide', 'misto'];
            $nabidka .= '<div class="karta-sluzba" style="cursor:default">
      <span class="karta-ikona">' . self::ikona($ikony[$i % 4]) . '</span>
      <h3' . self::dc("kariera.nabizime.polozky.{$k}.titulek") . '>' . $ctx->t("kariera.nabizime.polozky.{$k}.titulek") . '</h3>
      <p' . self::dc("kariera.nabizime.polozky.{$k}.popis") . '>' . $ctx->zk($ctx->t("kariera.nabizime.polozky.{$k}.popis")) . '</p>
    </div>';
            $i++;
        }

        $vedouci = null;
        foreach ($site['lide'] as $o) {
            if ($o['id'] === 'zdenek-bauska') {
                $vedouci = $o;
                break;
            }
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('kariera.stitek'),
            'titulek' => $ctx->t('kariera.titulek'),
            'lead' => $ctx->zk($ctx->t('kariera.lead')),
            'drobecky' => [['nazev' => $ctx->t('nav.kariera')]],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2' . self::dc('kariera.cohledame.titulek') . '>' . $ctx->t('kariera.cohledame.titulek') . '</h2>
        ' . Casti::seznamOdskrtnuty($ctx, 'kariera.cohledame.polozky') . '
      </div>
      <div>
        ' . $ctx->obrazek('foto-servis', ['alt' => $ctx->t('kariera.titulek'), 'sirky' => '(min-width: 940px) 40vw, 92vw', 'trida' => 'dvojsloupec-obraz']) . '
      </div>
    </div>
  </div>
</section>
<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2' . self::dc('kariera.nabizime.titulek') . '>' . $ctx->t('kariera.nabizime.titulek') . '</h2></div>
    <div class="mrizka mrizka-4">' . $nabidka . '</div>
  </div>
</section>
<section class="sekce" id="formular">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2' . self::dc('kariera.formular.titulek') . '>' . $ctx->t('kariera.formular.titulek') . '</h2>
        <p class="lead"' . self::dc('kariera.formular.lead') . '>' . $ctx->t('kariera.formular.lead') . '</p>
        <div style="margin-top:1.6rem;max-width:22rem">' . Casti::kartaClovek($ctx, $vedouci) . '</div>
      </div>
      <div>' . Casti::formular($ctx, ['predvolenyTyp' => 'kariera', 'id' => 'formular-kariera']) . '</div>
    </div>
  </div>
</section>';
    }
}
