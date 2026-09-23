#!/usr/bin/env bash
# Sestaví web a zabalí ho do _balicek/Green-Air-Tech-ukazka.zip k odeslání klientovi.
set -euo pipefail

KOREN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOREN"

echo "› sestavuji web"
node build.mjs

echo "› akceptační testy"
uv run pytest -q

BALICEK="$KOREN/_balicek"
STAGE="$BALICEK/Green-Air-Tech-ukazka"
rm -rf "$BALICEK"
mkdir -p "$STAGE"

cp -R "$KOREN/out/web" "$STAGE/web"
cp "$KOREN/dokumenty/PRECTI-ME.txt" "$STAGE/PRECTI-ME.txt"
cp "$KOREN/dokumenty/OTEVRIT-UKAZKU.html" "$STAGE/OTEVRIT-UKAZKU.html"
mkdir -p "$STAGE/dokumenty"
cp "$KOREN/dokumenty/co-je-kde.md" "$STAGE/dokumenty/co-je-kde.md"

cd "$BALICEK"
zip -qr "Green-Air-Tech-ukazka.zip" "Green-Air-Tech-ukazka"
rm -rf "$STAGE"

echo "› hotovo: _balicek/Green-Air-Tech-ukazka.zip ($(du -h "$BALICEK/Green-Air-Tech-ukazka.zip" | cut -f1))"
