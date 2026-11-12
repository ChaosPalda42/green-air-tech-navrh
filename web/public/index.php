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
use App\Auth\Pozvanka;
use App\Auth\Sezeni;
use App\Auth\Uzivatele;
use App\Auth\Zamek;
use App\Db\Spojeni;
use App\Db\UlozisteDb;
use App\Fotky\Zpracovani;
use App\Jadro\Adresa;
use App\Jadro\Config;
use App\Jadro\Metoda;
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

    /* Administrace ukládá PUTem a maže DELETE. Hosting u klienta ale ani
       jedno nepustí — Apache vrátí 403 dřív, než se PHP spustí, a správci
       se neuloží nic. Prohlížeč proto posílá POST se skutečnou metodou
       v hlavičce; rozhoduje o tom App\Jadro\Metoda. Pod poptávkou schválně:
       ta je veřejná a zůstává POST jako POST. */
    $metoda = Metoda::skutecna($metoda, $_SERVER);

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
        /* Soubor nad upload_max_filesize PHP zahodí a nechá jen číslo chyby.
           Bez něj Router nemá jak poznat „moc velký" od „žádný" a říkal
           správci, ať soubor vybere — přitom ho vybral. */
        'soubor_chyba' => isset($_FILES['fotka']['error'])
            ? (int) $_FILES['fotka']['error'] : null,
        /* A když požadavek přeteče post_max_size, PHP zahodí i $_FILES a
           $_POST. Zbyde jen délka těla — ta tedy rozhoduje. */
        'telo_velke' => $metoda === 'POST' && $_FILES === [] && $_POST === []
            && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0,
        /* Povolené klíče textů pro meze stavu (nález K2). Když soubor chybí
           nebo je rozbitý, jde dál prázdný seznam: jména klíčů se nehlídají,
           ale meze velikostí platí — administrace se kvůli jednomu
           chybějícímu souboru nesmí zaseknout. */
        'klice' => (static function (string $soubor): array {
            $json = is_file($soubor) ? (string) @file_get_contents($soubor) : '';
            $klice = $json !== '' ? json_decode($json, true) : null;
            return is_array($klice)
                ? array_values(array_filter($klice, static fn (mixed $k): bool => is_string($k)))
                : [];
        })($koren . '/data/admin-klice.json'),
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
           útočník všechny. Proto se bere adresa z hlavičky — ale JEN když
           nastavení webu řekne, že web za proxy opravdu stojí ('proxy' =>
           ['verit' => true]). Bez toho by si hlavičku poslal sám útočník a
           zámek podle adresy by obešel jedním řádkem v požadavku.
           Luští to App\Jadro\Adresa — stejně jako u stropu poptávek. */
        $ip = Adresa::navstevnika($_SERVER, Config::dej('proxy', []));

        /* Hádání hesla se počítá v databázi, a to ve dvou sadách: co přišlo
           z téhle adresy a co přišlo na tenhle účet. Každá má vlastní strop —
           kdyby byl jeden, útočník by desetkrát hádal heslo správce z deseti
           adres a držel ho venku. Zámek se ptá dřív, než se heslo vůbec ověří,
           a zamčený pokus se už nezapisuje. */
        $zamek = 0;
        if ($uloziste instanceof UlozisteDb) {
            $casy = $uloziste->casyChybnychHesel($jmeno, $ip, Zamek::OKNO);
            $zamek = Zamek::ceka($casy['adresa'], $casy['ucet'], time());
        }
        if ($zamek > 0) {
            header('Location: ' . $kamZpet . '?chyba=zamceno&minut=' . (int) ceil($zamek / 60), true, 303);
            return;
        }

        $uzivatel = $uloziste->uzivatelPodleJmena($jmeno);

        /* Heslo se ověřuje VŽDY, i když takový účet není (nález K3).
           `overHeslo` si na null dopočítá falešný hash, takže bcrypt stojí
           stejně dlouho jako u existujícího účtu. Kdyby se tu zkrátilo na
           `$uzivatel !== null && overHeslo(…)`, odpověď u neznámého jména
           přijde za jednotky milisekund místo dvou set — a kdo si projede
           seznam jmen, pozná z časů, která v administraci existují.
           Zkratka `&&` se proto musí rozdělit na dva kroky. */
        $hesloPlati = Uzivatele::overHeslo($uzivatel, (string) ($_POST['heslo'] ?? ''));
        if ($uzivatel !== null && $hesloPlati) {
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
    /* Pozvánka: nový uživatel z administrace zatím heslo nemá a nastaví si ho
       z odkazu administrace.html?pozvanka=<token>. O tom, co se smí stát,
       rozhoduje App\Auth\Pozvanka — tady se jen najde účet podle tokenu,
       zapíše hash a člověk se hned přihlásí, ať nemusí heslo psát dvakrát. */
    if ($akce === 'pozvanka' && $uloziste instanceof UlozisteDb
        && Sezeni::csrfPlati((string) ($_POST['csrf'] ?? ''))) {
        $token = trim((string) ($_POST['token'] ?? ''));
        $ucet = $token !== '' ? $uloziste->podleTokenu($token) : null;
        $vysledek = Pozvanka::prijmi(
            $ucet,
            $token,
            (string) ($_POST['heslo'] ?? ''),
            (string) ($_POST['heslo2'] ?? ''),
        );
        $sTokenem = $kamZpet . '?pozvanka=' . rawurlencode($token);

        // Propadlý i neznámý token skončí stejně — stránka u sebe řekne, že
        // pozvánka neplatí, a nic nenapoví o tom, který token existuje.
        if ($vysledek['stav'] === 'propadla') {
            header('Location: ' . $sTokenem, true, 303);
            return;
        }
        if ($vysledek['stav'] !== 'ok') {
            $duvod = $vysledek['stav'] === 'vadne-heslo'
                ? (string) ($vysledek['duvod'] ?? 'jinak')
                : $vysledek['stav'];
            header('Location: ' . $sTokenem . '&chyba=' . rawurlencode($duvod), true, 303);
            return;
        }

        $uloziste->ulozUzivatele($vysledek['zapis']);
        // Načte se znovu, a to bez hesla: do sezení patří role a aktivní
        // příznak z databáze, ne nic z formuláře.
        $novy = $uloziste->podleId((int) $vysledek['zapis']['id']);
        if ($novy !== null) {
            Sezeni::prihlas($novy);
            $uloziste->zapisPrihlaseni((int) $novy['id']);
            $uloziste->zapisUdalost((string) $novy['jmeno'], 'pozvanka');
        }
        header('Location: ' . $kamZpet, true, 303);
        return;
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
/* Chybová stránka odpovídá kódem 404, i když si o ni někdo řekne přímo
   adresou /404.html. Jako „200 OK" by to byla běžná stránka, kterou si
   vyhledávač zaindexuje. */
if ($kam['druh'] === 'chyba404') {
    http_response_code(404);
}
if ($kam['druh'] === 'administrace') {
    header('Cache-Control: no-store');
    Sezeni::zacni();
}
echo Stranka::vykresli($kam, $zdroj, $ukazka, $vychozi, $uloziste);
