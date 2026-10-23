# Green Air Tech — nasazení na server

Web je obyčejné PHP: žádný composer, žádný node, nic se nekompiluje.
Rozbalit, založit databázi, projít instalátor. Hotovo.

## Co server potřebuje

| | |
|---|---|
| Debian | 13 (trixie) |
| PHP | 8.5.12 a novější (testováno na 8.5.12), nebo 8.4.27 a novější |
| Rozšíření PHP | `php8.5-mysql` (PDO), `php8.5-gd` (fotky), `php8.5-mbstring` (české texty), `php8.5-curl` (statistiky) |
| Databáze | MariaDB 10.6+ (testováno na 11.8) |
| Web server | Apache 2.4 s `mod_rewrite`, nebo nginx |

**PHP 8.5 na Debianu 13 není ve výchozích repozitářích** — trixie má 8.4.
Buď přidejte repozitář Sury:

```bash
sudo apt install -y apt-transport-https lsb-release ca-certificates curl
sudo curl -sSLo /usr/share/keyrings/deb.sury.org-php.gpg https://packages.sury.org/php/apt.gpg
echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main" \
  | sudo tee /etc/apt/sources.list.d/sury-php.list
sudo apt update
```

…nebo nechte PHP z Debianu a všude níž čtěte `php8.4` místo `php8.5`
(web potřebuje 8.2 a novější, 8.4 mu stačí).

```bash
sudo apt install php8.5 php8.5-mysql php8.5-gd php8.5-mbstring php8.5-curl \
  libapache2-mod-php8.5 mariadb-server
sudo a2enmod rewrite headers expires
```

Zkontrolujte, že rozšíření opravdu jsou (prázdný výstup = chybí):

```bash
php -m | grep -E '^(pdo_mysql|gd|mbstring|curl|openssl|ctype)$'
```

Bez `mbstring` nebo `curl` se web nerozběhne — instalátor to pozná
a nepustí vás dál.

### Minimální verze PHP (tohle prosím nepřeskočte)

PHP vydalo 21. 10. 2026 mimořádné opravy dvou kritických chyb, které
dovolovaly spustit na serveru cizí kód bez přihlášení. **Nasazujte jen na
opravenou verzi:**

| Řada PHP | První opravená |
|---|---|
| 8.5 | **8.5.12** |
| 8.4 | **8.4.27** |
| 8.3 | 8.3.36 |
| 8.2 | 8.2.35 |

Ověříte si to takto — číslo musí být stejné nebo vyšší:

```bash
php -v
```

Když je nižší, doinstalujte aktualizace (u Sury i u Debianu stačí obojí):

```bash
sudo apt update && sudo apt upgrade
```

Instalátor verzi porovná sám a na starší to napíše červeně. **Aktualizace
PHP si pak nechte instalovat dál** — bezpečnostní opravy vycházejí každý
měsíc a server, který je nedostává, je otevřené okno:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Soubor `greenairtech.ini` (sekce 4) k tomu vypíná `session.upload_progress`
— tam je od 23. 10. 2026 další chyba, na kterou oprava zatím není. Web ho
nepoužívá, takže o nic nepřijdete.

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

## 4. Limity PHP (jinak nenahrajete fotky)

Čistý Debian pouští do PHP soubory jen do 2 MB a dává mu 128 MB paměti.
Fotka z telefonu se přes to nedostane — administrace řekne, že je moc velká.
V balíčku je proto hotové nastavení:

```bash
sudo cp /tmp/gat/greenairtech/greenairtech.ini \
  /etc/php/8.5/apache2/conf.d/99-greenairtech.ini
sudo systemctl reload apache2
```

Když PHP běží přes php-fpm (typicky u nginx), patří soubor do
`/etc/php/8.5/fpm/conf.d/` a restartuje se `sudo systemctl restart php8.5-fpm`.

Jsou v něm čtyři hodnoty: `upload_max_filesize = 12M` (víc administrace
neposílá — větší fotku odmítne už v prohlížeči), `post_max_size = 16M`,
`memory_limit = 512M` (fotka z telefonu má 24–50 megapixelů a knihovna GD jí
v paměti dá 4 bajty na pixel) a `max_execution_time = 60`.

Instalátor na další stránce ukáže, jaké hodnoty server zrovna má, a když
nestačí, napíše to. Instalaci to nezastaví — web poběží, jen nahrávání fotek
ne, takže se to dá dodělat i potom.

## 5. Instalátor

Otevřete `https://greenairtech.cz/install.php`, vyplňte přístup k databázi
a první účet správce. Instalátor:

1. zkontroluje verzi PHP a rozšíření,
2. zapíše `web/config/config.php` (mimo dokumentový koren),
3. založí tabulky,
4. vytvoří prvního správce,
5. smaže se sám.

Jakmile `web/config/config.php` existuje, instalátor už nic nemění — i kdyby
databáze zrovna neběžela. Kdyby se mu sebesmazání nepovedlo (práva na složku),
napíše to a smažete ho ručně:

```bash
sudo rm /var/www/greenairtech/web/public/install.php
```

## 6. Práva na složky

Zapisuje se jen do dvou míst:

```bash
sudo chown -R www-data:www-data /var/www/greenairtech/web/public/media
sudo chmod 775 /var/www/greenairtech/web/public/media
sudo chown www-data:www-data /var/www/greenairtech/web/config
```

## 7. Statistiky (Google Analytics)

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

## 8. Pošta

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

## 9. Mapa webu a Search Console

`sitemap.xml` i `robots.txt` vydává web sám — nejsou to soubory na disku.
Je v nich 135 adres ve třech jazycích (administrace a chybové stránky do
sitemapy nepatří) a nová realizace z administrace se v sitemapě objeví hned,
bez vašeho zásahu. V Google Search Console sitemapu přidejte ručně
(Soubory sitemap → vložit adresu `sitemap.xml`).

Kdyby v dokumentovém korenu zůstal starý `sitemap.xml` nebo `robots.txt`
(třeba z ručního nasazení), Apache by poslal ten soubor a sitemapa by
přestala stárnout — smažte je.

## 10. Zabezpečení — co web dělá sám

Bezpečnostní hlavičky posílá PHP, ne `.htaccess`. Platí proto i za nginxem
a nedá se je omylem vypnout přepsáním souboru:

| Hlavička | Co dělá |
| --- | --- |
| `Content-Security-Policy` | skripty jen z webu a z Google Tag Manageru (měření), stránku nelze vložit do cizího rámu, formulář nelze odeslat jinam |
| `X-Frame-Options: SAMEORIGIN` | totéž pro starší prohlížeče |
| `X-Content-Type-Options: nosniff` | prohlížeč nehádá typ souboru |
| `Referrer-Policy` | na cizí web neposílá celou adresu |
| `Permissions-Policy` | web si nesmí říct o polohu, mikrofon, kameru ani platby |
| `Strict-Transport-Security` | **jen po HTTPS**, 180 dní, i pro subdomény |

HSTS se po HTTP záměrně neposílá — na webu bez certifikátu by se tím dal
web zamknout. Certifikát tedy nasaďte dřív, než pustíte lidi na adresu.

Co ještě web hlídá sám:

- **Přihlašování**: 10 chybných hesel během 15 minut a přihlášení se na
  15 minut zamkne (počítá se podle jména i podle IP, takže nová cookie
  ani nový prohlížeč nepomůžou). Hesla se ukládají jen jako hash.
- **Administrace se neindexuje**: stránka má `noindex` a `robots.txt` ji
  zakazuje.
- **Poptávkový formulář** má skrytou past na roboty a strop 20 odeslání
  za 10 minut.
- **Nahrané fotky** se vždy převedou na WebP a ve složce `media` se nic
  nespustí jako PHP.
- **Instalátor se po nasazení sám smaže.** Kdyby na serveru z nějakého
  důvodu zůstal (`web/public/install.php`), smažte ho — podruhé se už
  nespustí, protože existuje `config/config.php`, ale nemá tam co dělat.
- **Chyby se nikdy nevypisují do stránky**, jde všechno do logu Apache.

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
