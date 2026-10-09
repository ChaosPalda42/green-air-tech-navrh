# Co je kde v ukázce

Web se dělí na dvě části. Úvodní stránka je rozcestník; z něj se jde buď
do části pro domácnosti, nebo pro firemní zákazníky.

## Společné

| Stránka | Soubor |
|---|---|
| Úvodní rozcestník | `web/index.html` |
| O nás | `web/o-nas.html` |
| Novinky | `web/novinky.html` |
| Kariéra | `web/kariera.html` |
| Kontakt | `web/kontakt.html` |
| Slovník zkratek | `web/slovnik.html` |
| **Administrace** | `web/administrace.html` |
| Ochrana osobních údajů | `web/ochrana-osobnich-udaju.html` |
| Stránka 404 | `web/404.html` |
| Sitemapa pro Google | `web/sitemap.xml` |

## Domácnosti

| Stránka | Soubor |
|---|---|
| Úvod části | `web/domacnosti.html` |
| Přehled služeb | `web/domacnosti-sluzby.html` |
| Klimatizace do domu a bytu | `web/sluzba-d-klimatizace.html` |
| Tepelná čerpadla | `web/sluzba-d-tepelna-cerpadla.html` |
| Rekuperace a větrání | `web/sluzba-d-rekuperace.html` |
| Servis a havárie | `web/sluzba-d-servis.html` |
| Realizace | `web/domacnosti-realizace.html` |

## Firemní zákazníci

| Stránka | Soubor |
|---|---|
| Úvod části | `web/firemni-zakaznici.html` |
| Přehled služeb | `web/firmy-sluzby.html` |
| Projekce TZB | `web/sluzba-projekce.html` |
| Realizace a montáže | `web/sluzba-realizace-montaze.html` |
| Servis a údržba | `web/sluzba-servis.html` |
| PENB, audity a refity | `web/sluzba-energetika.html` |
| Klimatizace a tepelná čerpadla | `web/sluzba-klimatizace.html` |
| EAC filtry Honeywell | `web/sluzba-eac-filtry.html` |
| Opravy výměníků | `web/sluzba-vymeniky.html` |
| Realizace | `web/firmy-realizace.html` |

Anglická verze je ve složce `web/en/`, německá ve `web/de/` — stejné názvy souborů.

## Administrace v kostce

1. Otevřete `web/administrace.html`, klikněte na **Vstoupit** (přihlášení nic nekontroluje).
2. **Nástěnka** — návštěvnost, zdroje, vstupní stránky, zařízení a odeslané poptávky.
   Nahoře přepínáte období (7 / 30 / 90 dní). U každé metriky je vysvětlivka —
   najeďte na její název. V ukázce jsou data vymyšlená.
3. **Texty webu** — vyberte jazyk, najděte text (dá se v nich hledat), přepište, uložte.
   U změněných textů je vidět původní znění a tlačítko „Vrátit původní".
4. **Realizace** — nahoře filtr podle části webu. Tlačítkem „Přidat realizaci"
   vyplníte formulář včetně toho, do které části patří; objeví se hned ve výpisu
   i s vlastní podstránkou.
5. **Uživatelé** — tři role: Správce (všechno), Editor obsahu (texty, realizace,
   novinky), Autor článků (jen novinky). Role se dají kdykoli změnit.
6. **Záloha a obnovení** — změny si stáhnete jako soubor JSON, nahrajete zpátky,
   nebo všechno vrátíte do výchozího stavu.

Změny žijí ve vašem prohlížeči. Když ukázku otevřete v jiném prohlížeči nebo
v anonymním okně, uvidíte zase výchozí stav.
