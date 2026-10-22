#!/usr/bin/env bash
# Sestaví balíček k nasazení u klienta: nasazeni/greenairtech-<datum>.zip
#
# Dovnitř jde jen to, co server potřebuje. Nejde tam nic z dílny (testy,
# kontrakty, zdrojové knihovny, ukázka) a hlavně nic z testovacího provozu
# (vlastní config.php, testovací účty, databáze).
set -euo pipefail

koren="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$koren"

datum="$(date +%Y-%m-%d)"
stavba="$(mktemp -d)"
cil="$stavba/greenairtech"
trap 'rm -rf "$stavba"' EXIT

mkdir -p "$cil/web/public" "$cil/web/config" "$cil/tools"

# --- aplikace -------------------------------------------------------------
cp -R web/app "$cil/web/app"
cp -R web/data "$cil/web/data"
cp -R web/public/assets "$cil/web/public/assets"
cp web/public/index.php web/public/.htaccess "$cil/web/public/"
mkdir -p "$cil/web/public/media"
printf '%s\n' "Nahrané fotky z administrace. Musí být zapisovatelná pro www-data." \
  > "$cil/web/public/media/README.txt"

# --- nastavení: jen vzor, nikdy vlastní config.php ------------------------
cp web/config/config.vzor.php "$cil/web/config/"

# --- instalátor a nástroje ------------------------------------------------
cp nasazeni/balicek/install.php "$cil/web/public/install.php"
cp tools/sitemap.php "$cil/tools/"
cp nasazeni/balicek/README-NASAZENI.md "$cil/README-NASAZENI.md"

# --- kontrola, že dovnitř nespadlo nic, co tam nepatří --------------------
spatne=0
while IFS= read -r nalez; do
  echo "NESMÍ V BALÍČKU BÝT: ${nalez#$cil/}"
  spatne=1
done < <(find "$cil" \( \
    -name 'config.php' -o -name 'seed-uzivatele*' -o -name '*.sqlite' -o \
    -name '.env' -o -name '*.log' -o -name 'ga4.json' -o -name '.git' \) -print)

if [ "$spatne" -ne 0 ]; then
  echo "Balíček se nesestavil." >&2
  exit 1
fi

# --- zabalit --------------------------------------------------------------
zip="$koren/nasazeni/greenairtech-$datum.zip"
rm -f "$zip"
( cd "$stavba" && zip -rq "$zip" greenairtech -x '*.DS_Store' )

souboru="$(find "$cil" -type f | wc -l | tr -d ' ')"
velikost="$(du -h "$zip" | cut -f1 | tr -d ' ')"
php -l "$cil/web/public/install.php" > /dev/null
echo "balíček: $zip"
echo "souborů: $souboru, velikost: $velikost"
