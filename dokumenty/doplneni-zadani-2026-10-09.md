# Doplnění zadání — schůzka s klientem 9. 10. 2026

Zdroj: zápis a přepis hovoru (Teams, 9. 10. 2026). Účastníci dle pozvánky: Karel Divina,
Michael Paleček, Alan Balha, Iva Adámková, Ondřej Petržilka.

Termín pro náhled: **pondělí 12. 10. 2026.**

---

## 1. Hlavní změna: web se dělí na dvě větve

Na úvodní stránce budou **dvě výrazné dlaždice**:

| Větev | Pro koho | Co tam patří |
|---|---|---|
| **Domácnosti** | soukromá osoba, „domkář" | malé realizace, servis, opravy a havárie v domácnostech — tepelná čerpadla, klimatizace, kotle, rekuperace |
| **Firemní zákazník** | B2B, průmysl, komerční objekty | velké realizace a tendry, projekce, kompletní TZB, energetika |

**Velikost dlaždic:** klient je chce výrazné — řádově třetina úvodního obsahu, zhruba šířka
dnešního hero obrázku a poloviční výška. Tedy **rozcestník, ne malý přepínač**.

**Co se liší mezi větvemi:** služby, realizace, servisní obsah.
**Co zůstává společné:** O nás, Novinky, Kariéra, Kontakt.
Po vstupu do větve už úvodní stránka v menu není potřeba.

**Hranice mezi větvemi (z přepisu):**
- Malé realizace zhruba **do 500–750 tis. Kč** řeší servisní oddělení (kolega Benák) → domácnosti.
- Větší realizace a tendry **od cca 1 mil. Kč** → firemní.
- Příklad servisní nabídky pro domácnosti: podzimní akce na klimatizaci za **28 tis. Kč**.
- Restaurace a podobné provozy už patří do firemní větve, ne do domácností.

## 2. Vzhled

- **Zesvětlit.** Tmavě zelená je podle klienta „fakt tmavá, hodně tmavá". Chce světlejší,
  „pocitově zelenou, barvu jako voda", která dobře působí na monitorech.
- **Světlý a tmavý režim podle nastavení zařízení.** Klient výslovně: „To udělej, mají to rád."
- **Tečky na pozadí zůstávají** — „zjemňuje to stránku, určitě bych to tam nechal".
- **Vysvětlivky zkratek zůstávají** — „jedna z věcí, která mě přesvědčila", „to zachováme".
- **Vítr při přechodu mezi stránkami: otevřená otázka.** Klientovi se animace na jeho stroji
  nezobrazovala, takže ji neviděl a nevyjádřil se. V zápisu je to vedené jako otevřený bod.

## 3. Poptávkový formulář

- **Co nejjednodušší, minimum povinných polí a kroků.** Argument padl přímo na schůzce:
  čím míň toho člověk musí vyplnit, tím spíš formulář odešle.
- U tlačítka „Poptat řešení" **rozbalovací volba typu poptávky** — řeším havárii, řeším
  instalaci tepelného čerpadla, řeším instalaci klimatizace apod.
- **Kam mají poptávky chodit: nedořešeno.** Padlo, že všechno na `info@`, ale zároveň že
  servisní poptávky by se měly napojit na jejich systém požadavků (dnes jim chodí
  „do mborku klukům jako požadavky i řízení"). Rozdělení poptávek nelze dokončit bez
  rozhodnutí klienta.

## 4. Administrace

- **Dvě samostatné administrace realizací** — zvlášť domácnosti, zvlášť firemní zákazníci.
  Řízení toho, co kam patří, bude plně na klientovi.
- Editovat se dají **texty, obrázky a další obsah**. **Rozložení webu zůstává pevné** —
  wireframe se needituje.
- Musí to být jednoduché: žádné kódování, žádné složité hledání.
- **Nástěnka se statistikami napojená na Google Analytics** přímo v administraci.
  Dohodnutý základ metrik:
  - počet návštěv a unikátních uživatelů za období
  - zdroje návštěvnosti (odkud lidé přišli)
  - vstupní stránky (landing pages)
  - míra okamžitého opuštění
  - čas strávený na stránce
  - zařízení (mobil / desktop)
  - odeslané poptávky a odkud přišly
  - vývoj v čase + přepínač časového rozmezí
  - **vysvětlivky pojmů** přímo u statistik (stejný princip jako zkratky na webu)
- **Více uživatelů s různými oprávněními** — např. samostatný login pro člověka z EcoAdepta,
  který bude psát články.
- V ukázce bude analytika **jen ukázková**; reálná data naběhnou až po nasazení a Google
  Analytics je začne zobrazovat zhruba po týdnu provozu.

## 5. SEO a marketing

- Zavést **samostatnou Google Search Console** a **sitemapu**.
- **Články důležité pro vyhledávání mají být primárně na webu Green Air Tech**, ne jen na
  externím webu (dnes EcoAdepto). Argument: návštěvník má přistát na webu klienta, ne na
  agregátoru.
- Spolupráce s EcoAdeptem stojí 24–25 tis. Kč na 2 roky a **její přínos se nijak neměří** —
  doporučeno doplnit do statistik samostatnou kolonku „kolik lidí přišlo z Adepta".
- U stávajícího WordPressu zaznělo riziko zastaralých modulů a chyb s certifikáty, pokud se
  pravidelně neudržuje (řádově 10 hodin měsíčně).

---

## Co z toho zapracuji do ukázky

1. Rozcestník na úvodu se dvěma velkými dlaždicemi.
2. Dvě větve webu s vlastními službami a realizacemi; společné O nás, Novinky, Kariéra, Kontakt.
3. Světlejší barevnost + automatický světlý/tmavý režim podle zařízení.
4. Zjednodušený poptávkový formulář s volbou typu poptávky.
5. Administrace: oddělené realizace pro obě větve, nástěnka se statistikami (ukázková data),
   správa uživatelů a oprávnění.
6. Sitemapa a příprava pro Search Console.
7. Tečky i vysvětlivky zůstávají beze změny.

## Co potřebuju rozhodnout od klienta

- **Kam mají chodit poptávky** zvlášť z domácností, firemních realizací a ze servisu.
- **Jestli nechat vítr** při přechodu mezi stránkami (klient ho zatím neviděl).
- **Kdo bude mít přístup do administrace** a s jakými oprávněními.
- **Jaké další metriky** nad rámec dohodnutého základu.
- **Kdo dodá texty, fotografie a první sadu realizací** pro obě větve.

## Co si zatím domýšlím (a je potřeba potvrdit)

- **Rozdělení služeb mezi větve.** Z hranice 500 tis. / 1 mil. Kč a z popisu v přepisu:
  - *Domácnosti:* klimatizace, tepelná čerpadla, rekuperace a větrání, servis a havárie.
  - *Firemní:* projekce TZB, realizace a montáže, servis TZB, PENB a audity, EAC filtry,
    opravy výměníků.
- **Pojmenování dlaždic.** Zatím „Domácnosti" a „Firemní zákazník" — v přepisu padlo, že
  přesné pojmenování je na klientovi („jak se to pojmenuje podle vás, ale řekněme malý
  zákazník, to je fuk").
- **Realizace pro domácnosti** zatím žádné nemáme; doplním ukázkové, označené jako smyšlené.
