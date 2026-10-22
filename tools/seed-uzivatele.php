<?php
/* Založí testovací účty z nasazeni/seed-uzivatele.json. Jen pro zkušební
   nasazení — v balíčku pro klienta tohle nahradí instalátor, který se na
   první účet zeptá. Hesla se nikam nevypisují, tiskne se jen jméno a role. */

declare(strict_types=1);

foreach ([dirname(__DIR__) . '/web', '/var/www/greenairtech'] as $koren) {
    if (is_file($koren . '/app/Jadro/Autoload.php')) {
        require $koren . '/app/Jadro/Autoload.php';
        break;
    }
}

use App\Auth\Uzivatele;
use App\Db\Spojeni;
use App\Db\UlozisteDb;

$cesty = [dirname(__DIR__) . '/nasazeni/seed-uzivatele.json', '/var/www/seed-uzivatele.json'];
$soubor = null;
foreach ($cesty as $c) {
    if (is_file($c)) { $soubor = $c; break; }
}
if ($soubor === null) {
    fwrite(STDERR, "seed-uzivatele.json nenalezen\n");
    exit(2);
}

$seed = json_decode((string) file_get_contents($soubor), true);
Spojeni::migruj();
$uloziste = new UlozisteDb(Spojeni::dej());

$zalozeno = 0;
$preskoceno = 0;
foreach ($seed['uzivatele'] ?? [] as $u) {
    if ($uloziste->uzivatelPodleJmena($u['jmeno']) !== null) {
        echo "- {$u['jmeno']} ({$u['role']}): už existuje\n";
        $preskoceno++;
        continue;
    }
    $uloziste->ulozUzivatele([
        'jmeno' => $u['jmeno'],
        'email' => $u['email'],
        'role' => $u['role'],
        'heslo_hash' => Uzivatele::hash($u['heslo']),
        'aktivni' => 1,
    ]);
    echo "- {$u['jmeno']} ({$u['role']}): založen\n";
    $zalozeno++;
}
echo "založeno {$zalozeno}, přeskočeno {$preskoceno}\n";
