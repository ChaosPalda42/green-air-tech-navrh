<?php
/* Obsah ze souborů: přesně to, co čte generátor ukázky. Na ostrém webu
   slouží jako výchozí hodnoty — co administrace nepřepsala, platí odtud. */

declare(strict_types=1);

namespace App\Obsah;

class ZdrojJson implements Zdroj
{
    private array $cache = [];

    public function __construct(
        protected readonly string $dataDir,
        protected readonly string $assetsDir,
    ) {
    }

    protected function json(string $jmeno): array
    {
        if (!array_key_exists($jmeno, $this->cache)) {
            $cesta = $this->dataDir . '/' . $jmeno;
            if (!is_file($cesta)) {
                throw new \RuntimeException("Chybí datový soubor: {$jmeno}");
            }
            $data = json_decode((string) file_get_contents($cesta), true, 512, JSON_THROW_ON_ERROR);
            $this->cache[$jmeno] = is_array($data) ? $data : [];
        }
        return $this->cache[$jmeno];
    }

    public function site(): array
    {
        return $this->json('site.json');
    }

    public function dict(string $jazyk): array
    {
        return $this->json('content/' . $jazyk . '.json');
    }

    public function slovnik(string $jazyk): array
    {
        $vlastni = $this->dict($jazyk)['slovnik']['terminy'] ?? null;
        if (!is_array($vlastni) || $vlastni === []) {
            $vlastni = $this->dict('cs')['slovnik']['terminy'] ?? [];
        }
        $navic = $this->json('content/zkratky-navic.json')[$jazyk] ?? [];
        return array_merge($vlastni, is_array($navic) ? $navic : []);
    }

    public function obrazky(): array
    {
        return $this->json('obrazky.json');
    }

    public function verzeAktiv(): array
    {
        $verze = [];
        foreach (['style.css', 'admin.css', 'app.js', 'admin.js'] as $jmeno) {
            $cesta = $this->assetsDir . '/' . $jmeno;
            if (is_file($cesta)) {
                $verze[$jmeno] = substr(sha1_file($cesta) ?: '', 0, 8);
            }
        }

        /* Obrázky verzi v názvu nenesou a .htaccess je posílá jako
           „immutable" — bez `?v=` by prohlížeč, který si starou fotku stáhl,
           novou na témže jméně celý rok nevyžádal. Otisky variant nese
           manifest z tools/optimize_images.py, takže se jen přečtou; zbytek
           složky (logo, odznak, favicon, og) jsou čtyři soubory a spočítají
           se tady. Totéž dělá build.mjs nad svou kopií týchž souborů —
           proto otisk obsahu, ne čas změny. */
        $varianty = [];
        foreach ($this->obrazky() as $zaznam) {
            foreach ($zaznam['varianty'] ?? [] as $v) {
                foreach (['webp', 'zaloha'] as $druh) {
                    if (isset($v[$druh], $v['verze'][$druh])) {
                        $verze['img/' . $v[$druh]] = (string) $v['verze'][$druh];
                        $varianty[$v[$druh]] = true;
                    }
                }
            }
        }
        foreach (glob($this->assetsDir . '/img/*') ?: [] as $cesta) {
            $jmeno = basename($cesta);
            if (!isset($varianty[$jmeno]) && is_file($cesta)) {
                $verze['img/' . $jmeno] = substr(sha1_file($cesta) ?: '', 0, 8);
            }
        }

        return $verze;
    }
}
