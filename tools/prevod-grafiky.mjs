/* Z ukázky vytáhne to, co je čistá dekorace nezávislá na obsahu, a zapíše to
   do PHP jako data. Ikony jsou tabulka cest, motivy a hero schéma hotové SVG.
   Důvod: v PHP by se to muselo počítat znovu (Math.cos, toFixed) a bajtová
   shoda s ukázkou by závisela na zaokrouhlování. Takhle je zaručená. */

import { writeFile } from "node:fs/promises";
import { ikona, nazvyIkon } from "../src/templates/ikony.mjs";
import { motivRealizace } from "../src/templates/motivy.mjs";
import { heroSchema } from "../src/templates/grafika.mjs";

const SENTINEL = "\u0001POPIS\u0001";

/** PHP literál v apostrofech (uvnitř se escapuje jen \ a '). */
const php = (s) => "'" + String(s).replace(/\\/g, "\\\\").replace(/'/g, "\\'") + "'";

/* ---------------------------------------------------------------- ikony */
// Z hotové ikony vytáhneme jen tu část, která se mezi ikonami liší.
const SKORAPKA = ikona("sip", { trida: "T", velikost: 9, popis: SENTINEL });
const cesty = {};
for (const n of nazvyIkon) {
  const cele = ikona(n, {});
  const m = cele.match(/stroke-linejoin="round">([\s\S]*)<\/svg>$/);
  if (!m) throw new Error(`ikona ${n}: nerozpoznaná skořápka`);
  cesty[n] = m[1];
}

const ikonyPhp = `<?php
/* Sada SVG ikon. Vše 24×24, tah 1.8, dědí currentColor.

   VYGENEROVÁNO z src/templates/ikony.mjs skriptem tools/prevod-grafiky.mjs.
   Needitovat ručně — změna se dělá v ukázce a převod se spustí znovu,
   aby ostrý web a ukázka nikdy nevypadaly jinak. */

declare(strict_types=1);

namespace App\\Sablony;

final class Ikony
{
    /** @var array<string,string> cesty uvnitř <svg> */
    private const CESTY = [
${Object.entries(cesty).map(([n, c]) => `        ${php(n)} => ${php(c)},`).join("\n")}
    ];

    /** Jedna ikona. Neznámé jméno je chyba v šabloně, ne vstup od uživatele. */
    public static function ikona(string $nazev, array $volby = []): string
    {
        $cesta = self::CESTY[$nazev] ?? null;
        if ($cesta === null) {
            throw new \\InvalidArgumentException("Neznámá ikona: {$nazev}");
        }
        $trida = (string) ($volby['trida'] ?? '');
        $velikost = $volby['velikost'] ?? 24;
        $popis = (string) ($volby['popis'] ?? '');
        $a11y = $popis !== ''
            ? 'role="img" aria-label="' . htmlspecialchars($popis, ENT_QUOTES, 'UTF-8') . '"'
            : 'aria-hidden="true" focusable="false"';

        return '<svg ' . $a11y . ' class="' . htmlspecialchars($trida, ENT_QUOTES, 'UTF-8') . '"'
            . ' width="' . $velikost . '" height="' . $velikost . '" viewBox="0 0 24 24" '
            . 'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            . 'stroke-linejoin="round">' . $cesta . '</svg>';
    }

    /** @return list<string> */
    public static function nazvy(): array
    {
        return array_keys(self::CESTY);
    }
}
`;

/* --------------------------------------------------------------- motivy */
const motivy = [];
for (let i = 1; i <= 8; i++) {
  const svg = motivRealizace(i, { popis: SENTINEL });
  const sPlaceholderem = svg.replace(`role="img" aria-label="${SENTINEL}"`, "%A11Y%");
  if (sPlaceholderem === svg) throw new Error(`motiv ${i}: nenašel jsem místo pro popis`);
  motivy.push(sPlaceholderem);
}
// kontrola, že osmi motivy je množina vyčerpaná a devátý je zase první
if (motivRealizace(9, {}) !== motivRealizace(1, {})) {
  throw new Error("motivů není osm — převod je potřeba upravit");
}

const grafikaPhp = `<?php
/* Technická grafika místo stockových fotek: schéma pod hero obrázkem a osm
   náhledů realizací.

   VYGENEROVÁNO z src/templates/motivy.mjs a grafika.mjs skriptem
   tools/prevod-grafiky.mjs. Je to dekorace, která nezávisí na obsahu — proto
   se nepočítá znovu v PHP, ale přenáší se hotová. Needitovat ručně. */

declare(strict_types=1);

namespace App\\Sablony;

final class Grafika
{
    private const HERO = ${php(heroSchema())};

    /** @var list<string> osm schémat; %A11Y% je místo pro přístupnostní atributy */
    private const MOTIVY = [
${motivy.map((m) => `        ${php(m)},`).join("\n")}
    ];

    public static function heroSchema(): string
    {
        return self::HERO;
    }

    /** Náhled realizace. Číslo motivu se cyklicky zarovná do rozsahu 1..8. */
    public static function motivRealizace(mixed $motiv = 1, array $volby = []): string
    {
        $cislo = (int) round(is_numeric($motiv) ? (float) $motiv : 1);
        $cislo = ((max(1, $cislo) - 1) % count(self::MOTIVY)) + 1;
        $popis = (string) ($volby['popis'] ?? '');
        $a11y = $popis !== ''
            ? 'role="img" aria-label="' . htmlspecialchars($popis, ENT_QUOTES, 'UTF-8') . '"'
            : 'aria-hidden="true" focusable="false"';

        return str_replace('%A11Y%', $a11y, self::MOTIVY[$cislo - 1]);
    }
}
`;

await writeFile(new URL("../web/app/Sablony/Ikony.php", import.meta.url), ikonyPhp);
await writeFile(new URL("../web/app/Sablony/Grafika.php", import.meta.url), grafikaPhp);
console.log(`Ikony.php: ${nazvyIkon.length} ikon`);
console.log(`Grafika.php: hero schéma + ${motivy.length} motivů`);
