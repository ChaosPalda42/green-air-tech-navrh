<?php
/* Z adresy na hotové HTML. Jedno místo, které ví, čím se která stránka vykreslí.

   Tohle je přepis smyčky z build.mjs: stejné stránky, stejné meta klíče, stejná
   třída na <body>. Používá to jak tools/vykresli.php (bajtový diff proti ukázce),
   tak web/public/index.php (ostrý web). */

declare(strict_types=1);

namespace App\Jadro;

use App\Obsah\Zdroj;
use App\Sablony\Layout;
use App\Sablony\Stranky\Firma;
use App\Sablony\Stranky\Realizace;
use App\Sablony\Stranky\Rozcestnik;
use App\Sablony\Stranky\Sluzby;
use App\Sablony\Stranky\Spolecne;

final class Stranka
{
    /** Vykreslí stránku na adrese, nebo vrátí null, když taková není. */
    public static function html(string $cesta, Zdroj $zdroj, bool $ukazka = true): ?string
    {
        $site = $zdroj->site();
        $kam = Odkazy::rozpoznej($cesta, $site);
        if ($kam === null) {
            return null;
        }
        return self::vykresli($kam, $zdroj, $ukazka);
    }

    /**
     * @param array{jazyk:string,druh:string,id:?string,vetev:?string,soubor:string} $kam
     * @param ?Zdroj $vychozi výchozí obsah ze souborů (administrace proti němu ukazuje, co se přepsalo)
     * @param ?\App\Api\Uloziste $uloziste odkud se vezme stav administrace na ostrém webu
     */
    public static function vykresli(
        array $kam,
        Zdroj $zdroj,
        bool $ukazka = true,
        ?Zdroj $vychozi = null,
        ?\App\Api\Uloziste $uloziste = null,
    ): string {
        $site = $zdroj->site();
        $druh = $kam['druh'];
        $id = $kam['id'];
        $vetev = $kam['vetev'];

        $ctx = static fn (string $aktivni, ?string $v = null): Kontext => new Kontext(
            $kam['jazyk'],
            $v,
            $kam['soubor'],
            $aktivni,
            $zdroj,
            $ukazka,
        );

        [$k, $telo, $meta, $trida, $skripty] = match ($druh) {
            'index' => [
                $c = $ctx('index'),
                Rozcestnik::rozcestnik($c),
                'home',
                'je-rozcestnik',
                '',
            ],
            'vetev' => [
                $c = $ctx('vetev', $vetev),
                Rozcestnik::vetevDomu($c),
                "vetve.{$vetev}",
                '',
                '',
            ],
            'sluzby' => [
                $c = $ctx('sluzby', $vetev),
                Sluzby::sluzbyPrehled($c),
                "sluzbyVetve.{$vetev}",
                '',
                '',
            ],
            'sluzba' => [
                $c = $ctx('sluzby', $vetev),
                Sluzby::sluzbaDetail($c, self::najdi($site['sluzby'], (string) $id)),
                "sluzbyVetve.{$vetev}",
                '',
                '',
            ],
            'realizace' => $id === null || $id === ''
                ? [
                    $c = $ctx('realizace', $vetev),
                    Realizace::realizacePrehled($c),
                    "realizaceVetve.{$vetev}",
                    '',
                    '',
                ]
                : [
                    $c = $ctx('realizace', $vetev),
                    Realizace::realizaceDetail($c, self::najdi($site['realizace'], (string) $id)),
                    "realizaceVetve.{$vetev}",
                    '',
                    '',
                ],
            'realizaceDetail' => [
                $c = $ctx('realizace', $vetev),
                Realizace::realizaceSablona($c),
                "realizaceVetve.{$vetev}",
                '',
                '',
            ],
            'onas' => [$c = $ctx('onas'), Firma::oNas($c), 'onas', '', ''],
            'novinky' => [$c = $ctx('novinky'), Firma::novinkyPrehled($c), 'novinky', '', ''],
            'novinka' => [
                $c = $ctx('novinky'),
                Firma::novinkaDetail($c, self::najdi($site['novinky'], (string) $id)),
                'novinky',
                '',
                '',
            ],
            'kariera' => [$c = $ctx('kariera'), Firma::kariera($c), 'kariera', '', ''],
            'kontakt' => [$c = $ctx('kontakt'), Spolecne::kontakt($c), 'kontakt', '', ''],
            'slovnik' => [$c = $ctx('slovnik'), Spolecne::slovnik($c), 'slovnik', '', ''],
            'gdpr' => [$c = $ctx(''), Spolecne::gdpr($c), 'gdpr', '', ''],
            'chyba404' => [$c = $ctx(''), Spolecne::chyba404($c), 'chyba404', '', ''],
            'administrace' => self::administrace($zdroj, $ukazka, $vychozi, $uloziste),
            default => throw new \RuntimeException("Neznámý druh stránky: {$druh}"),
        };

        return Layout::stranka($k, [
            'telo' => $telo,
            'titulek' => $k->t("meta.{$meta}.titulek"),
            'popis' => $k->t("meta.{$meta}.popis"),
            'trida' => $trida,
            'skripty' => $skripty,
        ]);
    }

    /** @return array{0:Kontext,1:string,2:string,3:string,4:string} */
    private static function administrace(
        Zdroj $zdroj,
        bool $ukazka,
        ?Zdroj $vychozi = null,
        ?\App\Api\Uloziste $uloziste = null,
    ): array {
        $ctx = new Kontext('cs', null, Odkazy::SOUBORY['administrace'], 'administrace', $zdroj, $ukazka);
        $skripty = '<link rel="stylesheet" href="' . $ctx->asset('admin.css') . '">' . "\n"
            . '<script src="' . $ctx->asset('admin.js') . '" defer></script>';

        // Nabídka textů se staví z VÝCHOZÍHO obsahu ze souborů — administrace pak
        // vedle sebe ukáže, co je původní a co už někdo přepsal.
        $data = Administrace::data(
            $ctx,
            $vychozi ?? $zdroj,
            dirname(__DIR__, 2) . '/data/admin-klice.json',
        );

        if (!$ukazka) {
            $uzivatel = \App\Auth\Sezeni::uzivatel();
            $data['csrf'] = \App\Auth\Sezeni::csrf();
            $data['chybaPrihlaseni'] = isset($_GET['chyba']);
            $stav = $uloziste?->stav() ?? [];
            $skripty .= "\n" . '<script>'
                . 'window.GAT_SERVER = true;'
                . 'window.GAT_CSRF = ' . self::js($data['csrf']) . ';'
                . 'window.GAT_UZIVATEL = ' . self::js($uzivatel === null ? null : [
                    'jmeno' => $uzivatel['jmeno'],
                    'email' => $uzivatel['email'],
                    'role' => $uzivatel['role'],
                ]) . ';'
                . 'window.GAT_STAV = ' . self::js($stav === [] ? null : $stav) . ';'
                . '</script>';
        }

        return [
            $ctx,
            \App\Sablony\Stranky\Administrace::administrace($ctx, $data),
            'administrace',
            'je-administrace',
            $skripty,
        ];
    }

    /** Totéž co JSON.stringify v prohlížeči. */
    private static function js(mixed $data): string
    {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    }

    /** @param list<array<string,mixed>> $seznam */
    private static function najdi(array $seznam, string $id): array
    {
        foreach ($seznam as $x) {
            if ($x['id'] === $id) {
                return $x;
            }
        }
        throw new \RuntimeException("Není v datech: {$id}");
    }

    /** Všechny stránky webu — v témže pořadí, v jakém je staví ukázka. */
    public static function seznam(array $site): array
    {
        $vse = [];
        foreach ($site['jazyky'] as $j) {
            $a = $j['adresar'] === '' ? '' : $j['adresar'] . '/';
            $vse[] = $a . Odkazy::SOUBORY['index'];
            foreach ($site['vetve'] as $v) {
                $vse[] = $a . Odkazy::soubor('vetev', $v['id'], null, $site);
                $vse[] = $a . Odkazy::soubor('sluzby', $v['id'], $v['id'], $site);
                foreach ($site['sluzby'] as $s) {
                    if ($s['vetev'] === $v['id']) {
                        $vse[] = $a . Odkazy::soubor('sluzba', $s['id'], null, $site);
                    }
                }
                $vse[] = $a . Odkazy::soubor('realizace', null, $v['id'], $site);
                foreach ($site['realizace'] as $r) {
                    if ($r['vetev'] === $v['id']) {
                        $vse[] = $a . Odkazy::soubor('realizace', $r['id'], null, $site);
                    }
                }
                $vse[] = $a . Odkazy::soubor('realizaceDetail', $v['id'], $v['id'], $site);
            }
            foreach (['onas', 'novinky'] as $d) {
                $vse[] = $a . Odkazy::SOUBORY[$d];
            }
            foreach ($site['novinky'] as $n) {
                $vse[] = $a . Odkazy::soubor('novinka', $n['id'], null, $site);
            }
            foreach (['kariera', 'kontakt', 'slovnik', 'gdpr', 'chyba404'] as $d) {
                $vse[] = $a . Odkazy::SOUBORY[$d];
            }
        }
        $vse[] = Odkazy::SOUBORY['administrace'];
        return $vse;
    }
}
