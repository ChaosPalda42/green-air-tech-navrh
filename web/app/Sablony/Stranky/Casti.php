<?php
/* Sdílené díly stránek: karty, seznamy, postup, kontaktní formulář, dlaždice větve.

   Doslovný přepis sdílené části src/templates/stranky.mjs. Shodu hlídá bajtový
   diff proti out/web (tests/test_php_shoda_stranek.py). */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Grafika;
use App\Sablony\Ikony;
use App\Obsah\StavVyrezu;

final class Casti
{
    /** Značka pro administraci — který text se tímhle prvkem edituje. */
    public static function dc(string $k): string
    {
        return ' data-cms="' . $k . '"';
    }

    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    public static function kartaSluzby(Kontext $ctx, array $s, array $volby = []): string
    {
        $kompakt = (bool) ($volby['kompakt'] ?? false);
        $id = $s['id'];
        return '<a class="karta-sluzba" href="' . $ctx->odkaz('sluzba', $id) . '">
    <span class="karta-ikona">' . self::ikona($s['ikona']) . '</span>
    <h3' . self::dc("sluzby.polozky.{$id}.nazev") . '>' . $ctx->t("sluzby.polozky.{$id}.nazev") . '</h3>
    ' . ($kompakt ? '' : '<p' . self::dc("sluzby.polozky.{$id}.kratky") . '>' . $ctx->zk($ctx->t("sluzby.polozky.{$id}.kratky")) . '</p>') . '
    <span class="odkaz-sip">' . $ctx->t('ui.viceOSluzbe') . self::ikona('sip') . '</span>
  </a>';
    }

    public static function kartaRealizace(Kontext $ctx, array $r): string
    {
        $id = $r['id'];
        $nazev = $ctx->t("realizace.polozky.{$id}.nazev");
        $stitky = '';
        foreach (array_slice($r['kategorie'], 0, 2) as $k) {
            $stitky .= '<span class="odznak">' . $ctx->t("realizace.kategorie.{$k}") . '</span>';
        }
        return '<a class="karta-realizace" href="' . $ctx->odkaz('realizace', $id) . '">
    <span class="karta-nahled" data-motiv="' . $r['motiv'] . '" data-realizace-nahled="' . $id . '">' . Grafika::motivRealizace($r['motiv']) . '<span class="stitky">' . $stitky . '</span></span>
    <span class="telo">
      <h3' . self::dc("realizace.polozky.{$id}.nazev") . '>' . $nazev . '</h3>
      <span class="karta-meta">
        <span>' . self::ikona('misto', ['velikost' => 15]) . $ctx->t("realizace.polozky.{$id}.misto") . '</span>
        <span>' . self::ikona('kalendar', ['velikost' => 15]) . $ctx->datum($r['datum'], 'mesic') . '</span>
      </span>
      <p' . self::dc("realizace.polozky.{$id}.perex") . '>' . $ctx->zk($ctx->t("realizace.polozky.{$id}.perex")) . '</p>
      <span class="odkaz-sip">' . $ctx->t('ui.vice') . self::ikona('sip') . '</span>
    </span>
  </a>';
    }

    public static function kartaNovinky(Kontext $ctx, array $n): string
    {
        $id = $n['id'];
        return '<a class="karta-clanek" href="' . $ctx->odkaz('novinka', $id) . '">
    <span class="nahled">' . Grafika::motivRealizace($n['motiv']) . '</span>
    <span class="telo">
      <span class="datum">' . $ctx->datum($n['datum']) . '</span>
      <h3' . self::dc("novinky.polozky.{$id}.nazev") . '>' . $ctx->t("novinky.polozky.{$id}.nazev") . '</h3>
      <p' . self::dc("novinky.polozky.{$id}.perex") . '>' . $ctx->zk($ctx->t("novinky.polozky.{$id}.perex")) . '</p>
      <span class="odkaz-sip">' . $ctx->t('ui.cist') . self::ikona('sip') . '</span>
    </span>
  </a>';
    }

    public static function kartaClovek(Kontext $ctx, array $osoba): string
    {
        $id = $osoba['id'];
        /* Výřez fotky v kolečku: hlava sedí na každé fotce jinak, tak si
           ho správce nastaví v administraci (App\Obsah\StavVyrezu). */
        $styl = StavVyrezu::styl($osoba['vyrez'] ?? null);
        /* Fotku nahranou v administraci nese stav jako cestu do media/.
           V manifestu obrázků není (ten vzniká při sestavení), takže z ní
           nejde udělat <picture> s variantami — jde jen jeden <img>. */
        if (($osoba['fotka'] ?? '') !== '') {
            $e = static fn (string $x): string => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
            $portret = '<img src="' . $e($ctx->odkazKoren((string) $osoba['fotka']))
                . '" width="72" height="72" alt="' . $e((string) $osoba['jmeno'])
                . '" class="portret"' . ($styl !== '' ? ' style="' . $e($styl) . '"' : '')
                . ' loading="lazy" decoding="async">';
        } elseif ($ctx->maObrazek("portret-{$id}")) {
            $portret = $ctx->obrazek("portret-{$id}", [
                'alt' => $osoba['jmeno'],
                'sirky' => '72px',
                'trida' => 'portret',
                'styl' => $styl,
            ]);
        } else {
            $portret = '';
        }
        return '<div class="karta-clovek">
    <span class="avatar" data-cms-vyrez="' . $id . '">
      <span class="inicialy" aria-hidden="true">' . $osoba['inicialy'] . '</span>
      ' . $portret . '
    </span>
    <span class="jmeno">' . $osoba['jmeno'] . '</span>
    <span class="role"' . self::dc("lide.{$id}") . '>'
            . ($ctx->existuje("lide.{$id}") ? $ctx->t("lide.{$id}") : '') . '</span>
    <a href="tel:' . $osoba['telefonHref'] . '">' . self::ikona('telefon') . $osoba['telefon'] . '</a>
    <a href="mailto:' . $osoba['email'] . '">' . self::ikona('mail') . $osoba['email'] . '</a>
  </div>';
    }

    public static function seznamOdskrtnuty(Kontext $ctx, string $prefix): string
    {
        $polozky = '';
        foreach ($ctx->klice($prefix) as $k) {
            $polozky .= '<li>' . self::ikona('fajfka') . '<span' . self::dc("{$prefix}.{$k}") . '>'
                . $ctx->zk($ctx->t("{$prefix}.{$k}")) . '</span></li>';
        }
        return '<ul class="seznam-odskrtnuty">' . $polozky . '</ul>';
    }

    public static function kroky(Kontext $ctx, string $prefix): string
    {
        $polozky = '';
        foreach ($ctx->klice($prefix) as $k) {
            $polozky .= '<div class="krok">
        <h3' . self::dc("{$prefix}.{$k}.titulek") . '>' . $ctx->t("{$prefix}.{$k}.titulek") . '</h3>
        <p' . self::dc("{$prefix}.{$k}.popis") . '>' . $ctx->zk($ctx->t("{$prefix}.{$k}.popis")) . '</p>
      </div>';
        }
        return '<div class="postup">' . $polozky . '</div>';
    }

    /** Kontaktní formulář — stejná komponenta na Kontaktu i v Kariéře. */
    public static function formular(Kontext $ctx, array $volby = []): string
    {
        $predvolenyTyp = (string) ($volby['predvolenyTyp'] ?? '');
        $id = (string) ($volby['id'] ?? 'formular');

        /* Hláška „v ukázce se nic neodesílá" patří jen do nákresu. Na ostrém
           webu formulář doopravdy odesílá, a kdyby tam ta věta zůstala, čte ji
           návštěvník nad odesílacím tlačítkem a poptávku rovnou vzdá. */
        $demoHlaska = $ctx->ukazka
            ? '<div class="hlaska hlaska-info">' . self::ikona('info')
                . '<span' . self::dc('kontakt.formular.odeslanoDemo') . '>'
                . $ctx->t('kontakt.formular.odeslanoDemo') . '</span></div>'
            : '';

        $moznosti = '';
        foreach ($ctx->klice('kontakt.formular.typy') as $k) {
            $moznosti .= '<option value="' . $k . '"' . ($k === $predvolenyTyp ? ' selected' : '') . '>'
                . $ctx->t("kontakt.formular.typy.{$k}") . '</option>';
        }

        // Záměrně co nejmíň polí: čím víc toho člověk musí vyplnit, tím míň
        // formulářů odejde. Firma, adresa a podrobnosti se doberou po telefonu.
        return '<form class="formular" id="' . $id . '" data-formular novalidate>
  ' . $demoHlaska . '
  <div class="pole">
    <label for="' . $id . '-typ">' . $ctx->t('kontakt.formular.typ') . ' <span aria-hidden="true">*</span></label>
    <select id="' . $id . '-typ" name="typ" required>
      <option value="">' . $ctx->t('kontakt.formular.typPlaceholder') . '</option>
      ' . $moznosti . '
    </select>
  </div>
  <div class="pole">
    <label for="' . $id . '-jmeno">' . $ctx->t('kontakt.formular.jmeno') . ' <span aria-hidden="true">*</span></label>
    <input type="text" id="' . $id . '-jmeno" name="jmeno" autocomplete="name" required>
  </div>
  <div class="formular-dvojice">
    <div class="pole">
      <label for="' . $id . '-telefon">' . $ctx->t('kontakt.formular.telefon') . '</label>
      <input type="tel" id="' . $id . '-telefon" name="telefon" autocomplete="tel" inputmode="tel">
    </div>
    <div class="pole">
      <label for="' . $id . '-email">' . $ctx->t('kontakt.formular.email') . '</label>
      <input type="email" id="' . $id . '-email" name="email" autocomplete="email">
    </div>
  </div>
  <p class="napoveda" style="margin:-0.5rem 0 1.05rem">' . $ctx->t('kontakt.formular.kontaktHint') . '</p>
  <div class="pole">
    <label for="' . $id . '-zprava">' . $ctx->t('kontakt.formular.zprava') . '</label>
    <textarea id="' . $id . '-zprava" name="zprava" rows="3"></textarea>
    <span class="napoveda">' . $ctx->t('kontakt.formular.zpravaHint') . '</span>
  </div>
  <div class="pole">
    <label class="zaskrtavatko">
      <input type="checkbox" name="souhlas" value="1" required>
      <span>' . $ctx->t('kontakt.formular.souhlas') . ' <a href="' . $ctx->odkaz('gdpr') . '">' . $ctx->t('kontakt.formular.souhlasOdkaz') . '</a></span>
    </label>
  </div>
  <input type="text" class="medovy" name="vebsajt" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button type="submit" class="tl tl-hlavni">' . self::ikona('mail') . $ctx->t('ui.odeslat') . '</button>
</form>';
    }

    /** Dlaždice větve — hlavní prvek úvodní stránky. */
    public static function dlazdiceVetve(Kontext $ctx, array $v): string
    {
        $id = $v['id'];
        return '<a class="dlazdice" href="' . $ctx->odkazVetve($id, 'vetev') . '">
    <span class="dlazdice-obraz">
      ' . $ctx->obrazek($v['foto'], ['alt' => '', 'sirky' => '46vw']) . '
      <span class="dlazdice-ikona">' . self::ikona($v['ikona'], ['velikost' => 30]) . '</span>
    </span>
    <span class="dlazdice-telo">
      <span class="dlazdice-nazev"' . self::dc("vetve.{$id}.nazev") . '>' . $ctx->t("vetve.{$id}.nazev") . '</span>
      <span class="dlazdice-podtitul"' . self::dc("vetve.{$id}.podtitul") . '>' . $ctx->t("vetve.{$id}.podtitul") . '</span>
      <span class="dlazdice-perex"' . self::dc("vetve.{$id}.perex") . '>' . $ctx->zk($ctx->t("vetve.{$id}.perex")) . '</span>
      <span class="odkaz-sip">' . $ctx->t("vetve.{$id}.cta") . self::ikona('sip') . '</span>
    </span>
  </a>';
    }
}
