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

    'analytics' => [
        // ID měřicího streamu GA4, např. G-XXXXXXXXXX — vkládá se do stránek
        'mereni' => '',
        // číslo property (jen číslice) — odtud se čtou statistiky
        'property' => '',
        // cesta ke klíči servisního účtu (JSON), MIMO dokumentový koren
        'klic' => '',
    ],
];
