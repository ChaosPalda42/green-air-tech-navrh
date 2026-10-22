<?php
/* Kontext jedné vykreslované stránky: jazyk, větev, překlady a pomocné
   funkce, které šablony potřebují. Je to PHP obdoba `vytvorKontext` z
   build.mjs — schválně stejná jména i chování, aby se výstup dal porovnat
   s ukázkou bajt na bajt. */

declare(strict_types=1);

namespace App\Jadro;

use App\Obsah\Datum;
use App\Obsah\I18n;
use App\Obsah\Slovnik;
use App\Obsah\Zdroj;

final class Kontext
{
    /** @var list<array{abbr:string,full:string,popis:string}> */
    public readonly array $terminy;

    private array $site;
    private array $dict;
    private array $zaskok;
    private array $obrazky;
    private array $verze;

    public function __construct(
        public readonly string $lang,
        public readonly ?string $vetev,
        public readonly string $aktualniSoubor,
        public readonly string $aktivni,
        private readonly Zdroj $zdroj,
        /** Ukázkový režim: noindex a poznámka „ukázka" v patičce. */
        public readonly bool $ukazka = true,
    ) {
        $this->site = $zdroj->site();
        $this->dict = $zdroj->dict($lang);
        $this->zaskok = $lang === 'cs' ? $this->dict : $zdroj->dict('cs');
        $this->obrazky = $zdroj->obrazky();
        $this->verze = $zdroj->verzeAktiv();

        $terminy = [];
        foreach ($zdroj->slovnik($lang) as $abbr => $v) {
            $terminy[] = ['abbr' => (string) $abbr, 'full' => $v['full'] ?? '', 'popis' => $v['popis'] ?? ''];
        }
        $this->terminy = $terminy;
    }

    public function site(): array
    {
        return $this->site;
    }

    private function jazyk(string $kod): array
    {
        foreach ($this->site['jazyky'] as $j) {
            if ($j['kod'] === $kod) {
                return $j;
            }
        }
        throw new \InvalidArgumentException("Neznámý jazyk: {$kod}");
    }

    /** Prefix k návratu do kořene z jazykového podadresáře. */
    private function prefix(): string
    {
        return $this->jazyk($this->lang)['adresar'] !== '' ? '../' : '';
    }

    public function t(string $klic, array $vars = []): string
    {
        return I18n::t($this->dict, $klic, $vars, $this->zaskok);
    }

    public function existuje(string $klic): bool
    {
        $v = I18n::get($this->dict, $klic) ?? I18n::get($this->zaskok, $klic);
        if (is_string($v)) {
            return trim($v) !== '';
        }
        return $v !== null;
    }

    /** @return list<string> */
    public function klice(string $prefix): array
    {
        $v = I18n::get($this->dict, $prefix) ?? I18n::get($this->zaskok, $prefix);
        return is_array($v) ? array_map('strval', array_keys($v)) : [];
    }

    public function datum(string $iso, string $tvar = 'plny'): string
    {
        return Datum::format($this->lang, $iso, $tvar);
    }

    public function asset(string $p): string
    {
        $v = $this->verze[$p] ?? null;
        return $this->prefix() . 'assets/' . $p . ($v !== null ? '?v=' . $v : '');
    }

    public function odkaz(string $druh, ?string $id = null): string
    {
        return Odkazy::soubor($druh, $id, $this->vetev, $this->site);
    }

    /** Administrace je jen v kořeni; z jazykových podadresářů se na ni jde o patro výš. */
    public function odkazKoren(string $jmeno): string
    {
        return $this->prefix() . $jmeno;
    }

    public function odkazVetve(string $vetevId, string $druh = 'vetev'): string
    {
        if ($druh === 'vetev') {
            return Odkazy::soubor('vetev', $vetevId, null, $this->site);
        }
        if ($druh === 'sluzby') {
            return $vetevId . '-sluzby.html';
        }
        if ($druh === 'realizace') {
            return $vetevId . '-realizace.html';
        }
        throw new \InvalidArgumentException("odkazVetve: neznámý druh {$druh}");
    }

    public function jazykOdkaz(string $kod): string
    {
        $cil = $this->jazyk($kod);
        $jmeno = ($this->aktualniSoubor === Odkazy::SOUBORY['administrace'] && $kod !== 'cs')
            ? Odkazy::SOUBORY['index']
            : $this->aktualniSoubor;
        return $this->prefix() . ($cil['adresar'] !== '' ? $cil['adresar'] . '/' : '') . $jmeno;
    }

    /** Doplní do textu vysvětlivky zkratek (první výskyt každé). */
    public function zk(mixed $html): string
    {
        return Slovnik::annotate((string) ($html ?? ''), $this->terminy, ['once' => true]);
    }

    public function skupinyZkratek(): array
    {
        return Slovnik::groupTerms($this->terminy);
    }

    /** @return list<array<string,mixed>> */
    public function sluzbyVetve(string $v): array
    {
        return array_values(array_filter($this->site['sluzby'], static fn ($s) => $s['vetev'] === $v));
    }

    /** @return list<array<string,mixed>> */
    public function realizaceVetve(string $v): array
    {
        return array_values(array_filter($this->site['realizace'], static fn ($r) => $r['vetev'] === $v));
    }

    /** @return list<array<string,mixed>> */
    public function realizaceSeznam(): array
    {
        return $this->vetev !== null ? $this->realizaceVetve($this->vetev) : array_values($this->site['realizace']);
    }

    /** @return list<array<string,mixed>> */
    public function novinkySeznam(): array
    {
        return array_values($this->site['novinky']);
    }

    public function maObrazek(string $jmeno): bool
    {
        return array_key_exists($jmeno, $this->obrazky);
    }

    /** <picture> s WebP a záložním formátem podle manifestu z optimize_images.py */
    public function obrazek(string $jmeno, array $volby = []): string
    {
        $z = $this->obrazky[$jmeno] ?? null;
        if ($z === null) {
            throw new \InvalidArgumentException("Chybí obrázek v manifestu: {$jmeno}");
        }
        $alt = (string) ($volby['alt'] ?? '');
        $sirky = (string) ($volby['sirky'] ?? '100vw');
        $trida = (string) ($volby['trida'] ?? '');
        $prioritni = (bool) ($volby['prioritni'] ?? false);

        $cesta = fn (string $f): string => $this->asset('img/' . $f);
        $srcset = function (string $druh) use ($z, $cesta): string {
            $casti = [];
            foreach ($z['varianty'] as $v) {
                $casti[] = $cesta($v[$druh]) . ' ' . $v['w'] . 'w';
            }
            return implode(', ', $casti);
        };
        $posledni = $z['varianty'][count($z['varianty']) - 1];
        $e = static fn (string $s): string => htmlspecialchars($s, ENT_QUOTES, 'UTF-8');

        return '<picture>
      <source type="image/webp" srcset="' . $srcset('webp') . '" sizes="' . $sirky . '">
      <img src="' . $cesta($posledni['zaloha']) . '" srcset="' . $srcset('zaloha') . '" sizes="' . $sirky . '"
        width="' . $posledni['w'] . '" height="' . $posledni['h'] . '" alt="' . $e($alt) . '" class="' . $e($trida) . '"
        ' . ($prioritni ? 'fetchpriority="high"' : 'loading="lazy"') . ' decoding="async">
    </picture>';
    }

    /** @return array<string,string> */
    public function chybyFormulare(): array
    {
        $out = [];
        foreach ($this->klice('kontakt.formular.chyby') as $k) {
            $out[$k] = $this->t('kontakt.formular.chyby.' . $k);
        }
        return $out;
    }

    /** Kopie kontextu pro jinou stránku (jiný soubor, jiná větev). */
    public function pro(string $aktualniSoubor, ?string $vetev = null, string $aktivni = ''): self
    {
        return new self($this->lang, $vetev, $aktualniSoubor, $aktivni, $this->zdroj, $this->ukazka);
    }
}
