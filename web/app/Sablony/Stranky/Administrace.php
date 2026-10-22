<?php
/* Kostra administrace. Vykreslování obsahu obstarává assets/admin.js.

   Přepis src/templates/administrace.mjs. Proti ukázce je tu jeden rozdíl,
   který dělá `Kontext::$ukazka`: v ukázce je přihlášení nákres s předvyplněným
   „green / demo", na ostrém webu je to skutečný formulář, který se odesílá na
   server, a zmizí upozornění, že se změny ukládají jen v prohlížeči.
   Administrace proto NENÍ v bajtovém diffu (tests/test_php_shoda_stranek.py). */

declare(strict_types=1);

namespace App\Sablony\Stranky;

use App\Jadro\Kontext;
use App\Sablony\Ikony;
use App\Sablony\Layout;

final class Administrace
{
    public const SKUPINY = [
        'rozcestnik' => 'Úvodní rozcestník',
        'vetve' => 'Domácnosti a firmy',
        'home' => 'Společné bloky úvodu',
        'sluzby' => 'Služby',
        'realizace' => 'Realizace',
        'novinky' => 'Novinky',
        'onas' => 'O nás',
        'kariera' => 'Kariéra',
        'kontakt' => 'Kontakt',
        'slovnik' => 'Slovník zkratek',
        'gdpr' => 'Ochrana osobních údajů',
        'chyba404' => 'Stránka 404',
        'footer' => 'Patička',
        'nav' => 'Navigace',
        'ui' => 'Tlačítka a popisky',
        'lide' => 'Lidé',
        'meta' => 'Titulky pro vyhledávače',
    ];

    public const METRIKY = ['navstevy', 'uzivatele', 'zobrazeni', 'poptavky', 'cas', 'opusteni'];

    /* Ostrý web mluví jinak než ukázka ("změny se ukládají do vašeho
       prohlížeče"). Když ke klíči existuje varianta se suffixem _server,
       použije se na serveru ona; jinak zůstane původní text. */
    private static function text(\App\Jadro\Kontext $ctx, string $klic): string
    {
        if ($ctx->ukazka) {
            return $ctx->t($klic);
        }
        $serverovy = $klic . '_server';
        $hodnota = $ctx->t($serverovy);

        return $hodnota === $serverovy ? $ctx->t($klic) : $hodnota;
    }

    private static function ikona(string $n, array $volby = []): string
    {
        return Ikony::ikona($n, $volby);
    }

    private static function js(mixed $data): string
    {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    }

    public static function administrace(Kontext $ctx, array $data): string
    {
        $data += ['klice' => [], 'slovniky' => [], 'realizace' => [], 'kategorie' => [], 'vetve' => []];
        $site = $ctx->site();

        $zalozka = static fn (string $id, string $popisek, string $ikonaId): string =>
            '<button type="button" class="admin-zalozka" data-zalozka="' . $id . '" aria-selected="false">'
            . self::ikona($ikonaId) . '<span>' . $popisek . '</span></button>';

        $dlazdiceMetrik = '';
        foreach (self::METRIKY as $k) {
            $nazev = $ctx->t("admin.nastenka.metriky.{$k}");
            $dlazdiceMetrik .= '<div class="admin-metrika" data-metrika="' . $k . '">
      <span class="admin-metrika-nazev">
        <abbr class="zkratka" tabindex="0" data-abbr="' . Layout::a($nazev) . '">' . $nazev . '</abbr>
      </span>
      <strong data-hodnota>—</strong>
      <span class="admin-metrika-zmena" data-zmena>—</span>
      <span class="admin-metrika-popis">' . $ctx->t('admin.nastenka.protiMinulemu') . '</span>
    </div>';
        }

        $rozpad = static fn (string $klic, string $nadpis): string =>
            '<div class="admin-rozpad">
      <h3>' . $nadpis . '</h3>
      <div data-rozpad="' . $klic . '"></div>
    </div>';

        $jazyky = '';
        foreach ($site['jazyky'] as $j) {
            $jazyky .= '<option value="' . $j['kod'] . '">' . $j['nazev'] . '</option>';
        }
        $chipyVetvi = '';
        $moznostiVetvi = '';
        foreach ($data['vetve'] as $v) {
            $chipyVetvi .= '<button type="button" class="chip" data-filtr-vetev="' . $v['id'] . '">' . $v['nazev'] . '</button>';
            $moznostiVetvi .= '<option value="' . $v['id'] . '">' . $v['nazev'] . '</option>';
        }
        $kategorie = '';
        foreach ($data['kategorie'] as $k => $v) {
            $kategorie .= '<label class="zaskrtavatko"><input type="checkbox" name="kategorie" value="' . $k . '"><span>' . $v . '</span></label>';
        }

        // --- přihlášení: v ukázce nákres, na ostrém webu skutečný formulář ---
        if ($ctx->ukazka) {
            $prihlaseni = '<div class="formular" style="max-width:26rem;margin-inline:auto">
        <p class="admin-login-nadpis">' . $ctx->t('admin.prihlaseni.titulek') . '</p>
        <p class="lead" style="font-size:.98rem;margin-bottom:1.4rem">' . $ctx->t('admin.prihlaseni.lead') . '</p>
        <div class="pole">
          <label for="admin-jmeno">' . $ctx->t('admin.prihlaseni.jmeno') . '</label>
          <input type="text" id="admin-jmeno" value="green" autocomplete="off">
        </div>
        <div class="pole">
          <label for="admin-heslo">' . $ctx->t('admin.prihlaseni.heslo') . '</label>
          <input type="password" id="admin-heslo" value="demo" autocomplete="off">
        </div>
        <button type="button" class="tl tl-hlavni" style="width:100%" data-vstoupit>' . self::ikona('sip') . $ctx->t('admin.prihlaseni.vstoupit') . '</button>
        <p class="napoveda" style="margin-top:1rem;text-align:center">' . $ctx->t('admin.prihlaseni.poznamka') . '</p>
      </div>';
            $upozorneni = '<div class="hlaska hlaska-info">' . self::ikona('info') . '<span>' . $ctx->t('admin.demoUpozorneni') . '</span></div>

      ';
        } else {
            $prihlaseni = '<form class="formular" method="post" action="' . $ctx->odkazKoren('administrace.html') . '" style="max-width:26rem;margin-inline:auto">
        <p class="admin-login-nadpis">' . $ctx->t('admin.prihlaseni.titulek') . '</p>
        <p class="lead" style="font-size:.98rem;margin-bottom:1.4rem">' . $ctx->t('admin.prihlaseni.lead_server') . '</p>
        ' . (($data['chybaPrihlaseni'] ?? false)
            // Pozor na `hidden`: .hlaska má v CSS display:flex, který atribut
            // přebije, a hláška by svítila i bez chyby. Proto se nevykresluje.
            ? '<div class="hlaska hlaska-chyba" data-chyba-prihlaseni>' . self::ikona('info') . '<span>' . $ctx->t('admin.prihlaseni.chyba') . '</span></div>'
            : '') . '
        <div class="pole">
          <label for="admin-jmeno">' . $ctx->t('admin.prihlaseni.jmeno') . '</label>
          <input type="text" id="admin-jmeno" name="jmeno" autocomplete="username" required>
        </div>
        <div class="pole">
          <label for="admin-heslo">' . $ctx->t('admin.prihlaseni.heslo') . '</label>
          <input type="password" id="admin-heslo" name="heslo" autocomplete="current-password" required>
        </div>
        <input type="hidden" name="akce" value="prihlasit">
        <input type="hidden" name="csrf" value="' . Layout::a((string) ($data['csrf'] ?? '')) . '">
        <button type="submit" class="tl tl-hlavni" style="width:100%" data-vstoupit>' . self::ikona('sip') . $ctx->t('admin.prihlaseni.vstoupit') . '</button>
        <p class="napoveda" style="margin-top:1rem;text-align:center">' . $ctx->t('admin.prihlaseni.poznamka_server') . '</p>
      </form>';
            $upozorneni = '';
        }

        $metrikyNazvy = [];
        $napovedy = [];
        foreach (self::METRIKY as $k) {
            $metrikyNazvy[$k] = $ctx->t("admin.nastenka.metriky.{$k}");
            $napovedy[$ctx->t("admin.nastenka.metriky.{$k}")] = [
                'full' => 'ukazatel z Google Analytics',
                'popis' => $ctx->t("admin.nastenka.napoveda.{$k}"),
            ];
        }
        $rozpadPolozky = static function (string $prefix) use ($ctx): array {
            $out = [];
            foreach ($ctx->klice($prefix) as $k) {
                $out[] = $ctx->t("{$prefix}.{$k}");
            }
            return $out;
        };
        $popisky = [];
        foreach ([
            'puvodni' => 'admin.texty.puvodni', 'zmeneno' => 'admin.texty.zmeneno',
            'vratit' => 'admin.texty.vratit', 'ulozit' => 'admin.texty.ulozit',
            'ulozeno' => 'admin.texty.ulozeno', 'upravit' => 'admin.realizace.upravit',
            'smazat' => 'admin.realizace.smazat', 'smazatPotvrzeni' => 'admin.realizace.smazatPotvrzeni',
            'vlastni' => 'admin.realizace.vlastni', 'upravena' => 'admin.realizace.upravena',
            'prazdne' => 'admin.realizace.prazdne', 'pridat' => 'admin.realizace.pridat',
            'posledniZmena' => 'admin.data.posledniZmena', 'zadnaZmena' => 'admin.data.zadnaZmena',
            'chybaImportu' => 'admin.data.chybaImportu', 'vymazatPotvrzeni' => 'admin.data.vymazatPotvrzeni',
            'odebrat' => 'admin.uzivatele.odebrat', 'odebratPotvrzeni' => 'admin.uzivatele.odebratPotvrzeni',
            'uzivateleprazdne' => 'admin.uzivatele.prazdne', 'role' => 'admin.uzivatele.role',
            'pravaSloupec' => 'admin.uzivatele.pravaSloupec', 'fotkyPrazdno' => 'admin.realizace.fotkyPrazdno',
            'fotkySouhrn' => 'admin.realizace.fotkySouhrn', 'fotkyTitulni' => 'admin.realizace.fotkyTitulni',
            'fotkyNastavTitulni' => 'admin.realizace.fotkyNastavTitulni',
            'fotkyOdebrat' => 'admin.realizace.fotkyOdebrat', 'fotkyDoleva' => 'admin.realizace.fotkyDoleva',
            'fotkyDoprava' => 'admin.realizace.fotkyDoprava', 'fotkyPlno' => 'admin.realizace.fotkyPlno',
        ] as $jmeno => $klic) {
            $popisky[$jmeno] = $ctx->t($klic);
        }
        $chybyFotek = [];
        foreach (['typ', 'velikost', 'pocet', 'misto', 'duplikat', 'neplatny', 'nacteni'] as $k) {
            $chybyFotek[$k] = $ctx->t("admin.realizace.fotkyChyba.{$k}");
        }
        $popisky['fotkyChyba'] = $chybyFotek;

        return '<section class="admin" data-admin>
  <div class="admin-prihlaseni" data-prihlaseni>
    <div class="obal obal-uzky">
      ' . $prihlaseni . '
    </div>
  </div>

  <div class="admin-app" data-app hidden>
    <div class="obal">
      <div class="admin-hlavicka">
        <div>
          <h1>' . $ctx->t('admin.titulek') . '</h1>
          <p class="lead" style="font-size:.98rem">' . self::text($ctx, 'admin.uvod') . '</p>
        </div>
        <div class="admin-akce">
          <a class="tl tl-obrys tl-mala" href="' . $ctx->odkaz('index') . '">' . self::ikona('externi') . $ctx->t('admin.zpetNaWeb') . '</a>
          <button type="button" class="tl tl-obrys tl-mala" data-odhlasit>' . $ctx->t('admin.odhlasit') . '</button>
        </div>
      </div>

      ' . $upozorneni . '<div class="admin-zalozky" role="tablist">
        ' . $zalozka('nastenka', $ctx->t('admin.zalozky.nastenka'), 'graf') . '
        ' . $zalozka('texty', $ctx->t('admin.zalozky.texty'), 'upravit') . '
        ' . $zalozka('realizace', $ctx->t('admin.zalozky.realizace'), 'montaz') . '
        ' . $zalozka('uzivatele', $ctx->t('admin.zalozky.uzivatele'), 'klic') . '
        ' . $zalozka('data', $ctx->t('admin.zalozky.data'), 'ulozit') . '
      </div>

      <!-- ------------------------------------------------- nástěnka -->
      <div class="admin-panel" data-panel="nastenka">
        <div class="admin-nastroje">
          <p class="lead" style="font-size:.95rem;flex:1;min-width:16rem">' . self::text($ctx, 'admin.nastenka.lead') . '</p>
          <div class="admin-obdobi" role="group" aria-label="' . Layout::a($ctx->t('admin.nastenka.obdobi')) . '">
            <button type="button" class="chip" data-obdobi="7">' . $ctx->t('admin.nastenka.obdobi7') . '</button>
            <button type="button" class="chip" data-obdobi="30" aria-pressed="true">' . $ctx->t('admin.nastenka.obdobi30') . '</button>
            <button type="button" class="chip" data-obdobi="90">' . $ctx->t('admin.nastenka.obdobi90') . '</button>
          </div>
        </div>
        <div class="hlaska hlaska-info" data-nastenka-upozorneni>' . self::ikona('varovani') . '<span>' . self::text($ctx, 'admin.nastenka.upozorneni') . '</span></div>
        <div class="admin-metriky">' . $dlazdiceMetrik . '</div>
        <div class="admin-graf">
          <h3>' . $ctx->t('admin.nastenka.grafTitulek') . '</h3>
          <div data-graf></div>
        </div>
        <div class="admin-rozpady">
          ' . $rozpad('zdroje', $ctx->t('admin.nastenka.zdroje')) . '
          ' . $rozpad('vstupni', $ctx->t('admin.nastenka.vstupni')) . '
          ' . $rozpad('zarizeni', $ctx->t('admin.nastenka.zarizeni')) . '
        </div>
      </div>

      <!-- ---------------------------------------------------- texty -->
      <div class="admin-panel" data-panel="texty" hidden>
        <div class="admin-nastroje">
          <label class="hledani" style="flex:1;min-width:220px">
            <span class="vizualne-skryto">' . $ctx->t('admin.texty.hledat') . '</span>
            ' . self::ikona('lupa') . '
            <input type="search" data-admin-hledani placeholder="' . Layout::a($ctx->t('admin.texty.hledat')) . '…">
          </label>
          <label class="admin-jazyk">
            <span>' . $ctx->t('admin.texty.jazyk') . '</span>
            <select data-admin-jazyk>
              ' . $jazyky . '
            </select>
          </label>
        </div>
        <p class="lead" style="font-size:.95rem">' . $ctx->t('admin.texty.lead') . '</p>
        <div data-admin-texty></div>
        <p data-admin-texty-prazdno hidden class="lead" style="text-align:center;padding:2rem">' . $ctx->t('admin.texty.zadnyVysledek') . '</p>
      </div>

      <!-- ------------------------------------------------ realizace -->
      <div class="admin-panel" data-panel="realizace" hidden>
        <div class="admin-nastroje">
          <p class="lead" style="font-size:.95rem;flex:1;min-width:16rem">' . $ctx->t('admin.realizace.lead') . '</p>
          <div class="filtry-chipy">
            <button type="button" class="chip" data-filtr-vetev="vse" aria-pressed="true">' . $ctx->t('admin.realizace.vsechnyVetve') . '</button>
            ' . $chipyVetvi . '
          </div>
          <button type="button" class="tl tl-hlavni tl-mala" data-pridat-realizaci>' . self::ikona('plus') . $ctx->t('admin.realizace.pridat') . '</button>
        </div>
        <div data-admin-realizace></div>
      </div>

      <!-- ------------------------------------------------- uživatelé -->
      <div class="admin-panel" data-panel="uzivatele" hidden>
        <div class="admin-nastroje">
          <p class="lead" style="font-size:.95rem;flex:1;min-width:16rem">' . $ctx->t('admin.uzivatele.lead') . '</p>
          <button type="button" class="tl tl-hlavni tl-mala" data-pridat-uzivatele>' . self::ikona('plus') . $ctx->t('admin.uzivatele.pridat') . '</button>
        </div>
        <div data-admin-uzivatele></div>
        <p class="napoveda" style="margin-top:1rem">' . self::text($ctx, 'admin.uzivatele.poznamka') . '</p>
      </div>

      <!-- ----------------------------------------------------- data -->
      <div class="admin-panel" data-panel="data" hidden>
        <p class="lead" style="font-size:.95rem">' . self::text($ctx, 'admin.data.lead') . '</p>
        <p class="admin-cas" data-admin-cas></p>
        <div class="tlacitka" style="margin-top:1.4rem">
          <button type="button" class="tl tl-obrys" data-export>' . self::ikona('stahnout') . $ctx->t('admin.data.stahnout') . '</button>
          <label class="tl tl-obrys" style="cursor:pointer">
            ' . self::ikona('nahrat') . $ctx->t('admin.data.nahrat') . '
            <input type="file" accept="application/json" data-import hidden>
          </label>
          <button type="button" class="tl tl-obrys" data-reset style="border-color:var(--cihlová-obrys);color:var(--cihlová)">' . self::ikona('kos') . $ctx->t('admin.data.vymazat') . '</button>
        </div>
      </div>
    </div>
  </div>

  <dialog class="admin-dialog" data-dialog>
    <form method="dialog" data-realizace-form>
      <h2 data-dialog-titulek>' . $ctx->t('admin.realizace.pridat') . '</h2>
      <div class="formular-dvojice">
        <div class="pole"><label for="r-nazev">' . $ctx->t('admin.realizace.nazev') . '</label><input type="text" id="r-nazev" name="nazev" required></div>
        <div class="pole">
          <label for="r-vetev">' . $ctx->t('admin.realizace.vetev') . '</label>
          <select id="r-vetev" name="vetev">
            ' . $moznostiVetvi . '
          </select>
        </div>
        <div class="pole"><label for="r-misto">' . $ctx->t('admin.realizace.misto') . '</label><input type="text" id="r-misto" name="misto"></div>
        <div class="pole"><label for="r-datum">' . $ctx->t('admin.realizace.datum') . '</label><input type="date" id="r-datum" name="datum"></div>
        <div class="pole"><label for="r-plocha">' . $ctx->t('admin.realizace.plocha') . '</label><input type="text" id="r-plocha" name="plocha"></div>
        <div class="pole"><label for="r-doba">' . $ctx->t('admin.realizace.doba') . '</label><input type="text" id="r-doba" name="doba"></div>
      </div>
      <div class="pole">
        <label>' . $ctx->t('admin.realizace.kategorie') . '</label>
        <div class="admin-kategorie">' . $kategorie . '</div>
      </div>
      <div class="pole"><label for="r-perex">' . $ctx->t('admin.realizace.perex') . '</label><textarea id="r-perex" name="perex" style="min-height:70px"></textarea></div>
      <div class="pole"><label for="r-zadani">' . $ctx->t('admin.realizace.zadani') . '</label><textarea id="r-zadani" name="zadani" style="min-height:70px"></textarea></div>
      <div class="pole"><label for="r-rozsah">' . $ctx->t('admin.realizace.rozsah') . '</label><textarea id="r-rozsah" name="rozsah" style="min-height:110px"></textarea></div>
      <div class="pole"><label for="r-technologie">' . $ctx->t('admin.realizace.technologie') . '</label><input type="text" id="r-technologie" name="technologie"></div>
      <div class="pole"><label for="r-vysledek">' . $ctx->t('admin.realizace.vysledek') . '</label><textarea id="r-vysledek" name="vysledek" style="min-height:90px"></textarea></div>
      <div class="pole">
        <label>' . $ctx->t('admin.realizace.fotky') . '</label>
        <div class="admin-fotky-zona" data-fotky-zona>
          <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-fotky-vstup>
          <button type="button" class="tl tl-obrys tl-mala" data-fotky-vybrat>' . self::ikona('obrazek') . $ctx->t('admin.realizace.fotkyVybrat') . '</button>
          <p class="napoveda">' . $ctx->t('admin.realizace.fotkyNapoveda') . '</p>
        </div>
        <div class="admin-fotky" data-fotky-seznam></div>
        <p class="napoveda" data-fotky-souhrn></p>
        <div class="admin-fotky-chyby" data-fotky-chyby hidden></div>
      </div>
      <input type="hidden" name="id">
      <div class="tlacitka" style="justify-content:flex-end;margin-top:1rem">
        <button type="button" class="tl tl-obrys tl-mala" data-zavrit-dialog>' . $ctx->t('admin.realizace.zrusit') . '</button>
        <button type="submit" class="tl tl-hlavni tl-mala">' . self::ikona('ulozit') . $ctx->t('admin.realizace.ulozit') . '</button>
      </div>
    </form>
  </dialog>

  <dialog class="admin-dialog" data-dialog-uzivatel>
    <form method="dialog" data-uzivatel-form>
      <h2>' . $ctx->t('admin.uzivatele.pridat') . '</h2>
      <div class="formular-dvojice">
        <div class="pole"><label for="u-jmeno">' . $ctx->t('admin.uzivatele.jmeno') . '</label><input type="text" id="u-jmeno" name="jmeno" required></div>
        <div class="pole"><label for="u-email">' . $ctx->t('admin.uzivatele.email') . '</label><input type="email" id="u-email" name="email"></div>
      </div>
      <div class="pole">
        <label for="u-role">' . $ctx->t('admin.uzivatele.role') . '</label>
        <select id="u-role" name="role">
          <option value="spravce">' . $ctx->t('admin.uzivatele.role_spravce') . '</option>
          <option value="editor" selected>' . $ctx->t('admin.uzivatele.role_editor') . '</option>
          <option value="autor">' . $ctx->t('admin.uzivatele.role_autor') . '</option>
        </select>
      </div>
      <div class="tlacitka" style="justify-content:flex-end;margin-top:1rem">
        <button type="button" class="tl tl-obrys tl-mala" data-zavrit-uzivatel>' . $ctx->t('admin.uzivatele.zrusit') . '</button>
        <button type="submit" class="tl tl-hlavni tl-mala">' . self::ikona('ulozit') . $ctx->t('admin.uzivatele.ulozit') . '</button>
      </div>
    </form>
  </dialog>
</section>

<script type="application/json" data-admin-data>' . self::js($data) . '</script>
<script type="application/json" data-admin-texty-slovnik>' . self::js([
            'skupiny' => self::SKUPINY,
            'metriky' => $metrikyNazvy,
            'rozpady' => [
                'zdroje' => $rozpadPolozky('admin.nastenka.zdrojePolozky'),
                'vstupni' => $rozpadPolozky('admin.nastenka.vstupniPolozky'),
                'zarizeni' => $rozpadPolozky('admin.nastenka.zarizeniPolozky'),
            ],
            'role' => [
                'spravce' => ['nazev' => $ctx->t('admin.uzivatele.role_spravce'), 'prava' => $ctx->t('admin.uzivatele.prava_spravce')],
                'editor' => ['nazev' => $ctx->t('admin.uzivatele.role_editor'), 'prava' => $ctx->t('admin.uzivatele.prava_editor')],
                'autor' => ['nazev' => $ctx->t('admin.uzivatele.role_autor'), 'prava' => $ctx->t('admin.uzivatele.prava_autor')],
            ],
            'popisky' => $popisky,
        ]) . '</script>
<script>
/* vysvětlivky k metrikám jedou přes stejnou bublinu jako zkratky na webu */
window.GAT_SLOVNIK = window.GAT_SLOVNIK || { terminy: {} };
Object.assign(window.GAT_SLOVNIK.terminy, ' . self::js($napovedy) . ');
</script>';
    }
}
