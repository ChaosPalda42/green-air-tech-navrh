<?php
/* Rozcestník (úvodní stránka) a domovská stránka větve.

   Doslovný přepis odpovídající části src/templates/stranky.mjs. */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Grafika;
use App\Sablony\Ikony;

final class Rozcestnik
{
    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function dc(string $k): string
    {
        return Casti::dc($k);
    }

    public static function rozcestnik(Kontext $ctx): string
    {
        $site = $ctx->site();

        $cisla = '';
        foreach (['praxe', 'oblasti', 'dispecink', 'technici'] as $k) {
            $cisla .= '<div><b' . self::dc("home.cisla.{$k}.hodnota") . '>' . $ctx->t("home.cisla.{$k}.hodnota")
                . '</b><span' . self::dc("home.cisla.{$k}.popis") . '>' . $ctx->t("home.cisla.{$k}.popis") . '</span></div>';
        }

        $duvody = '';
        foreach ($ctx->klice('home.duvody.polozky') as $k) {
            $ikona = $k === 'udrzitelnost' ? 'list' : ($k === 'jedenTym' ? 'lide' : 'hodiny');
            $duvody .= '<div class="karta-sluzba" style="cursor:default">
        <span class="karta-ikona">' . self::ikona($ikona) . '</span>
        <h3' . self::dc("home.duvody.polozky.{$k}.titulek") . '>' . $ctx->t("home.duvody.polozky.{$k}.titulek") . '</h3>
        <p' . self::dc("home.duvody.polozky.{$k}.popis") . '>' . $ctx->zk($ctx->t("home.duvody.polozky.{$k}.popis")) . '</p>
      </div>';
        }

        $dlazdice = '';
        foreach ($site['vetve'] as $v) {
            $dlazdice .= Casti::dlazdiceVetve($ctx, $v);
        }

        return '<section class="hero hero-rozcestnik">
  <canvas class="hero-platno" data-vitr="hero" aria-hidden="true"></canvas>
  <div class="obal">
    <div class="rozcestnik-uvod">
      <span class="stitek"' . self::dc('rozcestnik.stitek') . '>' . $ctx->t('rozcestnik.stitek') . '</span>
      <h1' . self::dc('rozcestnik.titulek') . '>' . $ctx->t('rozcestnik.titulek') . '</h1>
      <p class="lead"' . self::dc('rozcestnik.lead') . '>' . $ctx->zk($ctx->t('rozcestnik.lead')) . '</p>
    </div>
    <div class="rozcestnik">' . $dlazdice . '</div>
    <p class="rozcestnik-pomoc"' . self::dc('rozcestnik.vyberteLead') . '>' . $ctx->t('rozcestnik.vyberteLead') . '</p>
  </div>
  <div class="obal"><div class="hero-pruh">' . $cisla . '</div></div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"' . self::dc('home.postup.stitek') . '>' . $ctx->t('home.postup.stitek') . '</span>
      <h2' . self::dc('home.postup.titulek') . '>' . $ctx->t('home.postup.titulek') . '</h2>
      <p class="lead"' . self::dc('home.postup.lead') . '>' . $ctx->zk($ctx->t('home.postup.lead')) . '</p>
    </div>
    ' . Casti::kroky($ctx, 'home.postup.kroky') . '
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"' . self::dc('home.duvody.stitek') . '>' . $ctx->t('home.duvody.stitek') . '</span>
      <h2' . self::dc('home.duvody.titulek') . '>' . $ctx->t('home.duvody.titulek') . '</h2>
    </div>
    <div class="mrizka mrizka-3">' . $duvody . '</div>
  </div>
</section>

<section class="sekce sekce-tmava">
  <canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <span class="stitek"' . self::dc('home.slovnik.stitek') . '>' . $ctx->t('home.slovnik.stitek') . '</span>
        <h2' . self::dc('home.slovnik.titulek') . '>' . $ctx->t('home.slovnik.titulek') . '</h2>
        <p class="lead" style="margin-bottom:1.6rem"' . self::dc('home.slovnik.lead') . '>' . $ctx->t('home.slovnik.lead') . '</p>
        <p class="slovnik-ukazka"' . self::dc('home.slovnik.ukazka') . '>' . $ctx->zk($ctx->t('home.slovnik.ukazka')) . '</p>
        <a class="tl tl-obrys" href="' . $ctx->odkaz('slovnik') . '">' . self::ikona('dokument') . $ctx->t('home.slovnik.cta') . '</a>
      </div>
      <div>
        ' . $ctx->obrazek('foto-servis', ['alt' => 'Kazetová klimatizační jednotka pod stropem', 'sirky' => '(min-width: 940px) 40vw, 92vw', 'trida' => 'dvojsloupec-obraz']) . '
      </div>
    </div>
  </div>
</section>

' . Spolecne::sekceKontakt($ctx);
    }

    public static function vetevDomu(Kontext $ctx): string
    {
        $site = $ctx->site();
        $vetev = (string) $ctx->vetev;
        $v = null;
        $druha = null;
        foreach ($site['vetve'] as $x) {
            if ($x['id'] === $vetev) {
                $v = $x;
            } else {
                $druha ??= $x;
            }
        }
        $sluzby = '';
        foreach ($ctx->sluzbyVetve($vetev) as $s) {
            $sluzby .= Casti::kartaSluzby($ctx, $s);
        }
        $realizace = '';
        foreach (array_slice($ctx->realizaceVetve($vetev), 0, 3) as $r) {
            $realizace .= Casti::kartaRealizace($ctx, $r);
        }
        $f = $site['firma'];

        return '<section class="hero">
  <canvas class="hero-platno" data-vitr="hero" aria-hidden="true"></canvas>
  <div class="obal hero-vnitrek">
    <div>
      <span class="stitek"' . self::dc("vetve.{$vetev}.nazev") . '>' . $ctx->t("vetve.{$vetev}.nazev") . '</span>
      <h1' . self::dc("vetve.{$vetev}.titulek") . '>' . $ctx->t("vetve.{$vetev}.titulek") . '</h1>
      <p class="lead"' . self::dc("vetve.{$vetev}.lead") . '>' . $ctx->zk($ctx->t("vetve.{$vetev}.lead")) . '</p>
      <div class="tlacitka">
        <a class="tl tl-hlavni" href="' . $ctx->odkaz('kontakt') . '#formular">' . self::ikona('mail') . $ctx->t('home.hero.cta') . '</a>
        <a class="tl tl-obrys" href="' . $ctx->odkaz('sluzby') . '">' . self::ikona('sipDolu') . $ctx->t('home.hero.ctaDruhe') . '</a>
      </div>
      <a class="hero-dispecink" href="tel:' . $f['dispecinkTelefonHref'] . '">
        <span class="zivy">' . self::ikona('telefon', ['velikost' => 16]) . '</span>
        <span>' . $ctx->t('home.hero.dispecinkStitek') . ' <b>' . $f['dispecinkTelefon'] . '</b></span>
      </a>
    </div>
    <div class="hero-obrazek">
      ' . $ctx->obrazek($v['foto'], ['alt' => '', 'sirky' => '(min-width: 1000px) 44vw, 92vw', 'prioritni' => true]) . '
      ' . Grafika::heroSchema() . '
    </div>
  </div>
</section>

<section class="sekce" id="sluzby">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek">' . $ctx->t('nav.sluzby') . '</span>
      <h2' . self::dc("vetve.{$vetev}.sluzbyTitulek") . '>' . $ctx->t("vetve.{$vetev}.sluzbyTitulek") . '</h2>
      <p class="lead"' . self::dc("vetve.{$vetev}.sluzbyLead") . '>' . $ctx->zk($ctx->t("vetve.{$vetev}.sluzbyLead")) . '</p>
    </div>
    <div class="mrizka mrizka-3">' . $sluzby . '</div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"' . self::dc('home.postup.stitek') . '>' . $ctx->t('home.postup.stitek') . '</span>
      <h2' . self::dc('home.postup.titulek') . '>' . $ctx->t('home.postup.titulek') . '</h2>
    </div>
    ' . Casti::kroky($ctx, 'home.postup.kroky') . '
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek">' . $ctx->t('nav.realizace') . '</span>
      <h2' . self::dc("vetve.{$vetev}.realizaceTitulek") . '>' . $ctx->t("vetve.{$vetev}.realizaceTitulek") . '</h2>
      <p class="lead"' . self::dc("vetve.{$vetev}.realizaceLead") . '>' . $ctx->zk($ctx->t("vetve.{$vetev}.realizaceLead")) . '</p>
    </div>
    <div class="mrizka mrizka-3">' . $realizace . '</div>
    <div class="tlacitka" style="margin-top:2rem">
      <a class="tl tl-obrys" href="' . $ctx->odkaz('realizace') . '">' . $ctx->t('ui.vsechnyRealizace') . self::ikona('sip') . '</a>
    </div>
    <div class="panel-info" style="margin-top:2.4rem">
      <p' . self::dc("vetve.{$vetev}.poznamka") . '>' . $ctx->zk($ctx->t("vetve.{$vetev}.poznamka")) . '</p>
      <p style="margin-top:.8rem"><a class="odkaz-sip" href="' . $ctx->odkazVetve($druha['id'], 'vetev') . '">' . $ctx->t("vetve.{$druha['id']}.cta") . self::ikona('sip') . '</a></p>
    </div>
  </div>
</section>

' . Spolecne::sekceKontakt($ctx);
    }
}
