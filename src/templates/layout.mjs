/* Kostra stránky: hlavička, mobilní panel, spodní lišta, patička.

   Web má dvě větve — domácnosti a firemní zákazníci. Navigace se podle toho
   mění: na rozcestníku a na společných stránkách nabízí obě větve, uvnitř
   větve ukazuje její služby a realizace plus přepínač na tu druhou. */

import { ikona } from "./ikony.mjs";

const KLIC_NAV = {
  index: "nav.uvod",
  sluzby: "nav.sluzby",
  realizace: "nav.realizace",
  onas: "nav.onas",
  novinky: "nav.novinky",
  kariera: "nav.kariera",
  kontakt: "nav.kontakt",
  slovnik: "nav.slovnik",
};

const SPOLECNE = ["onas", "novinky", "kariera", "kontakt"];

/** Hlavička s logem, menu, telefonem a přepínačem jazyků. */
function hlavicka(ctx) {
  const { t, odkaz, aktivni, site, lang, jazykOdkaz, vetev, odkazVetve } = ctx;

  const sluzbyVetve = (v) => site.sluzby.filter((s) => s.vetev === v);

  // --- desktopové menu -----------------------------------------------
  let menu;
  if (vetev) {
    const pod = sluzbyVetve(vetev)
      .map(
        (s) =>
          `<a href="${odkaz("sluzba", s.id)}">${ikona(s.ikona)}<span>${t(`sluzby.polozky.${s.id}.nazev`)}</span></a>`
      )
      .join("");
    menu =
      `<div class="menu-rozbal">
        <a href="${odkaz("sluzby")}"${aktivni.startsWith("sluzb") ? ' aria-current="page"' : ""}>${t("nav.sluzby")}</a>
        <div class="menu-panel"><div class="menu-panel-mrizka">${pod}</div></div>
      </div>` +
      `<a href="${odkaz("realizace")}"${aktivni === "realizace" ? ' aria-current="page"' : ""}>${t("nav.realizace")}</a>` +
      SPOLECNE.map(
        (k) => `<a href="${odkaz(k)}"${aktivni === k ? ' aria-current="page"' : ""}>${t(KLIC_NAV[k])}</a>`
      ).join("");
  } else {
    menu =
      `<a href="${odkaz("index")}"${aktivni === "index" ? ' aria-current="page"' : ""}>${t("nav.uvod")}</a>` +
      site.vetve
        .map(
          (v) =>
            `<a href="${odkazVetve(v.id, "vetev")}">${t(`vetve.${v.id}.nazev`)}</a>`
        )
        .join("") +
      SPOLECNE.map(
        (k) => `<a href="${odkaz(k)}"${aktivni === k ? ' aria-current="page"' : ""}>${t(KLIC_NAV[k])}</a>`
      ).join("");
  }

  // --- odznak větve s přepnutím na tu druhou --------------------------
  const druha = vetev ? site.vetve.find((v) => v.id !== vetev) : null;
  const odznakVetve = vetev
    ? `<a class="lista-vetev" href="${odkazVetve(druha.id, "vetev")}" title="${t("rozcestnik.prepnout")}">
        <span class="lista-vetev-nazev">${t(`vetve.${vetev}.nazev`)}</span>
        <span class="lista-vetev-prepni">${ikona("prepnout", { velikost: 15 })}<span class="vizualne-skryto">${t("rozcestnik.prepnout")}</span></span>
      </a>`
    : "";

  const jazyky = site.jazyky
    .map(
      (j) =>
        `<a href="${jazykOdkaz(j.kod)}" lang="${j.html}"${j.kod === lang ? ' aria-current="true"' : ""}>${j.nazev}</a>`
    )
    .join("");

  // --- mobilní panel ---------------------------------------------------
  const panelVetev = site.vetve
    .map((v) => {
      const sluzby = sluzbyVetve(v.id)
        .map((s) => `<a href="${odkaz("sluzba", s.id)}">${t(`sluzby.polozky.${s.id}.nazev`)}</a>`)
        .join("");
      return `<div class="panel-skupina"${v.id === vetev ? ' data-aktivni="1"' : ""}>
        <div class="panel-nadpis">${t(`vetve.${v.id}.nazev`)}</div>
        <div class="panel-podpolozky">
          <a href="${odkazVetve(v.id, "vetev")}"><strong>${t(`vetve.${v.id}.titulek`)}</strong></a>
          <a href="${odkazVetve(v.id, "sluzby")}">${t("nav.sluzby")}</a>
          ${sluzby}
          <a href="${odkazVetve(v.id, "realizace")}">${t("nav.realizace")}</a>
        </div>
      </div>`;
    })
    .join("");

  const panelSpolecne = [...SPOLECNE, "slovnik"]
    .map(
      (k) =>
        `<a class="panel-polozka" href="${odkaz(k)}"${aktivni === k ? ' aria-current="page"' : ""}>${t(KLIC_NAV[k])}${ikona("sip")}</a>`
    )
    .join("");

  return `<header class="lista" id="lista">
  <div class="obal lista-vnitrek">
    <a class="logo" href="${odkaz("index")}" aria-label="${site.firma.nazev} — ${t("nav.uvod")}">
      <img src="${ctx.asset("img/logo.png")}" width="400" height="181" alt="${site.firma.nazev}">
    </a>
    ${odznakVetve}
    <nav class="menu" aria-label="${t("ui.menu")}">${menu}</nav>
    <div class="lista-akce">
      <a class="lista-tel" href="tel:${site.firma.dispecinkTelefonHref}">
        <span class="tecka" aria-hidden="true"></span>${site.firma.dispecinkTelefon}
      </a>
      <div class="jazyky" data-jazyky>
        <button type="button" class="jazyky-tl" aria-expanded="false" aria-label="${t("ui.jazyk")}">
          ${site.jazyky.find((j) => j.kod === lang).zkratka}${ikona("sipDolu", { velikost: 14 })}
        </button>
        <div class="jazyky-seznam">${jazyky}</div>
      </div>
      <button type="button" class="hamburger" data-hamburger aria-expanded="false" aria-controls="panel" aria-label="${t("ui.menu")}"><span></span></button>
    </div>
  </div>
</header>
<!-- Panel je ZÁMĚRNĚ mimo <header>: kdyby hlavička někdy zase dostala
     backdrop-filter, stala by se vztažným rámcem pro position:fixed
     a panel by se roztáhl jen přes ni. -->
<div class="panel" id="panel" data-panel>
    <a class="panel-polozka" href="${odkaz("index")}"${aktivni === "index" ? ' aria-current="page"' : ""}>${t("nav.uvod")}${ikona("sip")}</a>
    ${panelVetev}
    ${panelSpolecne}
    <div class="panel-kontakt">
      <a class="tl tl-hlavni" href="tel:${site.firma.dispecinkTelefonHref}">${ikona("telefon")}${t("ui.dispecink")}</a>
      <a class="tl tl-obrys" href="mailto:${site.firma.email}">${ikona("mail")}${site.firma.email}</a>
    </div>
</div>`;
}

/** Spodní akční lišta — na mobilu pořád po ruce. */
function spodniLista(ctx) {
  const { t, site, odkaz } = ctx;
  return `<nav class="spodni-lista" aria-label="${t("ui.kontaktujteNas")}">
  <a href="tel:${site.firma.mobilKancelarHref}">${ikona("telefon")}<span>${t("ui.zavolat")}</span></a>
  <a class="zvyrazneno" href="tel:${site.firma.dispecinkTelefonHref}">${ikona("hodiny")}<span>${t("ui.dispecink")}</span></a>
  <a href="${odkaz("kontakt")}#formular">${ikona("mail")}<span>${t("ui.napsatNam")}</span></a>
</nav>`;
}

/** Patička: obě větve vedle sebe, pak firma a kontakt. */
function paticka(ctx) {
  const { t, site, odkaz, odkazVetve, asset, odkazKoren } = ctx;

  const sloupecVetve = (v) => {
    const sluzby = site.sluzby
      .filter((s) => s.vetev === v.id)
      .map((s) => `<li><a href="${odkaz("sluzba", s.id)}">${t(`sluzby.polozky.${s.id}.nazev`)}</a></li>`)
      .join("");
    return `<div>
      <h4>${t(`vetve.${v.id}.nazev`)}</h4>
      <ul>
        ${sluzby}
        <li><a href="${odkazVetve(v.id, "realizace")}"><strong style="color:#fff">${t("nav.realizace")}</strong></a></li>
      </ul>
    </div>`;
  };

  const firma = ["onas", "novinky", "kariera", "slovnik"]
    .map((k) => `<li><a href="${odkaz(k)}">${t(KLIC_NAV[k])}</a></li>`)
    .join("");

  return `<footer class="paticka">
  <div class="obal">
    <div class="paticka-mrizka">
      <div>
        <span class="paticka-logo"><img src="${asset("img/logo.png")}" width="400" height="181" alt="${site.firma.nazev}" loading="lazy"></span>
        <p>${t("footer.tagline")}</p>
        <p><strong style="color:#fff">IČO</strong> ${site.firma.ico} · <strong style="color:#fff">DIČ</strong> ${site.firma.dic}</p>
      </div>
      ${site.vetve.map(sloupecVetve).join("")}
      <div>
        <h4>${t("footer.firma")}</h4>
        <ul>${firma}<li><a href="${odkaz("gdpr")}">${t("gdpr.titulek")}</a></li></ul>
        <h4 style="margin-top:1.4rem">${t("footer.kontakt")}</h4>
        <ul>
          <li><a href="tel:${site.firma.dispecinkTelefonHref}"><strong style="color:#fff">${t("footer.dispecink")}</strong><br>${site.firma.dispecinkTelefon}</a></li>
          <li><a href="mailto:${site.firma.email}">${site.firma.email}</a></li>
        </ul>
        <address style="margin-top:1rem">${site.firma.sidlo.ulice}, ${site.firma.sidlo.psc} ${site.firma.sidlo.mesto}<br>
        ${site.firma.provozovna.ulice}, ${site.firma.provozovna.psc} ${site.firma.provozovna.mesto}</address>
      </div>
    </div>
    <div class="paticka-dole">
      <span>© ${new Date().getFullYear()} ${site.firma.nazev}. ${t("footer.prava")}</span>
      <span class="paticka-ukazka">${t("footer.ukazka")}</span>
      <a href="${odkazKoren("administrace.html")}" class="paticka-admin">${t("footer.administrace")}</a>
    </div>
  </div>
</footer>`;
}

/** Složí celou HTML stránku. */
export function stranka(ctx, { telo, titulek, popis, trida = "", skripty = "" }) {
  const { lang, site, asset, t, vetev } = ctx;
  const jineJazyky = site.jazyky
    .filter((j) => j.kod !== lang)
    .map((j) => `<link rel="alternate" hreflang="${j.html}" href="${ctx.jazykOdkaz(j.kod)}">`)
    .join("\n  ");

  return `<!doctype html>
<html lang="${site.jazyky.find((j) => j.kod === lang).html}" class="bez-js"${vetev ? ` data-vetev="${vetev}"` : ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${titulek}</title>
<meta name="description" content="${popis}">
<meta name="robots" content="noindex, nofollow">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#e7f3df" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#122018" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="${titulek}">
<meta property="og:description" content="${popis}">
<meta property="og:type" content="website">
<meta property="og:image" content="${asset("img/og.svg")}">
<meta property="og:site_name" content="${site.firma.nazev}">
<link rel="icon" href="${asset("img/favicon.svg")}" type="image/svg+xml">
<link rel="apple-touch-icon" href="${asset("img/favicon.svg")}">
<link rel="preload" href="${asset("fonts/Barlow-700-latin.woff2")}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="${asset("fonts/Inter-400-latin.woff2")}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="${asset("style.css")}">
${jineJazyky}
<script>document.documentElement.classList.remove('bez-js');document.documentElement.classList.add('js');</script>
<script>
window.GAT_SLOVNIK = ${JSON.stringify({
    terminy: Object.fromEntries(ctx.terminy.map((x) => [x.abbr, { full: x.full, popis: x.popis }])),
    zavrit: t("ui.zavrit"),
  })};
window.GAT_CHYBY = ${JSON.stringify(ctx.chybyFormulare())};
window.GAT_TEXTY = ${JSON.stringify({ odeslano: t("kontakt.formular.odeslano") })};
</script>
</head>
<body class="${trida}">
<a class="preskok" href="#obsah">${t("ui.prejitNaObsah")}</a>
${hlavicka(ctx)}
<main id="obsah">
${telo}
</main>
${paticka(ctx)}
${spodniLista(ctx)}
<button type="button" class="nahoru" data-nahoru aria-label="${t("ui.nahoru")}">${ikona("sipNahoru")}</button>
<script src="${asset("app.js")}" defer></script>
${skripty}
</body>
</html>`;
}

/** Tmavé podhlaví vnitřních stránek s drobečkovou navigací. */
export function podhlavi(ctx, { stitek, titulek, lead, drobecky = [], platno = true }) {
  const { t, odkaz } = ctx;
  const cesta = [{ nazev: t("nav.uvod"), klic: "index" }, ...drobecky];
  const polozky = cesta
    .map((d, i) => {
      const posledni = i === cesta.length - 1;
      if (posledni) return `<li aria-current="page">${d.nazev}</li>`;
      return `<li><a href="${d.klic ? odkaz(d.klic) : d.href}">${d.nazev}</a></li>`;
    })
    .join("");

  return `<section class="podhlavi">
  ${platno ? '<canvas class="podhlavi-platno" data-vitr="klid" aria-hidden="true"></canvas>' : ""}
  <div class="obal">
    <nav class="drobecky" aria-label="Drobečková navigace"><ol>${polozky}</ol></nav>
    ${stitek ? `<span class="stitek">${stitek}</span>` : ""}
    <h1>${titulek}</h1>
    ${lead ? `<p class="lead">${lead}</p>` : ""}
  </div>
</section>`;
}

/** Zelený/tmavý pruh s výzvou k akci. */
export function vyzva(ctx, { titulek, lead, primarni, sekundarni } = {}) {
  const { t, site, odkaz } = ctx;
  return `<section class="sekce">
  <div class="obal">
    <div class="vyzva">
      <h2>${titulek || t("home.kontakt.titulek")}</h2>
      <p>${lead || t("home.kontakt.lead")}</p>
      <div class="tlacitka">
        <a class="tl tl-hlavni" href="${odkaz("kontakt")}#formular">${ikona("mail")}${primarni || t("ui.nezavaznaPoptavka")}</a>
        <a class="tl tl-obrys" href="tel:${site.firma.dispecinkTelefonHref}">${ikona("telefon")}${sekundarni || `${t("ui.dispecink")} · ${site.firma.dispecinkTelefon}`}</a>
      </div>
    </div>
  </div>
</section>`;
}

export { ikona };
