<?php
/* Čistý převod odpovědí Google Analytics Data API (runReport, v1beta) do tvaru,
   kterému rozumí nástěnka administrace. Žádná síť, žádný čas, žádný stav —
   všechno, co tady běží, je aritmetika nad polemi. */

declare(strict_types=1);

namespace App\Statistiky;

final class Ga4Prevod
{
    /** Jména metrik GA4 → klíče denního řádku nástěnky. */
    private const METRIKY = [
        'sessions' => 'navstevy',
        'totalUsers' => 'uzivatele',
        'screenPageViews' => 'zobrazeni',
        'averageSessionDuration' => 'cas',
        'bounceRate' => 'opusteni',
    ];

    /**
     * Denní řada pro nástěnku: přesně $pocet dnů, nejstarší první, poslední
     * je $konec. Dny, které v odpovědi chybí, jsou nulové; poptávky přibíráme
     * z naší databáze ($poptavky: 'Y-m-d' => int).
     */
    public static function dny(array $odpoved, int $pocet, string $konec, array $poptavky = []): array
    {
        $podleData = self::radkyPodleData($odpoved);

        $dny = [];
        $den = new \DateTimeImmutable($konec);
        for ($i = 0; $i < $pocet; $i++) {
            $datum = $den->format('Y-m-d');
            $radek = $podleData[$datum] ?? null;

            $dny[] = [
                'datum' => $datum,
                'navstevy' => $radek === null ? 0 : (int) $radek['navstevy'],
                'uzivatele' => $radek === null ? 0 : (int) $radek['uzivatele'],
                'zobrazeni' => $radek === null ? 0 : (int) $radek['zobrazeni'],
                'poptavky' => (int) ($poptavky[$datum] ?? 0),
                'cas' => $radek === null ? 0.0 : round((float) $radek['cas'], 1),
                'opusteni' => $radek === null ? 0.0 : round((float) $radek['opusteni'] * 100, 2),
            ];
            $den = $den->modify('-1 day');
        }

        return array_reverse($dny);
    }

    /**
     * Rozpad podle jednoho rozměru: seznam ['nazev', 'podil'] od největšího podílu.
     * Součet podílů je přesně 100.
     */
    public static function rozpad(array $odpoved, array $preklad = [], int $maxRadku = 6): array
    {
        $celkem = 0.0;
        $soucety = [];
        foreach ((array) ($odpoved['rows'] ?? []) as $radek) {
            $hodnota = (float) ($radek['metricValues'][0]['value'] ?? 0);
            $celkem += $hodnota;
            $nazev = (string) ($radek['dimensionValues'][0]['value'] ?? '');
            $nazev = $preklad[$nazev] ?? $nazev;
            $soucety[$nazev] = ($soucety[$nazev] ?? 0.0) + $hodnota;
        }

        if ($maxRadku <= 0 || $soucety === []) {
            return [];
        }

        $seznam = [];
        foreach ($soucety as $nazev => $hodnota) {
            $seznam[] = ['nazev' => $nazev, 'hodnota' => $hodnota];
        }
        usort($seznam, static fn (array $a, array $b): int => $b['hodnota'] <=> $a['hodnota']);

        $seznam = array_slice($seznam, 0, $maxRadku);

        if ($celkem <= 0.0) {
            $final = [];
            foreach ($seznam as $item) {
                $final[] = ['nazev' => $item['nazev'], 'podil' => 0];
            }
            return $final;
        }

        $radky = [];
        $sumPodily = 0;
        foreach ($seznam as $item) {
            $podil = (int) floor($item['hodnota'] * 100 / $celkem);
            $radky[] = [
                'nazev' => $item['nazev'],
                'podil' => $podil,
                'remainder' => fmod($item['hodnota'] * 100 / $celkem, 1.0),
                'hodnota' => $item['hodnota']
            ];
            $sumPodily += $podil;
        }

        $chybi = 100 - $sumPodily;
        if ($chybi > 0 && !empty($radky)) {
            usort($radky, static fn (array $a, array $b): int =>
                $b['remainder'] <=> $a['remainder'] ?:
                $b['hodnota'] <=> $a['hodnota'] ?:
                strcmp($a['nazev'], $b['nazev']));

            for ($i = 0; $i < $chybi; $i++) {
                $radky[$i % count($radky)]['podil']++;
            }
        }

        $final = [];
        foreach ($radky as $r) {
            if ($r['podil'] > 0) {
                $final[] = ['nazev' => $r['nazev'], 'podil' => $r['podil']];
            }
        }
        
        usort($final, static fn (array $a, array $b): int => $b['podil'] <=> $a['podil']);

        return $final;
    }

    /**
     * @return array<string,array{navstevy:int,uzivatele:int,zobrazeni:int,cas:float,opusteni:float}>
     */
    private static function radkyPodleData(array $odpoved): array
    {
        $pozice = [];
        foreach ((array) ($odpoved['metricHeaders'] ?? []) as $i => $hlavicka) {
            $jmeno = (string) ($hlavicka['name'] ?? '');
            if ($jmeno !== '' && isset(self::METRIKY[$jmeno])) {
                $pozice[$jmeno] = $i;
            }
        }

        $podleData = [];
        foreach ((array) ($odpoved['rows'] ?? []) as $radek) {
            $hodnota = (string) ($radek['dimensionValues'][0]['value'] ?? '');
            $datum = self::datum($hodnota);
            if ($datum === null) {
                continue;
            }
            $podleData[$datum] = [
                'navstevy' => self::metrika($radek, $pozice, 'sessions'),
                'uzivatele' => self::metrika($radek, $pozice, 'totalUsers'),
                'zobrazeni' => self::metrika($radek, $pozice, 'screenPageViews'),
                'cas' => self::metrika($radek, $pozice, 'averageSessionDuration'),
                'opusteni' => self::metrika($radek, $pozice, 'bounceRate'),
            ];
        }

        return $podleData;
    }

    /** '20261022' i '2026-10-22' → '2026-10-22'; cokoliv jiného → null. */
    private static function datum(string $hodnota): ?string
    {
        if (preg_match('/^(\\d{4})-?(\\d{2})-?(\\d{2})$/', $hodnota, $c) !== 1) {
            return null;
        }

        return $c[1] . '-' . $c[2] . '-' . $c[3];
    }

    /** Hodnota metriky podle jména (ne pozice); chybí → 0. */
    private static function metrika(array $radek, array $pozice, string $jmeno): float
    {
        if (!isset($pozice[$jmeno])) {
            return 0.0;
        }
        $hodnota = $radek['metricValues'][$pozice[$jmeno]]['value'] ?? null;

        return is_numeric($hodnota) ? (float) $hodnota : 0.0;
    }
}
