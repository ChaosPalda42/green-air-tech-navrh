# Testovací běh v tom, co má klient: Debian 13 + PHP 8.5.12 + Apache.
# Databáze je vedle, ve službě "databaze" (MariaDB) — viz compose.yaml.
FROM php:8.5-apache

# Základní obraz nemá pdo_mysql ani gd; klient je bude muset doinstalovat taky
# (v README to stojí jako apt-get install php8.5-mysql php8.5-gd).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends libfreetype6-dev libjpeg62-turbo-dev libpng-dev libwebp-dev; \
    docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp; \
    docker-php-ext-install -j"$(nproc)" pdo_mysql gd; \
    rm -rf /var/lib/apt/lists/*

RUN a2enmod rewrite headers

COPY vhost.conf /etc/apache2/sites-available/000-default.conf
COPY php.ini /usr/local/etc/php/conf.d/greenairtech.ini
