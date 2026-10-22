<?php
/* Konfigurace testovacího běhu v Dockeru. Na klientově serveru vzniká
   obdobný soubor při instalaci z web/config/config.vzor.php. */

declare(strict_types=1);

return [
    'ukazka' => false,
    'databaze' => [
        'host' => 'databaze',
        'port' => 3306,
        'jmeno' => 'greenairtech',
        'uzivatel' => 'greenairtech',
        'heslo' => 'heslo-jen-pro-test',
    ],
    'web' => 'http://localhost:8080',
    'posta' => [
        'prijemce' => 'poptavky@greenairtech.test',
        'odesilatel' => 'web@greenairtech.test',
        'zpusob' => 'log',
        'smtp' => ['host' => '', 'port' => 587, 'uzivatel' => '', 'heslo' => '', 'zabezpeceni' => 'tls'],
    ],
    'analytics' => ['mereni' => '', 'property' => '', 'klic' => ''],
];
