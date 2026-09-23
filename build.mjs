/* Generátor statického webu Green Air Tech.
   `node build.mjs` -> out/web/  (funguje z file://, z GitHub Pages i z libovolného hostingu) */

import { readFile, writeFile, mkdir, rm, cp, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as i18n from "./src/lib/i18n.mjs";
import * as slovnikLib from "./src/lib/glossary.mjs";
import { stranka } from "./src/templates/layout.mjs";
import { favicon, ogObrazek } from "./src/templates/grafika.mjs";
import * as S from "./src/templates/stranky.mjs";
import { administrace } from "./src/templates/administrace.mjs";

const spawn = promisify(execFile);
const KOREN = path.dirname(fileURLToPath(import.meta.url));
const VEN = path.join(KOREN, "out", "web");

const nacti = async (p) => JSON.parse(await readFile(path.join(KOREN, p), "utf8"));

/* ----------------------------------------------------------- odkazy */
const SOUBORY = {
  index: "index.html",
  sluzby: "sluzby.html",
  realizace: "realizace.html",
  realizaceDetail: "realizace-detail.html",
  novinky: "novinky.html",
  onas: "o-nas.html",
  kariera: "kariera.html",
  kontakt: "kontakt.html",
  slovnik: "slovnik.html",
  gdpr: "ochrana-osobnich-udaju.html",
  chyba404: "404.html",
  administrace: "administrace.html",
};

function soubor(druh, id) {
  if (druh === "sluzba") return `sluzba-${id}.html`;
  if (druh === "realizace" && id) return `realizace-${id}.html`;
  if (druh === "novinka") return `novinka-${id}.html`;
  const s = SOUBORY[druh];
  if (!s) throw new Error(`Neznámý druh odkazu: ${druh}`);
  return s;
}

/* ----------------------------------------------------------- kontext */
function vytvorKontext({ lang, site, slovnik, zaskok, aktualniSoubor, obrazky }) {
  const jazyk = site.jazyky.find((j) => j.kod === lang);
  const prefix = jazyk.adresar ? "../" : "";
  const terminy = Object.entries(slovnik).map(([abbr, v]) => ({ abbr, full: v.full, popis: v.popis }));

  const dict = zaskok.dict;
  const t = (klic, vars = {}) => i18n.t(dict, klic, vars, zaskok.cs);
  const existuje = (klic) => {
    const v = i18n.get(dict, klic) ?? i18n.get(zaskok.cs, klic);
    return typeof v === "string" ? v.trim() !== "" : v != null;
  };
  const klice = (prefixKlice) => {
    const v = i18n.get(dict, prefixKlice) ?? i18n.get(zaskok.cs, prefixKlice);
    return v && typeof v === "object" ? Object.keys(v) : [];
  };

  const locale = { cs: "cs-CZ", en: "en-GB", de: "de-DE" }[lang] || "cs-CZ";
  const datum = (iso, tvar = "plny") => {
    const d = new Date(`${iso}T12:00:00Z`);
    const opts =
      tvar === "mesic"
        ? { month: "long", year: "numeric" }
        : { day: "numeric", month: "long", year: "numeric" };
    return new Intl.DateTimeFormat(locale, { ...opts, timeZone: "UTC" }).format(d);
  };

  const asset = (p) => `${prefix}assets/${p}`;
  const odkaz = (druh, id) => `${soubor(druh, id)}`;
  const jazykOdkaz = (kod) => {
    const cil = site.jazyky.find((j) => j.kod === kod);
    const jmeno = aktualniSoubor === SOUBORY.administrace && kod !== "cs" ? SOUBORY.index : aktualniSoubor;
    return `${prefix}${cil.adresar ? `${cil.adresar}/` : ""}${jmeno}`;
  };

  const zk = (html) => slovnikLib.annotate(String(html ?? ""), terminy, { once: true });
  const skupinyZkratek = () => slovnikLib.groupTerms(terminy);

  /** <picture> s WebP a záložním formátem podle manifestu z tools/optimize_images.py */
  const obrazek = (jmeno, { alt = "", sirky = "100vw", trida = "", prioritni = false } = {}) => {
    const z = obrazky[jmeno];
    if (!z) throw new Error(`Chybí obrázek v manifestu: ${jmeno}`);
    const cesta = (f) => asset(`img/${f}`);
    const srcset = (druh) => z.varianty.map((v) => `${cesta(v[druh])} ${v.w}w`).join(", ");
    const posledni = z.varianty[z.varianty.length - 1];
    return `<picture>
      <source type="image/webp" srcset="${srcset("webp")}" sizes="${sirky}">
      <img src="${cesta(posledni.zaloha)}" srcset="${srcset("zaloha")}" sizes="${sirky}"
        width="${posledni.w}" height="${posledni.h}" alt="${alt}" class="${trida}"
        ${prioritni ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">
    </picture>`;
  };

  const maObrazek = (jmeno) => Object.prototype.hasOwnProperty.call(obrazky, jmeno);

  const chybyFormulare = () =>
    Object.fromEntries(klice("kontakt.formular.chyby").map((k) => [k, t(`kontakt.formular.chyby.${k}`)]));

  return {
    lang, site, t, existuje, klice, datum, asset, odkaz, jazykOdkaz, zk, skupinyZkratek, obrazek, terminy,
    chybyFormulare, maObrazek,
    realizaceSeznam: site.realizace,
    novinkySeznam: site.novinky,
  };
}

/* ----------------------------------------------------------- bundl JS */
/** src/lib/*.mjs -> jeden klasický skript, aby web fungoval i z file:// (ESM tam CORS blokuje). */
async function bundlKnihoven() {
  const dir = path.join(KOREN, "src", "lib");
  const soubory = (await readdir(dir)).filter((f) => f.endsWith(".mjs")).sort();
  const casti = [];
  for (const f of soubory) {
    const zdroj = await readFile(path.join(dir, f), "utf8");
    if (/^\s*import\s/m.test(zdroj)) throw new Error(`${f}: modul v bundlu nesmí nic importovat`);
    const jmena = [...zdroj.matchAll(/^export\s+(?:function|const|let|class)\s+([A-Za-z0-9_$]+)/gm)].map((m) => m[1]);
    if (!jmena.length) throw new Error(`${f}: nenalezen žádný export`);
    const telo = zdroj.replace(/^export\s+/gm, "");
    const nazev = path.basename(f, ".mjs").replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    casti.push(
      `GAT.${nazev} = (function () {\n${telo}\nreturn { ${jmena.join(", ")} };\n})();`
    );
  }
  return `/* Sestaveno z src/lib/*.mjs – needitovat ručně. */\nvar GAT = window.GAT || {};\nwindow.GAT = GAT;\n${casti.join("\n\n")}\n`;
}

/* ----------------------------------------------------------- obrázky */
async function pripravObrazky() {
  const src = path.join(KOREN, "src", "assets", "img");
  const out = path.join(VEN, "assets", "img");
  await mkdir(out, { recursive: true });
  const { stdout } = await spawn(
    "uv",
    ["run", "python", "tools/optimize_images.py", src, out],
    { cwd: KOREN, maxBuffer: 1024 * 1024 * 16 }
  );
  return JSON.parse(stdout);
}

/* ----------------------------------------------------------- sestavení */
async function main() {
  const site = await nacti("data/site.json");
  const cs = await nacti("data/content/cs.json");
  const zkratkyNavic = await nacti("data/content/zkratky-navic.json");

  await rm(path.join(KOREN, "out"), { recursive: true, force: true });
  await mkdir(VEN, { recursive: true });

  // statická aktiva
  await mkdir(path.join(VEN, "assets"), { recursive: true });
  await cp(path.join(KOREN, "src", "assets", "style.css"), path.join(VEN, "assets", "style.css"));
  await cp(path.join(KOREN, "src", "assets", "admin.css"), path.join(VEN, "assets", "admin.css"));
  await cp(path.join(KOREN, "src", "assets", "fonts"), path.join(VEN, "assets", "fonts"), { recursive: true });

  const obrazky = await pripravObrazky();
  await cp(path.join(KOREN, "src", "assets", "img", "logo.png"), path.join(VEN, "assets", "img", "logo.png"));
  await cp(
    path.join(KOREN, "src", "assets", "img", "odznak-spolehliva-firma.png"),
    path.join(VEN, "assets", "img", "odznak-spolehliva-firma.png")
  );
  await writeFile(path.join(VEN, "assets", "img", "favicon.svg"), favicon());
  await writeFile(
    path.join(VEN, "assets", "img", "og.svg"),
    ogObrazek("Projekce · realizace · servis TZB")
  );

  const bundl = await bundlKnihoven();
  const app = await readFile(path.join(KOREN, "src", "assets", "app.js"), "utf8");
  const adminJs = await readFile(path.join(KOREN, "src", "assets", "admin.js"), "utf8");
  await writeFile(path.join(VEN, "assets", "app.js"), `${bundl}\n${app}`);
  await writeFile(path.join(VEN, "assets", "admin.js"), adminJs);

  await writeFile(
    path.join(VEN, "robots.txt"),
    "# Ukázkový návrh webu – neindexovat.\nUser-agent: *\nDisallow: /\n"
  );
  await writeFile(path.join(VEN, ".nojekyll"), "");

  let pocet = 0;
  const editovatelneKlice = new Set();
  const zapis = async (adresar, jmeno, html) => {
    const cil = path.join(VEN, adresar, jmeno);
    await mkdir(path.dirname(cil), { recursive: true });
    await writeFile(cil, html);
    for (const m of html.matchAll(/data-cms="([^"]+)"/g)) editovatelneKlice.add(m[1]);
    pocet += 1;
  };

  const jazyky = [];
  for (const j of site.jazyky) {
    const cesta = path.join(KOREN, "data", "content", `${j.kod}.json`);
    if (!existsSync(cesta)) {
      console.warn(`  ! chybí data/content/${j.kod}.json — jazyk ${j.kod} se přeskakuje`);
      continue;
    }
    jazyky.push({ ...j, dict: await nacti(`data/content/${j.kod}.json`) });
  }

  // do navigace a hreflang patří jen jazyky, které se opravdu postavily
  site.jazyky = jazyky.map(({ dict, ...zbytek }) => zbytek);

  for (const j of jazyky) {
    const adresar = j.adresar;
    // slovník jazyka + zkratky, které vznikly až překladem (TGA, RLT, MEP …)
    const slovnikTerminy = { ...(j.dict.slovnik?.terminy || cs.slovnik.terminy), ...(zkratkyNavic[j.kod] || {}) };

    const ctxPro = (aktualniSoubor) =>
      vytvorKontext({
        lang: j.kod,
        site,
        slovnik: slovnikTerminy,
        zaskok: { dict: j.dict, cs },
        aktualniSoubor,
        obrazky,
      });

    const vykresli = async (jmenoSouboru, telo, metaKlic, aktivni = "", trida = "", skripty = "") => {
      const ctx = ctxPro(jmenoSouboru);
      const html = stranka(
        { ...ctx, aktivni },
        {
          telo: typeof telo === "function" ? telo(ctx) : telo,
          titulek: ctx.t(`meta.${metaKlic}.titulek`),
          popis: ctx.t(`meta.${metaKlic}.popis`),
          trida,
          skripty,
        }
      );
      await zapis(adresar, jmenoSouboru, html);
    };

    await vykresli(SOUBORY.index, S.domu, "home", "index");
    await vykresli(SOUBORY.sluzby, S.sluzbyPrehled, "sluzby", "sluzby");
    for (const s of site.sluzby) {
      await vykresli(soubor("sluzba", s.id), (c) => S.sluzbaDetail(c, s), "sluzby", "sluzby");
    }
    await vykresli(SOUBORY.realizace, S.realizacePrehled, "realizace", "realizace");
    for (const r of site.realizace) {
      await vykresli(soubor("realizace", r.id), (c) => S.realizaceDetail(c, r), "realizace", "realizace");
    }
    await vykresli(SOUBORY.realizaceDetail, S.realizaceSablona, "realizace", "realizace");
    await vykresli(SOUBORY.onas, S.oNas, "onas", "onas");
    await vykresli(SOUBORY.novinky, S.novinkyPrehled, "novinky", "novinky");
    for (const n of site.novinky) {
      await vykresli(soubor("novinka", n.id), (c) => S.novinkaDetail(c, n), "novinky", "novinky");
    }
    await vykresli(SOUBORY.kariera, S.kariera, "kariera", "kariera");
    await vykresli(SOUBORY.kontakt, S.kontakt, "kontakt", "kontakt");
    await vykresli(SOUBORY.slovnik, S.slovnik, "slovnik", "slovnik");
    await vykresli(SOUBORY.gdpr, S.gdpr, "gdpr");
    await vykresli(SOUBORY.chyba404, S.chyba404, "chyba404");
  }

  // administrace jen v češtině
  {
    const ctx = vytvorKontext({
      lang: "cs",
      site,
      slovnik: cs.slovnik.terminy,
      zaskok: { dict: cs, cs },
      aktualniSoubor: SOUBORY.administrace,
      obrazky,
    });
    const slovniky = Object.fromEntries(jazyky.map((j) => [j.kod, i18n.flatten(j.dict)]));
    const realizaceProAdmin = site.realizace.map((r) => ({
      id: r.id,
      motiv: r.motiv,
      datum: r.datum,
      kategorie: r.kategorie,
      plocha: r.plocha,
      doba: r.doba,
      nazev: ctx.t(`realizace.polozky.${r.id}.nazev`),
      misto: ctx.t(`realizace.polozky.${r.id}.misto`),
      perex: ctx.t(`realizace.polozky.${r.id}.perex`),
      zadani: ctx.t(`realizace.polozky.${r.id}.zadani`),
      vysledek: ctx.t(`realizace.polozky.${r.id}.vysledek`),
      rozsah: ctx.klice(`realizace.polozky.${r.id}.rozsah`).map((k) => ctx.t(`realizace.polozky.${r.id}.rozsah.${k}`)),
      technologie: ctx
        .klice(`realizace.polozky.${r.id}.technologie`)
        .map((k) => ctx.t(`realizace.polozky.${r.id}.technologie.${k}`)),
    }));
    const adminData = {
      klice: [...editovatelneKlice].sort(),
      slovniky,
      realizace: realizaceProAdmin,
      kategorie: Object.fromEntries(site.kategorieRealizaci.map((k) => [k, ctx.t(`realizace.kategorie.${k}`)])),
    };
    const html = stranka(
      { ...ctx, aktivni: "administrace" },
      {
        telo: administrace(ctx, adminData),
        titulek: ctx.t("meta.administrace.titulek"),
        popis: ctx.t("meta.administrace.popis"),
        trida: "je-administrace",
        skripty: `<link rel="stylesheet" href="${ctx.asset("admin.css")}">\n<script src="${ctx.asset("admin.js")}" defer></script>`,
      }
    );
    await zapis("", SOUBORY.administrace, html);
  }

  // kontrola úplnosti překladů
  for (const j of jazyky.filter((x) => x.kod !== "cs")) {
    const chybi = i18n.missingKeys(cs, j.dict);
    if (chybi.length) {
      console.warn(`  ! ${j.kod}: chybí ${chybi.length} překladů (např. ${chybi.slice(0, 3).join(", ")})`);
    }
  }

  console.log(`Hotovo: ${pocet} stránek v ${jazyky.length} jazycích -> out/web`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
