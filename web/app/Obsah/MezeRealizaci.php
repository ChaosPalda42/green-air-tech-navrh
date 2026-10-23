<?php
/* Meze realizací a fotek ve stavu administrace (C-033).
   Řekne, jestli to, co administrace posílá v klíči `realizace`, smí projít.
   Čisté PHP: žádný stav, žádná síť, žádná databáze, žádný echo, žádné
   superglobály. Pole podá volající a nesmí se mutovat. */

declare(strict_types=1);

namespace App\Obsah;

final class MezeRealizaci
{
    public const MAX_HODNOTA = 20000;  // znaků v jedné textové hodnotě
    public const MAX_FOTEK = 8;        // fotek u jedné realizace

    /** Pole, které dialog administrace u realizace opravdu skládá. */
    private const POLE_POLOZKY = [
        'id', 'vetev', 'nazev', 'misto', 'datum', 'plocha', 'doba',
        'perex', 'zadani', 'vysledek', 'rozsah', 'technologie',
        'kategorie', 'motiv', 'fotky',
    ];

    /** Textová pole (skalární). */
    private const POLE_TEXT = [
        'vetev', 'nazev', 'misto', 'datum', 'plocha', 'doba',
        'perex', 'zadani', 'vysledek',
    ];

    /** Seznamová pole (seznam textů). */
    private const POLE_SEZNAM = ['rozsah', 'technologie', 'kategorie'];

    /** Pole fotky — záznam o souboru v `media/`, ne data URL. */
    private const POLE_FOTKY = ['id', 'nazev', 'typ', 'sirka', 'vyska', 'bajty', 'dataUrl'];

    /** Jméno souboru ve složce media. Tečka smí, dvě za sebou se hlídají zvlášť. */
    private const RE_JMENO = '/^[A-Za-z0-9._-]{1,120}$/';

    /** Id do adresy: malá písmena, číslice a pomlčky, bez pomlček na krajích. */
    private const RE_ID = '/^[a-z0-9]+(?:-[a-z0-9]+)*$/';

    /**
     * Dostane obsah klíče 'realizace' ze stavu administrace:
     * ['added' => list<array>, 'edited' => map<id, array>, 'removed' => list<id>].
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}
     */
    public static function zkontroluj(array $realizace): array
    {
        foreach (array_keys($realizace) as $klic) {
            if (!in_array($klic, ['added', 'edited', 'removed'], true)) {
                return self::chyba('nezname-pole', (string) $klic);
            }
        }
        foreach (['added', 'edited', 'removed'] as $klic) {
            if (array_key_exists($klic, $realizace) && !is_array($realizace[$klic])) {
                return self::chyba('nezname-pole', $klic);
            }
        }

        $added = $realizace['added'] ?? [];
        if (!self::jeSeznam($added)) {
            return self::chyba('nezname-pole', 'added');
        }
        foreach ($added as $index => $polozka) {
            if (!is_array($polozka)) {
                return self::chyba('nezname-pole', "added[$index]");
            }
            $chyba = self::zkontrolujPolozku($polozka);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        $edited = $realizace['edited'] ?? [];
        foreach ($edited as $id => $zmena) {
            if (!self::jePlatneId((string) $id)) {
                return self::chyba('vadne-id', (string) $id);
            }
            if (!is_array($zmena)) {
                return self::chyba('nezname-pole', "edited[$id]");
            }
            $chyba = self::zkontrolujPolozku($zmena, true);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        $removed = $realizace['removed'] ?? [];
        if (!self::jeSeznam($removed)) {
            return self::chyba('nezname-pole', 'removed');
        }
        foreach ($removed as $id) {
            if (!is_string($id) || !self::jePlatneId($id)) {
                return self::chyba('vadne-id', is_string($id) ? $id : gettype($id));
            }
        }

        return ['ok' => true, 'chyba' => null, 'detail' => null];
    }

    /* ------------------------------------------------------------ pomocné */

    /**
     * Jedna položka (v added i edited). Změna (edited) nemusí mít id ani
     * nemusí být úplná — kontrolují se jen ta pole, která jsou přítomná.
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}|null null = v pořádku
     */
    private static function zkontrolujPolozku(array $polozka, bool $zmena = false): ?array
    {
        foreach (array_keys($polozka) as $klic) {
            if (!in_array($klic, self::POLE_POLOZKY, true)) {
                return self::chyba('nezname-pole', (string) $klic);
            }
        }

        if (array_key_exists('id', $polozka)) {
            $id = $polozka['id'];
            if (!is_string($id) || !self::jePlatneId($id)) {
                return self::chyba('vadne-id', is_string($id) ? $id : gettype($id));
            }
        } elseif (!$zmena) {
            return self::chyba('vadne-id', 'id');
        }

        foreach (self::POLE_TEXT as $klic) {
            if (!array_key_exists($klic, $polozka)) {
                continue;
            }
            $hodnota = $polozka[$klic];
            if (!is_string($hodnota)) {
                return self::chyba('vadna-hodnota', $klic);
            }
            if (self::dlzka($hodnota) > self::MAX_HODNOTA) {
                return self::chyba('dlouhy-text', $klic);
            }
        }

        foreach (self::POLE_SEZNAM as $klic) {
            if (!array_key_exists($klic, $polozka)) {
                continue;
            }
            $seznam = $polozka[$klic];
            if (!is_array($seznam) || !self::jeSeznam($seznam)) {
                return self::chyba('vadna-hodnota', $klic);
            }
            if (count($seznam) > 100) {
                return self::chyba('vadna-hodnota', $klic);
            }
            foreach ($seznam as $polozkaSeznamu) {
                if (!is_string($polozkaSeznamu)) {
                    return self::chyba('vadna-hodnota', $klic);
                }
                if (self::dlzka($polozkaSeznamu) > self::MAX_HODNOTA) {
                    return self::chyba('dlouhy-text', $klic);
                }
            }
        }

        if (array_key_exists('motiv', $polozka)) {
            $motiv = $polozka['motiv'];
            if (is_string($motiv)) {
                if (preg_match('/^[0-9]{1,2}$/', $motiv) !== 1) {
                    return self::chyba('vadna-hodnota', 'motiv');
                }
            } elseif (!is_int($motiv) || $motiv < 0 || $motiv > 99) {
                return self::chyba('vadna-hodnota', 'motiv');
            }
        }

        if (array_key_exists('fotky', $polozka)) {
            $chyba = self::zkontrolujFotky($polozka['fotky']);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        return null;
    }

    /**
     * Galerie fotek. Fotka je jen záznam o souboru v `media/` — data URL
     * sem nepatří (na ostrém webu se obrázek nahrává zvlášť přes /api/fotka).
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}|null null = v pořádku
     */
    private static function zkontrolujFotky(mixed $fotky): ?array
    {
        if (!is_array($fotky) || !self::jeSeznam($fotky)) {
            return self::chyba('vadna-fotka', 'fotky');
        }
        if (count($fotky) > self::MAX_FOTEK) {
            return self::chyba('moc-fotek', 'fotky');
        }
        foreach ($fotky as $index => $fotka) {
            if (!is_array($fotka)) {
                return self::chyba('vadna-fotka', "fotky[$index]");
            }
            foreach (array_keys($fotka) as $klic) {
                if (!in_array($klic, self::POLE_FOTKY, true)) {
                    return self::chyba('vadna-fotka', (string) $klic);
                }
            }

            /* id musí být, a krátké: chodí do jména souboru i do adresy. */
            $id = $fotka['id'] ?? null;
            if (!is_string($id) || $id === '' || self::dlzka($id) > 64) {
                return self::chyba('vadna-fotka', 'id');
            }

            /* nazev a typ jsou jen popisky; když přijdou, drží se do 200. */
            foreach (['nazev' => 200, 'typ' => 200] as $klic => $strop) {
                if (!array_key_exists($klic, $fotka)) {
                    continue;
                }
                $hodnota = $fotka[$klic];
                if (!is_string($hodnota) || self::dlzka($hodnota) > $strop) {
                    return self::chyba('vadna-fotka', $klic);
                }
            }

            /* rozměry smí přijít i jako text z JSONu ('1600'), ale nezáporné. */
            foreach (['sirka', 'vyska', 'bajty'] as $klic) {
                if (!array_key_exists($klic, $fotka)) {
                    continue;
                }
                $hodnota = $fotka[$klic];
                if (is_int($hodnota)) {
                    if ($hodnota < 0) {
                        return self::chyba('vadna-fotka', $klic);
                    }
                    continue;
                }
                if (!is_string($hodnota) || preg_match('/^[0-9]{1,15}$/', $hodnota) !== 1) {
                    return self::chyba('vadna-fotka', $klic);
                }
            }

            /* Tohle je ten nález: do stavu patří CESTA, ne obrázek. */
            $dataUrl = $fotka['dataUrl'] ?? null;
            if (!is_string($dataUrl) || !str_starts_with($dataUrl, 'media/')) {
                return self::chyba('vadna-fotka', 'dataUrl');
            }
            $jmeno = substr($dataUrl, strlen('media/'));
            if (str_contains($jmeno, '..') || preg_match(self::RE_JMENO, $jmeno) !== 1) {
                return self::chyba('vadna-fotka', 'dataUrl');
            }
        }

        return null;
    }

    /** Je to list (počítané od nuly, bez děr)? */
    private static function jeSeznam(array $co): bool
    {
        return array_is_list($co);
    }

    /** Id do adresy: malá písmena, číslice a pomlčky, bez pomlček na krajích. */
    private static function jePlatneId(string $id): bool
    {
        return preg_match(self::RE_ID, $id) === 1;
    }

    /** Počet znaků, ne bajtů — texty chodí v UTF-8. */
    private static function dlzka(string $text): int
    {
        return mb_strlen($text, 'UTF-8');
    }

    private static function chyba(string $kod, string $detail): array
    {
        return ['ok' => false, 'chyba' => $kod, 'detail' => $detail];
    }
}
