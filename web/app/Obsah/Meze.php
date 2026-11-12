<?php
/* Meze stavu administrace (C-032): velikost, nejvyšší úroveň a texty.
   Řekne, jestli se stav z administrace smí uložit. Čisté PHP: žádný stav,
   žádná síť, žádná databáze, žádný echo, žádné superglobály. Pole podá
   volající a nesmí se mutovat.

   Realizace a fotky se nekontrolují tady — na to je App\Obsah\MezeRealizaci
   (C-033); Meze se jí zeptá a její kódy předá bez změny. */

declare(strict_types=1);

namespace App\Obsah;

final class Meze
{
    public const MAX_HODNOTA = 20000;   // znaků v jedné hodnotě
    public const MAX_CELKEM = 1048576;  // bajtů celého stavu v JSONu

    /** Jazyky, které administrace posílá. */
    private const JAZYKY = ['cs', 'en', 'de'];

    /** Pole na nejvyšší úrovni stavu. */
    private const POLE_STAVU = ['texts', 'realizace', 'portrety', 'updatedAt'];

    /** Nejvíc výřezů portrétů; tým má jednotky lidí, ne stovky. */
    public const MAX_PORTRETU = 50;

    /** Id realizace v klíči: malá písmena, číslice a pomlčky, bez krajních pomlček. */
    private const RE_ID_REALIZACE = '/^[a-z0-9]+(?:-[a-z0-9]+)*$/';

    /** Pole nové realizace, která se smí objevit v dynamických klíčích textů. */
    private const POLE_REALIZACE = [
        'nazev', 'misto', 'perex', 'zadani', 'vysledek',
        'rozsah', 'technologie', 'kategorie',
    ];

    /** Pole jednoho výřezu portrétu; nic jiného se v něm neuznává. */
    private const POLE_VYREZU = ['zoom', 'x', 'y'];

    /** Podklíč seznamu: písmeno a číslovaní (r1, t12, b3). */
    private const RE_PODKLIC_SEZNAMU = '/^[a-z][0-9]+$/';

    /**
     * Zkontroluje očištěný stav administrace.
     *
     * @param array $stav  už očištěný stav (App\Obsah\Ocista::stav)
     * @param array $klice seznam povolených klíčů textů (admin-klice.json);
     *                     prázdný seznam znamená „seznam nemám“ a klíče se nehlídají
     * @return array{ok: bool, chyba: ?string, detail: ?string}
     */
    public static function stav(array $stav, array $klice): array
    {
        /* Nejprve velikost celého stavu v JSONu — i stav, který se jinak
           nesejde, musí skončit srozumitelnou chybou, ne výjimkou. */
        $json = json_encode($stav, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        if ($json === false) {
            return self::chyba('vadna-hodnota', 'stav');
        }
        if (strlen($json) > self::MAX_CELKEM) {
            return self::chyba('moc-dat', 'stav');
        }

        /* Nejvyšší úroveň: jen ta pole, která administrace posílá. */
        foreach (array_keys($stav) as $klic) {
            if (!in_array($klic, self::POLE_STAVU, true)) {
                return self::chyba('nezname-pole', (string) $klic);
            }
        }

        /* Texty: jazyky, klíče a délka hodnot. */
        if (array_key_exists('texts', $stav)) {
            $chyba = self::zkontrolujTexty($stav['texts'], $klice);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        /* Realizace: pravidla má C-033, kódy se předávají bez změny. */
        if (array_key_exists('realizace', $stav)) {
            if (!is_array($stav['realizace'])) {
                return self::chyba('vadna-hodnota', 'realizace');
            }
            $vysledek = MezeRealizaci::zkontroluj($stav['realizace']);
            if (!$vysledek['ok']) {
                return $vysledek;
            }
        }

        /* Portréty: výřez fotky v kolečku týmu. */
        if (array_key_exists('portrety', $stav)) {
            $chyba = self::zkontrolujPortrety($stav['portrety']);
            if ($chyba !== null) {
                return $chyba;
            }
        }

        /* updatedAt: text do 64 znaků, nebo null. */
        if (array_key_exists('updatedAt', $stav)) {
            $cas = $stav['updatedAt'];
            if ($cas !== null && (!is_string($cas) || self::dlzka($cas) > 64)) {
                return self::chyba('vadna-hodnota', 'updatedAt');
            }
        }

        return ['ok' => true, 'chyba' => null, 'detail' => null];
    }

    /* ------------------------------------------------------------ pomocné */

    /**
     * Texty podle jazyka.
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}|null null = v pořádku
     */
    private static function zkontrolujTexty(mixed $texty, array $klice): ?array
    {
        if (!is_array($texty)) {
            return self::chyba('vadna-hodnota', 'texts');
        }
        foreach ($texty as $jazyk => $dvojice) {
            if (!in_array((string) $jazyk, self::JAZYKY, true)) {
                return self::chyba('neznamy-jazyk', (string) $jazyk);
            }
            if (!is_array($dvojice)) {
                return self::chyba('vadna-hodnota', (string) $jazyk);
            }
            foreach ($dvojice as $klic => $hodnota) {
                if (!is_string($hodnota)) {
                    return self::chyba('vadna-hodnota', (string) $klic);
                }
                if (self::dlzka($hodnota) > self::MAX_HODNOTA) {
                    return self::chyba('dlouhy-text', (string) $klic);
                }
                if ($klice !== [] && !self::jePovolenyKlic((string) $klic, $klice)) {
                    return self::chyba('neznamy-klic', (string) $klic);
                }
            }
        }

        return null;
    }

    /**
     * Výřezy portrétů: mapa id člověka => ['zoom' => …, 'x' => …, 'y' => …].
     * Hodnoty se tady NEZKRACUJÍ — prohlížeč posílá už zarovnaný výřez
     * (src/lib/cms-store.mjs) a co se do mezí nevejde, je vada vstupu.
     *
     * @return array{ok: bool, chyba: ?string, detail: ?string}|null null = v pořádku
     */
    private static function zkontrolujPortrety(mixed $portrety): ?array
    {
        if (!is_array($portrety)) {
            return self::chyba('vadna-hodnota', 'portrety');
        }
        if (count($portrety) > self::MAX_PORTRETU) {
            return self::chyba('moc-dat', 'portrety');
        }
        foreach ($portrety as $id => $vyrez) {
            if (!is_string($id) || preg_match(self::RE_ID_REALIZACE, $id) !== 1) {
                return self::chyba('neznamy-klic', (string) $id);
            }
            if (!is_array($vyrez)) {
                return self::chyba('vadna-hodnota', (string) $id);
            }
            foreach (array_keys($vyrez) as $pole) {
                if (!in_array($pole, self::POLE_VYREZU, true)) {
                    return self::chyba('nezname-pole', $id . '.' . (string) $pole);
                }
            }
            $zoom = $vyrez['zoom'] ?? null;
            if (!is_int($zoom) && !is_float($zoom)) {
                return self::chyba('vadna-hodnota', $id . '.zoom');
            }
            if ($zoom < 100 || $zoom > StavVyrezu::MAX_ZOOM) {
                return self::chyba('vadna-hodnota', $id . '.zoom');
            }
            $mez = ((float) $zoom - 100) / 2;
            foreach (['x', 'y'] as $osa) {
                $posun = $vyrez[$osa] ?? null;
                if (!is_int($posun) && !is_float($posun)) {
                    return self::chyba('vadna-hodnota', $id . '.' . $osa);
                }
                if (abs((float) $posun) > $mez) {
                    return self::chyba('vadna-hodnota', $id . '.' . $osa);
                }
            }
        }

        return null;
    }

    /**
     * Klíč je povolený, když je v seznamu, nebo když je dynamický klíč nové
     * realizace: `realizace.polozky.<id>.<pole>[.<podklíč>]`.
     */
    private static function jePovolenyKlic(string $klic, array $seznam): bool
    {
        if (in_array($klic, $seznam, true)) {
            return true;
        }

        $casti = explode('.', $klic);
        if (count($casti) < 4 || $casti[0] !== 'realizace' || $casti[1] !== 'polozky') {
            return false;
        }
        if (preg_match(self::RE_ID_REALIZACE, $casti[2]) !== 1) {
            return false;
        }
        if (!in_array($casti[3], self::POLE_REALIZACE, true)) {
            return false;
        }
        if (count($casti) === 4) {
            return true;
        }
        if (count($casti) === 5) {
            return in_array($casti[3], ['rozsah', 'technologie', 'kategorie'], true)
                && preg_match(self::RE_PODKLIC_SEZNAMU, $casti[4]) === 1;
        }

        return false;
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
