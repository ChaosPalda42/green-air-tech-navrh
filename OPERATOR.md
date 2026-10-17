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

## Rozhodnutí (10. 10. 2026, večer)

13. **Odkaz do administrace je v patičce** (`footer.administrace`). Klient si ji jinak
    musí pamatovat jako URL. Z jazykových podadresářů vede o patro výš přes nový
    `odkazKoren()` v kontextu.
14. **Barvy jen přes tokeny.** Projetí všech 22 typů stránek v tmavém režimu našlo pět
    ploch, které zůstaly světlé pod světlým textem (spodní lišta, přepínač jazyků,
    rozbalovací menu, jantarový panel, chybové hlášky), a zelená se ve tmě zesvětluje,
    takže bílý text na tlačítkách měl kontrast 1,9 : 1. Nové tokeny: `--na-zelené`,
    `--lišta-spodní`, `--jantar-závoj`, `--cihlová`, `--fialová-závoj`,
    `--fialová-na-tmavém`. Pravidlo do příště: **v šabloně ani v CSS žádná pevná barva
    na ploše, která se v tmavém režimu mění.**
15. **Dotykové plochy na mobilu min. 30 px.** Odkazy v patičce a drobečky měly výšku
    řádku; zvětšuje se klikací plocha, ne písmo.
16. **Záložky administrace se na mobilu posouvají do strany** i s popisky. Dřív se
    názvy schovávaly a zbylo pět ikon. `scroll-snap` se nesnáší s dopočítaným posunem,
    takže je pryč.
17. **Tlačítko „nahoru" je na mobilu schované** — překrývalo čísla v pravém sloupci
    a rychlé akce má spodní lišta.
18. **Čísla na nástěnce musí vypadat jako z Analytics** (kontrakt C-009 novelizován):
    týdenní rytmus, mírný růst, klidné kolísání, čas a míra opuštění jako náhodná
    procházka v pásmu. Čistě náhodná čísla poznal člověk na první pohled.

### Jak se ověřuje (10. 10. 2026)

Kontrast a přetékání se neodhaduje ze snímků. V prohlížeči běží sken: každá stránka se
načte do iframu 375 × 812, projdou se všechny prvky s vlastním textem, dohledá se
nejbližší neprůhledné pozadí v předcích a spočítá se kontrast. Gradienty (`.vyzva`,
`.avatar`) jsou falešné nálezy — pozadí nemají jako barvu.

## Rozhodnutí (10. 10. 2026, fotky u realizací)

19. **Fotky nahrává klient v administraci**, u každé realizace nejvýš osm.
    Obrázek se v prohlížeči zmenší na dlouhou hranu 1600 px a překlopí do JPEG
    (kvalita 0,82) — bez toho by se do `localStorage` vešly dvě fotky z mobilu.
    Zmenšování dělá canvas v `admin.js`; pořadí, limity, duplicity a formátování
    velikostí řeší `src/lib/fotky.mjs` (kontrakt **C-010**, zelený, 226 testů).
20. **Fotky bydlí přímo v položce realizace** (`polozka.fotky`), ne ve vlastním
    klíči. Díky tomu je nese export i import zálohy a `mergeRealizace` je dostane
    na web bez dalšího zařizování. Cena za to je strop `localStorage` —
    `uloz()` proto hlídá výjimku, vrátí stav zpátky a řekne to uživateli.
    Ověřeno podstrčením `QuotaExceededError`: uložený stav zůstal nedotčený.
21. **Statické stránky mají jen háčky.** Karta realizace nese
    `data-realizace-nahled="<id>"`, detail `data-realizace-galerie="<id>"`;
    `app.js` při startu zjistí, jestli je k id v `localStorage` galerie, a teprve
    pak nahradí kreslené schéma fotkou. Funguje to i pro realizace, které jsou
    součástí ukázky (ukládají se do `edited`), ne jen pro nově přidané.
22. Na detailu se z fotek skládá malá galerie: velký snímek a pásek miniatur,
    kliknutí přehodí hlavní obrázek. Bez fotek zůstane schéma — klient tak nikdy
    neuvidí prázdné místo.

### Co review u C-010 našlo

Dvě drobnosti (položka, která není objekt, se odmítala jako „duplikát"; soubor bez
použitelné velikosti prošel kontrolou). Obojí jsem **nedopisoval ručně** — doplnil
jsem kontrakt a test a pustil Factory znovu, aby zdrojem pravdy zůstal harness.

## Rozhodnutí (10. 10. 2026, zesvětlení webu)

23. **Velké plochy jsou světlé.** Ze schůzky: tmavě zelená je „fakt tmavá, hodně
    tmavá", klient chce „pocitově zelenou, barvu jako voda". První oprava jen
    zesvětlila `--inkoust`, to nestačilo. Teď mají hero, podhlaví, zvýrazněné sekce,
    výzvy a zvýrazněná kontaktní karta vlastní rodinu tokenů:
    `--plocha` (#dcefe7), `--plocha-2`, `--plocha-text`, `--plocha-text-tlumený`,
    `--plocha-nadpis`, `--plocha-akcent`, `--plocha-obrys`, `--plocha-obrys-plocha`,
    `--plocha-kresba`. V tmavém režimu se celá rodina přebíjí zpět na tmavou.
24. **`--inkoust` zůstal tmavý** a slouží dál tomu, co tmavé zůstat má: bublina
    s vysvětlivkou, náhledy karet s technickými schématy, tlačítko „nahoru".
    Rozdělení ploch a inkoustu je to, co celou výměnu udrželo v mezích.
25. **Patička je o stupeň lehčí** (`--paticka-pozadi: #2d6b55`, „hluboká voda").
    Tmavá zůstala schválně — ukončuje stránku. Text v ní musel zesvětlit
    (`--text-na-tmavém-tlumený` z #b4c9b7 na #d2e4d4), jinak spadl na 3,58 : 1.

### Co se při tom našlo

- `hero-schema` kreslilo bílými tahy (`rgba(255,255,255,.22)`) — na světlé ploše
  zmizelo. Teď kreslí `var(--plocha-kresba)`.
- V šabloně zůstal inline `style="color:var(--zelena-svetlá)"` u servisního e-mailu.
  Inline styl přebije všechno, žádné pravidlo v CSS ho nenajde — hledal jsem ho
  procházkou `document.styleSheets` a našel až v `outerHTML`. Test to teď hlídá.
- `.slovnik-karta dt` mělo `color: var(--inkoust)`, tedy barvu plochy jako barvu
  textu; v tmavém režimu z toho byl tmavý text na tmavé kartě (1,10 : 1). Stará
  chyba, kterou předchozí sken minul, protože se díval jen na prvky s vlastním
  pozadím. Nový sken dohledává nejbližší neprůhledné pozadí v předcích.

Po změně neprojde na 21 stránkách ve světlém ani tmavém režimu nic pod 4,3 : 1.

26. **Ještě o stupeň světleji** (druhé kolo téhož dne): klient chtěl blíž k bílé
    podložce loga. `--plocha` #dcefe7 -> **#ecf7f1**, `--plocha-2` -> #daefe4,
    lišta #e7f3df -> #f2f9ec. Při prvním pokusu (#f1f9f4) plocha splynula se
    sekcí na `--papír-2` (#f5f8f3) a zmizel rytmus pruhů; `.sekce-tmava` proto
    dostala vlasovou linku `border-block` a plocha se vrátila o chlup zpět.
    Ponaučení: u skoro bílých ploch nedrží pruh barva, ale linka.

## Rozhodnutí (15. 10. 2026)

27. **Rozcestník má dva sloupce na každé šířce.** Na telefonu se dlaždice skládaly
    pod sebe a druhá volba byla pod ohybem — u rozcestníku je to chyba, obě
    možnosti musí být vidět najednou. Dvousloupcovost už nevisí na `min-width`.
    Dlaždice má pro úzký sloupec kompaktní variantu: menší ikona (42 px), menší
    písmo, perex zkrácený na tři řádky přes `-webkit-line-clamp`, pod 380 px na
    dva. Ověřeno na 320, 360, 375, 768 px — nikde nepřetéká a názvy se vejdou.

## Rozhodnutí (17. 10. 2026)

28. **Text na zelených kolečkách se řídí režimem.** `factory prohlizec zmer` změřil
    u iniciál v kolečku kontrast 2,86 — bílá na `--zelena` (#58ac25), zatímco velký
    tučný text potřebuje 3,0. Světlejší konec přechodu ztmavl na `--zelena-avatar`
    (#52a022, tedy 3,28) a barva textu jde přes `--na-zelené`.
    Při tom vyšla najevo horší věc: v **tmavém** režimu je `--zelena-tmavá` světlá
    (#7bd13f), takže bílé iniciály na ní měly **1,9**. Stejně na tom byla ikona
    v dlaždici rozcestníku a ikona služby při najetí. Po opravě: světlý režim
    3,28 / 6,58, tmavý 5,15 / 8,87.

### Proč to předchozí sken nenašel

Můj průchod kontrastem bral text nad gradientem jako falešný nález a `.avatar` jsem
z něj ručně vyřadil (`el.closest('.avatar')`). Ten filtr schovával skutečnou vadu.
Ponaučení: **falešný nález se nemá filtrovat selektorem, ale správným dopočtem
podkladu** — u gradientu nejhorší zastávkou. To dnes umí `zmer` a je to i důvod,
proč u něj nestačí „vypadá to dobře".
