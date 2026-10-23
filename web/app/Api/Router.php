<?php
/* C-020 — jediná cesta, kterou se změny z prohlížeče dostanou do webu.
   Vstupní bod (web/public/index.php) sem předá požadavek a dostane zpět
   ['stav' => int, 'telo' => array]; hlavičky a tisknutí je jeho věc. */

declare(strict_types=1);

namespace App\Api;

use App\Auth\Uzivatele;
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
        $metoda = (string) ($pozadavek['metoda'] ?? '');
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

            // Obsazený e-mail je konflikt, ne spadlý server: správce má vědět,
            // že takový uživatel už existuje.
            try {
                $ulozeny = $uloziste->ulozUzivatele([
                    'jmeno' => trim((string) $novy['jmeno']),
                    'email' => trim((string) $novy['email']),
                    'role' => (string) $novy['role'],
                ]);
            } catch (Konflikt $e) {
                return self::chyba(409, $e->getMessage());
            }
            return self::ok(['uzivatel' => $ulozeny]);
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
        if (!is_array($soubor)
            || !isset($soubor['tmp_name'], $soubor['name'])
            || !is_string($soubor['tmp_name']) || $soubor['tmp_name'] === ''
            || !is_string($soubor['name']) || $soubor['name'] === '') {
            return self::chyba(400, 'chybi-soubor');
        }

        if ($fotky === null) {
            return self::chyba(503, 'fotky-nejsou');
        }

        try {
            $fotka = $fotky->uloz($soubor['tmp_name'], $soubor['name']);
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
