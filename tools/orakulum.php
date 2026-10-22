<?php
/* Spustí PHP implementaci na vzorcích z tests/orakulum/<jmeno>.json a vypíše
   výsledky jako JSON. Porovnání dělá pytest; tento skript nic nehodnotí.
   Není součástí balíčku pro klienta — je to jen měřidlo. */

declare(strict_types=1);

require __DIR__ . '/../web/app/Jadro/Autoload.php';

$jmeno = $argv[1] ?? '';
$cesta = __DIR__ . '/../tests/orakulum/' . $jmeno . '.json';
if (!is_file($cesta)) {
    fwrite(STDERR, "neznámé orákulum: {$jmeno}\n");
    exit(2);
}

/** Kam která skupina vzorků patří. */
const CILE = [
    'i18n' => [
        'get' => ['App\\Obsah\\I18n', 'get'],
        't' => ['App\\Obsah\\I18n', 't'],
        'flatten' => ['App\\Obsah\\I18n', 'flatten'],
        'unflatten' => ['App\\Obsah\\I18n', 'unflatten'],
        'missingKeys' => ['App\\Obsah\\I18n', 'missingKeys'],
    ],
    'razeni-cs' => [
        'porovnej' => ['App\\Obsah\\RazeniCs', 'porovnej'],
        'seradit' => ['App\\Obsah\\RazeniCs', 'seradit'],
    ],
    'slovnik' => [
        'annotate' => ['App\\Obsah\\Slovnik', 'annotate'],
        'findTerm' => ['App\\Obsah\\Slovnik', 'findTerm'],
        'sortTerms' => ['App\\Obsah\\Slovnik', 'sortTerms'],
        'groupTerms' => ['App\\Obsah\\Slovnik', 'groupTerms'],
    ],
    'realizace-filtr' => [
        'normalizeText' => ['App\\Obsah\\RealizaceFiltr', 'normalizeText'],
        'filterItems' => ['App\\Obsah\\RealizaceFiltr', 'filterItems'],
        'collectKategorie' => ['App\\Obsah\\RealizaceFiltr', 'collectKategorie'],
        'collectRoky' => ['App\\Obsah\\RealizaceFiltr', 'collectRoky'],
        'sortItems' => ['App\\Obsah\\RealizaceFiltr', 'sortItems'],
        'paginate' => ['App\\Obsah\\RealizaceFiltr', 'paginate'],
    ],
    'formular' => [
        'isEmail' => ['App\\Formular\\Validace', 'isEmail'],
        'normalizePhone' => ['App\\Formular\\Validace', 'normalizePhone'],
        'isPhoneCz' => ['App\\Formular\\Validace', 'isPhoneCz'],
        'validateContact' => ['App\\Formular\\Validace', 'validateContact'],
    ],
    'datum' => [
        'format' => ['App\\Obsah\\Datum', 'format'],
    ],
    'cms-store' => [
        'emptyState' => ['App\\Obsah\\Stav', 'prazdny'],
        'slugify' => ['App\\Obsah\\Stav', 'slug'],
        'setText' => ['App\\Obsah\\Stav', 'nastavText'],
        'getText' => ['App\\Obsah\\Stav', 'text'],
        'mergeTexts' => ['App\\Obsah\\Stav', 'spojTexty'],
        'upsertRealizace' => ['App\\Obsah\\StavRealizace', 'ulozRealizaci'],
        'removeRealizace' => ['App\\Obsah\\StavRealizace', 'smazRealizaci'],
        'mergeRealizace' => ['App\\Obsah\\StavRealizace', 'spojRealizace'],
        'importJson' => ['App\\Obsah\\Stav', 'zJson'],
    ],
    'ga4' => [
        'dny' => ['App\\Statistiky\\Ga4Prevod', 'dny'],
        'rozpad' => ['App\\Statistiky\\Ga4Prevod', 'rozpad'],
    ],
    'grafika' => [
        'ikona' => ['App\\Sablony\\Ikony', 'ikona'],
        'motivRealizace' => ['App\\Sablony\\Grafika', 'motivRealizace'],
        'heroSchema' => ['App\\Sablony\\Grafika', 'heroSchema'],
    ],
];

$ZNACKA_UNDEF = "\0undefined";
$vzorky = json_decode((string) file_get_contents($cesta), true, 512, JSON_THROW_ON_ERROR);
$vystup = [];

foreach ($vzorky as $funkce => $pripady) {
    $cil = CILE[$jmeno][$funkce] ?? null;
    $vystup[$funkce] = [];
    foreach ($pripady as $i => $pripad) {
        if ($cil === null || !class_exists($cil[0]) || !method_exists($cil[0], $cil[1])) {
            $vystup[$funkce][] = ['chyba' => 'chybí implementace ' . ($cil[0] ?? '?') . '::' . ($cil[1] ?? $funkce)];
            continue;
        }
        $args = array_map(
            static fn ($a) => $a === $ZNACKA_UNDEF ? null : $a,
            $pripad['args']
        );
        try {
            $vystup[$funkce][] = ['out' => $cil(...$args)];
        } catch (\Throwable $e) {
            $vystup[$funkce][] = ['chyba' => get_class($e) . ': ' . $e->getMessage()];
        }
    }
}

echo json_encode($vystup, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR), "\n";
