<?php
/* Obsah ostrého webu: výchozí hodnoty ze souborů (ZdrojJson) přelepené stavem
   administrace. Co administrace nepřepsala, zůstává přesně tak, jak je ve
   souborech — na tom stojí shoda ostrého webu s ukázkou. */

declare(strict_types=1);

namespace App\Obsah;

class ZdrojDb extends ZdrojJson
{
    /** Stav administrace, jak přišel. */
    private array $stav;

    public function __construct(
        string $dataDir,
        string $assetsDir,
        array $stav = [],
    ) {
        parent::__construct($dataDir, $assetsDir);
        $this->stav = $stav;
    }

    /** Vrátí stav administrace tak, jak přišel. */
    public function stav(): array
    {
        return $this->stav;
    }

    /** Překlady jednoho jazyka: soubor přelepený přepsanými texty. */
    public function dict(string $jazyk): array
    {
        $vychozi = I18n::flatten(parent::dict($jazyk));
        $spojene = Stav::spojTexty($this->stav, $jazyk, $vychozi);

        return I18n::unflatten($spojene);
    }

    /** Struktura webu: realizace a výřezy portrétů se změnami administrace, zbytek ze souborů. */
    public function site(): array
    {
        $site = parent::site();
        $zaklad = is_array($site['realizace'] ?? null) ? $site['realizace'] : [];
        foreach ($zaklad as $i => $polozka) {
            if (is_array($polozka) && !array_key_exists('nazev', $polozka)) {
                $zaklad[$i]['nazev'] = (string) ($polozka['nazev-cs'] ?? $polozka['nazev-en'] ?? $polozka['id'] ?? '');
            }
        }
        $site['realizace'] = StavRealizace::spojRealizace($this->stav, $zaklad);

        /* Výřez portrétu si správce nastavuje v administraci, takže ho musí
           přelepit stejně jako texty — jinak by se posun fotky projevil až
           dalším nasazením dat. */
        if (is_array($site['lide'] ?? null)) {
            $site['lide'] = StavVyrezu::spojVyrezy($this->stav, $site['lide']);
        }

        return $site;
    }
}
