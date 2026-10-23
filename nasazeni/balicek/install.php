<?php
/* Průvodce nasazením. Leží v dokumentovém korenu, po instalaci se SMAŽE.
   Nic nepředpokládá: zkontroluje PHP, zapíše config, založí tabulky a
   prvního správce. Když už je web nastavený, odmítne cokoli měnit. */

declare(strict_types=1);

$koren = dirname(__DIR__);                 // …/web
require $koren . '/app/Jadro/Autoload.php';

use App\Auth\Uzivatele;
use App\Db\Spojeni;
use App\Db\UlozisteDb;

const POTREBA = ['pdo_mysql', 'gd', 'json', 'mbstring' => false];
$configSoubor = $koren . '/config/config.php';

session_start();
if (empty($_SESSION['instalator_csrf'])) {
    $_SESSION['instalator_csrf'] = bin2hex(random_bytes(32));
}
$csrf = $_SESSION['instalator_csrf'];

/* ---------------------------------------------------------- prostředí */
$kontroly = [];
$kontroly[] = ['PHP 8.2 nebo novější (' . PHP_VERSION . ')', version_compare(PHP_VERSION, '8.2.0', '>='), 'php8.5 php8.5-mysql php8.5-gd'];
$kontroly[] = ['rozšíření pdo_mysql', extension_loaded('pdo_mysql'), 'apt install php8.5-mysql'];
$kontroly[] = ['rozšíření gd (zmenšování fotek)', extension_loaded('gd'), 'apt install php8.5-gd'];
$kontroly[] = ['složka config je zapisovatelná', is_dir($koren . '/config') && is_writable($koren . '/config'), 'chown www-data ' . $koren . '/config'];
$kontroly[] = ['složka media je zapisovatelná', is_dir(__DIR__ . '/media') ? is_writable(__DIR__ . '/media') : is_writable(__DIR__), 'chown -R www-data:www-data ' . __DIR__ . '/media'];
$kontroly[] = ['složka cache je zapisovatelná (statistiky)', is_dir($koren . '/cache') ? is_writable($koren . '/cache') : is_writable($koren), 'chown -R www-data:www-data ' . $koren . '/cache'];
$kontroly[] = ['přepisy adres (mod_rewrite)', !function_exists('apache_get_modules') || in_array('mod_rewrite', apache_get_modules(), true), 'a2enmod rewrite'];
$prostrediOk = array_reduce($kontroly, static fn (bool $n, array $k): bool => $n && $k[1], true);

/* ------------------------------------------------- už je nainstalováno? */
/* Rozhoduje JEN existence config.php. Ptát se na to databáze by znamenalo,
   že při spadlé databázi (restart, plný disk) instalátor zase nabídne
   formulář — a kdokoli zvenčí by si tím přepsal nastavení a založil si
   vlastního správce. */
$hotovo = is_file($configSoubor);

/* ------------------------------------------------------------- zápis */
$chyby = [];
$uspech = false;
$smazano = false;
$sitemap = '';
$udaje = [
    'db_host' => 'localhost', 'db_port' => '3306',
    'db_jmeno' => 'greenairtech', 'db_uzivatel' => 'greenairtech',
    'web' => 'https://' . ($_SERVER['HTTP_HOST'] ?? 'www.greenairtech.cz'),
    'posta_prijemce' => '', 'posta_odesilatel' => '',
    /* Statistiky chodí z vlastnosti Green Air Tech v Analytics, klíč
       servisního účtu je v balíčku (config/ga4.json). Kdo chce měřit do
       svého, přepíše obě pole a klíč vymění. */
    'ga_mereni' => 'G-WJG99S0K3V', 'ga_property' => '560454014',
    'spravce_jmeno' => '', 'spravce_email' => '',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$hotovo) {
    if (!hash_equals($csrf, (string) ($_POST['csrf'] ?? ''))) {
        $chyby[] = 'Formulář vypršel, zkuste to znovu.';
    } else {
        foreach (array_keys($udaje) as $k) {
            $udaje[$k] = trim((string) ($_POST[$k] ?? ''));
        }
        $dbHeslo = (string) ($_POST['db_heslo'] ?? '');
        $spravceHeslo = (string) ($_POST['spravce_heslo'] ?? '');

        foreach (['db_host' => 'adresa databáze', 'db_jmeno' => 'název databáze', 'db_uzivatel' => 'uživatel databáze',
                  'web' => 'adresu webu', 'posta_prijemce' => 'e-mail pro poptávky',
                  'spravce_jmeno' => 'jméno správce', 'spravce_email' => 'e-mail správce'] as $k => $popis) {
            if ($udaje[$k] === '') {
                $chyby[] = "Vyplňte {$popis}.";
            }
        }
        if (!filter_var($udaje['posta_prijemce'], FILTER_VALIDATE_EMAIL)) {
            $chyby[] = 'E-mail pro poptávky nemá správný tvar.';
        }
        if ($udaje['ga_mereni'] !== '' && !preg_match('/^G-[A-Z0-9]{6,}$/', $udaje['ga_mereni'])) {
            $chyby[] = 'ID měření má tvar G-XXXXXXXXXX.';
        }
        if ($udaje['ga_property'] !== '' && !preg_match('/^[0-9]{6,}$/', $udaje['ga_property'])) {
            $chyby[] = 'Číslo property jsou jen číslice.';
        }
        if (!filter_var($udaje['spravce_email'], FILTER_VALIDATE_EMAIL)) {
            $chyby[] = 'E-mail správce nemá správný tvar.';
        }
        if (Uzivatele::zkontrolujHeslo($spravceHeslo) !== null) {
            $chyby[] = 'Heslo správce je krátké — dejte aspoň 12 znaků.';
        }

        if ($chyby === []) {
            try {
                $pdo = new PDO(
                    "mysql:host={$udaje['db_host']};port={$udaje['db_port']};dbname={$udaje['db_jmeno']};charset=utf8mb4",
                    $udaje['db_uzivatel'],
                    $dbHeslo,
                    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_EMULATE_PREPARES => false]
                );
            } catch (\Throwable $e) {
                $pdo = null;
                $chyby[] = 'K databázi se nepovedlo připojit. Zkontrolujte jméno, heslo a název databáze.';
            }

            if ($chyby === [] && $pdo !== null) {
                $v = static fn (mixed $x): string => var_export($x, true);
                /* Klíč se do nastavení zapíše, jen když tam opravdu leží —
                   cesta k souboru, který není, by nástěnku tiše vypnula. */
                $klicGa4 = is_file($koren . '/config/ga4.json') ? $koren . '/config/ga4.json' : '';
                if ($klicGa4 !== '') {
                    @chmod($klicGa4, 0o640);
                }
                $odesilatel = $udaje['posta_odesilatel'] !== ''
                    ? $udaje['posta_odesilatel']
                    : 'web@' . (parse_url($udaje['web'], PHP_URL_HOST) ?? 'localhost');
                $config = "<?php\n"
                    . "/* Nastaveni webu Green Air Tech. Vytvoril install.php " . date('j. n. Y H:i') . ". */\n\n"
                    . "return [\n"
                    . "    'ukazka' => false,\n\n"
                    . "    'databaze' => [\n"
                    . "        'host' => " . $v($udaje['db_host']) . ",\n"
                    . "        'port' => " . $v((int) ($udaje['db_port'] !== '' ? $udaje['db_port'] : 3306)) . ",\n"
                    . "        'jmeno' => " . $v($udaje['db_jmeno']) . ",\n"
                    . "        'uzivatel' => " . $v($udaje['db_uzivatel']) . ",\n"
                    . "        'heslo' => " . $v($dbHeslo) . ",\n"
                    . "    ],\n\n"
                    . "    'web' => " . $v(rtrim($udaje['web'], '/')) . ",\n\n"
                    . "    'posta' => [\n"
                    . "        'prijemce' => " . $v($udaje['posta_prijemce']) . ",\n"
                    . "        'odesilatel' => " . $v($odesilatel) . ",\n"
                    . "        'zpusob' => 'mail',\n"
                    . "        'smtp' => ['host' => '', 'port' => 587, 'uzivatel' => '', 'heslo' => '', 'zabezpeceni' => 'tls'],\n"
                    . "    ],\n\n"
                    . "    'analytics' => [\n"
                    . "        'mereni' => " . $v($udaje['ga_mereni']) . ",\n"
                    . "        'property' => " . $v($udaje['ga_property']) . ",\n"
                    . "        'klic' => " . $v($klicGa4 !== '' ? $klicGa4 : '') . ",\n"
                    . "    ],\n"
                    . "];\n";

                if (@file_put_contents($configSoubor, $config) === false) {
                    $chyby[] = 'Nastavení se nepovedlo zapsat do ' . $configSoubor . '.';
                } else {
                    @chmod($configSoubor, 0o640);
                    try {
                        Spojeni::nastav($pdo);
                        Spojeni::migruj();
                        $uloziste = new UlozisteDb($pdo);
                        $uloziste->ulozUzivatele([
                            'jmeno' => $udaje['spravce_jmeno'],
                            'email' => $udaje['spravce_email'],
                            'role' => 'spravce',
                            'heslo_hash' => Uzivatele::hash($spravceHeslo),
                            'aktivni' => 1,
                        ]);
                        $uspech = true;
                        /* sitemap.xml ani robots.txt se nezapisují: vydává je
                           web sám, takže o nové realizaci vědí hned. */
                        $sitemap = 'sitemap.xml a robots.txt web vydává sám pro doménu '
                            . htmlspecialchars(rtrim($udaje['web'], '/'), ENT_QUOTES, 'UTF-8') . '.';
                        /* Smazat se musí, ne jen připomenout: v kořeni by
                           dál stál soubor, který umí přepsat nastavení. */
                        $smazano = @unlink(__FILE__);
                    } catch (\Throwable $e) {
                        $chyby[] = 'Tabulky se nepovedlo založit: ' . $e->getMessage();
                    }
                }
            }
        }
    }
}

$a = static fn (string $t): string => htmlspecialchars($t, ENT_QUOTES, 'UTF-8');
?>
<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Green Air Tech — nasazení</title>
<style>
  :root { color-scheme: light dark; --zelena: #2f7d4f; --papir: #fbfdfb; --text: #16211a; }
  @media (prefers-color-scheme: dark) { :root { --papir: #101713; --text: #e8f0ea; } }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 2rem 1rem 4rem; background: var(--papir); color: var(--text);
         font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
  main { max-width: 44rem; margin-inline: auto; }
  h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
  h2 { font-size: 1.1rem; margin: 2rem 0 .5rem; }
  p.lead { opacity: .75; margin-top: 0; }
  ul { list-style: none; padding: 0; }
  li { padding: .35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--text) 12%, transparent); }
  li b { font-weight: 600; }
  .ok::before { content: "✓ "; color: var(--zelena); font-weight: 700; }
  .ne::before { content: "✗ "; color: #c0392b; font-weight: 700; }
  code { background: color-mix(in srgb, var(--text) 8%, transparent); padding: .1rem .35rem; border-radius: .25rem; }
  label { display: block; margin: .75rem 0 .2rem; font-weight: 600; font-size: .92rem; }
  input { width: 100%; padding: .55rem .7rem; border: 1px solid color-mix(in srgb, var(--text) 25%, transparent);
          border-radius: .4rem; background: transparent; color: inherit; font: inherit; }
  .dvojice { display: grid; gap: 0 1rem; grid-template-columns: 1fr 1fr; }
  @media (max-width: 34rem) { .dvojice { grid-template-columns: 1fr; } }
  button { margin-top: 1.5rem; padding: .7rem 1.4rem; border: 0; border-radius: .4rem;
           background: var(--zelena); color: #fff; font: inherit; font-weight: 600; cursor: pointer; }
  .hlaska { padding: .8rem 1rem; border-radius: .4rem; margin: 1rem 0;
            background: color-mix(in srgb, var(--zelena) 14%, transparent); }
  .hlaska-chyba { background: color-mix(in srgb, #c0392b 14%, transparent); }
  .napoveda { font-size: .85rem; opacity: .7; margin: .2rem 0 0; }
</style>
</head>
<body>
<main>
<h1>Green Air Tech — nasazení</h1>
<p class="lead">Projděte tenhle formulář a web začne fungovat. Potom tenhle soubor smažte.</p>

<?php if ($hotovo): ?>
  <div class="hlaska">
    <b>Web už je nastavený.</b> Instalátor nic nemění.
    Smažte ho: <code>rm <?= $a(__FILE__) ?></code>
  </div>
<?php elseif ($uspech): ?>
  <div class="hlaska">
    <b>Hotovo.</b> Tabulky jsou založené a účet správce vytvořený.
    <?php if ($sitemap !== ''): ?><p><?= $sitemap ?></p><?php endif; ?>
    <?php if ($smazano): ?>
      <p>Instalátor se sám smazal, není co dodělávat.</p>
    <?php else: ?>
      <p><b>Smažte instalátor</b> — sám se smazat nedokázal:</p>
      <p><code>sudo rm <?= $a(__FILE__) ?></code></p>
    <?php endif; ?>
    <p>A přihlaste se do administrace: <a href="administrace.html">administrace.html</a></p>
  </div>
<?php else: ?>

  <h2>Co server umí</h2>
  <ul>
  <?php foreach ($kontroly as [$popis, $ok, $rada]): ?>
    <li class="<?= $ok ? 'ok' : 'ne' ?>"><b><?= $a($popis) ?></b>
      <?php if (!$ok): ?><p class="napoveda"><code><?= $a($rada) ?></code></p><?php endif; ?>
    </li>
  <?php endforeach; ?>
  </ul>

  <?php foreach ($chyby as $ch): ?>
    <div class="hlaska hlaska-chyba"><?= $a($ch) ?></div>
  <?php endforeach; ?>

  <form method="post">
    <input type="hidden" name="csrf" value="<?= $a($csrf) ?>">

    <h2>Databáze</h2>
    <div class="dvojice">
      <div><label for="db_host">Adresa</label>
        <input id="db_host" name="db_host" value="<?= $a($udaje['db_host']) ?>" required></div>
      <div><label for="db_jmeno">Název databáze</label>
        <input id="db_jmeno" name="db_jmeno" value="<?= $a($udaje['db_jmeno']) ?>" required></div>
      <div><label for="db_uzivatel">Uživatel</label>
        <input id="db_uzivatel" name="db_uzivatel" value="<?= $a($udaje['db_uzivatel']) ?>" required></div>
      <div><label for="db_heslo">Heslo</label>
        <input id="db_heslo" name="db_heslo" type="password" autocomplete="off"></div>
      <div><label for="db_port">Port</label>
        <input id="db_port" name="db_port" value="<?= $a($udaje['db_port']) ?>" inputmode="numeric"></div>
    </div>

    <h2>Web a pošta</h2>
    <label for="web">Adresa webu</label>
    <input id="web" name="web" value="<?= $a($udaje['web']) ?>" required>
    <p class="napoveda">Bez lomítka na konci. Použije se v sitemap.xml a v odkazech v e-mailech.</p>
    <div class="dvojice">
      <div><label for="posta_prijemce">Kam chodí poptávky</label>
        <input id="posta_prijemce" name="posta_prijemce" type="email" value="<?= $a($udaje['posta_prijemce']) ?>" required></div>
      <div><label for="posta_odesilatel">Odesílatel (nepovinné)</label>
        <input id="posta_odesilatel" name="posta_odesilatel" value="<?= $a($udaje['posta_odesilatel']) ?>"></div>
    </div>
    <p class="napoveda">Odesílatel musí být na vaší doméně, jinak pošta skončí ve spamu.</p>

    <h2>První účet správce</h2>
    <div class="dvojice">
      <div><label for="spravce_jmeno">Jméno</label>
        <input id="spravce_jmeno" name="spravce_jmeno" value="<?= $a($udaje['spravce_jmeno']) ?>" required></div>
      <div><label for="spravce_email">E-mail</label>
        <input id="spravce_email" name="spravce_email" type="email" value="<?= $a($udaje['spravce_email']) ?>" required></div>
    </div>
    <label for="spravce_heslo">Heslo (aspoň 12 znaků)</label>
    <input id="spravce_heslo" name="spravce_heslo" type="password" autocomplete="new-password" required>
    <p class="napoveda">Dalším lidem pak pošlete pozvánku z administrace, heslo si zvolí sami.</p>

    <h2>Statistiky</h2>
    <div class="dvojice">
      <div><label for="ga_mereni">ID měření (G-…)</label>
        <input id="ga_mereni" name="ga_mereni" value="<?= $a($udaje['ga_mereni']) ?>"></div>
      <div><label for="ga_property">Číslo property</label>
        <input id="ga_property" name="ga_property" value="<?= $a($udaje['ga_property']) ?>" inputmode="numeric"></div>
    </div>
    <p class="napoveda">Předvyplněné je měření, které pro vás máme založené v Google Analytics;
    klíč k němu je v balíčku jako <code><?= $a(dirname(__DIR__)) ?>/config/ga4.json</code>
    <?= is_file(dirname(__DIR__) . '/config/ga4.json') ? '(našel jsem ho)' : '(nenašel jsem ho — nástěnka zůstane prázdná)' ?>.
    ID měření vkládá do stránek měřicí kód, číslo property potřebuje nástěnka v administraci.
    Chcete-li měřit do vlastního účtu, obě pole přepište a vyměňte klíč; prázdná pole
    statistiky vypnou a web běží dál.</p>

    <button type="submit"<?= $prostrediOk ? '' : ' disabled' ?>>Nastavit web</button>
    <?php if (!$prostrediOk): ?>
      <p class="napoveda">Nejdřív spravte to, co je výš červené.</p>
    <?php endif; ?>
  </form>
<?php endif; ?>
</main>
</body>
</html>
