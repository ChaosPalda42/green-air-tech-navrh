# Green Air Tech — návrh nového webu

## Co a proč

Klient: **Green Air Tech s.r.o.** (IČO 19667531), Pobřežní 394/12, Praha 8 + provozovna
Milevsko. Obor: technická zařízení budov — projekce, realizace a servis vzduchotechniky,
chlazení, vytápění, ZTI a MaR, PENB a energetické audity, klimatizace a tepelná čerpadla,
EAC filtry Honeywell, opravy výměníků.

Současný web: <https://www.greenairtech.cz/> (WordPress, šablona HOTdesign, DE mutace přes
Polylang). Obsah je věcný, ale web působí staře, kontaktní formulář vede na externí
app.mwork365.com a na mobilu není co chytit.

Cíl zakázky: klikací ukázka nového webu, kterou lze poslat klientovi k náhledu.

## Zadání od klienta (24. 9. 2026)

- animace větru / motiv vzduchotechnického potrubí, „vyšperkované"
- administrace na úpravu textů a přidávání realizací
- důraz na mobil
- držet se zelené (logo), **logo zachovat** (mají ho i na tištěných materiálech)
- snadný kontakt a snadná orientace
- na úvodu musí být decentně, ale jasně vidět, co umí
- **zkratky s vysvětlivkou po najetí** (používají jich hodně)
- klikací prohlídka přes GitHub

Doplněno v průběhu: vítr za kurzorem, „foukající" přechody mezi stránkami.

## Rozhodnutí (24. 9. 2026)

1. **Administrace = demo v ukázce.** Plné rozhraní (přihlášení, editace textů ve třech
   jazycích, přidávání/mazání realizací, export a import změn), stav se drží v
   `localStorage` pod klíčem `gat-cms-v1`. Klient si tak vše osahá bez hostingu.
   Na ostré verzi se stejná logika napojí na server nebo na git-based CMS.
2. **Realizace jsou smyšlené** — osm věrohodných zakázek. Klient je v administraci
   přepíše skutečnými. Je to napsáno v PRECTI-ME.
3. **Jazyky CZ / EN / DE.** Čeština je zdroj, EN a DE překládá lokální model
   (`tools/translate.py`). Zkratky, které vzniknou až překladem (TGA, RLT, MSR, KWK, MEP…),
   jsou v `data/content/zkratky-navic.json`.
4. **Bez stockových fotek.** Náhledy realizací jsou vlastní technická schémata
   (`src/templates/motivy.mjs`, osm různých kompozic). Fotky klienta se použily tam, kde
   sedí: strojovna v hero a na O nás, kazetová jednotka u slovníku, výkresy u projekce,
   filtry Honeywell u EAC, venkovní jednotka u tepelných čerpadel.
   Smyšlené realizace záměrně **nemají** fotky klienta, aby nevznikl dojem, že ty stavby
   skutečně proběhly.
5. **Ploché názvy souborů** (`sluzba-projekce.html`, `realizace-poliklinika-pisek.html`)
   a jen relativní odkazy — web běží z `file://`, z GitHub Pages i z podadresáře.
6. **Žádné ESM v prohlížeči.** `build.mjs` sesypává `src/lib/*.mjs` do jednoho klasického
   skriptu; moduly ESM by z `file://` padaly na CORS.
7. **Ukázka je neindexovaná** — `noindex, nofollow` na každé stránce + `robots.txt`.

## Kde to je

```
data/site.json             fakta o firmě, lidé, seznam služeb, realizací a novinek (nepřekládá se)
data/content/cs.json       veškeré texty — zdroj pravdy
data/content/en|de.json    překlady z lokálního modelu
data/content/zkratky-navic.json  zkratky, které existují jen v cizojazyčné verzi
src/lib/*.mjs              čistá logika (kontrakty C-001…C-005, psaly lokální modely)
src/templates/*.mjs        layout, stránky, ikony, technická grafika, administrace
src/assets/style.css       design systém
src/assets/app.js          runtime: vítr, vysvětlivky, filtry, formulář, CMS náhledy
src/assets/admin.js        demo administrace
tools/optimize_images.py   responzivní obrázky (kontrakt C-006)
tools/translate.py         překlad lokálním modelem (kontrakt C-007)
build.mjs                  generátor -> out/web
```

## Jak to spustit

```bash
node build.mjs                 # sestaví out/web (volá i tools/optimize_images.py)
uv run pytest -q               # 124 akceptačních testů
./tools/pack.sh                # _balicek/Green-Air-Tech-ukazka.zip
```

Náhled: `.claude/launch.json` → `gat-ukazka` (http.server 4190 nad `out/web`).

Překlad po změně češtiny:

```bash
FACTORY_BASE_URL=http://127.0.0.1:8080/v1 FACTORY_MODEL=qwen3.8-flash-next \
  uv run python tools/translate.py data/content/cs.json data/content/en.json en
FACTORY_BASE_URL=http://127.0.0.1:8081/v1 FACTORY_MODEL=gemma-4-26b-a4b \
  uv run python tools/translate.py data/content/cs.json data/content/de.json de
```

## Factory

Kontrakty C-001 … C-007 (vysvětlivky zkratek, i18n, stav administrace, validace formuláře,
filtr realizací, responzivní obrázky, překladač) běžely na jeden zátah: **7 zelených,
35 iterací, ~6 minut, 0 balíčků.** Coder `qwen3.6-35b-a3b` (port 8082), překlady
`qwen3.8-flash-next` (8080) a `gemma-4-26b-a4b` (8081).

Design systém, šablony, SVG grafiku a canvas animace psal operátor — podle lekce ze
Sršně se kreslicí a layoutový kód nevyplácí zadávat kontraktem.

## Otevřené body pro klienta

- Realizace: dodat skutečné zakázky (název, místo, rozsah, výsledek) — ideálně i fotky.
- Kontakty: potvrdit, že mají zůstat přímá čísla a e-maily celého týmu.
- Formulář: kam mají poptávky chodit (teď je to ukázka, na ostro `info@greenairtech.cz`),
  a jestli zachovat i odkaz na app.mwork365.com.
- EN/DE: překlad je strojový, před spuštěním chce projít rodilým mluvčím.
- Text ochrany osobních údajů je ukázkový, nechat zkontrolovat.
- Nasazení na doménu s HTTPS, přesměrování ze starých URL.

## Doplnění zadání ze schůzky s klientem (9. 10. 2026)

Přepis schůzky zpracoval lokální model (kontrakt C-008, `tools/zadani_ze_schuzky.py`),
výsledek je v `dokumenty/doplneni-zadani-2026-10-09.md`. Z něj plynou rozhodnutí níže.

## Rozhodnutí (10. 10. 2026)

8. **Web se dělí na dvě větve** — Domácnosti a Firemní zákazník. Rozcestník je přímo
   v heru úvodní stránky, každá větev má vlastní domovskou stránku, vlastní služby
   a vlastní realizace; O nás, Novinky, Kariéra a Kontakt zůstávají společné.
   V `data/site.json` přibylo pole `vetve`, každá služba i realizace má `vetev`.
   `build.mjs` staví odkazy přes `odkazVetve()` a `soubor()` vyhodí chybu, když větev
   chybí — jinak vznikaly odkazy typu `realizace-domacnosti.html`.
9. **Světlejší inkoust.** `--inkoust` z `#101a12` na `#23583a`; tmavě zelená byla
   podle klienta moc tmavá.
10. **Kratší formulář** (kontrakt C-004 novelizován, před přestavbou `factory contract
    reset C-004`): první otázka je typ poptávky, pak jméno a jeden kontakt — telefon
    NEBO e-mail. Zpráva nepovinná, pole Firma zrušeno. Chyba `kontakt` se ukazuje
    u telefonu.
11. **Nástěnka se statistikami a správa uživatelů v administraci.** Čísla generuje
    deterministicky `src/lib/statistiky.mjs` (kontrakt C-009), aby náhled vypadal
    pokaždé stejně. Role: Správce / Editor obsahu / Autor článků — klient chtěl dát
    externímu autorovi přístup jen k Novinkám. Uživatelé mají vlastní klíč
    v localStorage (`gat-admin-uzivatele`), aby je nesmazal import zálohy obsahu.
12. **Sitemapa a robots.txt** se generují při buildu (klient je chce do Search Console).

### Provozní lekce (10. 10. 2026)

- **Před každým `factory run` commitnout.** Harness vrací soubory, které nevlastní
  kontrakt. Dvakrát za den tím zmizela hotová práce v `admin.js`, `admin.css`
  a `app.js`. Zapsáno i do `~/factory/docs/OPERATOR_PREFERENCES.md`.
- **Neověřovat nasazení curlem.** GitHub Pages servíruje assety s `max-age=600`,
  takže curl ukazuje novou verzi, zatímco prohlížeč klienta pořád starou. Proto mají
  CSS i JS v odkazu otisk obsahu (`?v=<sha1[:8]>`) a ověřuje se v prohlížeči.
- `factory.toml` přesměrován na modely, které jsou opravdu nahrané: coder/tester
  `qwen3.8-27b` (:8085), coder_retry/text `gemma-4-26b-a4b` (:8081). Služby
  llama-server jsem kvůli tomu nerestartoval.
- Zabitý běh nechá v `state.json` `outcome: running` a další běh pak tiše skončí
  s prázdným logem — stav je potřeba uklidit.

### Stav k 10. 10. 2026

139 stránek ve třech jazycích, 9/9 kontraktů zelených, 179 akceptačních testů prochází.
Překlad EN/DE běžel nadvakrát: 47 německých hodnot se v prvním průchodu vrátilo
v češtině (vypadl jeden chunk), doplněno druhým během po menších dávkách.
