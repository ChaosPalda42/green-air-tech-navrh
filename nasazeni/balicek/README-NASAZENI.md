# Green Air Tech — nasazení na server

Web je obyčejné PHP: žádný composer, žádný node, nic se nekompiluje.
Rozbalit, založit databázi, projít instalátor. Hotovo.

## Co server potřebuje

| | |
|---|---|
| Debian | 13 (trixie) |
| PHP | 8.5 (testováno na 8.5.12) |
| Rozšíření PHP | `php8.5-mysql` (PDO), `php8.5-gd` (fotky) |
| Databáze | MariaDB 10.6+ (testováno na 11.8) |
| Web server | Apache 2.4 s `mod_rewrite`, nebo nginx |

```bash
sudo apt install php8.5 php8.5-mysql php8.5-gd libapache2-mod-php8.5 mariadb-server
sudo a2enmod rewrite headers expires
```

## 1. Rozbalit

```bash
sudo mkdir -p /var/www/greenairtech
sudo unzip greenairtech-<datum>.zip -d /tmp/gat
sudo cp -R /tmp/gat/greenairtech/. /var/www/greenairtech/
sudo chown -R www-data:www-data /var/www/greenairtech
```

**Dokumentový koren je `/var/www/greenairtech/web/public`**, ne složka nad ním.
Nic jiného z balíčku nesmí být z internetu vidět.

## 2. Databáze

```sql
CREATE DATABASE greenairtech CHARACTER SET utf8mb4 COLLATE utf8mb4_czech_ci;
CREATE USER 'greenairtech'@'localhost' IDENTIFIED BY 'sem-dejte-silne-heslo';
GRANT ALL PRIVILEGES ON greenairtech.* TO 'greenairtech'@'localhost';
```

Tabulky zakládá instalátor sám, SQL spouštět ručně nemusíte
(je v `web/databaze/schema.sql`, kdyby bylo potřeba).

## 3. Apache

```apache
<VirtualHost *:80>
  ServerName greenairtech.cz
  ServerAlias www.greenairtech.cz
  DocumentRoot /var/www/greenairtech/web/public

  <Directory /var/www/greenairtech/web/public>
    AllowOverride All
    Require all granted
  </Directory>

  ErrorLog  ${APACHE_LOG_DIR}/greenairtech-error.log
  CustomLog ${APACHE_LOG_DIR}/greenairtech-access.log combined
</VirtualHost>
```

`AllowOverride All` je potřeba — přepisy adres, hlavičky a cache jsou
v `web/public/.htaccess`. Potom:

```bash
sudo a2ensite greenairtech && sudo systemctl reload apache2
sudo certbot --apache -d greenairtech.cz -d www.greenairtech.cz
```

### nginx místo Apache

```nginx
server {
  server_name greenairtech.cz www.greenairtech.cz;
  root /var/www/greenairtech/web/public;
  index index.php;

  location / { try_files $uri $uri/ /index.php?$query_string; }
  location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/run/php/php8.5-fpm.sock;
  }
  location ~ ^/media/.*\.(php|phtml|phar|html?)$ { return 403; }
  location ~ /\.(?!well-known) { deny all; }
}
```

## 4. Instalátor

Otevřete `https://greenairtech.cz/install.php`, vyplňte přístup k databázi
a první účet správce. Instalátor:

1. zkontroluje verzi PHP a rozšíření,
2. zapíše `web/config/config.php` (mimo dokumentový koren),
3. založí tabulky,
4. vytvoří prvního správce,
5. řekne vám, že se má `install.php` smazat — **smažte ho**.

```bash
sudo rm /var/www/greenairtech/web/public/install.php
```

## 5. Práva na složky

Zapisuje se jen do dvou míst:

```bash
sudo chown -R www-data:www-data /var/www/greenairtech/web/public/media
sudo chmod 775 /var/www/greenairtech/web/public/media
sudo chown www-data:www-data /var/www/greenairtech/web/config
```

## 6. Statistiky (Google Analytics)

**Nemusíte nic zařizovat — měření je připravené.** Vlastnost v Google
Analytics je pro Green Air Tech založená a klíč k ní je v balíčku jako
`web/config/ga4.json`. Instalátor má obě pole předvyplněná, takže stačí
projít formulářem a nástěnka začne po pár hodinách ukazovat návštěvnost.

Jen jedna věc po rozbalení — klíč patří mimo dokumentový kořen (v balíčku
už tam je) a nikomu jinému než webu do něj nic není:

```bash
sudo chown www-data:www-data /var/www/greenairtech/web/config/ga4.json
sudo chmod 640 /var/www/greenairtech/web/config/ga4.json
```

Měření na webu a nástěnka v administraci jsou dvě různé věci; obojí se
nastavuje v instalátoru nebo později v `web/config/config.php` (sekce
`analytics`):

- **ID měření** (`analytics.mereni`, tvar `G-XXXXXXXXXX`, v Analytics →
  Správce → Datové streamy) — vkládá do stránek měřicí kód. Bez něj se
  návštěvnost vůbec nesbírá.
- **číslo property** (`analytics.property`, jen číslice, Analytics → Správce →
  Podrobnosti o vlastnictví) — odtud nástěnka čte hotová čísla.
- **servisní účet** (`analytics.klic`) — cesta ke klíči, standardně
  `web/config/ga4.json`.

Chcete-li měřit do vlastního účtu Google Analytics, založte si vlastnost
a servisní účet, jeho klíč uložte pod stejným jménem místo dodaného,
v Analytics ho přidejte jako **čtenáře** vlastnosti a v `config.php`
přepište `mereni` a `property`. Když se `analytics` vyprázdní, web běží
normálně dál, jen nástěnka řekne, že statistiky nejsou nastavené.

## 7. Pošta

Poptávky z webu chodí na adresu z `config.php` (`posta.prijemce`). Server musí
umět `mail()` — na Debianu stačí:

```bash
sudo apt install msmtp-mta
```

a nastavit `/etc/msmtprc` na firemní SMTP. Dokud pošta nejede, poptávky se
**neztrácejí** — ukládají se do databáze (tabulka `poptavky`). Administrace
je zatím jen počítá na nástěnce; vypsat je umí databáze:

```sql
SELECT prijato, jmeno, email, telefon, vetev FROM poptavky ORDER BY prijato DESC LIMIT 20;
```

## 8. Mapa webu a Search Console

`sitemap.xml` i `robots.txt` vytvoří instalátor pro vaši doménu — je v nich
135 adres ve třech jazycích (administrace a chybové stránky do sitemapy
nepatří). V Google Search Console sitemapu přidejte ručně
(Soubory sitemap → vložit adresu `sitemap.xml`).

Když někdy přibude stránka, oba soubory se dají vytvořit znovu:

```bash
cd /var/www/greenairtech && sudo -u www-data php tools/sitemap.php
```

## Co kde je

```
web/
  public/        dokumentový koren: index.php, .htaccess, assets/, media/
  app/           kód webu (šablony, obsah, API, databáze)
  data/          výchozí texty a obsah ve třech jazycích
  databaze/      schema.sql
  config/        config.php (vytvoří instalátor), ga4.json (klíč ke statistikám)
```

Aktualizace webu = rozbalit nový balíček přes starý. Složky `config`,
`media` a databáze zůstávají; texty změněné v administraci jsou v databázi,
takže se novým balíčkem nepřepíšou.
