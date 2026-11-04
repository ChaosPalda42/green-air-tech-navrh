<?php
/* Kontakt, slovník, ochrana osobních údajů, 404.

   Doslovný přepis odpovídající části src/templates/stranky.mjs. */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Ikony;
use App\Sablony\Layout;

final class Spolecne
{
    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function dc(string $k): string
    {
        return Casti::dc($k);
    }

    /** Totéž co encodeURIComponent v JavaScriptu. */
    private static function uri(string $s): string
    {
        return strtr(rawurlencode($s), [
            '%21' => '!', '%2A' => '*', '%27' => "'", '%28' => '(', '%29' => ')',
        ]);
    }

    private static function mapa(array $a): string
    {
        return 'https://www.google.com/maps/search/?api=1&query='
            . self::uri($a['ulice'] . ', ' . $a['psc'] . ' ' . $a['mesto']);
    }

    /** Společná kontaktní sekce — na rozcestníku i na domovských stránkách větví. */
    public static function sekceKontakt(Kontext $ctx): string
    {
        $f = $ctx->site()['firma'];
        return '<section class="sekce sekce-papir" id="kontakt">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <span class="stitek"' . self::dc('home.kontakt.stitek') . '>' . $ctx->t('home.kontakt.stitek') . '</span>
        <h2' . self::dc('home.kontakt.titulek') . '>' . $ctx->t('home.kontakt.titulek') . '</h2>
        <p class="lead"' . self::dc('home.kontakt.lead') . '>' . $ctx->t('home.kontakt.lead') . '</p>
        <div class="mrizka" style="margin-top:1.8rem">
          <a class="karta-kontakt zvyrazneny" href="tel:' . $f['dispecinkTelefonHref'] . '">
            <h3>' . $ctx->t('kontakt.rychle.dispecink.titulek') . '</h3>
            <span class="velky">' . $f['dispecinkTelefon'] . '</span>
            <p>' . $ctx->t('kontakt.rychle.dispecink.popis') . '</p>
          </a>
          <a class="karta-kontakt" href="mailto:' . $f['email'] . '">
            <h3>' . $ctx->t('kontakt.rychle.poptavka.titulek') . '</h3>
            <span class="velky">' . $f['email'] . '</span>
            <p>' . $ctx->t('kontakt.rychle.poptavka.popis') . '</p>
          </a>
        </div>
      </div>
      <div>' . Casti::formular($ctx) . '</div>
    </div>
  </div>
</section>';
    }

    public static function kontakt(Kontext $ctx): string
    {
        $site = $ctx->site();
        $f = $site['firma'];

        $lide = '';
        foreach ($site['lide'] as $o) {
            $lide .= Casti::kartaClovek($ctx, $o);
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('kontakt.stitek'),
            'titulek' => $ctx->t('kontakt.titulek'),
            'lead' => $ctx->t('kontakt.lead'),
            'drobecky' => [['nazev' => $ctx->t('nav.kontakt')]],
        ]) . '

<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">
      <a class="karta-kontakt zvyrazneny" href="tel:' . $f['dispecinkTelefonHref'] . '">
        <h3' . self::dc('kontakt.rychle.dispecink.titulek') . '>' . $ctx->t('kontakt.rychle.dispecink.titulek') . '</h3>
        <span class="velky">' . $f['dispecinkTelefon'] . '</span>
        <p' . self::dc('kontakt.rychle.dispecink.popis') . '>' . $ctx->t('kontakt.rychle.dispecink.popis') . '</p>
        <span class="odkaz-sip" style="color:var(--plocha-akcent)">' . $f['dispecinkEmail'] . '</span>
      </a>
      <a class="karta-kontakt" href="#formular">
        <h3' . self::dc('kontakt.rychle.poptavka.titulek') . '>' . $ctx->t('kontakt.rychle.poptavka.titulek') . '</h3>
        <span class="velky">' . $f['email'] . '</span>
        <p' . self::dc('kontakt.rychle.poptavka.popis') . '>' . $ctx->t('kontakt.rychle.poptavka.popis') . '</p>
        <span class="odkaz-sip">' . $ctx->t('ui.napsatNam') . self::ikona('sip') . '</span>
      </a>
      <a class="karta-kontakt" href="tel:' . $f['mobilKancelarHref'] . '">
        <h3' . self::dc('kontakt.rychle.kancelar.titulek') . '>' . $ctx->t('kontakt.rychle.kancelar.titulek') . '</h3>
        <span class="velky">' . $f['mobilKancelar'] . '</span>
        <p' . self::dc('kontakt.rychle.kancelar.popis') . '>' . $ctx->t('kontakt.rychle.kancelar.popis') . '</p>
      </a>
    </div>
  </div>
</section>

<section class="sekce sekce-papir" id="formular">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2' . self::dc('kontakt.formular.titulek') . '>' . $ctx->t('kontakt.formular.titulek') . '</h2>
        <p class="lead"' . self::dc('kontakt.formular.lead') . '>' . $ctx->t('kontakt.formular.lead') . '</p>
        <div class="mrizka" style="margin-top:1.8rem">
          <div class="adresa-karta">
            <h3>' . $ctx->t('kontakt.adresy.sidlo') . '</h3>
            <address>' . $f['sidlo']['ulice'] . '<br>' . $f['sidlo']['psc'] . ' ' . $f['sidlo']['mesto'] . '</address>
            <p style="margin-top:.7rem"><a class="odkaz-sip" href="' . self::mapa($f['sidlo']) . '" target="_blank" rel="noopener">' . $ctx->t('kontakt.adresy.otevritMapu') . self::ikona('externi', ['velikost' => 16]) . '</a></p>
          </div>
          <div class="adresa-karta">
            <h3>' . $ctx->t('kontakt.adresy.provozovna') . '</h3>
            <address>' . $f['provozovna']['ulice'] . '<br>' . $f['provozovna']['psc'] . ' ' . $f['provozovna']['mesto'] . '</address>
            <p style="margin-top:.7rem"><a class="odkaz-sip" href="' . self::mapa($f['provozovna']) . '" target="_blank" rel="noopener">' . $ctx->t('kontakt.adresy.otevritMapu') . self::ikona('externi', ['velikost' => 16]) . '</a></p>
          </div>
          <div class="adresa-karta">
            <h3>' . $ctx->t('kontakt.adresy.fakturacni') . '</h3>
            <address>
              ' . $f['nazev'] . '<br>
              IČO ' . $f['ico'] . ' · DIČ ' . $f['dic'] . '<br>
              ' . $f['banka'] . '<br>
              ' . $f['ucet'] . '<br>
              ID datové schránky: ' . $f['datovaSchranka'] . '
            </address>
          </div>
        </div>
      </div>
      <div>' . Casti::formular($ctx) . '</div>
    </div>
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <h2' . self::dc('kontakt.tym.titulek') . '>' . $ctx->t('kontakt.tym.titulek') . '</h2>
      <p class="lead"' . self::dc('kontakt.tym.lead') . '>' . $ctx->t('kontakt.tym.lead') . '</p>
    </div>
    <div class="mrizka mrizka-3">' . $lide . '</div>
  </div>
</section>';
    }

    public static function slovnik(Kontext $ctx): string
    {
        $skupiny = '';
        foreach ($ctx->skupinyZkratek() as $g) {
            $polozky = '';
            foreach ($g['items'] as $term) {
                $polozky .= '<dl class="slovnik-karta" data-zkratka="' . mb_strtolower($term['abbr'], 'UTF-8') . ' ' . mb_strtolower($term['full'], 'UTF-8') . '">
            <dt>' . $term['abbr'] . '</dt>
            <div class="rozepsano">' . $term['full'] . '</div>
            <dd>' . $term['popis'] . '</dd>
          </dl>';
            }
            $skupiny .= '<div class="slovnik-skupina">
      <h2 class="slovnik-pismeno" id="pismeno-' . $g['letter'] . '">' . $g['letter'] . '</h2>
      <div class="slovnik-polozky">
        ' . $polozky . '
      </div>
    </div>';
        }

        return Layout::podhlavi($ctx, [
            'stitek' => $ctx->t('slovnik.stranka.stitek'),
            'titulek' => $ctx->t('slovnik.stranka.titulek'),
            'lead' => $ctx->t('slovnik.stranka.lead'),
            'drobecky' => [['nazev' => $ctx->t('nav.slovnik')]],
        ]) . '
<section class="sekce">
  <div class="obal">
    <div class="filtry" data-jen-js style="max-width:32rem">
      <label class="hledani" style="width:100%">
        <span class="vizualne-skryto">' . $ctx->t('slovnik.stranka.hledat') . '</span>
        ' . self::ikona('lupa') . '
        <input type="search" data-hledani-slovnik placeholder="' . Layout::a($ctx->t('slovnik.stranka.hledat')) . '">
      </label>
    </div>
    <div data-slovnik>' . $skupiny . '</div>
    <p class="lead" data-slovnik-prazdno hidden style="text-align:center;padding:2rem 0">' . $ctx->t('slovnik.stranka.nenalezeno') . '</p>
  </div>
</section>
' . Layout::vyzva($ctx);
    }

    public static function gdpr(Kontext $ctx): string
    {
        $sekce = '';
        foreach ($ctx->klice('gdpr.sekce') as $k) {
            $sekce .= '<h2' . self::dc("gdpr.sekce.{$k}.titulek") . '>' . $ctx->t("gdpr.sekce.{$k}.titulek") . '</h2>
      <p' . self::dc("gdpr.sekce.{$k}.text") . '>' . $ctx->t("gdpr.sekce.{$k}.text") . '</p>';
        }
        /* Poznámka „tenhle text je ukázkový, nechte si ho zkontrolovat" je
           vzkaz klientovi, ne návštěvníkovi — na ostrém webu se nevykresluje. */
        $poznamka = $ctx->ukazka
            ? '<div class="panel-info varovny" style="margin-top:2.5rem">
      <p' . self::dc('gdpr.poznamka') . '>' . $ctx->t('gdpr.poznamka') . '</p>
    </div>'
            : '';

        return Layout::podhlavi($ctx, [
            'titulek' => $ctx->t('gdpr.titulek'),
            'lead' => $ctx->t('gdpr.lead'),
            'drobecky' => [['nazev' => $ctx->t('gdpr.titulek')]],
            'platno' => false,
        ]) . '
<section class="sekce">
  <div class="obal obal-uzky">
    <div class="text-blok" style="max-width:none">' . $sekce . '</div>
    ' . $poznamka . '
  </div>
</section>';
    }

    public static function chyba404(Kontext $ctx): string
    {
        $vetve = '';
        foreach ($ctx->site()['vetve'] as $v) {
            $vetve .= '<a class="tl tl-obrys" href="' . $ctx->odkazVetve($v['id'], 'vetev') . '">'
                . $ctx->t("vetve.{$v['id']}.nazev") . self::ikona('sip') . '</a>';
        }
        return '<section class="hero">
  <canvas class="hero-platno" data-vitr="hero" aria-hidden="true"></canvas>
  <div class="obal hero-vnitrek" style="grid-template-columns:1fr;text-align:center;justify-items:center">
    <div>
      <span class="stitek" style="justify-content:center">404</span>
      <h1>' . $ctx->t('chyba404.titulek') . '</h1>
      <p class="lead" style="margin-inline:auto">' . $ctx->t('chyba404.lead') . '</p>
      <div class="tlacitka" style="justify-content:center;margin-top:1.8rem">
        <a class="tl tl-hlavni" href="' . $ctx->odkaz('index') . '">' . self::ikona('sipZpet') . $ctx->t('chyba404.cta') . '</a>
        ' . $vetve . '
      </div>
    </div>
  </div>
</section>';
    }
}
