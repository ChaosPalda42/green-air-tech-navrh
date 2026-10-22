<?php
/* C-022 — poptávka z webu na e-mail firmy. Složí zprávu (předmět, tělo,
   hlavičky) a předá ji přepravci. Hlavičky jsou pevné: do nich se nikdy
   nedostane nic, co napsal cizí člověk do formuláře (žádné podstrčení
   Bcc/CC přes zlom řádku). */

declare(strict_types=1);

namespace App\Posta;

use App\Formular\Validace;

final class Odeslani
{
    /**
     * Složí zprávu z poptávky.
     *
     * @param array<string,mixed> $poptavka
     * @param array<string,mixed> $nastaveni  klíče: 'prijemce', 'odesilatel'
     * @param array<string,mixed> $slovik     klíče: 'typy' (mapa kód => název), 'predmet'
     * @return array{komu:string, predmet:string, telo:string, hlavicky:array<string,string>}
     */
    public static function zprava(array $poptavka, array $nastaveni, array $slovnik): array
    {
        $typ = self::text($poptavka['typ'] ?? '');
        $jmeno = self::text($poptavka['jmeno'] ?? '');
        $email = self::text($poptavka['email'] ?? '');
        $telefon = self::text($poptavka['telefon'] ?? '');
        $zprava = self::text($poptavka['zprava'] ?? '');
        $vetev = self::text($poptavka['vetev'] ?? '');
        $jazyk = self::text($poptavka['jazyk'] ?? '');

        $typy = is_array($slovnik['typy'] ?? null) ? $slovnik['typy'] : [];
        $nazevTypu = is_string($typy[$typ] ?? null) ? $typy[$typ] : $typ;
        $predmetZaklad = is_string($slovnik['predmet'] ?? null) && $slovnik['predmet'] !== ''
            ? $slovnik['predmet'] : 'Poptávka z webu';

        $predmet = self::hlavicka($predmetZaklad . ' — ' . $nazevTypu);

        $radky = [];
        if ($jmeno !== '') {
            $radky[] = 'Jméno: ' . $jmeno;
        }
        if ($email !== '') {
            $radky[] = 'E-mail: ' . $email;
        }
        if ($telefon !== '') {
            $radky[] = 'Telefon: ' . $telefon;
        }
        $radky[] = 'Typ: ' . $nazevTypu;
        if ($vetev !== '') {
            $radky[] = 'Stránka: ' . $vetev;
        }
        if ($jazyk !== '') {
            $radky[] = 'Jazyk: ' . $jazyk;
        }
        $radky[] = '';
        $radky[] = $zprava;

        $telo = implode("\n", $radky);

        $hlavicky = [
            'From' => self::hlavicka((string) ($nastaveni['odesilatel'] ?? '')),
            'MIME-Version' => '1.0',
            'Content-Type' => 'text/plain; charset="UTF-8"',
        ];
        if (Validace::isEmail($email)) {
            $hlavicky['Reply-To'] = self::hlavicka($email);
        }

        return [
            'komu' => self::hlavicka((string) ($nastaveni['prijemce'] ?? '')),
            'predmet' => $predmet,
            'telo' => $telo,
            'hlavicky' => $hlavicky,
        ];
    }

    /**
     * Složí zprávu a předá ji přepravci; vrací to, co vrátila přepravka.
     *
     * @param array<string,mixed> $poptavka
     * @param array<string,mixed> $nastaveni
     * @param array<string,mixed> $slovik
     */
    public static function posli(array $poptavka, array $nastaveni, array $slovnik, Prepravka $prepravka): bool
    {
        $zprava = self::zprava($poptavka, $nastaveni, $slovnik);
        return $prepravka->posli($zprava['komu'], $zprava['predmet'], $zprava['telo'], $zprava['hlavicky']);
    }

    /** Hodnota z formuláře jako čistý text (bez čísel, bez zbytků). */
    private static function text(mixed $hodnota): string
    {
        return is_string($hodnota) ? $hodnota : '';
    }

    /** Hodnota hlavičky: bez zlomů řádků, aby se do hlavičky nic nepodstrčilo. */
    private static function hlavicka(string $hodnota): string
    {
        return str_replace(["\r", "\n"], '', $hodnota);
    }
}
