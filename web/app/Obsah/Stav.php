<?php
/* Stav administrace — texty přepsané ve webu a import zálohy. Zdroj pravdy je
   src/lib/cms-store.mjs z ukázky; tady je to samé v PHP, aby se server chovat
   přesně jako prohlížeč.

   Realizace (přidané, změněné, smazané) má na starost App\Obsah\StavRealizace,
   výřezy portrétů App\Obsah\StavVyrezu. */

declare(strict_types=1);

namespace App\Obsah;

final class Stav
{
    /** Diakritika na ASCII bez mbstring i intl. Velká i malá, výsledek je malý. */
    private const BEZ_DIAKRITIKY = [
        'á' => 'a', 'à' => 'a', 'â' => 'a', 'ä' => 'a', 'ã' => 'a', 'å' => 'a', 'ā' => 'a',
        'Á' => 'a', 'À' => 'a', 'Â' => 'a', 'Ä' => 'a', 'Ã' => 'a', 'Å' => 'a', 'Ā' => 'a',
        'č' => 'c', 'ć' => 'c', 'ç' => 'c', 'Č' => 'c', 'Ć' => 'c', 'Ç' => 'c',
        'ď' => 'd', 'đ' => 'd', 'Ď' => 'd', 'Đ' => 'd',
        'é' => 'e', 'è' => 'e', 'ê' => 'e', 'ë' => 'e', 'ě' => 'e', 'ē' => 'e',
        'É' => 'e', 'È' => 'e', 'Ê' => 'e', 'Ë' => 'e', 'Ě' => 'e', 'Ē' => 'e',
        'í' => 'i', 'ì' => 'i', 'î' => 'i', 'ï' => 'i', 'ī' => 'i',
        'Í' => 'i', 'Ì' => 'i', 'Î' => 'i', 'Ï' => 'i', 'Ī' => 'i',
        'ĺ' => 'l', 'ľ' => 'l', 'ł' => 'l', 'Ĺ' => 'l', 'Ľ' => 'l', 'Ł' => 'l',
        'ň' => 'n', 'ń' => 'n', 'ñ' => 'n', 'Ň' => 'n', 'Ń' => 'n', 'Ñ' => 'n',
        'ó' => 'o', 'ò' => 'o', 'ô' => 'o', 'ö' => 'o', 'õ' => 'o', 'ø' => 'o', 'ō' => 'o',
        'Ó' => 'o', 'Ò' => 'o', 'Ô' => 'o', 'Ö' => 'o', 'Õ' => 'o', 'Ø' => 'o', 'Ō' => 'o',
        'ř' => 'r', 'ŕ' => 'r', 'Ř' => 'r', 'Ŕ' => 'r',
        'š' => 's', 'ś' => 's', 'ş' => 's', 'Š' => 's', 'Ś' => 's', 'Ş' => 's',
        'ť' => 't', 'ţ' => 't', 'Ť' => 't', 'Ţ' => 't',
        'ú' => 'u', 'ù' => 'u', 'û' => 'u', 'ü' => 'u', 'ů' => 'u', 'ū' => 'u',
        'Ú' => 'u', 'Ù' => 'u', 'Û' => 'u', 'Ü' => 'u', 'Ů' => 'u', 'Ū' => 'u',
        'ý' => 'y', 'ÿ' => 'y', 'Ý' => 'y', 'Ÿ' => 'y',
        'ž' => 'z', 'ź' => 'z', 'ż' => 'z', 'Ž' => 'z', 'Ź' => 'z', 'Ż' => 'z',
    ];

    /* Stav pro JSON do stránky: mapy musí zůstat objekty. PHP prázdné pole
       zakóduje jako [], prohlížeč z toho udělá pole a první zápis textu se
       při JSON.stringify ztratí — uloží se prázdný stav. Seznamy (added,
       removed) poli zůstávají. */
    public static function proJs(array $stav): array
    {
        $texts = [];
        foreach ((array) ($stav['texts'] ?? []) as $jazyk => $dvojice) {
            $texts[$jazyk] = (object) (array) $dvojice;
        }
        $stav['texts'] = (object) $texts;

        $realizace = (array) ($stav['realizace'] ?? []);
        $realizace['added'] = array_values((array) ($realizace['added'] ?? []));
        $realizace['removed'] = array_values((array) ($realizace['removed'] ?? []));
        $realizace['edited'] = (object) (array) ($realizace['edited'] ?? []);
        $stav['realizace'] = $realizace;

        /* portrety je mapa id => výřez; prázdná musí zůstat objektem, viz výš. */
        $stav['portrety'] = (object) (array) ($stav['portrety'] ?? []);

        return $stav;
    }

    /** @return array{texts: array, realizace: array{added: list, edited: array, removed: list}, portrety: array, updatedAt: null} */
    public static function prazdny(): array
    {
        return [
            'texts' => [],
            'realizace' => ['added' => [], 'edited' => [], 'removed' => []],
            'portrety' => [],
            'updatedAt' => null,
        ];
    }

    /**
     * Název na id do adresy: malá písmena, diakritika srovnaná, cokoli jiného
     * než a-z0-9 je pomlčka, pomlčky na krajích pryč. POZOR: 'ß' není a-z,
     * takže z něj je pomlčka — 'Grün Air Straße' => 'grun-air-stra-e'.
     */
    public static function slug(string $text): string
    {
        $bez = strtr($text, self::BEZ_DIAKRITIKY);
        $male = strtolower($bez);
        $pomlcky = preg_replace('/[^a-z0-9]+/', '-', $male) ?? '';

        return trim($pomlcky, '-');
    }

    /**
     * Přepis jednoho textu. Prázdná hodnota (i samé mezery) klíč SMAŽE, ale
     * jazyk ve stavu nechá — i když po smazání nic nezbude.
     */
    public static function nastavText(array $stav, string $jazyk, string $klic, string $hodnota): array
    {
        $novy = self::uplny($stav);
        if (!isset($novy['texts'][$jazyk]) || !is_array($novy['texts'][$jazyk])) {
            $novy['texts'][$jazyk] = [];
        }
        if (trim($hodnota) === '') {
            unset($novy['texts'][$jazyk][$klic]);
        } else {
            $novy['texts'][$jazyk][$klic] = $hodnota;
        }

        return $novy;
    }

    public static function text(array $stav, string $jazyk, string $klic): ?string
    {
        $texty = $stav['texts'][$jazyk] ?? null;
        if (!is_array($texty) || !array_key_exists($klic, $texty)) {
            return null;
        }

        return (string) $texty[$klic];
    }

    /**
     * Výchozí texty webu přelepené tím, co se přepsalo v administraci.
     * NEVRACÍ STAV, vrací jen ten plochý slovník textů.
     *
     * @param array<string,string> $vychozi
     * @return array<string,string>
     */
    public static function spojTexty(array $stav, string $jazyk, array $vychozi): array
    {
        $vysledek = $vychozi;
        $prepisy = $stav['texts'][$jazyk] ?? null;
        if (is_array($prepisy)) {
            foreach ($prepisy as $klic => $hodnota) {
                $vysledek[$klic] = $hodnota;
            }
        }

        return $vysledek;
    }

    /**
     * Import zálohy. Přijímá jen JSON objekt — pole, řetězec, číslo ani null
     * nejsou stav. Chybějící klíče se doplní, nic se nepřidává nad to (zejména
     * NE 'updatedAt', když v zálohe nebylo).
     *
     * @return array{ok: bool, state?: array, error?: string}
     */
    public static function zJson(array $stav, string $json): array
    {
        $rozebrane = json_decode($json, false, 512);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return ['ok' => false, 'error' => json_last_error_msg()];
        }
        if (!$rozebrane instanceof \stdClass) {
            return ['ok' => false, 'error' => 'Invalid JSON structure'];
        }

        return ['ok' => true, 'state' => self::uplny(self::naPole($rozebrane))];
    }

    /* ------------------------------------------------------------ pomocné */

    /** Doplní chybějící klíče stavu; 'updatedAt' nepřidává. */
    private static function uplny(array $stav): array
    {
        if (!isset($stav['texts']) || !is_array($stav['texts'])) {
            $stav['texts'] = [];
        }
        if (!isset($stav['realizace']) || !is_array($stav['realizace'])) {
            $stav['realizace'] = ['added' => [], 'edited' => [], 'removed' => []];
        }
        foreach (['added' => [], 'edited' => [], 'removed' => []] as $klic => $prazdne) {
            if (!array_key_exists($klic, $stav['realizace'])) {
                $stav['realizace'][$klic] = $prazdne;
            }
        }
        if (!isset($stav['portrety']) || !is_array($stav['portrety'])) {
            $stav['portrety'] = [];
        }

        return $stav;
    }

    private static function naPole(mixed $co): mixed
    {
        if ($co instanceof \stdClass) {
            $ven = [];
            foreach (get_object_vars($co) as $klic => $hodnota) {
                $ven[$klic] = self::naPole($hodnota);
            }

            return $ven;
        }
        if (is_array($co)) {
            return array_map([self::class, 'naPole'], $co);
        }

        return $co;
    }
}
