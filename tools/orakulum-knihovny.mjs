/* Orákulum pro přepis knihoven do PHP.
   Spustí funkce z src/lib/*.mjs na skutečných datech webu i na okrajových
   vstupech a zapíše ZAZNAMENANÉ vzorky do tests/orakulum/*.json.
   PHP implementace se pak musí na týchž vstupech chovat stejně. */

import { readFile, writeFile } from "node:fs/promises";
import * as i18n from "../src/lib/i18n.mjs";
import * as glos from "../src/lib/glossary.mjs";
import * as filtr from "../src/lib/realizace-filter.mjs";
import * as form from "../src/lib/form-validate.mjs";
import * as cms from "../src/lib/cms-store.mjs";

const nacti = async (p) => JSON.parse(await readFile(new URL(`../${p}`, import.meta.url), "utf8"));
const cs = await nacti("data/content/cs.json");
const en = await nacti("data/content/en.json");
const de = await nacti("data/content/de.json");
const zkratkyNavic = await nacti("data/content/zkratky-navic.json");
const site = await nacti("data/site.json");

/** undefined se v JSON nepřenese; zapisujeme ho jako značku. */
const ZNACKA_UNDEF = "\u0000undefined";
const uprav = (v) => (v === undefined ? ZNACKA_UNDEF : v);

const pripady = (vzorky) =>
  vzorky.map(([args, out]) => ({ args: args.map(uprav), out: uprav(out) }));

const vzorek = (fn, seznamArgs) => pripady(seznamArgs.map((a) => [a, fn(...a)]));

/* --------------------------------------------------------------- i18n */
const terminy = Object.entries(cs.slovnik.terminy).map(([abbr, v]) => ({
  abbr, full: v.full, popis: v.popis,
}));

const i18nVzorky = {
  get: vzorek(i18n.get, [
    [cs, "nav.sluzby"],
    [cs, "meta.home.titulek"],
    [cs, "slovnik.terminy"],
    [cs, "neexistuje.vubec"],
    [cs, "nav"],
    [cs, ""],
    [cs, "nav.sluzby.hloubeji"],
    [null, "nav.sluzby"],
  ]),
  t: vzorek(i18n.t, [
    [cs, "nav.sluzby", {}, null],
    [cs, "kontakt.formular.odeslat", {}, null],
    [en, "nav.sluzby", {}, cs],
    [en, "neexistuje.klic", {}, cs],
    [cs, "neexistuje.klic", {}, null],
    [cs, "admin.realizace.fotkySouhrn", { pocet: 3, velikost: "742 kB" }, null],
    [cs, "admin.realizace.fotkySouhrn", {}, null],
    [cs, "slovnik.terminy", {}, null],
  ]),
  flatten: vzorek(i18n.flatten, [[cs], [{ a: { b: "x" }, c: "y" }], [{}]]),
  missingKeys: vzorek(i18n.missingKeys, [[cs, en], [cs, {}], [{ a: "1" }, { a: "2" }]]),
};
i18nVzorky.unflatten = vzorek(i18n.unflatten, [
  [i18n.flatten({ a: { b: "x" }, c: "y" })],
  [{ "x.y.z": "1", "x.y.w": "2" }],
  [{}],
]);

/* ----------------------------------------------------------- slovník */
const textyKAnotaci = [
  cs.vetve.firmy.perex,
  cs.vetve.firmy.lead,
  cs.vetve.domacnosti.perex,
  cs.sluzby.polozky.projekce.popis,
  cs.meta.home.popis,
  "<p>TZB a VZT v jedné větě, TZB podruhé.</p>",
  "<p>Odkaz s <a href='#'>TZB uvnitř</a> a TZB mimo.</p>",
  "<p>V atributu alt=\"TZB\" se nic nenahrazuje.</p>",
  "Prostý text bez značek s HVAC.",
  "",
  "<p>EPC, PENB, VZT, TUV — čtyři zkratky za sebou.</p>",
];
/* Řazení a seskupení se musí ověřit i na diakritice: v ukázce padá ČSN do
   skupiny „Č", ne „C". Proto plné seznamy všech tří jazyků (včetně zkratek,
   které vzniknou až překladem) a navíc syntetická sada, kde na sebe narazí
   C/Č, R/Ř, S/Š, Z/Ž, A/Á a dvojí velikost písmen. */
const terminyZ = (dict, kod) => Object.entries({
  ...(dict.slovnik?.terminy || cs.slovnik.terminy),
  ...(zkratkyNavic[kod] || {}),
}).map(([abbr, v]) => ({ abbr, full: v.full, popis: v.popis }));
const terminyEn = terminyZ(en, "en");
const terminyDe = terminyZ(de, "de");
const diakritika = [
  "ČSN", "CZT", "Čerpadlo", "ČEZ", "COP", "ÚNMZ", "UV", "Úspora", "ŘSD", "RD",
  "ŠKODA", "SFDI", "ŽB", "ZTI", "Áčko", "ADS", "ĎOUBEK", "DN", "ŇUFÍK", "NN",
  "ŤUKAT", "TUV", "ĚČKO", "EPC", "CHLAZENÍ", "CO2", "a", "A", "ár", "Ár",
].map((abbr, i) => ({ abbr, full: `plné ${abbr}`, popis: i % 3 === 0 ? `popis ${abbr}` : undefined }));
const jednoPismeno = ["Z", "A", "Č", "C", "Ž", "S", "Š", "R", "Ř"]
  .map((abbr) => ({ abbr, full: abbr, popis: abbr }));

/* ------------------------------------------------- české řazení
   Tři místa v ukázce řadí přes localeCompare(x, 'cs'): zkratky ve slovníku,
   id kategorií a názvy realizací. PHP nemá intl, takže se comparator píše
   ručně — a tohle orákulum je jeho jediná pravda. Páry se generují křížem,
   aby se neminulo nic z toho, co ICU dělá: ch jako jedno písmeno mezi h a i,
   diakritika jako druhá úroveň (a < á < b) a malá písmena před velkými. */
const slovaKRazeni = [
  "", "a", "A", "á", "Á", "ar", "ár", "Ar", "b", "c", "C", "ca", "ča", "cb",
  "č", "Č", "CSN", "ČSN", "ch", "CH", "Chlazení", "ci", "h", "hz", "i",
  "r", "ř", "rz", "s", "š", "sz", "t", "ť", "u", "ú", "ů", "z", "ž", "zz",
  "e", "ě", "é", "n", "ň", "d", "ď", "o", "ó", "y", "ý",
  "PM2,5", "PM 10", "PM-10", "TZB", "tzb", "VZT", "Straße", "Grün", "Gründach",
  "Österreich", "Ostern", "Ärger", "Arger", "1", "2", "10", "A1", "A2",
];
const razeniVzorky = {
  porovnej: pripady(
    slovaKRazeni.flatMap((a) => slovaKRazeni.map((b) => [[a, b], Math.sign(a.localeCompare(b, "cs"))]))
  ),
  seradit: pripady([
    [[slovaKRazeni.slice()], slovaKRazeni.slice().sort((a, b) => a.localeCompare(b, "cs"))],
    [[["ČSN", "CSN", "CZT", "COP"]], ["ČSN", "CSN", "CZT", "COP"].sort((a, b) => a.localeCompare(b, "cs"))],
    [[[]], []],
    [[["jediny"]], ["jediny"]],
  ]),
};

const slovnikVzorky = {
  annotate: pripady(
    textyKAnotaci.flatMap((h) => [
      [[h, terminy, { once: true }], glos.annotate(h, terminy, { once: true })],
      [[h, terminy, {}], glos.annotate(h, terminy, {})],
    ])
  ),
  findTerm: vzorek(glos.findTerm, [
    [terminy, "TZB"], [terminy, "tzb"], [terminy, "NENI"], [terminy, ""], [[], "TZB"],
  ]),
  sortTerms: vzorek(glos.sortTerms, [
    [terminy], [terminyEn], [terminyDe], [diakritika], [jednoPismeno],
    [[]], [[diakritika[0]]],
  ]),
  groupTerms: vzorek(glos.groupTerms, [
    [terminy], [terminyEn], [terminyDe], [diakritika], [jednoPismeno],
    [[]], [[diakritika[0]]],
  ]),
};

/* -------------------------------------------------- filtr realizací */
const dictT = (klic) => i18n.t(cs, klic, {}, cs);
const realizaceProFiltr = site.realizace.map((r) => ({
  ...r,
  nazev: dictT(`realizace.polozky.${r.id}.nazev`),
  misto: dictT(`realizace.polozky.${r.id}.misto`),
  perex: dictT(`realizace.polozky.${r.id}.perex`),
}));
const filtrVzorky = {
  normalizeText: vzorek(filtr.normalizeText, [
    ["Příšerně žluťoučký kůň"], ["  MEZERY  "], [""], [null], [123], ["ČESKÁ ULICE 5"],
  ]),
  filterItems: pripady([
    [[realizaceProFiltr, {}], filtr.filterItems(realizaceProFiltr, {})],
    [[realizaceProFiltr, { kategorie: "vzt" }], filtr.filterItems(realizaceProFiltr, { kategorie: "vzt" })],
    [[realizaceProFiltr, { dotaz: "praha" }], filtr.filterItems(realizaceProFiltr, { dotaz: "praha" })],
    [[realizaceProFiltr, { dotaz: "PÍSEK" }], filtr.filterItems(realizaceProFiltr, { dotaz: "PÍSEK" })],
    [[realizaceProFiltr, { rok: 2025 }], filtr.filterItems(realizaceProFiltr, { rok: 2025 })],
    [[realizaceProFiltr, { rok: "2025" }], filtr.filterItems(realizaceProFiltr, { rok: "2025" })],
    [[realizaceProFiltr, { kategorie: "vzt", dotaz: "a" }], filtr.filterItems(realizaceProFiltr, { kategorie: "vzt", dotaz: "a" })],
    [[realizaceProFiltr, { dotaz: "nic-takoveho-neni" }], filtr.filterItems(realizaceProFiltr, { dotaz: "nic-takoveho-neni" })],
    [[[], {}], filtr.filterItems([], {})],
  ]),
  collectKategorie: vzorek(filtr.collectKategorie, [[realizaceProFiltr], [[]]]),
  collectRoky: vzorek(filtr.collectRoky, [[realizaceProFiltr], [[]]]),
  sortItems: vzorek(filtr.sortItems, [
    [realizaceProFiltr, "datum"], [realizaceProFiltr, "datum-vzestupne"],
    [realizaceProFiltr, "nazev"], [realizaceProFiltr, "neznamy"], [[], "datum"],
  ]),
  paginate: vzorek(filtr.paginate, [
    [realizaceProFiltr, 1, 3], [realizaceProFiltr, 2, 3], [realizaceProFiltr, 99, 3],
    [realizaceProFiltr, 0, 3], [realizaceProFiltr, 1, 0], [[], 1, 3],
  ]),
};

/* -------------------------------------------------------- formulář */
const zpravy = Object.fromEntries(
  Object.keys(cs.kontakt.formular.chyby).map((k) => [k, cs.kontakt.formular.chyby[k]])
);
const formVzorky = {
  isEmail: vzorek(form.isEmail, [
    ["a@b.cz"], ["jan.novak@green-air.cz"], ["bez-zavinace"], ["a@b"], ["a@@b.cz"],
    [" a@b.cz "], [""], [null], ["a@b.c"], ["velmi.dlouhy+tag@sub.domena.co.uk"],
  ]),
  normalizePhone: vzorek(form.normalizePhone, [
    ["+420 601 123 456"], ["601123456"], ["00420601123456"], ["601-123-456"],
    [""], [null], ["abc"], [" 601 123 456 "],
  ]),
  isPhoneCz: vzorek(form.isPhoneCz, [
    ["+420 601 123 456"], ["601123456"], ["123"], [""], [null], ["00420601123456"], ["+421601123456"],
  ]),
  validateContact: pripady([
    [[{ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz." }, zpravy],
      form.validateContact({ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz." }, zpravy)],
    [[{}, zpravy], form.validateContact({}, zpravy)],
    [[{ jmeno: " ", email: "spatny", zprava: "" }, zpravy],
      form.validateContact({ jmeno: " ", email: "spatny", zprava: "" }, zpravy)],
    [[{ jmeno: "Jan", email: "a@b.cz", zprava: "krátká", telefon: "123" }, zpravy],
      form.validateContact({ jmeno: "Jan", email: "a@b.cz", zprava: "krátká", telefon: "123" }, zpravy)],
    [[{ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz.", telefon: "+420 601 123 456" }, zpravy],
      form.validateContact({ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz.", telefon: "+420 601 123 456" }, zpravy)],
    [[{ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz." }, {}],
      form.validateContact({ jmeno: "Jan", email: "a@b.cz", zprava: "Dobrý den, mám dotaz." }, {})],
  ]),
};

/* -------------------------------------------------------- datumy */
const datumVzorky = { format: [] };
for (const [lang, locale] of [["cs", "cs-CZ"], ["en", "en-GB"], ["de", "de-DE"]]) {
  for (const iso of ["2026-01-01", "2026-02-09", "2026-03-31", "2026-05-15", "2026-07-04",
                     "2026-09-30", "2026-10-22", "2026-12-24", "2025-06-01", "2024-11-11"]) {
    for (const tvar of ["plny", "mesic"]) {
      const d = new Date(`${iso}T12:00:00Z`);
      const opts = tvar === "mesic" ? { month: "long", year: "numeric" }
                                    : { day: "numeric", month: "long", year: "numeric" };
      datumVzorky.format.push({
        args: [lang, iso, tvar],
        out: new Intl.DateTimeFormat(locale, { ...opts, timeZone: "UTC" }).format(d),
      });
    }
  }
}


/* ----------------------------------------------------- stav administrace */
/* Předloha je src/lib/cms-store.mjs: administrace drží změny jako "stav"
   (přepsané texty + přidané/změněné/smazané realizace) a teprve při
   vykreslení se překládá přes výchozí obsah. PHP to musí umět stejně,
   protože ostrý web vykresluje server. */
const zaklad = site.realizace.map((r) => ({
  id: r.id, nazev: r.nazev, datum: r.datum, vetev: r.vetev, kategorie: r.kategorie,
}));
const prazdny = cms.emptyState();
const sTexty = cms.setText(cms.setText(prazdny, "cs", "nav.sluzby", "Co umíme"), "en", "nav.sluzby", "What we do");
const sPridana = cms.upsertRealizace(prazdny, { nazev: "Nová čistírna Říčany", datum: "2026-11-02", vetev: "firmy" }, zaklad);
const sDve = cms.upsertRealizace(sPridana, { nazev: "Nová čistírna Říčany", datum: "2026-11-03", vetev: "firmy" }, zaklad);
const sZmenena = cms.upsertRealizace(prazdny, { id: zaklad[0].id, nazev: "Jiný název" }, zaklad);
const sSmazana = cms.removeRealizace(sZmenena, zaklad[1].id);
const sPlny = cms.removeRealizace(cms.upsertRealizace(sSmazana, { nazev: "Bez data" }, zaklad), zaklad[2].id);

const cmsVzorky = {
  emptyState: vzorek(cms.emptyState, [[]]),
  slugify: vzorek(cms.slugify, [
    ["Rekonstrukce kotelny Říčany"], ["ČOV Hostivice – 2. etapa"], ["  více   mezer  "],
    ["ÚPLNĚ Velká ŽLUŤOUČKÁ zpráva"], ["---"], [""], ["2026 / rok"], ["Grün Air Straße"],
  ]),
  setText: vzorek(cms.setText, [
    [prazdny, "cs", "nav.sluzby", "Co umíme"],
    [sTexty, "cs", "nav.sluzby", "Jinak"],
    [sTexty, "cs", "nav.sluzby", ""],
    [sTexty, "cs", "nav.sluzby", "   "],
    [sTexty, "de", "nav.kontakt", "Kontakt"],
    [prazdny, "cs", "slovnik.terminy", "nesmysl"],
  ]),
  getText: vzorek(cms.getText, [
    [sTexty, "cs", "nav.sluzby"], [sTexty, "cs", "neexistuje"], [sTexty, "de", "nav.sluzby"],
    [prazdny, "cs", "nav.sluzby"],
  ]),
  mergeTexts: vzorek(cms.mergeTexts, [
    [sTexty, "cs", i18n.flatten(cs)],
    [sTexty, "en", i18n.flatten(en)],
    [sTexty, "de", { "nav.sluzby": "Leistungen" }],
    [prazdny, "cs", { "nav.sluzby": "Služby" }],
    [sTexty, "cs", {}],
  ]),
  upsertRealizace: vzorek(cms.upsertRealizace, [
    [prazdny, { nazev: "Nová čistírna Říčany", datum: "2026-11-02", vetev: "firmy" }, zaklad],
    [sPridana, { nazev: "Nová čistírna Říčany", datum: "2026-11-05", vetev: "firmy" }, zaklad],
    [sDve, { id: "nova-cistirna-ricany", nazev: "Přejmenovaná" }, zaklad],
    [prazdny, { id: zaklad[0].id, nazev: "Jiný název" }, zaklad],
    [sSmazana, { id: zaklad[1].id, nazev: "Vrácená" }, zaklad],
    [prazdny, { nazev: "Bez data" }, zaklad],
    [prazdny, { nazev: "Bez základu" }, []],
  ]),
  removeRealizace: vzorek(cms.removeRealizace, [
    [sPridana, "nova-cistirna-ricany"],
    [sZmenena, zaklad[0].id],
    [prazdny, zaklad[1].id],
    [sSmazana, zaklad[1].id],
    [prazdny, "neexistuje"],
  ]),
  mergeRealizace: vzorek(cms.mergeRealizace, [
    [prazdny, zaklad],
    [sPridana, zaklad],
    [sPlny, zaklad],
    [sZmenena, zaklad],
    [prazdny, []],
    [sPridana, []],
  ]),
  importJson: vzorek(cms.importJson, [
    [prazdny, JSON.stringify(sTexty)],
    [prazdny, JSON.stringify({ texts: { cs: { "a.b": "x" } } })],
    [prazdny, JSON.stringify({})],
    [prazdny, JSON.stringify([1, 2])],
    [prazdny, JSON.stringify("text")],
    [prazdny, JSON.stringify(null)],
  ]),
};

/* -------------------------------------------------------------- zápis */
const vse = {
  "i18n": i18nVzorky,
  "razeni-cs": razeniVzorky,
  "slovnik": slovnikVzorky,
  "realizace-filtr": filtrVzorky,
  "formular": formVzorky,
  "datum": datumVzorky,
  "cms-store": cmsVzorky,
};
/* Dá se vybrat jen část: `node tools/orakulum-knihovny.mjs cms-store`.
   Orákulum běžícího kontraktu se nesmí přepsat pod rukama. */
const jen = process.argv.slice(2);
let celkem = 0;
for (const [jmeno, data] of Object.entries(vse)) {
  if (jen.length > 0 && !jen.includes(jmeno)) continue;
  const cesta = new URL(`../tests/orakulum/${jmeno}.json`, import.meta.url);
  await writeFile(cesta, JSON.stringify(data, null, 1));
  const n = Object.values(data).reduce((s, v) => s + v.length, 0);
  celkem += n;
  console.log(`  ${jmeno}.json: ${Object.keys(data).length} funkcí, ${n} vzorků`);
}
console.log(`Celkem ${celkem} zaznamenaných vzorků.`);
