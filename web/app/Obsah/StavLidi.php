<?php
/* Stav administrace — část 'lide': přidaní, změnění a odebraní lidé z týmu.
   Zrcadlí src/lib/cms-store.mjs (upsertClovek, removeClovek, mergeLide,
   inicialyZJmena, telefonHref), aby server složil tým přesně jako prohlížeč.

   Výřez fotky v kolečku má vlastní část stavu ('portrety', App\Obsah\StavVyrezu)
   a klíčuje se stejným id. Odebraný člověk proto bere svůj výřez s sebou —
   jinak by v datech zůstal záznam, ke kterému už nikdo nepatří.

   Role člověka je text jako každý jiný: `lide.<id>` v části 'texts'. Tady se
   neukládá, aby šla přeložit do všech jazyků jedním místem (Meze::jePovolenyKlic
   ten klíč pouští i u člověka, který v souborech ještě není). */

declare(strict_types=1);

namespace App\Obsah;

final class StavLidi
{
    /** Kolik lidí smí administrace přidat. Tým není adresář. */
    public const MAX_PRIDANYCH = 30;

    /** Pole, která o člověku drží site.json a skládá dialog administrace. */
    public const POLE = ['id', 'jmeno', 'telefon', 'telefonHref', 'email', 'inicialy', 'fotka'];

    /**
     * Přidá nebo změní jednoho člověka. Bez id se id vyrobí ze jména (slug);
     * při kolizi se připojuje -2, -3, … Id ze souborů jde do 'edited'
     * (sloučeno s předchozí změnou) a vybere se z 'removed', jinak do 'added'.
     *
     * @param list<array> $zaklad lidé ze souborů
     * @return array CELÝ nový stav
     */
    public static function ulozClovek(array $stav, array $osoba, array $zaklad = []): array
    {
        $novy = self::uplny($stav);
        $lide = $novy['lide'];

        $zakladniId = [];
        foreach ($zaklad as $z) {
            if (is_array($z) && isset($z['id'])) {
                $zakladniId[(string) $z['id']] = true;
            }
        }
        $pridaneId = [];
        foreach ($lide['added'] as $p) {
            if (is_array($p) && isset($p['id'])) {
                $pridaneId[(string) $p['id']] = true;
            }
        }

        $id = $osoba['id'] ?? null;
        if ($id === null || $id === '') {
            $zaklad_id = Stav::slug((string) ($osoba['jmeno'] ?? ''));
            $id = $zaklad_id;
            $pripojka = 2;
            while (isset($zakladniId[$id]) || isset($pridaneId[$id]) || array_key_exists($id, $lide['edited'])) {
                $id = $zaklad_id . '-' . $pripojka;
                $pripojka++;
            }
        }
        $id = (string) $id;

        $zapis = self::ocisti($osoba);
        unset($zapis['id']);

        /* Zkratka a odkaz na telefon se odvozují ze jména a z čísla. Když
           se zdroj změní a odvozené pole nepřijde, přepočítá se — jinak by
           po opravě čísla zůstal odkaz `tel:` na to staré. */
        if (array_key_exists('jmeno', $zapis) && !array_key_exists('inicialy', $zapis)) {
            $zapis['inicialy'] = self::inicialyZJmena((string) $zapis['jmeno']);
        }
        if (array_key_exists('telefon', $zapis) && !array_key_exists('telefonHref', $zapis)) {
            $zapis['telefonHref'] = self::telefonHref((string) $zapis['telefon']);
        }

        /* Nejdřív `added`: administrace na ostrém webu dostává do stránky
           sloučený seznam, takže `zaklad` už přidané lidi obsahuje. Kdyby
           rozhodoval základ, oprava přidaného člověka by skončila v
           `edited` — a tu spojení zahodí, protože v site.json to id není. */
        $kde = null;
        foreach ($lide['added'] as $i => $p) {
            if (is_array($p) && (string) ($p['id'] ?? '') === $id) {
                $kde = $i;
                break;
            }
        }
        if ($kde !== null) {
            $lide['added'][$kde] = self::doplnene(array_merge($lide['added'][$kde], $zapis, ['id' => $id]));
        } elseif (isset($zakladniId[$id])) {
            $drive = $lide['edited'][$id] ?? [];
            $lide['edited'][$id] = array_merge(is_array($drive) ? $drive : [], $zapis);
            $lide['removed'] = array_values(array_filter(
                $lide['removed'],
                static fn ($odebrane) => $odebrane !== $id
            ));
        } else {
            $lide['added'][] = self::doplnene(array_merge($zapis, ['id' => $id]));
        }

        $novy['lide'] = $lide;

        return $novy;
    }

    /**
     * Odebere člověka. Přidaný zmizí z 'added' (nebyl nikdy v souborech),
     * ten ze souborů se zapíše do 'removed'. Výřez fotky jde s ním.
     *
     * @return array CELÝ nový stav
     */
    public static function odeberClovek(array $stav, string $id): array
    {
        $novy = self::uplny($stav);
        $lide = $novy['lide'];

        $kde = null;
        foreach ($lide['added'] as $i => $p) {
            if (is_array($p) && (string) ($p['id'] ?? '') === $id) {
                $kde = $i;
                break;
            }
        }
        if ($kde !== null) {
            array_splice($lide['added'], $kde, 1);
        } else {
            if (!in_array($id, $lide['removed'], true)) {
                $lide['removed'][] = $id;
            }
            unset($lide['edited'][$id]);
        }

        $novy['lide'] = $lide;
        if (isset($novy['portrety']) && is_array($novy['portrety'])) {
            unset($novy['portrety'][$id]);
        }

        return $novy;
    }

    /**
     * Lidé ze souborů se změnami administrace: odebraní vypadnou, změněným
     * se přelepí pole, přidaní se připojí na konec.
     *
     * @param list<array> $zaklad
     * @return list<array>
     */
    public static function spojLide(array $stav, array $zaklad): array
    {
        $lide = self::castStavu($stav);
        $odebrani = [];
        foreach ($lide['removed'] as $id) {
            $odebrani[(string) $id] = true;
        }

        $vysledek = [];
        foreach ($zaklad as $osoba) {
            if (!is_array($osoba)) {
                continue;
            }
            $id = (string) ($osoba['id'] ?? '');
            if (isset($odebrani[$id])) {
                continue;
            }
            $zmena = $lide['edited'][$id] ?? null;
            $vysledek[] = is_array($zmena)
                ? self::doplnene(array_merge($osoba, self::ocisti($zmena), ['id' => $id]))
                : $osoba;
        }
        foreach ($lide['added'] as $osoba) {
            if (!is_array($osoba) || ($osoba['id'] ?? '') === '') {
                continue;
            }
            $vysledek[] = self::doplnene(self::ocisti($osoba));
        }

        return $vysledek;
    }

    /** Zkratka ze jména: první písmena prvních dvou slov, velká. */
    public static function inicialyZJmena(string $jmeno): string
    {
        $slova = preg_split('/\s+/u', trim($jmeno)) ?: [];
        $zkratka = '';
        foreach ($slova as $slovo) {
            if ($slovo === '') {
                continue;
            }
            $zkratka .= mb_substr($slovo, 0, 1, 'UTF-8');
            if (mb_strlen($zkratka, 'UTF-8') >= 2) {
                break;
            }
        }

        return mb_strtoupper($zkratka, 'UTF-8');
    }

    /** Telefon do odkazu tel:: jen číslice a jedno plus na začátku. */
    public static function telefonHref(string $telefon): string
    {
        $cisla = preg_replace('/[^0-9]/', '', $telefon) ?? '';
        $plus = str_starts_with(ltrim($telefon), '+') ? '+' : '';

        return $cisla === '' ? '' : $plus . $cisla;
    }

    /** Doplní zkratku a telefon do odkazu, pokud chybí. */
    public static function doplnene(array $osoba): array
    {
        $jmeno = (string) ($osoba['jmeno'] ?? '');
        if (($osoba['inicialy'] ?? '') === '') {
            $osoba['inicialy'] = self::inicialyZJmena($jmeno);
        }
        if (($osoba['telefonHref'] ?? '') === '') {
            $osoba['telefonHref'] = self::telefonHref((string) ($osoba['telefon'] ?? ''));
        }

        return $osoba;
    }

    /* ------------------------------------------------------------ pomocné */

    /** Jen pole, která o člověku známe; řetězce, ořezané. */
    private static function ocisti(array $osoba): array
    {
        $ven = [];
        foreach (self::POLE as $pole) {
            if (!array_key_exists($pole, $osoba)) {
                continue;
            }
            $hodnota = $osoba[$pole];
            if (!is_string($hodnota)) {
                continue;
            }
            $ven[$pole] = trim($hodnota);
        }

        return $ven;
    }

    /** Část 'lide' ve tvaru, se kterým se dá počítat. */
    private static function castStavu(array $stav): array
    {
        $lide = is_array($stav['lide'] ?? null) ? $stav['lide'] : [];

        return [
            'added' => array_values(is_array($lide['added'] ?? null) ? $lide['added'] : []),
            'edited' => is_array($lide['edited'] ?? null) ? $lide['edited'] : [],
            'removed' => array_values(is_array($lide['removed'] ?? null) ? $lide['removed'] : []),
        ];
    }

    /** Doplní 'lide' do stavu, který ho ještě nemá. */
    private static function uplny(array $stav): array
    {
        $stav['lide'] = self::castStavu($stav);

        return $stav;
    }
}
