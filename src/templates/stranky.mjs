/* Těla jednotlivých stránek. */

import { ikona } from "./ikony.mjs";
import { podhlavi, vyzva, potrubiDelic } from "./layout.mjs";
import { motivRealizace, heroSchema } from "./grafika.mjs";

const dc = (k) => ` data-cms="${k}"`;

/* ------------------------------------------------------------ sdílené díly */

function kartaSluzby(ctx, s, { kompakt = false } = {}) {
  const { t, odkaz } = ctx;
  return `<a class="karta-sluzba" href="${odkaz("sluzba", s.id)}">
    <span class="karta-ikona">${ikona(s.ikona)}</span>
    <h3${dc(`sluzby.polozky.${s.id}.nazev`)}>${t(`sluzby.polozky.${s.id}.nazev`)}</h3>
    ${kompakt ? "" : `<p${dc(`sluzby.polozky.${s.id}.kratky`)}>${ctx.zk(t(`sluzby.polozky.${s.id}.kratky`))}</p>`}
    <span class="odkaz-sip">${t("ui.viceOSluzbe")}${ikona("sip")}</span>
  </a>`;
}

function kartaRealizace(ctx, r) {
  const { t, odkaz, datum } = ctx;
  const nazev = t(`realizace.polozky.${r.id}.nazev`);
  const stitky = r.kategorie
    .slice(0, 2)
    .map((k) => `<span class="odznak">${t(`realizace.kategorie.${k}`)}</span>`)
    .join("");
  return `<a class="karta-realizace" href="${odkaz("realizace", r.id)}">
    <span class="karta-nahled" data-motiv="${r.motiv}">${motivRealizace(r.motiv)}<span class="stitky">${stitky}</span></span>
    <span class="telo">
      <h3${dc(`realizace.polozky.${r.id}.nazev`)}>${nazev}</h3>
      <span class="karta-meta">
        <span>${ikona("misto", { velikost: 15 })}${t(`realizace.polozky.${r.id}.misto`)}</span>
        <span>${ikona("kalendar", { velikost: 15 })}${datum(r.datum, "mesic")}</span>
      </span>
      <p${dc(`realizace.polozky.${r.id}.perex`)}>${ctx.zk(t(`realizace.polozky.${r.id}.perex`))}</p>
      <span class="odkaz-sip">${t("ui.vice")}${ikona("sip")}</span>
    </span>
  </a>`;
}

function kartaNovinky(ctx, n) {
  const { t, odkaz, datum } = ctx;
  return `<a class="karta-clanek" href="${odkaz("novinka", n.id)}">
    <span class="nahled">${motivRealizace(n.motiv)}</span>
    <span class="telo">
      <span class="datum">${datum(n.datum)}</span>
      <h3${dc(`novinky.polozky.${n.id}.nazev`)}>${t(`novinky.polozky.${n.id}.nazev`)}</h3>
      <p${dc(`novinky.polozky.${n.id}.perex`)}>${ctx.zk(t(`novinky.polozky.${n.id}.perex`))}</p>
      <span class="odkaz-sip">${t("ui.cist")}${ikona("sip")}</span>
    </span>
  </a>`;
}

function kartaClovek(ctx, osoba) {
  const { t } = ctx;
  return `<div class="karta-clovek">
    <span class="avatar" aria-hidden="true">${osoba.inicialy}</span>
    <span class="jmeno">${osoba.jmeno}</span>
    <span class="role"${dc(`lide.${osoba.id}`)}>${t(`lide.${osoba.id}`)}</span>
    <a href="tel:${osoba.telefonHref}">${ikona("telefon")}${osoba.telefon}</a>
    <a href="mailto:${osoba.email}">${ikona("mail")}${osoba.email}</a>
  </div>`;
}

function seznamOdskrtnuty(ctx, prefix) {
  const { t, klice } = ctx;
  return `<ul class="seznam-odskrtnuty">${klice(prefix)
    .map((k) => `<li>${ikona("fajfka")}<span${dc(`${prefix}.${k}`)}>${ctx.zk(t(`${prefix}.${k}`))}</span></li>`)
    .join("")}</ul>`;
}

function kroky(ctx, prefix) {
  const { t, klice } = ctx;
  return `<div class="postup">${klice(prefix)
    .map(
      (k) => `<div class="krok">
        <h3${dc(`${prefix}.${k}.titulek`)}>${t(`${prefix}.${k}.titulek`)}</h3>
        <p${dc(`${prefix}.${k}.popis`)}>${ctx.zk(t(`${prefix}.${k}.popis`))}</p>
      </div>`
    )
    .join("")}</div>`;
}

/** Kontaktní formulář — stejná komponenta na Kontaktu i v Kariéře. */
export function formular(ctx, { predvolenyTyp = "", id = "formular" } = {}) {
  const { t, odkaz } = ctx;
  const typy = ctx.klice("kontakt.formular.typy");
  const volby = typy
    .map(
      (k) =>
        `<option value="${k}"${k === predvolenyTyp ? " selected" : ""}>${t(`kontakt.formular.typy.${k}`)}</option>`
    )
    .join("");
  return `<form class="formular" id="${id}" data-formular novalidate>
  <div class="hlaska hlaska-info">${ikona("info")}<span${dc("kontakt.formular.odeslanoDemo")}>${t("kontakt.formular.odeslanoDemo")}</span></div>
  <div class="formular-dvojice">
    <div class="pole">
      <label for="${id}-jmeno">${t("kontakt.formular.jmeno")} <span aria-hidden="true">*</span></label>
      <input type="text" id="${id}-jmeno" name="jmeno" autocomplete="name" required>
    </div>
    <div class="pole">
      <label for="${id}-firma">${t("kontakt.formular.firma")}</label>
      <input type="text" id="${id}-firma" name="firma" autocomplete="organization">
    </div>
    <div class="pole">
      <label for="${id}-email">${t("kontakt.formular.email")} <span aria-hidden="true">*</span></label>
      <input type="email" id="${id}-email" name="email" autocomplete="email" required>
    </div>
    <div class="pole">
      <label for="${id}-telefon">${t("kontakt.formular.telefon")}</label>
      <input type="tel" id="${id}-telefon" name="telefon" autocomplete="tel" inputmode="tel">
    </div>
  </div>
  <div class="pole">
    <label for="${id}-typ">${t("kontakt.formular.typ")}</label>
    <select id="${id}-typ" name="typ">${volby}</select>
  </div>
  <div class="pole">
    <label for="${id}-zprava">${t("kontakt.formular.zprava")} <span aria-hidden="true">*</span></label>
    <textarea id="${id}-zprava" name="zprava" required></textarea>
    <span class="napoveda">${t("kontakt.formular.zpravaHint")}</span>
  </div>
  <div class="pole">
    <label class="zaskrtavatko">
      <input type="checkbox" name="souhlas" value="1" required>
      <span>${t("kontakt.formular.souhlas")} <a href="${odkaz("gdpr")}">${t("kontakt.formular.souhlasOdkaz")}</a></span>
    </label>
  </div>
  <input type="text" class="medovy" name="vebsajt" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button type="submit" class="tl tl-hlavni">${ikona("mail")}${t("ui.odeslat")}</button>
</form>`;
}

/* ------------------------------------------------------------------ úvod */

export function domu(ctx) {
  const { t, site, odkaz, asset } = ctx;
  const cisla = ["praxe", "oblasti", "dispecink", "technici"]
    .map(
      (k) =>
        `<div><b${dc(`home.cisla.${k}.hodnota`)}>${t(`home.cisla.${k}.hodnota`)}</b><span${dc(`home.cisla.${k}.popis`)}>${t(`home.cisla.${k}.popis`)}</span></div>`
    )
    .join("");

  const posledni = ctx.realizaceSeznam.slice(0, 3).map((r) => kartaRealizace(ctx, r)).join("");
  const duvody = ctx
    .klice("home.duvody.polozky")
    .map(
      (k) => `<div class="karta-sluzba" style="cursor:default">
        <span class="karta-ikona">${ikona(k === "udrzitelnost" ? "list" : k === "jedenTym" ? "lide" : "hodiny")}</span>
        <h3${dc(`home.duvody.polozky.${k}.titulek`)}>${t(`home.duvody.polozky.${k}.titulek`)}</h3>
        <p${dc(`home.duvody.polozky.${k}.popis`)}>${ctx.zk(t(`home.duvody.polozky.${k}.popis`))}</p>
      </div>`
    )
    .join("");

  return `<section class="hero">
  <canvas class="hero-platno" data-vitr="hero" aria-hidden="true"></canvas>
  <div class="obal hero-vnitrek">
    <div>
      <span class="stitek"${dc("home.hero.stitek")}>${t("home.hero.stitek")}</span>
      <h1${dc("home.hero.titulek")}>${t("home.hero.titulek")}</h1>
      <p class="lead"${dc("home.hero.lead")}>${ctx.zk(t("home.hero.lead"))}</p>
      <div class="tlacitka">
        <a class="tl tl-hlavni" href="${odkaz("kontakt")}#formular">${ikona("mail")}${t("home.hero.cta")}</a>
        <a class="tl tl-obrys" href="#sluzby">${ikona("sipDolu")}${t("home.hero.ctaDruhe")}</a>
      </div>
      <a class="hero-dispecink" href="tel:${site.firma.dispecinkTelefonHref}">
        <span class="zivy">${ikona("telefon", { velikost: 16 })}</span>
        <span>${t("home.hero.dispecinkStitek")} <b>${site.firma.dispecinkTelefon}</b></span>
      </a>
    </div>
    <div class="hero-obrazek">
      ${ctx.obrazek("foto-strojovna", { alt: "Strojovna s rozvody vzduchotechniky", sirky: "(min-width: 1000px) 44vw, 92vw", prioritni: true })}
      ${heroSchema()}
    </div>
  </div>
  <div class="obal"><div class="hero-pruh">${cisla}</div></div>
</section>

<section class="sekce" id="sluzby">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"${dc("home.sluzby.stitek")}>${t("home.sluzby.stitek")}</span>
      <h2${dc("home.sluzby.titulek")}>${t("home.sluzby.titulek")}</h2>
      <p class="lead"${dc("home.sluzby.lead")}>${ctx.zk(t("home.sluzby.lead"))}</p>
    </div>
    <div class="mrizka mrizka-3">${site.sluzby.map((s) => kartaSluzby(ctx, s)).join("")}</div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"${dc("home.postup.stitek")}>${t("home.postup.stitek")}</span>
      <h2${dc("home.postup.titulek")}>${t("home.postup.titulek")}</h2>
      <p class="lead"${dc("home.postup.lead")}>${ctx.zk(t("home.postup.lead"))}</p>
    </div>
    ${kroky(ctx, "home.postup.kroky")}
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"${dc("home.realizace.stitek")}>${t("home.realizace.stitek")}</span>
      <h2${dc("home.realizace.titulek")}>${t("home.realizace.titulek")}</h2>
      <p class="lead"${dc("home.realizace.lead")}>${ctx.zk(t("home.realizace.lead"))}</p>
    </div>
    <div class="mrizka mrizka-3">${posledni}</div>
    <div class="tlacitka" style="margin-top:2rem">
      <a class="tl tl-obrys" href="${odkaz("realizace")}">${t("ui.vsechnyRealizace")}${ikona("sip")}</a>
    </div>
  </div>
</section>

${potrubiDelic()}

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek"${dc("home.duvody.stitek")}>${t("home.duvody.stitek")}</span>
      <h2${dc("home.duvody.titulek")}>${t("home.duvody.titulek")}</h2>
    </div>
    <div class="mrizka mrizka-3">${duvody}</div>
  </div>
</section>

<section class="sekce sekce-tmava">
  <canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <span class="stitek"${dc("home.slovnik.stitek")}>${t("home.slovnik.stitek")}</span>
        <h2${dc("home.slovnik.titulek")}>${t("home.slovnik.titulek")}</h2>
        <p class="lead" style="margin-bottom:1.6rem"${dc("home.slovnik.lead")}>${t("home.slovnik.lead")}</p>
        <p class="slovnik-ukazka"${dc("home.slovnik.ukazka")}>${ctx.zk(t("home.slovnik.ukazka"))}</p>
        <a class="tl tl-obrys" href="${odkaz("slovnik")}">${ikona("dokument")}${t("home.slovnik.cta")}</a>
      </div>
      <div>
        ${ctx.obrazek("foto-servis", { alt: "Kazetová klimatizační jednotka pod stropem", sirky: "(min-width: 940px) 40vw, 92vw", trida: "dvojsloupec-obraz" })}
      </div>
    </div>
  </div>
</section>

<section class="sekce sekce-papir" id="kontakt">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <span class="stitek"${dc("home.kontakt.stitek")}>${t("home.kontakt.stitek")}</span>
        <h2${dc("home.kontakt.titulek")}>${t("home.kontakt.titulek")}</h2>
        <p class="lead"${dc("home.kontakt.lead")}>${t("home.kontakt.lead")}</p>
        <div class="mrizka" style="margin-top:1.8rem">
          <a class="karta-kontakt zvyrazneny" href="tel:${site.firma.dispecinkTelefonHref}">
            <h3>${t("kontakt.rychle.dispecink.titulek")}</h3>
            <span class="velky">${site.firma.dispecinkTelefon}</span>
            <p>${t("kontakt.rychle.dispecink.popis")}</p>
          </a>
          <a class="karta-kontakt" href="mailto:${site.firma.email}">
            <h3>${t("kontakt.rychle.poptavka.titulek")}</h3>
            <span class="velky">${site.firma.email}</span>
            <p>${t("kontakt.rychle.poptavka.popis")}</p>
          </a>
        </div>
      </div>
      <div>${formular(ctx)}</div>
    </div>
  </div>
</section>`;
}

/* ------------------------------------------------------------- služby */

export function sluzbyPrehled(ctx) {
  const { t, site } = ctx;
  return `${podhlavi(ctx, {
    stitek: t("sluzby.prehled.stitek"),
    titulek: t("sluzby.prehled.titulek"),
    lead: ctx.zk(t("sluzby.prehled.lead")),
    drobecky: [{ nazev: t("nav.sluzby") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">${site.sluzby.map((s) => kartaSluzby(ctx, s)).join("")}</div>
  </div>
</section>
${kroky_sekce(ctx)}
${vyzva(ctx)}`;
}

function kroky_sekce(ctx) {
  const { t } = ctx;
  return `<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <span class="stitek">${t("home.postup.stitek")}</span>
      <h2>${t("home.postup.titulek")}</h2>
    </div>
    ${kroky(ctx, "home.postup.kroky")}
  </div>
</section>`;
}

export function sluzbaDetail(ctx, s) {
  const { t, site, odkaz, klice } = ctx;
  const p = `sluzby.polozky.${s.id}`;
  const maKroky = klice(`${p}.kroky`).length > 0;
  const souvisi = site.sluzby.filter((x) => x.id !== s.id).slice(0, 3);

  const doplnky = ["upozorneni", "refit", "dispecink", "servis"]
    .filter((k) => ctx.existuje(`${p}.${k}.titulek`))
    .map(
      (k) => `<div class="panel-info${k === "upozorneni" ? " varovny" : ""}" style="margin-top:1.6rem">
        <h3${dc(`${p}.${k}.titulek`)}>${t(`${p}.${k}.titulek`)}</h3>
        <p${dc(`${p}.${k}.popis`)}>${ctx.zk(t(`${p}.${k}.popis`))}</p>
      </div>`
    )
    .join("");

  return `${podhlavi(ctx, {
    stitek: t("sluzby.prehled.stitek"),
    titulek: t(`${p}.titulek`),
    lead: ctx.zk(t(`${p}.lead`)),
    drobecky: [{ nazev: t("nav.sluzby"), klic: "sluzby" }, { nazev: t(`${p}.nazev`) }],
  })}

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2${dc(`${p}.nazev`)}>${t(`${p}.nazev`)}</h2>
        <p class="lead"${dc(`${p}.popis`)}>${ctx.zk(t(`${p}.popis`))}</p>
        <h3 style="margin-top:2.2rem">${t("sluzby.spolecne.coZahrnuje")}</h3>
        ${seznamOdskrtnuty(ctx, `${p}.body`)}
        ${doplnky}
      </div>
      <div>
        ${ctx.obrazek(s.foto, { alt: t(`${p}.nazev`), sirky: "(min-width: 940px) 40vw, 92vw", trida: "dvojsloupec-obraz" })}
        <p class="popiska">${t("ui.ilustracniGrafika")} · ${t(`${p}.nazev`)}</p>
      </div>
    </div>
  </div>
</section>

${
  maKroky
    ? `<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>${t("sluzby.spolecne.jakProbiha")}</h2></div>
    ${kroky(ctx, `${p}.kroky`)}
  </div>
</section>`
    : ""
}

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>${t("sluzby.spolecne.souvisi")}</h2></div>
    <div class="mrizka mrizka-3">${souvisi.map((x) => kartaSluzby(ctx, x)).join("")}</div>
  </div>
</section>

${vyzva(ctx, { titulek: t("sluzby.spolecne.zajimaVas"), lead: t("sluzby.spolecne.zajimaVasLead") })}`;
}

/* ---------------------------------------------------------- realizace */

export function realizacePrehled(ctx) {
  const { t, site, odkaz, datum } = ctx;
  const kategorie = ["vse", ...site.kategorieRealizaci];
  const chipy = kategorie
    .map(
      (k) =>
        `<button type="button" class="chip" data-kategorie="${k}" aria-pressed="${k === "vse"}">${t(`realizace.kategorie.${k}`)}</button>`
    )
    .join("");

  const data = ctx.realizaceSeznam.map((r) => ({
    id: r.id,
    nazev: t(`realizace.polozky.${r.id}.nazev`),
    misto: t(`realizace.polozky.${r.id}.misto`),
    perex: t(`realizace.polozky.${r.id}.perex`),
    datum: r.datum,
    kategorie: r.kategorie,
    motiv: r.motiv,
    odkaz: odkaz("realizace", r.id),
  }));

  return `${podhlavi(ctx, {
    stitek: t("realizace.stranka.stitek"),
    titulek: t("realizace.stranka.titulek"),
    lead: ctx.zk(t("realizace.stranka.lead")),
    drobecky: [{ nazev: t("nav.realizace") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="filtry" data-jen-js>
      <div class="filtry-chipy">${chipy}</div>
      <div class="filtry-vpravo">
        <label class="hledani">
          <span class="vizualne-skryto">${t("ui.hledat")}</span>
          ${ikona("lupa")}
          <input type="search" data-hledani placeholder="${t("ui.hledat")}…">
        </label>
        <span class="pocet-vysledku" data-pocet aria-live="polite"></span>
      </div>
    </div>
    <div class="mrizka mrizka-3" data-vypis-realizaci>${ctx.realizaceSeznam.map((r) => kartaRealizace(ctx, r)).join("")}</div>
    <p class="lead" data-prazdno hidden style="text-align:center;padding:3rem 0">${t("ui.nenalezeno")}</p>
  </div>
</section>
<script type="application/json" data-realizace-data>${JSON.stringify({
    polozky: data,
    kategorie: Object.fromEntries(kategorie.map((k) => [k, t(`realizace.kategorie.${k}`)])),
    texty: {
      vice: t("ui.vice"),
      nenalezeno: t("ui.nenalezeno"),
      pocet: t("ui.filtrovat"),
    },
    detailSablona: odkaz("realizaceDetail"),
  })}</script>
${vyzva(ctx)}`;
}

export function realizaceDetail(ctx, r) {
  const { t, datum, odkaz } = ctx;
  const p = `realizace.polozky.${r.id}`;
  const dalsi = ctx.realizaceSeznam.filter((x) => x.id !== r.id).slice(0, 3);
  const technologie = ctx
    .klice(`${p}.technologie`)
    .map((k) => `<span class="odznak odznak-zeleny">${t(`${p}.technologie.${k}`)}</span>`)
    .join(" ");

  return `${podhlavi(ctx, {
    stitek: t("realizace.stranka.stitek"),
    titulek: t(`${p}.nazev`),
    lead: ctx.zk(t(`${p}.perex`)),
    drobecky: [{ nazev: t("nav.realizace"), klic: "realizace" }, { nazev: t(`${p}.nazev`) }],
  })}

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <div style="border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/10;margin-bottom:2rem">${motivRealizace(r.motiv, { popis: t(`${p}.nazev`) })}</div>
        <h2>${t("realizace.detail.rozsah")}</h2>
        <p${dc(`${p}.zadani`)}>${ctx.zk(t(`${p}.zadani`))}</p>
        ${seznamOdskrtnuty(ctx, `${p}.rozsah`)}
        <h2 style="margin-top:2.4rem">${t("realizace.detail.vysledek")}</h2>
        <p${dc(`${p}.vysledek`)}>${ctx.zk(t(`${p}.vysledek`))}</p>
      </div>
      <div>
        <h3>${t("realizace.detail.parametry")}</h3>
        <dl class="parametry">
          <div><dt>${t("realizace.detail.kraj")}</dt><dd>${t(`${p}.misto`)}, ${r.kraj}</dd></div>
          <div><dt>${t("realizace.detail.dokonceno")}</dt><dd>${datum(r.datum, "mesic")}</dd></div>
          <div><dt>${t("realizace.detail.plocha")}</dt><dd>${r.plocha}</dd></div>
          <div><dt>${t("realizace.detail.doba")}</dt><dd>${r.doba}</dd></div>
          <div><dt>${t("ui.kategorie")}</dt><dd>${r.kategorie.map((k) => t(`realizace.kategorie.${k}`)).join(", ")}</dd></div>
        </dl>
        <h3 style="margin-top:2rem">${t("realizace.detail.technologie")}</h3>
        <div style="display:flex;flex-wrap:wrap;gap:.4rem">${technologie}</div>
      </div>
    </div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>${t("realizace.detail.dalsiRealizace")}</h2></div>
    <div class="mrizka mrizka-3">${dalsi.map((x) => kartaRealizace(ctx, x)).join("")}</div>
  </div>
</section>

${vyzva(ctx, { titulek: t("realizace.detail.maObdobny"), lead: t("realizace.detail.maObdobnyLead") })}`;
}

/** Stránka pro realizace přidané v administraci (vykresluje se z JSON v prohlížeči). */
export function realizaceSablona(ctx) {
  const { t, odkaz } = ctx;
  const data = ctx.realizaceSeznam.map((r) => ({
    id: r.id,
    nazev: t(`realizace.polozky.${r.id}.nazev`),
    odkaz: odkaz("realizace", r.id),
  }));
  return `${podhlavi(ctx, {
    stitek: t("realizace.stranka.stitek"),
    titulek: `<span data-sablona="nazev">${t("realizace.stranka.titulek")}</span>`,
    lead: `<span data-sablona="perex"></span>`,
    drobecky: [{ nazev: t("nav.realizace"), klic: "realizace" }, { nazev: t("realizace.stranka.stitek") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <div data-sablona="nahled" style="border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/10;margin-bottom:2rem">${motivRealizace(1)}</div>
        <h2>${t("realizace.detail.rozsah")}</h2>
        <p data-sablona="zadani"></p>
        <ul class="seznam-odskrtnuty" data-sablona="rozsah"></ul>
        <h2 style="margin-top:2.4rem">${t("realizace.detail.vysledek")}</h2>
        <p data-sablona="vysledek"></p>
      </div>
      <div>
        <h3>${t("realizace.detail.parametry")}</h3>
        <dl class="parametry" data-sablona="parametry"></dl>
        <h3 style="margin-top:2rem">${t("realizace.detail.technologie")}</h3>
        <div data-sablona="technologie" style="display:flex;flex-wrap:wrap;gap:.4rem"></div>
        <p style="margin-top:2rem"><a class="odkaz-sip" href="${odkaz("realizace")}">${t("ui.vsechnyRealizace")}${ikona("sip")}</a></p>
      </div>
    </div>
  </div>
</section>
<script type="application/json" data-sablona-data>${JSON.stringify({
    zakladni: data,
    popisky: {
      kraj: t("realizace.detail.kraj"),
      dokonceno: t("realizace.detail.dokonceno"),
      plocha: t("realizace.detail.plocha"),
      doba: t("realizace.detail.doba"),
      kategorie: t("ui.kategorie"),
    },
    kategorie: Object.fromEntries(ctx.site.kategorieRealizaci.map((k) => [k, t(`realizace.kategorie.${k}`)])),
  })}</script>
${vyzva(ctx)}`;
}

/* ------------------------------------------------------------- o nás */

export function oNas(ctx) {
  const { t, site, klice } = ctx;
  const hodnoty = klice("onas.hodnoty.polozky")
    .map(
      (k, i) => `<div class="karta-sluzba" style="cursor:default">
      <span class="karta-ikona">${ikona(["list", "lide", "stit", "dokument"][i % 4])}</span>
      <h3${dc(`onas.hodnoty.polozky.${k}.titulek`)}>${t(`onas.hodnoty.polozky.${k}.titulek`)}</h3>
      <p${dc(`onas.hodnoty.polozky.${k}.popis`)}>${ctx.zk(t(`onas.hodnoty.polozky.${k}.popis`))}</p>
    </div>`
    )
    .join("");

  const divize = klice("onas.divize.polozky")
    .map(
      (k, i) => `<div class="krok">
      <h3${dc(`onas.divize.polozky.${k}.titulek`)}>${t(`onas.divize.polozky.${k}.titulek`)}</h3>
      <p${dc(`onas.divize.polozky.${k}.popis`)}>${ctx.zk(t(`onas.divize.polozky.${k}.popis`))}</p>
    </div>`
    )
    .join("");

  return `${podhlavi(ctx, {
    stitek: t("onas.stitek"),
    titulek: t("onas.titulek"),
    lead: ctx.zk(t("onas.lead")),
    drobecky: [{ nazev: t("nav.onas") }],
  })}

<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div class="text-blok">
        <h2${dc("onas.pribeh.titulek")}>${t("onas.pribeh.titulek")}</h2>
        <p${dc("onas.pribeh.p1")}>${ctx.zk(t("onas.pribeh.p1"))}</p>
        <p${dc("onas.pribeh.p2")}>${ctx.zk(t("onas.pribeh.p2"))}</p>
        <p${dc("onas.pribeh.p3")}>${ctx.zk(t("onas.pribeh.p3"))}</p>
      </div>
      <div>
        ${ctx.obrazek("foto-strojovna", { alt: "Strojovna s rozvody", sirky: "(min-width: 940px) 40vw, 92vw", trida: "dvojsloupec-obraz" })}
        <div class="panel-info" style="margin-top:1.4rem;display:flex;gap:1rem;align-items:center">
          <img src="${ctx.asset("img/odznak-spolehliva-firma.png")}" alt="" width="300" height="300" loading="lazy" style="width:72px;height:72px;background:none;flex:none">
          <div>
            <h3 style="margin-bottom:.25rem"${dc("onas.odznak.titulek")}>${t("onas.odznak.titulek")}</h3>
            <p style="font-size:.9rem"${dc("onas.odznak.popis")}>${t("onas.odznak.popis")}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sekce sekce-tmava">
  <canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>
  <div class="obal">
    <div class="hlavicka-sekce"><h2${dc("onas.divize.titulek")}>${t("onas.divize.titulek")}</h2></div>
    <div class="postup" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">${divize}</div>
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce"><h2${dc("onas.hodnoty.titulek")}>${t("onas.hodnoty.titulek")}</h2></div>
    <div class="mrizka mrizka-4">${hodnoty}</div>
  </div>
</section>

<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce">
      <h2${dc("onas.tym.titulek")}>${t("onas.tym.titulek")}</h2>
      <p class="lead"${dc("onas.tym.lead")}>${t("onas.tym.lead")}</p>
    </div>
    <div class="mrizka mrizka-3">${site.lide.map((o) => kartaClovek(ctx, o)).join("")}</div>
  </div>
</section>

${vyzva(ctx)}`;
}

/* ------------------------------------------------------------ novinky */

export function novinkyPrehled(ctx) {
  const { t } = ctx;
  return `${podhlavi(ctx, {
    stitek: t("novinky.stranka.stitek"),
    titulek: t("novinky.stranka.titulek"),
    lead: t("novinky.stranka.lead"),
    drobecky: [{ nazev: t("nav.novinky") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">${ctx.novinkySeznam.map((n) => kartaNovinky(ctx, n)).join("")}</div>
  </div>
</section>
${vyzva(ctx)}`;
}

export function novinkaDetail(ctx, n) {
  const { t, datum, odkaz } = ctx;
  const p = `novinky.polozky.${n.id}`;
  const dalsi = ctx.novinkySeznam.filter((x) => x.id !== n.id).slice(0, 3);
  return `${podhlavi(ctx, {
    stitek: `${t("ui.publikovano")} ${datum(n.datum)}`,
    titulek: t(`${p}.nazev`),
    lead: ctx.zk(t(`${p}.perex`)),
    drobecky: [{ nazev: t("nav.novinky"), klic: "novinky" }, { nazev: t(`${p}.nazev`) }],
  })}
<section class="sekce">
  <div class="obal obal-uzky">
    <div style="border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/9;margin-bottom:2.2rem">${motivRealizace(n.motiv)}</div>
    <div class="text-blok" style="max-width:none">
      <p class="lead"${dc(`${p}.perex`)}>${ctx.zk(t(`${p}.perex`))}</p>
      <p${dc(`${p}.text`)}>${ctx.zk(t(`${p}.text`))}</p>
      ${
        n.odkaz
          ? `<p><a class="tl tl-obrys tl-mala" href="${n.odkaz}" target="_blank" rel="noopener">${ikona("externi")}${t("ui.externiClanek")}</a></p>`
          : ""
      }
      <p style="margin-top:2rem"><a class="odkaz-sip" href="${odkaz("novinky")}">${t("ui.vsechnyNovinky")}${ikona("sip")}</a></p>
    </div>
  </div>
</section>
<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2>${t("ui.vsechnyNovinky")}</h2></div>
    <div class="mrizka mrizka-3">${dalsi.map((x) => kartaNovinky(ctx, x)).join("")}</div>
  </div>
</section>`;
}

/* ------------------------------------------------------------ kariéra */

export function kariera(ctx) {
  const { t, klice, site } = ctx;
  const nabidka = klice("kariera.nabizime.polozky")
    .map(
      (k, i) => `<div class="karta-sluzba" style="cursor:default">
      <span class="karta-ikona">${ikona(["montaz", "dokument", "lide", "misto"][i % 4])}</span>
      <h3${dc(`kariera.nabizime.polozky.${k}.titulek`)}>${t(`kariera.nabizime.polozky.${k}.titulek`)}</h3>
      <p${dc(`kariera.nabizime.polozky.${k}.popis`)}>${ctx.zk(t(`kariera.nabizime.polozky.${k}.popis`))}</p>
    </div>`
    )
    .join("");
  const vedouci = site.lide.find((o) => o.id === "zdenek-bauska");

  return `${podhlavi(ctx, {
    stitek: t("kariera.stitek"),
    titulek: t("kariera.titulek"),
    lead: ctx.zk(t("kariera.lead")),
    drobecky: [{ nazev: t("nav.kariera") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2${dc("kariera.cohledame.titulek")}>${t("kariera.cohledame.titulek")}</h2>
        ${seznamOdskrtnuty(ctx, "kariera.cohledame.polozky")}
      </div>
      <div>
        ${ctx.obrazek("foto-servis", { alt: t("kariera.titulek"), sirky: "(min-width: 940px) 40vw, 92vw", trida: "dvojsloupec-obraz" })}
      </div>
    </div>
  </div>
</section>
<section class="sekce sekce-papir">
  <div class="obal">
    <div class="hlavicka-sekce"><h2${dc("kariera.nabizime.titulek")}>${t("kariera.nabizime.titulek")}</h2></div>
    <div class="mrizka mrizka-4">${nabidka}</div>
  </div>
</section>
<section class="sekce" id="formular">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2${dc("kariera.formular.titulek")}>${t("kariera.formular.titulek")}</h2>
        <p class="lead"${dc("kariera.formular.lead")}>${t("kariera.formular.lead")}</p>
        <div style="margin-top:1.6rem;max-width:22rem">${kartaClovek(ctx, vedouci)}</div>
      </div>
      <div>${formular(ctx, { predvolenyTyp: "kariera", id: "formular-kariera" })}</div>
    </div>
  </div>
</section>`;
}

/* ------------------------------------------------------------ kontakt */

export function kontakt(ctx) {
  const { t, site } = ctx;
  const mapa = (a) =>
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${a.ulice}, ${a.psc} ${a.mesto}`)}`;

  return `${podhlavi(ctx, {
    stitek: t("kontakt.stitek"),
    titulek: t("kontakt.titulek"),
    lead: t("kontakt.lead"),
    drobecky: [{ nazev: t("nav.kontakt") }],
  })}

<section class="sekce">
  <div class="obal">
    <div class="mrizka mrizka-3">
      <a class="karta-kontakt zvyrazneny" href="tel:${site.firma.dispecinkTelefonHref}">
        <h3${dc("kontakt.rychle.dispecink.titulek")}>${t("kontakt.rychle.dispecink.titulek")}</h3>
        <span class="velky">${site.firma.dispecinkTelefon}</span>
        <p${dc("kontakt.rychle.dispecink.popis")}>${t("kontakt.rychle.dispecink.popis")}</p>
        <span class="odkaz-sip" style="color:var(--zelena-svetlá)">${site.firma.dispecinkEmail}</span>
      </a>
      <a class="karta-kontakt" href="#formular">
        <h3${dc("kontakt.rychle.poptavka.titulek")}>${t("kontakt.rychle.poptavka.titulek")}</h3>
        <span class="velky">${site.firma.email}</span>
        <p${dc("kontakt.rychle.poptavka.popis")}>${t("kontakt.rychle.poptavka.popis")}</p>
        <span class="odkaz-sip">${t("ui.napsatNam")}${ikona("sip")}</span>
      </a>
      <a class="karta-kontakt" href="tel:${site.firma.mobilKancelarHref}">
        <h3${dc("kontakt.rychle.kancelar.titulek")}>${t("kontakt.rychle.kancelar.titulek")}</h3>
        <span class="velky">${site.firma.mobilKancelar}</span>
        <p${dc("kontakt.rychle.kancelar.popis")}>${t("kontakt.rychle.kancelar.popis")}</p>
      </a>
    </div>
  </div>
</section>

<section class="sekce sekce-papir" id="formular">
  <div class="obal">
    <div class="dvojsloupec">
      <div>
        <h2${dc("kontakt.formular.titulek")}>${t("kontakt.formular.titulek")}</h2>
        <p class="lead"${dc("kontakt.formular.lead")}>${t("kontakt.formular.lead")}</p>
        <div class="mrizka" style="margin-top:1.8rem">
          <div class="adresa-karta">
            <h3>${t("kontakt.adresy.sidlo")}</h3>
            <address>${site.firma.sidlo.ulice}<br>${site.firma.sidlo.psc} ${site.firma.sidlo.mesto}</address>
            <p style="margin-top:.7rem"><a class="odkaz-sip" href="${mapa(site.firma.sidlo)}" target="_blank" rel="noopener">${t("kontakt.adresy.otevritMapu")}${ikona("externi", { velikost: 16 })}</a></p>
          </div>
          <div class="adresa-karta">
            <h3>${t("kontakt.adresy.provozovna")}</h3>
            <address>${site.firma.provozovna.ulice}<br>${site.firma.provozovna.psc} ${site.firma.provozovna.mesto}</address>
            <p style="margin-top:.7rem"><a class="odkaz-sip" href="${mapa(site.firma.provozovna)}" target="_blank" rel="noopener">${t("kontakt.adresy.otevritMapu")}${ikona("externi", { velikost: 16 })}</a></p>
          </div>
          <div class="adresa-karta">
            <h3>${t("kontakt.adresy.fakturacni")}</h3>
            <address>
              ${site.firma.nazev}<br>
              IČO ${site.firma.ico} · DIČ ${site.firma.dic}<br>
              ${site.firma.banka}<br>
              ${site.firma.ucet}<br>
              ID datové schránky: ${site.firma.datovaSchranka}
            </address>
          </div>
        </div>
      </div>
      <div>${formular(ctx)}</div>
    </div>
  </div>
</section>

<section class="sekce">
  <div class="obal">
    <div class="hlavicka-sekce">
      <h2${dc("kontakt.tym.titulek")}>${t("kontakt.tym.titulek")}</h2>
      <p class="lead"${dc("kontakt.tym.lead")}>${t("kontakt.tym.lead")}</p>
    </div>
    <div class="mrizka mrizka-3">${site.lide.map((o) => kartaClovek(ctx, o)).join("")}</div>
  </div>
</section>`;
}

/* ------------------------------------------------------------ slovník */

export function slovnik(ctx) {
  const { t, skupinyZkratek } = ctx;
  const skupiny = skupinyZkratek()
    .map(
      (g) => `<div class="slovnik-skupina">
      <h2 class="slovnik-pismeno" id="pismeno-${g.letter}">${g.letter}</h2>
      <div class="slovnik-polozky">
        ${g.items
          .map(
            (term) => `<dl class="slovnik-karta" data-zkratka="${term.abbr.toLowerCase()} ${term.full.toLowerCase()}">
            <dt>${term.abbr}</dt>
            <div class="rozepsano">${term.full}</div>
            <dd>${term.popis}</dd>
          </dl>`
          )
          .join("")}
      </div>
    </div>`
    )
    .join("");

  return `${podhlavi(ctx, {
    stitek: t("slovnik.stranka.stitek"),
    titulek: t("slovnik.stranka.titulek"),
    lead: t("slovnik.stranka.lead"),
    drobecky: [{ nazev: t("nav.slovnik") }],
  })}
<section class="sekce">
  <div class="obal">
    <div class="filtry" data-jen-js style="max-width:32rem">
      <label class="hledani" style="width:100%">
        <span class="vizualne-skryto">${t("slovnik.stranka.hledat")}</span>
        ${ikona("lupa")}
        <input type="search" data-hledani-slovnik placeholder="${t("slovnik.stranka.hledat")}">
      </label>
    </div>
    <div data-slovnik>${skupiny}</div>
    <p class="lead" data-slovnik-prazdno hidden style="text-align:center;padding:2rem 0">${t("slovnik.stranka.nenalezeno")}</p>
  </div>
</section>
${vyzva(ctx)}`;
}

/* -------------------------------------------------------------- ostatní */

export function gdpr(ctx) {
  const { t, klice } = ctx;
  const sekce = klice("gdpr.sekce")
    .map(
      (k) => `<h2${dc(`gdpr.sekce.${k}.titulek`)}>${t(`gdpr.sekce.${k}.titulek`)}</h2>
      <p${dc(`gdpr.sekce.${k}.text`)}>${t(`gdpr.sekce.${k}.text`)}</p>`
    )
    .join("");
  return `${podhlavi(ctx, {
    titulek: t("gdpr.titulek"),
    lead: t("gdpr.lead"),
    drobecky: [{ nazev: t("gdpr.titulek") }],
    platno: false,
  })}
<section class="sekce">
  <div class="obal obal-uzky">
    <div class="text-blok" style="max-width:none">${sekce}</div>
    <div class="panel-info varovny" style="margin-top:2.5rem">
      <p${dc("gdpr.poznamka")}>${t("gdpr.poznamka")}</p>
    </div>
  </div>
</section>`;
}

export function chyba404(ctx) {
  const { t, odkaz } = ctx;
  return `<section class="hero">
  <canvas class="hero-platno" data-vitr="hero" aria-hidden="true"></canvas>
  <div class="obal hero-vnitrek" style="grid-template-columns:1fr;text-align:center;justify-items:center">
    <div>
      <span class="stitek" style="justify-content:center">404</span>
      <h1>${t("chyba404.titulek")}</h1>
      <p class="lead" style="margin-inline:auto">${t("chyba404.lead")}</p>
      <div class="tlacitka" style="justify-content:center;margin-top:1.8rem">
        <a class="tl tl-hlavni" href="${odkaz("index")}">${ikona("sipZpet")}${t("chyba404.cta")}</a>
        <a class="tl tl-obrys" href="${odkaz("sluzby")}">${t("chyba404.ctaDruhe")}${ikona("sip")}</a>
      </div>
    </div>
  </div>
</section>`;
}
