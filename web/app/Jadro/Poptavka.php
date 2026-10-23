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
    /** Okno, ve kterém se odeslané zprávy počítají. */
    private const OKNO = 600;

    /** Z jedné adresy: víc zpráv za okno už není zákazník, ale stroj. */
    private const STROP_ADRESA = 8;

    /**
     * Záchranná síť pro robota rozprostřeného po adresách. Schválně mnohem
     * vyšší než strop na adresu: globální strop je zároveň vypínač formuláře
     * pro všechny zákazníky, a ten se nesmí dát přepnout dvaceti zprávami.
     */
    private const STROP_CELKEM = 60;

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

        // Pozor: `?? 'cs'` v podmínce nekryje přístup v kladné větvi — bez klíče
        // 'jazyk' projde in_array s výchozím 'cs', ale $telo['jazyk'] už neexistuje
        // a dict('') pak shodí celou poptávku.
        $pozadovany = (string) ($telo['jazyk'] ?? 'cs');
        $jazyk = in_array($pozadovany, ['cs', 'en', 'de'], true) ? $pozadovany : 'cs';
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

        /* Strop se počítá až tady, za kontrolou polí: medová past ani
           nevyplněný formulář kvótu neujídají, protože se nikam neukládají —
           jinak by robot vypnul formulář nesmysly. */
        $ip = Adresa::navstevnika($_SERVER);
        if ($uloziste instanceof UlozisteDb
            && ($uloziste->pocetPoptavekZAdresy($ip, self::OKNO) >= self::STROP_ADRESA
                || $uloziste->pocetPoptavekZa(self::OKNO) >= self::STROP_CELKEM)) {
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
            $uloziste->zapisPoptavkuZAdresy($ip);
        }

        // Zákazníkovi se nikdy neříká „nepovedlo se": zpráva je uložená a firma
        // ji uvidí. Hlásí se jen to, že odeslání e-mailu nedoběhlo, a to do logu.
        if (!$odeslano) {
            error_log('Green Air Tech: poptávka uložena, ale e-mail se neodeslal.');
        }
        $odpoved(200, ['ok' => true]);
    }
}
