<?php
/* Poptávka z formuláře: jediná věc, kterou na webu dělá cizí člověk. Proto
   tady: medová past, kontrola polí týmž pravidlem jako v prohlížeči, strop na
   počet zpráv, odeslání e-mailem a záloha do databáze. */

declare(strict_types=1);

namespace App\Jadro;

use App\Api\Uloziste;
use App\Db\UlozisteDb;
use App\Formular\Validace;
use App\Obsah\I18n;
use App\Obsah\Zdroj;
use App\Posta\Odeslani;
use App\Posta\PrepravkaLog;
use App\Posta\PrepravkaMail;

final class Poptavka
{
    /** Víc zpráv za deset minut už není zákazník, ale stroj. */
    private const STROP = 20;

    public static function obsluz(string $metoda, Zdroj $zdroj, ?Uloziste $uloziste, callable $odpoved): void
    {
        if ($metoda !== 'POST') {
            $odpoved(405, ['chyba' => 'spatna-metoda']);
            return;
        }

        $telo = json_decode((string) file_get_contents('php://input'), true);
        if (!is_array($telo)) {
            $telo = $_POST;
        }

        // medová past: robot vyplní skryté pole a odejde s poděkováním
        if (trim((string) ($telo['vebsajt'] ?? '')) !== '') {
            $odpoved(200, ['ok' => true]);
            return;
        }

        $jazyk = in_array((string) ($telo['jazyk'] ?? 'cs'), ['cs', 'en', 'de'], true)
            ? (string) $telo['jazyk'] : 'cs';
        $dict = $zdroj->dict($jazyk);
        $zpravy = I18n::get($dict, 'kontakt.formular.chyby');

        $hodnoty = [
            'jmeno' => trim((string) ($telo['jmeno'] ?? '')),
            'email' => trim((string) ($telo['email'] ?? '')),
            'telefon' => trim((string) ($telo['telefon'] ?? '')),
            'typ' => trim((string) ($telo['typ'] ?? '')),
            'zprava' => trim((string) ($telo['zprava'] ?? '')),
            'souhlas' => (bool) ($telo['souhlas'] ?? false),
        ];

        $vysledek = Validace::validateContact($hodnoty, is_array($zpravy) ? $zpravy : []);
        if (($vysledek['ok'] ?? false) !== true) {
            $odpoved(422, ['ok' => false, 'chyby' => $vysledek['errors'] ?? [], 'hlasky' => $vysledek['messages'] ?? []]);
            return;
        }

        if ($uloziste instanceof UlozisteDb && $uloziste->pocetPoptavekZa(600) >= self::STROP) {
            $odpoved(429, ['ok' => false, 'chyba' => 'prilis-mnoho']);
            return;
        }

        $poptavka = $hodnoty + [
            'vetev' => trim((string) ($telo['vetev'] ?? '')),
            'jazyk' => $jazyk,
        ];

        $nastaveni = Config::dej('posta', []);
        $slovnik = [
            'typy' => (array) (I18n::get($dict, 'kontakt.formular.typy') ?? []),
            'predmet' => (string) (I18n::get($dict, 'kontakt.formular.predmet')
                ?? I18n::get($dict, 'kontakt.titulek') ?? 'Poptávka z webu'),
        ];

        $prepravka = ((string) ($nastaveni['zpusob'] ?? 'mail')) === 'log'
            ? new PrepravkaLog(dirname(__DIR__, 2) . '/data/posta.log')
            : new PrepravkaMail();

        $odeslano = false;
        try {
            $odeslano = Odeslani::posli($poptavka, $nastaveni, $slovnik, $prepravka);
        } catch (\Throwable) {
            $odeslano = false;
        }

        if ($uloziste instanceof UlozisteDb) {
            $uloziste->ulozPoptavku($poptavka, $odeslano);
        }

        // Zákazníkovi se nikdy neříká „nepovedlo se": zpráva je uložená a firma
        // ji uvidí. Hlásí se jen to, že odeslání e-mailu nedoběhlo, a to do logu.
        if (!$odeslano) {
            error_log('Green Air Tech: poptávka uložena, ale e-mail se neodeslal.');
        }
        $odpoved(200, ['ok' => true]);
    }
}
