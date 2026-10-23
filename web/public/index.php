<?php
/* Vstupní bod webu. Apache/nginx sem posílá všechno, co není soubor.

   Adresy zůstávají stejné jako v ukázce (/index.html, /en/kontakt.html).
   Tvar bez přípony funguje taky — odpoví přesměrováním na kanonický .html,
   aby každá stránka měla jednu adresu. */

declare(strict_types=1);

require dirname(__DIR__) . '/app/Jadro/Autoload.php';

// Dřív než se cokoli vytiskne: žádná hláska PHP nesmí odejít do odpovědi.
App\Jadro\Chyby::nastav();

// Bezpečnostní hlavičky posílá PHP, aby platily i tam, kde se .htaccess nečte.
App\Jadro\Hlavicky::posli();

use App\Api\Router;
use App\Auth\Sezeni;
use App\Auth\Uzivatele;
use App\Auth\Zamek;
use App\Db\Spojeni;
use App\Db\UlozisteDb;
use App\Fotky\Zpracovani;
use App\Jadro\Config;
use App\Jadro\Odkazy;
use App\Jadro\Stranka;
use App\Obsah\ZdrojDb;
use App\Obsah\ZdrojJson;

$koren = dirname(__DIR__);
$ukazka = Config::ukazka();

/* --------------------------------------------------------------- obsah */

$vychozi = new ZdrojJson($koren . '/data', __DIR__ . '/assets');
$uloziste = null;
$zdroj = $vychozi;

if (Spojeni::pripraveno()) {
    $uloziste = new UlozisteDb(Spojeni::dej());
    if (class_exists(ZdrojDb::class)) {
        $zdroj = new ZdrojDb($koren . '/data', __DIR__ . '/assets', $uloziste->stav());
    }
}

$site = $zdroj->site();
$cesta = ltrim(rawurldecode((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH)), '/');
$metoda = strtoupper((string) ($_SERVER['REQUEST_METHOD'] ?? 'GET'));

/* ------------------------------------------------------------------ API */

if (str_starts_with($cesta, 'api/')) {
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');

    $odpoved = static function (int $stav, array $telo): void {
        http_response_code($stav);
        echo json_encode($telo, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    };

    $cil = substr($cesta, 4);

    // poptávka z formuláře — jediný cíl, který je veřejný
    if ($cil === 'poptavka') {
        App\Jadro\Poptavka::obsluz($metoda, $zdroj, $uloziste, $odpoved);
        return;
    }

    if ($uloziste === null || !class_exists(Router::class)) {
        $odpoved(503, ['chyba' => 'api-neni']);
        return;
    }

    Sezeni::zacni();

    /* Statistiky na nástěnku: jen když je v nastavení vlastnost GA4 i klíč
       servisního účtu. Bez nich dostane Router null a nástěnka zůstane prázdná
       — vymyšlená čísla se na ostrém webu nekreslí. */
    $statistiky = null;
    $vlastnost = (string) Config::dej('analytics.property', '');
    $klicGa4 = (string) Config::dej('analytics.klic', '');
    if ($vlastnost !== '' && $klicGa4 !== '' && is_file($klicGa4) && class_exists(App\Statistiky\Ga4Prevod::class)) {
        $statistiky = new App\Statistiky\Ga4(
            $vlastnost,
            $klicGa4,
            $koren . '/cache',
            Spojeni::pripraveno() ? Spojeni::dej() : null
        );
    }

    $vysledek = Router::obsluz([
        'metoda' => $metoda,
        'cesta' => $cil,
        'telo' => (string) file_get_contents('php://input'),
        'dotaz' => $_GET,
        'uzivatel' => Sezeni::uzivatel(),
        'csrf_ok' => Sezeni::csrfPlati($_SERVER['HTTP_X_CSRF'] ?? ($_POST['csrf'] ?? null)),
        'soubor' => isset($_FILES['fotka']) && is_uploaded_file((string) $_FILES['fotka']['tmp_name'])
            ? ['tmp_name' => (string) $_FILES['fotka']['tmp_name'], 'name' => (string) $_FILES['fotka']['name']]
            : null,
    ], $uloziste, $statistiky, new Zpracovani(__DIR__ . '/media', 'media'));

    $odpoved((int) $vysledek['stav'], (array) $vysledek['telo']);
    return;
}

/* ------------------------------------------------- sitemapa a robots.txt

   Vydává je PHP, ne soubor na disku: realizace přidaná v administraci je pak
   v sitemapě hned a nikdo nemusí nic pouštět z příkazové řádky. */

if ($cesta === 'sitemap.xml' || $cesta === 'robots.txt') {
    $domena = rtrim((string) Config::dej('web', ''), '/');
    if ($domena === '') {
        $domena = (App\Jadro\Hlavicky::pozadavekPresHttps() ? 'https://' : 'http://')
            . (string) ($_SERVER['HTTP_HOST'] ?? 'localhost');
    }
    header('Cache-Control: public, max-age=3600');
    if ($cesta === 'robots.txt') {
        header('Content-Type: text/plain; charset=utf-8');
        echo App\Jadro\Sitemapa::robots($domena);
    } else {
        header('Content-Type: application/xml; charset=utf-8');
        echo App\Jadro\Sitemapa::xml($site, $domena, date('Y-m-d'));
    }
    return;
}

/* ----------------------------------------------------------- stránky */

$kam = Odkazy::rozpoznej($cesta, $site);

// tvar bez .html → přesměrování na kanonickou adresu
if ($kam !== null && $cesta !== '' && !str_ends_with($cesta, '.html')) {
    header('Location: /' . ($kam['jazyk'] !== 'cs' ? $kam['jazyk'] . '/' : '') . $kam['soubor'], true, 301);
    return;
}

/* přihlášení do administrace */
if ($kam !== null && $kam['druh'] === 'administrace' && $metoda === 'POST') {
    Sezeni::zacni();
    $akce = (string) ($_POST['akce'] ?? '');
    $kamZpet = '/' . Odkazy::SOUBORY['administrace'];

    if ($akce === 'odhlasit') {
        Sezeni::odhlas();
        header('Location: ' . $kamZpet, true, 303);
        return;
    }
    if ($akce === 'prihlasit' && $uloziste !== null && Sezeni::csrfPlati((string) ($_POST['csrf'] ?? ''))) {
        $jmeno = trim((string) ($_POST['jmeno'] ?? ''));

        /* Adresa návštěvníka. Za Cloudflare nebo za proxy má REMOTE_ADDR
           každý stejnou, a protože se zamyká i podle adresy, zamkl by jeden
           útočník všechny. Proto se bere adresa z hlavičky, když přijde.
           Podvržená hlavička nic neotevře: tvrdý strop je jméno, adresa je
           jen přidaná pojistka. */
        $ip = trim((string) ($_SERVER['HTTP_CF_CONNECTING_IP']
            ?? explode(',', (string) ($_SERVER['HTTP_X_FORWARDED_FOR'] ?? ''))[0]));
        if ($ip === '') {
            $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? '');
        }

        /* Hádání hesla se počítá v databázi. Zámek se ptá dřív, než se heslo
           vůbec ověří — a zamčený pokus se už nezapisuje, jinak by útočník
           držel správce venku, jak dlouho by chtěl. */
        $zamek = 0;
        if ($uloziste instanceof UlozisteDb) {
            $casy = $uloziste->casyChybnychHesel($jmeno, $ip, Zamek::OKNO);
            $zamek = Zamek::ceka($casy, time());
        }
        if ($zamek > 0) {
            header('Location: ' . $kamZpet . '?chyba=zamceno&minut=' . (int) ceil($zamek / 60), true, 303);
            return;
        }

        $uzivatel = $uloziste->uzivatelPodleJmena($jmeno);
        if ($uzivatel !== null && Uzivatele::overHeslo($uzivatel, (string) ($_POST['heslo'] ?? ''))) {
            Sezeni::prihlas($uzivatel);
            $uloziste->zapisPrihlaseni((int) $uzivatel['id']);
            $uloziste->zapisUdalost((string) $uzivatel['jmeno'], 'prihlaseni');
            header('Location: ' . $kamZpet, true, 303);
            return;
        }
        Sezeni::spatneHeslo();
        if ($uloziste instanceof UlozisteDb) {
            $uloziste->zapisChybneHeslo($jmeno, $ip);
        }
    }
    header('Location: ' . $kamZpet . '?chyba=1', true, 303);
    return;
}

if ($kam === null) {
    http_response_code(404);
    $jazyk = 'cs';
    foreach ($site['jazyky'] as $j) {
        if ($j['adresar'] !== '' && str_starts_with($cesta, $j['adresar'] . '/')) {
            $jazyk = $j['kod'];
        }
    }
    $kam = [
        'jazyk' => $jazyk, 'druh' => 'chyba404', 'id' => null, 'vetev' => null,
        'soubor' => Odkazy::SOUBORY['chyba404'],
    ];
}

header('Content-Type: text/html; charset=utf-8');
if ($kam['druh'] === 'administrace') {
    header('Cache-Control: no-store');
    Sezeni::zacni();
}
echo Stranka::vykresli($kam, $zdroj, $ukazka, $vychozi, $uloziste);
