<?php
/* C-020 — jediná cesta, kterou se změny z prohlížeče dostanou do webu.
   Vstupní bod (web/public/index.php) sem předá požadavek a dostane zpět
   ['stav' => int, 'telo' => array]; hlavičky a tisknutí je jeho věc.

   Cíle: stav, uzivatele, heslo, pozvanka, statistiky, fotka.
   Pořadí kontrol je u každého cíle stejné: CSRF, přihlášení, práva,
   metoda, data. Odmítnutý požadavek na úložiště nesáhne. */

declare(strict_types=1);

namespace App\Api;

use App\Auth\Uzivatele;
use App\Fotky\MocVelka;
use App\Fotky\Ulozny;
use App\Obsah\Ocista;
use App\Obsah\Stav;
use App\Statistiky\Poskytovatel;

final class Router
{
    /** Rozsah statistiky v dnech; víc než rok nemá smysl. */
    private const MAX_DNI = 365;

    public static function obsluz(
        array $pozadavek,
        Uloziste $uloziste,
        ?Poskytovatel $statistiky = null,
        ?Ulozny $fotky = null
    ): array {
        $cesta = (string) ($pozadavek['cesta'] ?? '');
        $uzivatel = $pozadavek['uzivatel'] ?? null;
        if (!is_array($uzivatel)) {
            $uzivatel = null;
        }

        switch ($cesta) {
            case 'stav':
                return self::stav($pozadavek, $uloziste, $uzivatel);
            case 'uzivatele':
                return self::uzivatele($pozadavek, $uloziste, $uzivatel);
            case 'heslo':
                return self::heslo($pozadavek, $uloziste, $uzivatel);
            case 'pozvanka':
                return self::pozvanka($pozadavek, $uloziste, $uzivatel);
            case 'statistiky':
                return self::statistiky($pozadavek, $statistiky, $uzivatel);
            case 'fotka':
                return self::fotka($pozadavek, $fotky, $uzivatel);
            default:
                return self::chyba(404, 'neznamy-cil');
        }
    }

    /* ------------------------------------------------------------- stav */

    private static function stav(array $pozadavek, Uloziste $uloziste, ?array $uzivatel): array
    {
        $metoda = (string) $pozadavek['metoda'];

        if ($metoda === 'GET') {
            if ($uzivatel === null) {
                return self::chyba(401, 'neprihlaseno');
            }
            return self::ok(['stav' => $uloziste->stav()]);
        }

        if ($metoda !== 'PUT') {
            return self::chyba(405, 'spatna-metoda');
        }

        if (!($pozadavek['csrf_ok'] ?? false)) {
            return self::chyba(403, 'csrf');
        }
        if ($uzivatel === null) {
            return self::chyba(401, 'neprihlaseno');
        }

        $stary = $uloziste->stav();
        $vysledek = Stav::zJson($stary, (string) $pozadavek['telo']);
        if (($vysledek['ok'] ?? false) !== true || !isset($vysledek['state']) || !is_array($vysledek['state'])) {
            return self::chyba(400, 'nesmyslny-stav');
        }
        // Texty z administrace se na webu vypisují jako HTML (kvůli <br>),
        // tak se tady očistí — jinak by si kdokoli s právem psát texty vložil
        // do webu vlastní skript.
        $novy = Ocista::stav($vysledek['state']);

        if (!Zmeny::smiZmenit((string) ($uzivatel['role'] ?? ''), $stary, $novy)) {
            return self::chyba(403, 'nesmis');
        }

        $uloziste->ulozStav($novy, (string) ($uzivatel['jmeno'] ?? ''));
        return self::ok(['stav' => $novy]);
    }

    /* -------------------------------------------------------- uzivatele */

    private static function uzivatele(array $pozadavek, Uloziste $uloziste, ?array $uzivatel): array
    {
        $metoda = (string) $pozadavek['metoda'];

        if ($metoda === 'GET') {
            if ($uzivatel === null) {
                return self::chyba(401, 'neprihlaseno');
            }
            if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'uzivatele')) {
                return self::chyba(403, 'nesmis');
            }
            return self::ok(['uzivatele' => $uloziste->uzivatele()]);
        }

        if ($metoda === 'POST') {
            if (!($pozadavek['csrf_ok'] ?? false)) {
                return self::chyba(403, 'csrf');
            }
            if ($uzivatel === null) {
                return self::chyba(401, 'neprihlaseno');
            }
            if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'uzivatele')) {
                return self::chyba(403, 'nesmis');
            }

            $novy = json_decode((string) $pozadavek['telo'], true);
            if (!is_array($novy)) {
                $novy = [];
            }
            $vady = Uzivatele::zkontroluj($novy);
            if ($vady !== []) {
                return self::chyba(400, 'vadna-data', ['pole' => $vady]);
            }

            // Nový uživatel se do administrace dostane přes pozvánku: token
            // a platnost se vyrobí tady, uloží se s účtem a vrátí zakládajícímu
            // — ten ho předá kolegovi. Heslo se přes API neposílá ani nevrací
            // nikdy; nastaví si ho nový uživatel sám při prvním přihlášení.
            $pozvanka = Uzivatele::pozvanka();

            // Obsazený e-mail je konflikt, ne spadlý server: správce má vědět,
            // že takový uživatel už existuje.
            try {
                $ulozeny = $uloziste->ulozUzivatele([
                    'jmeno' => trim((string) $novy['jmeno']),
                    'email' => trim((string) $novy['email']),
                    'role' => (string) $novy['role'],
                    'aktivni' => 1,
                    'pozvanka_token' => $pozvanka['token'],
                    'pozvanka_do' => $pozvanka['do'],
                ]);
            } catch (Konflikt $e) {
                return self::chyba(409, $e->getMessage());
            }
            return self::ok(['uzivatel' => $ulozeny, 'pozvanka' => $pozvanka]);
        }

        if ($metoda === 'DELETE') {
            if (!($pozadavek['csrf_ok'] ?? false)) {
                return self::chyba(403, 'csrf');
            }
            if ($uzivatel === null) {
                return self::chyba(401, 'neprihlaseno');
            }
            if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'uzivatele')) {
                return self::chyba(403, 'nesmis');
            }

            $id = (string) ($pozadavek['dotaz']['id'] ?? '');
            if ($id === '' || !ctype_digit($id)) {
                return self::chyba(400, 'chybi-id');
            }
            $id = (int) $id;

            // Sám sebe nikdo nesmaže. Id ze sezení je jistota; hledání podle
            // jména je záloha, když ho sezení nenese — dva lidé se můžou
            // jmenovat stejně, a to by zámek obešlo.
            $sveId = (int) ($uzivatel['id'] ?? 0);
            if ($sveId === 0) {
                $jmeno = (string) ($uzivatel['jmeno'] ?? '');
                $soucasny = $jmeno !== '' ? $uloziste->uzivatelPodleJmena($jmeno) : null;
                $sveId = (int) ($soucasny['id'] ?? 0);
            }
            if ($sveId !== 0 && $sveId === $id) {
                return self::chyba(409, 'nelze-sam-sebe');
            }

            $uloziste->smazUzivatele($id);
            return self::ok(['smazano' => $id]);
        }

        return self::chyba(405, 'spatna-metoda');
    }

    /* ------------------------------------------------------------- heslo */

    /**
     * Změna VLASTNÍHO hesla. Na tohle právo „uzivatele“ nežádá — to má jen
     * správce a heslo si musí umět změnit každý. Cizí účet se tudy měnit
     * nedá: zápis jde vždy na účet přihlášeného, tělo jen ověří staré a
     * dá nové heslo.
     */
    private static function heslo(array $pozadavek, Uloziste $uloziste, ?array $uzivatel): array
    {
        if (!($pozadavek['csrf_ok'] ?? false)) {
            return self::chyba(403, 'csrf');
        }
        if ($uzivatel === null) {
            return self::chyba(401, 'neprihlaseno');
        }
        if ((string) $pozadavek['metoda'] !== 'POST') {
            return self::chyba(405, 'spatna-metoda');
        }

        $telo = json_decode((string) $pozadavek['telo'], true);
        if (!is_array($telo)) {
            $telo = [];
        }
        $stare = $telo['stare'] ?? null;
        $nove = $telo['nove'] ?? null;
        if (!is_string($stare) || !is_string($nove)) {
            return self::chyba(400, 'vadne-heslo', ['duvod' => 'prazdne']);
        }

        // Nové heslo musí projít kontrolou síly dřív, než se ptáme na staré —
        // slabé heslo se neověřuje a neukládá.
        $duvod = Uzivatele::zkontrolujHeslo($nove);
        if ($duvod !== null) {
            return self::chyba(400, 'vadne-heslo', ['duvod' => $duvod]);
        }

        // Vždy se mění účet přihlášeného: hledání podle jména vrátí řádek
        // s hashem hesla (seznam uživatelů hash nese). Klíče id/jmeno/email
        // v těle se ignorují.
        $ucet = $uloziste->uzivatelPodleJmena((string) ($uzivatel['jmeno'] ?? ''));
        if ($ucet === null) {
            return self::chyba(401, 'neprihlaseno');
        }

        if (!Uzivatele::overHeslo($ucet, $stare)) {
            return self::chyba(403, 'spatne-stare-heslo');
        }

        // Kdo zná heslo, nemá potřebovat pozvánku — stará se ruší, aby do
        // účtu nevedly dvě cesty najednou.
        $uloziste->ulozUzivatele([
            'id' => (int) ($ucet['id'] ?? 0),
            'heslo_hash' => Uzivatele::hash($nove),
            'pozvanka_token' => null,
            'pozvanka_do' => null,
        ]);
        return self::ok(['ok' => true]);
    }

    /* ---------------------------------------------------------- pozvanka */

    /**
     * Pozvánka znovu: ztratila se, propadla, kolega heslo zapomněl. Staré
     * heslo se ruší — jinak by platily dvě cesty do účtu. Sám sobě ji nikdo
     * nevystaví: zrušil by si heslo a do administrace by ho musel pustit
     * někdo jiný.
     */
    private static function pozvanka(array $pozadavek, Uloziste $uloziste, ?array $uzivatel): array
    {
        if (!($pozadavek['csrf_ok'] ?? false)) {
            return self::chyba(403, 'csrf');
        }
        if ($uzivatel === null) {
            return self::chyba(401, 'neprihlaseno');
        }
        if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'uzivatele')) {
            return self::chyba(403, 'nesmis');
        }
        if ((string) $pozadavek['metoda'] !== 'POST') {
            return self::chyba(405, 'spatna-metoda');
        }

        $telo = json_decode((string) $pozadavek['telo'], true);
        if (!is_array($telo)) {
            $telo = [];
        }
        $id = $telo['id'] ?? null;
        if (!is_int($id) || $id < 1) {
            return self::chyba(400, 'chybi-id');
        }

        $ucet = self::hledaPodleId($uloziste, $id);
        if ($ucet === null) {
            return self::chyba(404, 'neznamy-uzivatel');
        }

        $sveId = (int) ($uzivatel['id'] ?? 0);
        if ($sveId === 0) {
            $sveId = (int) ($uloziste->uzivatelPodleJmena((string) ($uzivatel['jmeno'] ?? ''))['id'] ?? 0);
        }
        if ($sveId !== 0 && $sveId === $id) {
            return self::chyba(409, 'nelze-sam-sebe');
        }

        $pozvanka = Uzivatele::pozvanka();
        $uloziste->ulozUzivatele([
            'id' => $id,
            'pozvanka_token' => $pozvanka['token'],
            'pozvanka_do' => $pozvanka['do'],
            'heslo_hash' => null,
        ]);
        return self::ok(['pozvanka' => $pozvanka]);
    }

    /**
     * Účet podle id: v seznamu uživatelů, jinak podle jména (sezení zná
     * jméno, ne vždy id). Vrátí pole s heslem jen tehdy, když ho má.
     */
    private static function hledaPodleId(Uloziste $uloziste, int $id): ?array
    {
        foreach ($uloziste->uzivatele() as $radek) {
            if ((int) ($radek['id'] ?? 0) === $id) {
                return $radek;
            }
        }
        return null;
    }

    /* ------------------------------------------------------- statistiky */

    private static function statistiky(array $pozadavek, ?Poskytovatel $statistiky, ?array $uzivatel): array
    {
        if ((string) $pozadavek['metoda'] !== 'GET') {
            return self::chyba(405, 'spatna-metoda');
        }
        if ($uzivatel === null) {
            return self::chyba(401, 'neprihlaseno');
        }
        if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'statistiky')) {
            return self::chyba(403, 'nesmis');
        }

        $dni = (string) ($pozadavek['dotaz']['dni'] ?? '');
        if ($dni === '') {
            $dni = 30;
        } else {
            if (!ctype_digit($dni) || (int) $dni < 1 || (int) $dni > self::MAX_DNI) {
                return self::chyba(400, 'spatne-dni');
            }
            $dni = (int) $dni;
        }

        if ($statistiky === null) {
            return self::chyba(503, 'statistiky-nejsou');
        }

        return self::ok($statistiky->prehled($dni));
    }

    /* ------------------------------------------------------------- fotka */

    private static function fotka(array $pozadavek, ?Ulozny $fotky, ?array $uzivatel): array
    {
        if ((string) $pozadavek['metoda'] !== 'POST') {
            return self::chyba(405, 'spatna-metoda');
        }
        if (!($pozadavek['csrf_ok'] ?? false)) {
            return self::chyba(403, 'csrf');
        }
        if ($uzivatel === null) {
            return self::chyba(401, 'neprihlaseno');
        }
        if (!Uzivatele::smi((string) ($uzivatel['role'] ?? ''), 'realizace')) {
            return self::chyba(403, 'nesmis');
        }

        $soubor = $pozadavek['soubor'] ?? null;
        $maSoubor = is_array($soubor)
            && isset($soubor['tmp_name'], $soubor['name'])
            && is_string($soubor['tmp_name']) && $soubor['tmp_name'] !== ''
            && is_string($soubor['name']) && $soubor['name'] !== '';

        if (!$maSoubor) {
            /* Soubor nad upload_max_filesize PHP zahodí a nechá jen číslo
               chyby — proto se ptáme na ně DŘÍV než na chybějící soubor.
               Odpověď „chybi-soubor" by správce posílala vybrat soubor, který
               právě vybral. */
            $duvod = $pozadavek['soubor_chyba'] ?? null;
            if (($pozadavek['telo_velke'] ?? false)
                || $duvod === UPLOAD_ERR_INI_SIZE
                || $duvod === UPLOAD_ERR_FORM_SIZE) {
                return self::chyba(413, 'soubor-moc-velky');
            }
            if ($duvod === UPLOAD_ERR_PARTIAL) {
                return self::chyba(400, 'nahrani-preruseno');
            }
            if ($duvod === UPLOAD_ERR_NO_TMP_DIR || $duvod === UPLOAD_ERR_CANT_WRITE) {
                // Vada serveru, ne souboru: na fotce není co opravovat.
                return self::chyba(503, 'fotky-nejsou');
            }
            return self::chyba(400, 'chybi-soubor');
        }

        if ($fotky === null) {
            return self::chyba(503, 'fotky-nejsou');
        }

        try {
            $fotka = $fotky->uloz($soubor['tmp_name'], $soubor['name']);
        } catch (MocVelka) {
            // Obrázek to je, jen se nerozbalí do paměti. Chytá se dřív než
            // RuntimeException — je to jeho potomek.
            return self::chyba(413, 'fotka-moc-velka');
        } catch (\RuntimeException) {
            return self::chyba(400, 'fotka-nesla');
        }

        return self::ok(['fotka' => $fotka]);
    }

    /* ------------------------------------------------------------- pomoc */

    private static function ok(array $telo): array
    {
        return ['stav' => 200, 'telo' => $telo];
    }

    private static function chyba(int $stav, string $chyba, array $priloha = []): array
    {
        return ['stav' => $stav, 'telo' => array_merge(['chyba' => $chyba], $priloha)];
    }
}
