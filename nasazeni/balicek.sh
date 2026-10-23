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

mkdir -p "$cil/web/public" "$cil/web/config" "$cil/web/cache"

# --- aplikace -------------------------------------------------------------
cp -R web/app "$cil/web/app"
cp -R web/databaze "$cil/web/databaze"   # schema.sql — bez něj instalátor nezaloží tabulky
cp -R web/data "$cil/web/data"
# logy z testovacího provozu (poptávky!) do balíčku nepatří
find "$cil/web/data" -name '*.log' -delete
cp -R web/public/assets "$cil/web/public/assets"
cp web/public/index.php web/public/.htaccess "$cil/web/public/"
mkdir -p "$cil/web/public/media"
printf '%s\n' "Nahrané fotky z administrace. Musí být zapisovatelná pro www-data." \
  > "$cil/web/public/media/README.txt"
# .htaccess v media vypíná interpret — druhá závora k pravidlu v public/.htaccess
cp web/public/media/.htaccess "$cil/web/public/media/.htaccess"
printf '%s\n' "Krátká mezipaměť statistik z Google Analytics. Musí být zapisovatelná pro www-data." \
  > "$cil/web/cache/README.txt"

# --- nastavení: jen vzor, nikdy vlastní config.php ------------------------
cp web/config/config.vzor.php "$cil/web/config/"

# Klíč ke statistikám (čte vlastnost Green Air Tech v Analytics). Leží mimo
# git v nasazeni/klice/; bez něj se balíček sestaví taky, jen nástěnka
# zůstane u klienta prázdná.
klic="$koren/nasazeni/klice/ga4.json"
if [ -f "$klic" ]; then
  cp "$klic" "$cil/web/config/ga4.json"
  chmod 640 "$cil/web/config/ga4.json"
  klic_v_balicku="ano"
else
  klic_v_balicku="NE — nástěnka zůstane prázdná"
fi

# --- instalátor a nástroje ------------------------------------------------
cp nasazeni/balicek/install.php "$cil/web/public/install.php"
cp nasazeni/balicek/README-NASAZENI.md "$cil/README-NASAZENI.md"
# nastavení PHP: na čistém Debianu je upload_max_filesize 2M a fotka se nenahraje
cp nasazeni/balicek/greenairtech.ini "$cil/greenairtech.ini"

# --- kontrola, že dovnitř nespadlo nic, co tam nepatří --------------------
spatne=0
while IFS= read -r nalez; do
  echo "NESMÍ V BALÍČKU BÝT: ${nalez#$cil/}"
  spatne=1
done < <(find "$cil" \( \
    -name 'config.php' -o -name 'seed-uzivatele*' -o -name '*.sqlite' -o \
    -name '.env' -o -name '*.log' -o -name '.git' \) -print)

# Klíč smí být jedině ve web/config — v dokumentovém kořeni by si ho stáhl kdokoli
while IFS= read -r nalez; do
  if [ "${nalez#$cil/}" != "web/config/ga4.json" ]; then
    echo "KLÍČ NA ŠPATNÉM MÍSTĚ: ${nalez#$cil/}"
    spatne=1
  fi
done < <(find "$cil" -name 'ga4.json' -print)

# ...a naopak: co tam BÝT MUSÍ, jinak se web u klienta nerozběhne
for musi in web/databaze/schema.sql web/public/index.php web/public/install.php \
            web/config/config.vzor.php web/data/admin-klice.json \
            web/public/media/.htaccess; do
  if [ ! -f "$cil/$musi" ]; then
    echo "V BALÍČKU CHYBÍ: $musi"
    spatne=1
  fi
done

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
echo "klíč ke statistikám uvnitř: $klic_v_balicku"
