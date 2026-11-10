<?php
/* Kostra stránky: hlavička, mobilní panel, spodní lišta, patička.

   Web má dvě větve — domácnosti a firemní zákazníci. Navigace se podle toho
   mění: na rozcestníku a na společných stránkách nabízí obě větve, uvnitř
   větve ukazuje její služby a realizace plus přepínač na tu druhou.

   Přepis src/templates/layout.mjs z ukázky. Shodu hlídá tests/test_php_shoda_stranek.py
   (bajtový diff proti out/web). Proti ukázce je tu jediná změna: co se vkládá
   do atributu, projde htmlspecialchars — na ostrém webu ty texty píše
   administrace, ne my. */

declare(strict_types=1);

namespace App\Sablony;

use App\Jadro\Config;
use App\Jadro\Kontext;
use App\Jadro\Odkazy;

final class Layout
{
    private const KLIC_NAV = [
        'index' => 'nav.uvod',
        'sluzby' => 'nav.sluzby',
        'realizace' => 'nav.realizace',
        'onas' => 'nav.onas',
        'novinky' => 'nav.novinky',
        'kariera' => 'nav.kariera',
        'kontakt' => 'nav.kontakt',
        'slovnik' => 'nav.slovnik',
    ];

    private const SPOLECNE = ['onas', 'novinky', 'kariera', 'kontakt'];

    /** Text do atributu.

       Ukázka texty do atributů vkládala natvrdo — v administraci je ale píše
       člověk, takže uvozovka a ampersand se musí ošetřit. Apostrof se naopak
       nechává: v atributu v dvojitých uvozovkách nic nerozbije a ukázka ho
       taky nechává, takže bajtový diff dál platí. Dvojí kódování vypnuté ze
       stejného důvodu. */
    public static function a(string $s): string
    {
        return htmlspecialchars($s, ENT_COMPAT | ENT_SUBSTITUTE, 'UTF-8', false);
    }

    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    /** Hlavička s logem, menu, telefonem a přepínačem jazyků. */
    public static function hlavicka(Kontext $ctx): string
    {
        $site = $ctx->site();
        $aktivni = $ctx->aktivni;
        $vetev = $ctx->vetev;

        // --- desktopové menu -----------------------------------------------
        if ($vetev !== null) {
            $pod = '';
            foreach ($ctx->sluzbyVetve($vetev) as $s) {
                $pod .= '<a href="' . $ctx->odkaz('sluzba', $s['id']) . '">' . self::ikona($s['ikona'])
                    . '<span>' . $ctx->t("sluzby.polozky.{$s['id']}.nazev") . '</span></a>';
            }
            $menu = '<div class="menu-rozbal">
        <a href="' . $ctx->odkaz('sluzby') . '"' . (str_starts_with($aktivni, 'sluzb') ? ' aria-current="page"' : '') . '>' . $ctx->t('nav.sluzby') . '</a>
        <div class="menu-panel"><div class="menu-panel-mrizka">' . $pod . '</div></div>
      </div>';
            $menu .= '<a href="' . $ctx->odkaz('realizace') . '"' . ($aktivni === 'realizace' ? ' aria-current="page"' : '') . '>' . $ctx->t('nav.realizace') . '</a>';
            foreach (self::SPOLECNE as $k) {
                $menu .= '<a href="' . $ctx->odkaz($k) . '"' . ($aktivni === $k ? ' aria-current="page"' : '') . '>' . $ctx->t(self::KLIC_NAV[$k]) . '</a>';
            }
        } else {
            $menu = '<a href="' . $ctx->odkaz('index') . '"' . ($aktivni === 'index' ? ' aria-current="page"' : '') . '>' . $ctx->t('nav.uvod') . '</a>';
            foreach ($site['vetve'] as $v) {
                $menu .= '<a href="' . $ctx->odkazVetve($v['id'], 'vetev') . '">' . $ctx->t("vetve.{$v['id']}.nazev") . '</a>';
            }
            foreach (self::SPOLECNE as $k) {
                $menu .= '<a href="' . $ctx->odkaz($k) . '"' . ($aktivni === $k ? ' aria-current="page"' : '') . '>' . $ctx->t(self::KLIC_NAV[$k]) . '</a>';
            }
        }

        // --- odznak větve s přepnutím na tu druhou --------------------------
        $odznakVetve = '';
        if ($vetev !== null) {
            $druha = null;
            foreach ($site['vetve'] as $v) {
                if ($v['id'] !== $vetev) {
                    $druha = $v;
                    break;
                }
            }
            $prepnout = $ctx->t('rozcestnik.prepnout');
            $odznakVetve = '<a class="lista-vetev" href="' . $ctx->odkazVetve($druha['id'], 'vetev') . '" title="' . self::a($prepnout) . '">
        <span class="lista-vetev-nazev">' . $ctx->t("vetve.{$vetev}.nazev") . '</span>
        <span class="lista-vetev-prepni">' . self::ikona('prepnout', ['velikost' => 15]) . '<span class="vizualne-skryto">' . $prepnout . '</span></span>
      </a>';
        }

        $jazyky = '';
        foreach ($site['jazyky'] as $j) {
            $jazyky .= '<a href="' . $ctx->jazykOdkaz($j['kod']) . '" lang="' . $j['html'] . '"'
                . ($j['kod'] === $ctx->lang ? ' aria-current="true"' : '') . '>' . $j['nazev'] . '</a>';
        }

        // --- mobilní panel ---------------------------------------------------
        $panelVetev = '';
        foreach ($site['vetve'] as $v) {
            $sluzby = '';
            foreach ($ctx->sluzbyVetve($v['id']) as $s) {
                $sluzby .= '<a href="' . $ctx->odkaz('sluzba', $s['id']) . '">' . $ctx->t("sluzby.polozky.{$s['id']}.nazev") . '</a>';
            }
            $panelVetev .= '<div class="panel-skupina"' . ($v['id'] === $vetev ? ' data-aktivni="1"' : '') . '>
        <div class="panel-nadpis">' . $ctx->t("vetve.{$v['id']}.nazev") . '</div>
        <div class="panel-podpolozky">
          <a href="' . $ctx->odkazVetve($v['id'], 'vetev') . '"><strong>' . $ctx->t("vetve.{$v['id']}.titulek") . '</strong></a>
          <a href="' . $ctx->odkazVetve($v['id'], 'sluzby') . '">' . $ctx->t('nav.sluzby') . '</a>
          ' . $sluzby . '
          <a href="' . $ctx->odkazVetve($v['id'], 'realizace') . '">' . $ctx->t('nav.realizace') . '</a>
        </div>
      </div>';
        }

        $panelSpolecne = '';
        foreach ([...self::SPOLECNE, 'slovnik'] as $k) {
            $panelSpolecne .= '<a class="panel-polozka" href="' . $ctx->odkaz($k) . '"'
                . ($aktivni === $k ? ' aria-current="page"' : '') . '>' . $ctx->t(self::KLIC_NAV[$k]) . self::ikona('sip') . '</a>';
        }

        $f = $site['firma'];
        return '<header class="lista" id="lista">
  <div class="obal lista-vnitrek">
    <a class="logo" href="' . $ctx->odkaz('index') . '" aria-label="' . self::a($f['nazev'] . ' — ' . $ctx->t('nav.uvod')) . '">
      <img src="' . $ctx->asset('img/logo.png') . '" width="400" height="181" alt="' . self::a($f['nazev']) . '">
    </a>
    ' . $odznakVetve . '
    <nav class="menu" aria-label="' . self::a($ctx->t('ui.menu')) . '">' . $menu . '</nav>
    <div class="lista-akce">
      <a class="lista-tel" href="tel:' . $f['dispecinkTelefonHref'] . '">
        <span class="tecka" aria-hidden="true"></span>' . $f['dispecinkTelefon'] . '
      </a>
      <div class="jazyky" data-jazyky>
        <button type="button" class="jazyky-tl" aria-expanded="false" aria-label="' . self::a($ctx->t('ui.jazyk')) . '">
          ' . self::zkratkaJazyka($ctx) . self::ikona('sipDolu', ['velikost' => 14]) . '
        </button>
        <div class="jazyky-seznam">' . $jazyky . '</div>
      </div>
      <button type="button" class="hamburger" data-hamburger aria-expanded="false" aria-controls="panel" aria-label="' . self::a($ctx->t('ui.menu')) . '"><span></span></button>
    </div>
  </div>
</header>
<!-- Panel je ZÁMĚRNĚ mimo <header>: kdyby hlavička někdy zase dostala
     backdrop-filter, stala by se vztažným rámcem pro position:fixed
     a panel by se roztáhl jen přes ni. -->
<div class="panel" id="panel" data-panel>
    <a class="panel-polozka" href="' . $ctx->odkaz('index') . '"' . ($aktivni === 'index' ? ' aria-current="page"' : '') . '>' . $ctx->t('nav.uvod') . self::ikona('sip') . '</a>
    ' . $panelVetev . '
    ' . $panelSpolecne . '
    <div class="panel-kontakt">
      <a class="tl tl-hlavni" href="tel:' . $f['dispecinkTelefonHref'] . '">' . self::ikona('telefon') . $ctx->t('ui.dispecink') . '</a>
      <a class="tl tl-obrys" href="mailto:' . $f['email'] . '">' . self::ikona('mail') . $f['email'] . '</a>
    </div>
</div>';
    }

    private static function zkratkaJazyka(Kontext $ctx): string
    {
        foreach ($ctx->site()['jazyky'] as $j) {
            if ($j['kod'] === $ctx->lang) {
                return $j['zkratka'];
            }
        }
        return '';
    }

    /** Spodní akční lišta — na mobilu pořád po ruce. */
    public static function spodniLista(Kontext $ctx): string
    {
        $f = $ctx->site()['firma'];
        return '<nav class="spodni-lista" aria-label="' . self::a($ctx->t('ui.kontaktujteNas')) . '">
  <a href="tel:' . $f['mobilKancelarHref'] . '">' . self::ikona('telefon') . '<span>' . $ctx->t('ui.zavolat') . '</span></a>
  <a class="zvyrazneno" href="tel:' . $f['dispecinkTelefonHref'] . '">' . self::ikona('hodiny') . '<span>' . $ctx->t('ui.dispecink') . '</span></a>
  <a href="' . $ctx->odkaz('kontakt') . '#formular">' . self::ikona('mail') . '<span>' . $ctx->t('ui.napsatNam') . '</span></a>
</nav>';
    }

    /** Patička: obě větve vedle sebe, pak firma a kontakt. */
    public static function paticka(Kontext $ctx): string
    {
        $site = $ctx->site();
        $f = $site['firma'];

        $sloupceVetvi = '';
        foreach ($site['vetve'] as $v) {
            $sluzby = '';
            foreach ($site['sluzby'] as $s) {
                if ($s['vetev'] !== $v['id']) {
                    continue;
                }
                $sluzby .= '<li><a href="' . $ctx->odkaz('sluzba', $s['id']) . '">' . $ctx->t("sluzby.polozky.{$s['id']}.nazev") . '</a></li>';
            }
            $sloupceVetvi .= '<div>
      <h4>' . $ctx->t("vetve.{$v['id']}.nazev") . '</h4>
      <ul>
        ' . $sluzby . '
        <li><a href="' . $ctx->odkazVetve($v['id'], 'realizace') . '"><strong style="color:#fff">' . $ctx->t('nav.realizace') . '</strong></a></li>
      </ul>
    </div>';
        }

        $firma = '';
        foreach (['onas', 'novinky', 'kariera', 'slovnik'] as $k) {
            $firma .= '<li><a href="' . $ctx->odkaz($k) . '">' . $ctx->t(self::KLIC_NAV[$k]) . '</a></li>';
        }

        $ukazka = $ctx->ukazka ? '<span class="paticka-ukazka">' . $ctx->t('footer.ukazka') . '</span>' : '';

        return '<footer class="paticka">
  <div class="obal">
    <div class="paticka-mrizka">
      <div>
        <span class="paticka-logo"><img src="' . $ctx->asset('img/logo.png') . '" width="400" height="181" alt="' . self::a($f['nazev']) . '" loading="lazy"></span>
        <p>' . $ctx->t('footer.tagline') . '</p>
        <p><strong style="color:#fff">IČO</strong> ' . $f['ico'] . ' · <strong style="color:#fff">DIČ</strong> ' . $f['dic'] . '</p>
      </div>
      ' . $sloupceVetvi . '
      <div>
        <h4>' . $ctx->t('footer.firma') . '</h4>
        <ul>' . $firma . '<li><a href="' . $ctx->odkaz('gdpr') . '">' . $ctx->t('gdpr.titulek') . '</a></li></ul>
        <h4 style="margin-top:1.4rem">' . $ctx->t('footer.kontakt') . '</h4>
        <ul>
          <li><a href="tel:' . $f['dispecinkTelefonHref'] . '"><strong style="color:#fff">' . $ctx->t('footer.dispecink') . '</strong><br>' . $f['dispecinkTelefon'] . '</a></li>
          <li><a href="mailto:' . $f['email'] . '">' . $f['email'] . '</a></li>
        </ul>
        <address style="margin-top:1rem">' . $f['sidlo']['ulice'] . ', ' . $f['sidlo']['psc'] . ' ' . $f['sidlo']['mesto'] . '<br>
        ' . $f['provozovna']['ulice'] . ', ' . $f['provozovna']['psc'] . ' ' . $f['provozovna']['mesto'] . '</address>
      </div>
    </div>
    <div class="paticka-dole">
      <span>© ' . date('Y') . ' ' . $f['nazev'] . '. ' . $ctx->t('footer.prava') . '</span>
      ' . $ukazka . '
      <a href="' . $ctx->odkazKoren('administrace.html') . '" class="paticka-admin">' . $ctx->tServer('footer.administrace') . '</a>
    </div>
  </div>
</footer>';
    }

    /** Složí celou HTML stránku. */
    public static function stranka(Kontext $ctx, array $casti): string
    {
        $telo = (string) ($casti['telo'] ?? '');
        $titulek = (string) ($casti['titulek'] ?? '');
        $popis = (string) ($casti['popis'] ?? '');
        $trida = (string) ($casti['trida'] ?? '');
        $skripty = (string) ($casti['skripty'] ?? '');

        $site = $ctx->site();

        /* Adresa webu z nastavení (instalátor ji zapíše jako `web`). Ukázka ji
           nemá — staví se jako statické soubory do podsložky na GitHub Pages a
           je celá noindex, takže absolutní adresy by tam byly nejen zbytečné,
           ale rovnou lživé. Chybová stránka a přihlášení do administrace se
           neindexují, těm canonical nepatří. */
        $bezAdresy = in_array($ctx->aktualniSoubor, [
            Odkazy::SOUBORY['chyba404'], Odkazy::SOUBORY['administrace'],
        ], true);
        $zaklad = ($ctx->ukazka || $bezAdresy)
            ? ''
            : rtrim((string) Config::dej('web', ''), '/');

        $jine = [];
        if ($zaklad !== '') {
            /* hreflang musí být plné adresy a každá jazyková verze musí uvádět
               i sebe samu — bez odkazu na sebe Google celou skupinu zahodí. */
            foreach ($site['jazyky'] as $j) {
                $jine[] = '<link rel="alternate" hreflang="' . $j['html']
                    . '" href="' . $zaklad . '/' . $ctx->cestaVJazyce($j['kod']) . '">';
            }
            $jine[] = '<link rel="alternate" hreflang="x-default" href="'
                . $zaklad . '/' . $ctx->cestaVJazyce('cs') . '">';
        } else {
            foreach ($site['jazyky'] as $j) {
                if ($j['kod'] !== $ctx->lang) {
                    $jine[] = '<link rel="alternate" hreflang="' . $j['html'] . '" href="' . $ctx->jazykOdkaz($j['kod']) . '">';
                }
            }
        }
        $jineJazyky = implode("\n  ", $jine);

        /* Web odpovídá na www i bez www. Bez tohohle řádku si je vyhledávač
           indexuje jako dva weby a sílu odkazů si rozdělí napůl. */
        $kanonicka = $zaklad !== ''
            ? "\n" . '<link rel="canonical" href="' . $zaklad . '/' . $ctx->cestaVJazyce($ctx->lang) . '">'
            : '';

        $htmlJazyk = '';
        foreach ($site['jazyky'] as $j) {
            if ($j['kod'] === $ctx->lang) {
                $htmlJazyk = $j['html'];
            }
        }

        $terminy = [];
        foreach ($ctx->terminy as $x) {
            $terminy[$x['abbr']] = ['full' => $x['full'], 'popis' => $x['popis']];
        }
        $js = static fn (array $data): string => json_encode(
            $data,
            JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR
        );

        // Ukázka se neindexuje celá; na ostrém webu jen přihlášení do
        // administrace. robots.txt ji zakazuje taky, ale ten je jen žádost.
        $roboti = ($ctx->ukazka || $ctx->aktivni === 'administrace')
            ? "\n" . '<meta name="robots" content="noindex, nofollow">'
            : '';

        return '<!doctype html>
<html lang="' . $htmlJazyk . '" class="bez-js"' . ($ctx->vetev !== null ? ' data-vetev="' . $ctx->vetev . '"' : '') . '>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>' . $titulek . '</title>
<meta name="description" content="' . self::a($popis) . '">' . $roboti . $kanonicka . '
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#e7f3df" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#122018" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="' . self::a($titulek) . '">
<meta property="og:description" content="' . self::a($popis) . '">
<meta property="og:type" content="website">
<meta property="og:image" content="' . $ctx->asset('img/og.svg') . '">
<meta property="og:site_name" content="' . self::a($site['firma']['nazev']) . '">
<link rel="icon" href="' . $ctx->asset('img/favicon.svg') . '" type="image/svg+xml">
<link rel="apple-touch-icon" href="' . $ctx->asset('img/favicon.svg') . '">
<link rel="preload" href="' . $ctx->asset('fonts/Barlow-700-latin.woff2') . '" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="' . $ctx->asset('fonts/Inter-400-latin.woff2') . '" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="' . $ctx->asset('style.css') . '">
' . $jineJazyky . '
<script>document.documentElement.classList.remove(\'bez-js\');document.documentElement.classList.add(\'js\');</script>
<script>
window.GAT_SLOVNIK = ' . $js(['terminy' => $terminy, 'zavrit' => $ctx->t('ui.zavrit')]) . ';
window.GAT_CHYBY = ' . $js($ctx->chybyFormulare()) . ';
window.GAT_TEXTY = ' . $js(['odeslano' => $ctx->t('kontakt.formular.odeslano')]) . ';
</script>
</head>
<body class="' . $trida . '">
<a class="preskok" href="#obsah">' . $ctx->t('ui.prejitNaObsah') . '</a>
' . self::hlavicka($ctx) . '
<main id="obsah">
' . $telo . '
</main>
' . self::paticka($ctx) . '
' . self::spodniLista($ctx) . '
<button type="button" class="nahoru" data-nahoru aria-label="' . self::a($ctx->t('ui.nahoru')) . '">' . self::ikona('sipNahoru') . '</button>
<script src="' . $ctx->asset('app.js') . '" defer></script>
' . $skripty . '
</body>
</html>';
    }

    /** Tmavé podhlaví vnitřních stránek s drobečkovou navigací. */
    public static function podhlavi(Kontext $ctx, array $volby): string
    {
        $stitek = (string) ($volby['stitek'] ?? '');
        $titulek = (string) ($volby['titulek'] ?? '');
        $lead = (string) ($volby['lead'] ?? '');
        $drobecky = $volby['drobecky'] ?? [];
        $platno = (bool) ($volby['platno'] ?? true);

        $cesta = [['nazev' => $ctx->t('nav.uvod'), 'klic' => 'index'], ...$drobecky];
        $polozky = '';
        $posledniIndex = count($cesta) - 1;
        foreach ($cesta as $i => $d) {
            if ($i === $posledniIndex) {
                $polozky .= '<li aria-current="page">' . $d['nazev'] . '</li>';
                continue;
            }
            $href = isset($d['klic']) ? $ctx->odkaz($d['klic']) : (string) $d['href'];
            $polozky .= '<li><a href="' . $href . '">' . $d['nazev'] . '</a></li>';
        }

        return '<section class="podhlavi">
  ' . ($platno ? '<canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>' : '') . '
  <div class="obal">
    <nav class="drobecky" aria-label="Drobečková navigace"><ol>' . $polozky . '</ol></nav>
    ' . ($stitek !== '' ? '<span class="stitek">' . $stitek . '</span>' : '') . '
    <h1>' . $titulek . '</h1>
    ' . ($lead !== '' ? '<p class="lead">' . $lead . '</p>' : '') . '
  </div>
</section>';
    }

    /** Zelený/tmavý pruh s výzvou k akci. */
    public static function vyzva(Kontext $ctx, array $volby = []): string
    {
        $f = $ctx->site()['firma'];
        $titulek = (string) ($volby['titulek'] ?? '');
        $lead = (string) ($volby['lead'] ?? '');
        $primarni = (string) ($volby['primarni'] ?? '');
        $sekundarni = (string) ($volby['sekundarni'] ?? '');

        return '<section class="sekce">
  <div class="obal">
    <div class="vyzva">
      <h2>' . ($titulek !== '' ? $titulek : $ctx->t('home.kontakt.titulek')) . '</h2>
      <p>' . ($lead !== '' ? $lead : $ctx->t('home.kontakt.lead')) . '</p>
      <div class="tlacitka">
        <a class="tl tl-hlavni" href="' . $ctx->odkaz('kontakt') . '#formular">' . self::ikona('mail') . ($primarni !== '' ? $primarni : $ctx->t('ui.nezavaznaPoptavka')) . '</a>
        <a class="tl tl-obrys" href="tel:' . $f['dispecinkTelefonHref'] . '">' . self::ikona('telefon') . ($sekundarni !== '' ? $sekundarni : $ctx->t('ui.dispecink') . ' · ' . $f['dispecinkTelefon']) . '</a>
      </div>
    </div>
  </div>
</section>';
    }
}
