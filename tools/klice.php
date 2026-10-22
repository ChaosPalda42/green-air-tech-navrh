<?php
/* Předgeneruje seznam editovatelných klíčů do web/data/admin-klice.json.
   Patří do instalace i do balíčku — administrace ho pak jen přečte. */

declare(strict_types=1);

$koren = dirname(__DIR__);
require $koren . '/web/app/Jadro/Autoload.php';

use App\Jadro\Administrace;
use App\Obsah\ZdrojJson;

$zdroj = new ZdrojJson($koren . '/web/data', $koren . '/web/public/assets');
$klice = Administrace::spocitejKlice($zdroj);
$cil = $koren . '/web/data/admin-klice.json';
file_put_contents($cil, json_encode($klice, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT));
echo count($klice), " editovatelných klíčů -> web/data/admin-klice.json\n";
