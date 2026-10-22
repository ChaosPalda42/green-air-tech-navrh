<?php
/* Živá zkouška databázové vrstvy. Pouští se v kontejneru (nebo na serveru):
     docker compose exec web php /var/www/greenairtech/../tools/zkouska-db.php
   Nic netiskne kromě počtů a výsledků kontrol. Data jsou vymyšlená. */

declare(strict_types=1);

/* V kontejneru je web připojený jinam než tady, proto se autoload hledá. */
foreach ([dirname(__DIR__) . '/web', '/var/www/greenairtech'] as $koren) {
    if (is_file($koren . '/app/Jadro/Autoload.php')) {
        require $koren . '/app/Jadro/Autoload.php';
        break;
    }
}

use App\Db\Spojeni;
use App\Db\UlozisteDb;

$cesty = [
    getenv('GAT_CONFIG') ?: '',
    dirname(__DIR__) . '/web/config/config.php',
    '/var/www/greenairtech/config/config.php',
];
foreach ($cesty as $c) {
    if ($c !== '' && is_file($c)) {
        App\Jadro\Config::nastav(require $c);
        break;
    }
}

$kontroly = [];
$zkus = static function (string $jmeno, callable $co) use (&$kontroly): void {
    try {
        $kontroly[$jmeno] = $co() === true ? 'ok' : 'NESOUHLASÍ';
    } catch (\Throwable $e) {
        $kontroly[$jmeno] = 'SPADLO: ' . get_class($e) . ': ' . $e->getMessage();
    }
};

$zkus('spojeni', static fn (): bool => Spojeni::dej() instanceof PDO);
$zkus('migrace', static function (): bool {
    Spojeni::migruj();
    return Spojeni::pripraveno();
});
$zkus('migrace_jde_znovu', static function (): bool {
    Spojeni::migruj();
    return Spojeni::pripraveno();
});

$u = new UlozisteDb(Spojeni::dej());

$zkus('prazdny_stav', static fn (): bool => is_array($u->stav()));
$zkus('ulozeni_stavu', static function () use ($u): bool {
    $u->ulozStav(['texts' => ['cs' => ['nav.sluzby' => 'Co umíme']], 'realizace' => ['added' => [], 'edited' => [], 'removed' => []]], 'zkouska');
    return $u->stav()['texts']['cs']['nav.sluzby'] === 'Co umíme';
});
$zkus('diakritika_prezila', static function () use ($u): bool {
    $u->ulozStav(['texts' => ['cs' => ['x' => 'Řeřicha ťuká ÚŽASNĚ']], 'realizace' => []], 'zkouska');
    return $u->stav()['texts']['cs']['x'] === 'Řeřicha ťuká ÚŽASNĚ';
});
$zkus('historie_roste', static function () use ($u): bool {
    $pdo = Spojeni::dej();
    $pred = (int) $pdo->query('SELECT COUNT(*) FROM stav_historie')->fetchColumn();
    $u->ulozStav(['texts' => [], 'realizace' => []], 'zkouska');
    return (int) $pdo->query('SELECT COUNT(*) FROM stav_historie')->fetchColumn() === $pred + 1;
});

$email = 'zkouska-' . bin2hex(random_bytes(4)) . '@priklad.test';
$id = 0;
$zkus('zalozeni_uzivatele', static function () use ($u, $email, &$id): bool {
    $novy = $u->ulozUzivatele([
        'jmeno' => 'Zkušební Člověk', 'email' => $email, 'role' => 'editor',
        'heslo_hash' => password_hash('zkouska-heslo-123', PASSWORD_DEFAULT),
    ]);
    $id = (int) $novy['id'];
    return $id > 0 && !array_key_exists('heslo_hash', $novy);
});
$zkus('prihlaseni_overi_heslo', static function () use ($u, $email): bool {
    $radek = $u->uzivatelPodleJmena($email);
    return $radek !== null && password_verify('zkouska-heslo-123', (string) $radek['heslo_hash']);
});
$zkus('seznam_je_bez_hesel', static function () use ($u): bool {
    foreach ($u->uzivatele() as $radek) {
        if (array_key_exists('heslo_hash', $radek)) {
            return false;
        }
    }
    return true;
});
$zkus('zmena_role', static function () use ($u, $id): bool {
    $u->ulozUzivatele(['id' => $id, 'role' => 'autor']);
    return $u->podleId($id)['role'] === 'autor';
});
$zkus('smazani', static function () use ($u, $id): bool {
    $u->smazUzivatele($id);
    return $u->podleId($id) === null;
});
$zkus('poptavka', static function () use ($u): bool {
    $cislo = $u->ulozPoptavku([
        'typ' => 'projekce', 'jmeno' => 'Vymyšlená Osoba', 'email' => 'nikdo@priklad.test',
        'zprava' => "Více\nřádků", 'vetev' => 'firmy', 'jazyk' => 'cs',
    ], false);
    return $cislo > 0;
});
$zkus('udalost', static function () use ($u): bool {
    $u->zapisUdalost('zkouska', 'prihlaseni', 'zkouška');
    return (int) Spojeni::dej()->query('SELECT COUNT(*) FROM udalosti')->fetchColumn() > 0;
});

$spatne = 0;
foreach ($kontroly as $jmeno => $vysledek) {
    if ($vysledek !== 'ok') {
        $spatne++;
    }
    printf("%-24s %s\n", $jmeno, $vysledek);
}
printf("\n%d kontrol, %d špatně\n", count($kontroly), $spatne);
exit($spatne === 0 ? 0 : 1);
