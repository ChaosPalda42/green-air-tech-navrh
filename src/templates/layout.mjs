/* Kostra stránky: hlavička, mobilní panel, spodní lišta, patička. */

import { ikona } from "./ikony.mjs";

export const POLOZKY_MENU = ["index", "sluzby", "realizace", "onas", "novinky", "kariera", "kontakt"];

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

/** Hlavička s logem, menu, telefonem a přepínačem jazyků. */
function hlavicka(ctx) {
  const { t, odkaz, aktivni, site, lang, jazykOdkaz } = ctx;

  const menu = POLOZKY_MENU.map((k) => {
    if (k === "sluzby") {
      const pod = site.sluzby
        .map(
          (s) =>
            `<a href="${odkaz("sluzba", s.id)}">${ikona(s.ikona)}<span>${t(`sluzby.polozky.${s.id}.nazev`)}</span></a>`
        )
        .join("");
      return `<div class="menu-rozbal">
        <a href="${odkaz("sluzby")}"${aktivni.startsWith("sluzb") ? ' aria-current="page"' : ""}>${t(KLIC_NAV[k])}</a>
        <div class="menu-panel"><div class="menu-panel-mrizka">${pod}</div></div>
      </div>`;
    }
    return `<a href="${odkaz(k)}"${aktivni === k ? ' aria-current="page"' : ""}>${t(KLIC_NAV[k])}</a>`;
  }).join("");

  const jazyky = site.jazyky
    .map(
      (j) =>
        `<a href="${jazykOdkaz(j.kod)}" lang="${j.html}"${j.kod === lang ? ' aria-current="true"' : ""}>${j.nazev}</a>`
    )
    .join("");

  const panelSluzby = site.sluzby
    .map((s) => `<a href="${odkaz("sluzba", s.id)}">${t(`sluzby.polozky.${s.id}.nazev`)}</a>`)
    .join("");

  const panelOstatni = ["realizace", "onas", "novinky", "kariera", "kontakt", "slovnik"]
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
<!-- Panel je ZÁMĚRNĚ mimo <header>: hlavička má backdrop-filter, a ten by
     z ní udělal vztažný rámec pro position:fixed (panel by se pak roztáhl
     jen přes hlavičku, ne přes obrazovku). -->
<div class="panel" id="panel" data-panel>
    <a class="panel-polozka" href="${odkaz("index")}"${aktivni === "index" ? ' aria-current="page"' : ""}>${t("nav.uvod")}${ikona("sip")}</a>
    <div class="panel-skupina">
      <div class="panel-nadpis">${t("nav.sluzby")}</div>
      <div class="panel-podpolozky"><a href="${odkaz("sluzby")}"><strong>${t("sluzby.prehled.titulek")}</strong></a>${panelSluzby}</div>
    </div>
    ${panelOstatni}
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

/** Patička s rozcestníkem, adresami a fakturačními údaji. */
function paticka(ctx) {
  const { t, site, odkaz, asset } = ctx;
  const sluzby = site.sluzby
    .map((s) => `<li><a href="${odkaz("sluzba", s.id)}">${t(`sluzby.polozky.${s.id}.nazev`)}</a></li>`)
    .join("");
  const firma = ["onas", "realizace", "novinky", "kariera", "slovnik"]
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
      <div>
        <h4>${t("footer.sluzby")}</h4>
        <ul>${sluzby}</ul>
      </div>
      <div>
        <h4>${t("footer.firma")}</h4>
        <ul>${firma}<li><a href="${odkaz("gdpr")}">${t("gdpr.titulek")}</a></li></ul>
      </div>
      <div>
        <h4>${t("footer.kontakt")}</h4>
        <ul>
          <li><a href="tel:${site.firma.dispecinkTelefonHref}"><strong style="color:#fff">${t("footer.dispecink")}</strong><br>${site.firma.dispecinkTelefon}</a></li>
          <li><a href="mailto:${site.firma.email}">${site.firma.email}</a></li>
        </ul>
        <h4 style="margin-top:1.4rem">${t("footer.sidlo")}</h4>
        <address>${site.firma.sidlo.ulice}<br>${site.firma.sidlo.psc} ${site.firma.sidlo.mesto}</address>
        <h4 style="margin-top:1.2rem">${t("footer.provozovna")}</h4>
        <address>${site.firma.provozovna.ulice}<br>${site.firma.provozovna.psc} ${site.firma.provozovna.mesto}</address>
      </div>
    </div>
    <div class="paticka-dole">
      <span>© ${new Date().getFullYear()} ${site.firma.nazev}. ${t("footer.prava")}</span>
      <span class="paticka-ukazka">${t("footer.ukazka")}</span>
    </div>
  </div>
</footer>`;
}

/** Složí celou HTML stránku. */
export function stranka(ctx, { telo, titulek, popis, trida = "", skripty = "" }) {
  const { lang, site, asset, odkaz, t } = ctx;
  const jineJazyky = site.jazyky
    .filter((j) => j.kod !== lang)
    .map((j) => `<link rel="alternate" hreflang="${j.html}" href="${ctx.jazykOdkaz(j.kod)}">`)
    .join("\n  ");

  return `<!doctype html>
<html lang="${site.jazyky.find((j) => j.kod === lang).html}" class="bez-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${titulek}</title>
<meta name="description" content="${popis}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#101a12">
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
