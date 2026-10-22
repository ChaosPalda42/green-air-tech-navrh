<?php
/* Jmenný prostor App\ -> web/app/. Žádný composer: klient dostane balíček,
   který se jen rozbalí, a na serveru nemusí nic instalovat. */

declare(strict_types=1);

spl_autoload_register(static function (string $trida): void {
    if (!str_starts_with($trida, 'App\\')) {
        return;
    }
    $cesta = __DIR__ . '/../' . str_replace('\\', '/', substr($trida, 4)) . '.php';
    if (is_file($cesta)) {
        // require_once: kdyby soubor deklaroval jiné jméno třídy, než se hledá,
        // autoloader by se zavolal znovu a `require` by skončil fatálem
        // „Cannot redeclare". Takhle padne jasné „Class not found".
        require_once $cesta;
    }
});
