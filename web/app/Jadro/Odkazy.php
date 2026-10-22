<?php
/* Názvy souborů stránek a cesta zpátky: z adresy na stránku.

   Adresy zůstávají stejné jako v ukázce (index.html, domacnosti.html,
   sluzba-projekce.html, en/kontakt.html). Má to dva důvody: ukázka a ostrý
   web se dají porovnat bajt na bajt, a kdo si odkaz uložil, trefí i potom.
   Adresa bez .html funguje taky — PHP na ni odpoví přesměrováním na tvar
   s příponou, aby každá stránka měla jednu adresu. */

declare(strict_types=1);

namespace App\Jadro;

final class Odkazy
{
    public const SOUBORY = [
        'index' => 'index.html',
        'novinky' => 'novinky.html',
        'onas' => 'o-nas.html',
        'kariera' => 'kariera.html',
        'kontakt' => 'kontakt.html',
        'slovnik' => 'slovnik.html',
        'gdpr' => 'ochrana-osobnich-udaju.html',
        'chyba404' => '404.html',
        'administrace' => 'administrace.html',
    ];

    /**
     * Název souboru stránky. `$vetev` platí pro přehledy, které bez větve
     * nemají smysl; detaily služeb a realizací jsou napříč větvemi jedinečné.
     */
    public static function soubor(string $druh, ?string $id, ?string $vetev, array $site): string
    {
        if ($druh === 'sluzba') {
            return 'sluzba-' . $id . '.html';
        }
        if ($druh === 'novinka') {
            return 'novinka-' . $id . '.html';
        }
        if ($druh === 'vetev') {
            foreach ($site['vetve'] as $v) {
                if ($v['id'] === $id) {
                    return $v['soubor'] . '.html';
                }
            }
            throw new \InvalidArgumentException("Neznámá větev: {$id}");
        }
        if ($druh === 'sluzby') {
            $v = $id ?? $vetev;
            if ($v === null || $v === '') {
                throw new \InvalidArgumentException('odkaz na přehled služeb vyžaduje větev');
            }
            return $v . '-sluzby.html';
        }
        if ($druh === 'realizace') {
            if ($id !== null && $id !== '') {
                return 'realizace-' . $id . '.html';
            }
            if ($vetev === null || $vetev === '') {
                throw new \InvalidArgumentException('odkaz na přehled realizací vyžaduje větev');
            }
            return $vetev . '-realizace.html';
        }
        if ($druh === 'realizaceDetail') {
            $v = $id ?? $vetev;
            if ($v === null || $v === '') {
                throw new \InvalidArgumentException('šablona detailu realizace vyžaduje větev');
            }
            return $v . '-realizace-detail.html';
        }
        $s = self::SOUBORY[$druh] ?? null;
        if ($s === null) {
            throw new \InvalidArgumentException("Neznámý druh odkazu: {$druh}");
        }
        return $s;
    }

    /**
     * Z adresy udělá popis stránky, nebo null, když taková stránka není.
     *
     * @return array{jazyk:string,druh:string,id:?string,vetev:?string,soubor:string}|null
     */
    public static function rozpoznej(string $cesta, array $site): ?array
    {
        $cesta = ltrim($cesta, '/');
        $jazyk = 'cs';
        foreach ($site['jazyky'] as $j) {
            if ($j['adresar'] !== '' && ($cesta === $j['adresar'] || str_starts_with($cesta, $j['adresar'] . '/'))) {
                $jazyk = $j['kod'];
                $cesta = substr($cesta, strlen($j['adresar']) + 1);
                break;
            }
        }
        if ($cesta === '' || $cesta === false) {
            $cesta = 'index.html';
        }
        if (!str_contains($cesta, '/') && !str_ends_with($cesta, '.html')) {
            $cesta .= '.html';
        }
        if (str_contains($cesta, '/')) {
            return null;
        }

        $hotovo = static fn (string $druh, ?string $id = null, ?string $vetev = null): array => [
            'jazyk' => $jazyk, 'druh' => $druh, 'id' => $id, 'vetev' => $vetev, 'soubor' => $cesta,
        ];

        foreach (self::SOUBORY as $druh => $soubor) {
            if ($cesta === $soubor) {
                // administrace je jen česky a jen v kořeni
                if ($druh === 'administrace' && $jazyk !== 'cs') {
                    return null;
                }
                return $hotovo($druh);
            }
        }
        foreach ($site['vetve'] as $v) {
            if ($cesta === $v['soubor'] . '.html') {
                return $hotovo('vetev', $v['id'], $v['id']);
            }
            if ($cesta === $v['id'] . '-sluzby.html') {
                return $hotovo('sluzby', $v['id'], $v['id']);
            }
            if ($cesta === $v['id'] . '-realizace.html') {
                return $hotovo('realizace', null, $v['id']);
            }
            if ($cesta === $v['id'] . '-realizace-detail.html') {
                return $hotovo('realizaceDetail', $v['id'], $v['id']);
            }
        }
        if (preg_match('~^sluzba-([a-z0-9-]+)\.html$~', $cesta, $m) === 1) {
            foreach ($site['sluzby'] as $s) {
                if ($s['id'] === $m[1]) {
                    return $hotovo('sluzba', $s['id'], $s['vetev']);
                }
            }
            return null;
        }
        if (preg_match('~^realizace-([a-z0-9-]+)\.html$~', $cesta, $m) === 1) {
            foreach ($site['realizace'] as $r) {
                if ($r['id'] === $m[1]) {
                    return $hotovo('realizace', $r['id'], $r['vetev']);
                }
            }
            return null;
        }
        if (preg_match('~^novinka-([a-z0-9-]+)\.html$~', $cesta, $m) === 1) {
            foreach ($site['novinky'] as $n) {
                if ($n['id'] === $m[1]) {
                    return $hotovo('novinka', $n['id']);
                }
            }
            return null;
        }
        return null;
    }
}
