<?php
/* VZOR nastavení. Instalátor z něj udělá config/config.php a doplní údaje.
   Tenhle soubor se nikdy nepoužívá přímo — je jen předloha. */

return [
    // false = ostrý web (indexuje se, bez demo cedulek)
    'ukazka' => false,

    'databaze' => [
        'host' => 'localhost',
        'port' => 3306,
        'jmeno' => 'greenairtech',
        'uzivatel' => 'greenairtech',
        'heslo' => '',
    ],

    // Adresa webu bez lomítka na konci — do sitemap.xml a odkazů v e-mailech
    'web' => 'https://www.greenairtech.cz',

    'posta' => [
        // kam chodí poptávky z formuláře
        'prijemce' => 'info@greenairtech.cz',
        // odesílatel: musí být na vlastní doméně, jinak to skončí ve spamu
        'odesilatel' => 'web@greenairtech.cz',
        // 'mail' (funkce mail()) nebo 'smtp'
        'zpusob' => 'mail',
        'smtp' => ['host' => '', 'port' => 587, 'uzivatel' => '', 'heslo' => '', 'zabezpeceni' => 'tls'],
    ],

    /* Adresa návštěvníka. Strop poptávek a zámek administrace potřebují
       vědět, odkud požadavek přišel. Hlavičkám (X-Forwarded-For,
       CF-Connecting-IP) se věří JEN tehdy, když to tady povolíte — jinak by
       si kdokoli ke každé zprávě vymyslel jinou adresu a strop obešel.
         'verit'  => true jen když před webem opravdu stojí proxy nebo
                     Cloudflare; při přímém běhu na Apache nechte false.
         'adresy' => (nepovinné) adresy nebo sítě té proxy, například
                     ['10.0.0.5', '172.16.0.0/12', '2001:db8::/32'].
                     Prázdný seznam = věřit hlavičce od kohokoli. */
    'proxy' => [
        'verit' => false,
        'adresy' => [],
    ],

    'analytics' => [
        // ID měřicího streamu GA4, např. G-XXXXXXXXXX — vkládá se do stránek
        'mereni' => '',
        // číslo property (jen číslice) — odtud se čtou statistiky
        'property' => '',
        // cesta ke klíči servisního účtu (JSON), MIMO dokumentový koren
        'klic' => '',
    ],
];
