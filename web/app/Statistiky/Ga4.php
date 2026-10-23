<?php
/* Google Analytics 4 jako zdroj čísel pro nástěnku administrace. Servisní účet
   (config/ga4.json) se podepíše přes App\Statistiky\Ga4Token, výměnou přijde
   access token a tím se zavolá Data API. Odpovědi Googlu překládá do tvaru
   nástěnky App\Statistiky\Ga4Prevod — tady je jen doprava a mezipaměť.

   Poptávky nebere z Analytics, ale z naší vlastní tabulky `poptavky`: víme je
   přesně a nezávisle na tom, jestli návštěvník povolil měření. */

declare(strict_types=1);

namespace App\Statistiky;

final class Ga4 implements Poskytovatel
{
    private const ROZSAH = 'https://www.googleapis.com/auth/analytics.readonly';
    private const TOKEN = 'https://oauth2.googleapis.com/token';
    private const DATA = 'https://analyticsdata.googleapis.com/v1beta/properties/';

    /** Jak dlouho platí hotový přehled v mezipaměti (s). */
    private const PLATNOST = 600;

    /** Metriky denního přehledu — v tomto pořadí se posílají i čtou. */
    private const METRIKY = [
        'sessions',
        'totalUsers',
        'screenPageViews',
        'averageSessionDuration',
        'bounceRate',
    ];

    /** Kanály Googlu → názvy na nástěnce. Co tu není, projde jak přišlo. */
    private const KANALY = [
        'Organic Search' => 'Vyhledávání Google',
        'Direct' => 'Přímý přístup',
        'Organic Social' => 'Sociální sítě',
        'Paid Search' => 'Placené vyhledávání',
        'Referral' => 'Ostatní odkazy',
        'Email' => 'E-mail',
        'Unassigned' => 'Nezařazeno',
    ];

    private const ZARIZENI = [
        'mobile' => 'Mobil',
        'desktop' => 'Počítač',
        'tablet' => 'Tablet',
        'smart tv' => 'Televize',
    ];

    /** Vstupní stránky → názvy na nástěnce. Neznámá cesta zůstane cestou. */
    private const STRANKY = [
        '/' => 'Úvodní rozcestník',
        '/index.html' => 'Úvodní rozcestník',
        '/domacnosti.html' => 'Domácnosti',
        '/firmy.html' => 'Firemní zákazníci',
        '/servis.html' => 'Servis a havárie',
        '/kontakt.html' => 'Kontakt',
    ];

    public function __construct(
        private readonly string $property,
        private readonly string $klic,
        private readonly string $cache,
        private readonly ?\PDO $pdo = null,
    ) {
    }

    public function prehled(int $dni): array
    {
        $dni = max(1, min(400, $dni));
        $soubor = rtrim($this->cache, '/') . '/ga4-prehled-' . $dni . '.json';
        $hotovo = $this->zCache($soubor);
        if ($hotovo !== null) {
            return $hotovo;
        }

        $token = $this->token();
        $konec = (new \DateTimeImmutable('today'))->format('Y-m-d');

        $prehled = [
            'dny' => Ga4Prevod::dny(
                $this->report($token, [
                    'dateRanges' => [['startDate' => ($dni - 1) . 'daysAgo', 'endDate' => 'today']],
                    'dimensions' => [['name' => 'date']],
                    'metrics' => array_map(static fn (string $m): array => ['name' => $m], self::METRIKY),
                    'orderBys' => [['dimension' => ['dimensionName' => 'date']]],
                    'limit' => 400,
                ]),
                $dni,
                $konec,
                $this->poptavky($dni)
            ),
            'rozpady' => [
                'zdroje' => Ga4Prevod::rozpad($this->podleRozmeru($token, 'sessionDefaultChannelGroup', $dni), self::KANALY, 6),
                'vstupni' => Ga4Prevod::rozpad($this->podleRozmeru($token, 'landingPage', $dni), self::STRANKY, 5),
                'zarizeni' => Ga4Prevod::rozpad($this->podleRozmeru($token, 'deviceCategory', $dni), self::ZARIZENI, 3),
            ],
        ];

        $this->doCache($soubor, $prehled);

        return $prehled;
    }

    /* ------------------------------------------------------------ Google */

    /** Access token servisního účtu; drží se v mezipaměti, dokud platí. */
    private function token(): string
    {
        $soubor = rtrim($this->cache, '/') . '/ga4-token.json';
        $ulozeny = $this->precti($soubor);
        if (is_array($ulozeny) && isset($ulozeny['token'], $ulozeny['do'])
            && is_string($ulozeny['token']) && (int) $ulozeny['do'] > time() + 60) {
            return $ulozeny['token'];
        }

        $ucet = $this->precti($this->klic);
        if (!is_array($ucet) || !isset($ucet['client_email'], $ucet['private_key'])) {
            throw new \RuntimeException('ga4-klic-nejde-precist');
        }

        $jwt = Ga4Token::jwt($ucet, self::ROZSAH, time());
        $odpoved = $this->posli(self::TOKEN, Ga4Token::pozadavek($jwt), [
            'Content-Type: application/x-www-form-urlencoded',
        ]);

        $data = json_decode($odpoved, true);
        if (!is_array($data) || !isset($data['access_token']) || !is_string($data['access_token'])) {
            throw new \RuntimeException('ga4-token-odmitnut');
        }

        $this->doCache($soubor, [
            'token' => $data['access_token'],
            'do' => time() + (int) ($data['expires_in'] ?? 3600),
        ]);

        return $data['access_token'];
    }

    /** @return array<string,mixed> odpověď runReport */
    private function report(string $token, array $dotaz): array
    {
        $odpoved = $this->posli(
            self::DATA . rawurlencode($this->property) . ':runReport',
            json_encode($dotaz, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE),
            ['Content-Type: application/json', 'Authorization: Bearer ' . $token]
        );

        $data = json_decode($odpoved, true);
        if (!is_array($data)) {
            throw new \RuntimeException('ga4-odpoved-neni-json');
        }
        if (isset($data['error'])) {
            throw new \RuntimeException('ga4-chyba-api');
        }

        return $data;
    }

    /** @return array<string,mixed> jeden rozměr proti návštěvám, od nejsilnějšího */
    private function podleRozmeru(string $token, string $rozmer, int $dni): array
    {
        return $this->report($token, [
            'dateRanges' => [['startDate' => ($dni - 1) . 'daysAgo', 'endDate' => 'today']],
            'dimensions' => [['name' => $rozmer]],
            'metrics' => [['name' => 'sessions']],
            'orderBys' => [['metric' => ['metricName' => 'sessions'], 'desc' => true]],
            'limit' => 25,
        ]);
    }

    private function posli(string $adresa, string $telo, array $hlavicky): string
    {
        $ch = curl_init($adresa);
        if ($ch === false) {
            throw new \RuntimeException('ga4-curl-neni');
        }
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $telo,
            CURLOPT_HTTPHEADER => $hlavicky,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_CONNECTTIMEOUT => 5,
        ]);
        $odpoved = curl_exec($ch);
        $stav = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        // Zavírat se nic nemusí: od PHP 8.0 spojení uklidí sběrač a v 8.5 je
        // curl_close() zastaralé — na ostrém webu by jen plnilo log serveru.
        unset($ch);

        if (!is_string($odpoved) || $stav < 200 || $stav > 299) {
            throw new \RuntimeException('ga4-nedostupne-' . $stav);
        }

        return $odpoved;
    }

    /* ------------------------------------------------------ naše poptávky */

    /** @return array<string,int> datum => počet poptávek */
    private function poptavky(int $dni): array
    {
        if ($this->pdo === null) {
            return [];
        }
        try {
            $dotaz = $this->pdo->prepare(
                'SELECT DATE(prijato) AS den, COUNT(*) AS pocet FROM poptavky
                 WHERE prijato >= DATE_SUB(CURDATE(), INTERVAL ? DAY) GROUP BY den'
            );
            $dotaz->execute([$dni]);
            $podle = [];
            foreach ($dotaz->fetchAll(\PDO::FETCH_ASSOC) ?: [] as $radek) {
                $podle[(string) $radek['den']] = (int) $radek['pocet'];
            }
            return $podle;
        } catch (\Throwable) {
            return [];
        }
    }

    /* ---------------------------------------------------------- mezipaměť */

    private function precti(string $soubor): mixed
    {
        if (!is_file($soubor) || !is_readable($soubor)) {
            return null;
        }
        $obsah = file_get_contents($soubor);

        return $obsah === false ? null : json_decode($obsah, true);
    }

    private function zCache(string $soubor): ?array
    {
        if (!is_file($soubor) || time() - (int) filemtime($soubor) >= self::PLATNOST) {
            return null;
        }
        $data = $this->precti($soubor);

        return is_array($data) && isset($data['dny'], $data['rozpady']) ? $data : null;
    }

    private function doCache(string $soubor, array $data): void
    {
        $slozka = dirname($soubor);
        if (!is_dir($slozka) && !@mkdir($slozka, 0770, true) && !is_dir($slozka)) {
            return;
        }
        $docasny = $soubor . '.' . getmypid() . '.tmp';
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        if ($json !== false && file_put_contents($docasny, $json) !== false) {
            @chmod($docasny, 0640);
            @rename($docasny, $soubor);
        }
    }
}
