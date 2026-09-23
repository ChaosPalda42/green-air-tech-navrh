/* Demo administrace: kostra a data. Vykreslování obstarává assets/admin.js. */

import { ikona } from "./ikony.mjs";

const SKUPINY = {
  home: "Úvodní stránka",
  sluzby: "Služby",
  realizace: "Realizace",
  novinky: "Novinky",
  onas: "O nás",
  kariera: "Kariéra",
  kontakt: "Kontakt",
  slovnik: "Slovník zkratek",
  gdpr: "Ochrana osobních údajů",
  chyba404: "Stránka 404",
  footer: "Patička",
  nav: "Navigace",
  ui: "Tlačítka a popisky",
  lide: "Lidé",
  meta: "Titulky pro vyhledávače",
};

export function administrace(ctx, data = { klice: [], slovniky: {}, realizace: [], kategorie: {} }) {
  const { t, site, odkaz } = ctx;

  const zalozka = (id, popisek, ikonaId) =>
    `<button type="button" class="admin-zalozka" data-zalozka="${id}" aria-selected="false">${ikona(ikonaId)}<span>${popisek}</span></button>`;

  return `<section class="admin" data-admin>
  <div class="admin-prihlaseni" data-prihlaseni>
    <div class="obal obal-uzky">
      <div class="formular" style="max-width:26rem;margin-inline:auto">
        <p class="admin-login-nadpis">${t("admin.prihlaseni.titulek")}</p>
        <p class="lead" style="font-size:.98rem;margin-bottom:1.4rem">${t("admin.prihlaseni.lead")}</p>
        <div class="pole">
          <label for="admin-jmeno">${t("admin.prihlaseni.jmeno")}</label>
          <input type="text" id="admin-jmeno" value="green" autocomplete="off">
        </div>
        <div class="pole">
          <label for="admin-heslo">${t("admin.prihlaseni.heslo")}</label>
          <input type="password" id="admin-heslo" value="demo" autocomplete="off">
        </div>
        <button type="button" class="tl tl-hlavni" style="width:100%" data-vstoupit>${ikona("sip")}${t("admin.prihlaseni.vstoupit")}</button>
        <p class="napoveda" style="margin-top:1rem;text-align:center">${t("admin.prihlaseni.poznamka")}</p>
      </div>
    </div>
  </div>

  <div class="admin-app" data-app hidden>
    <div class="obal">
      <div class="admin-hlavicka">
        <div>
          <h1>${t("admin.titulek")}</h1>
          <p class="lead" style="font-size:.98rem">${t("admin.uvod")}</p>
        </div>
        <div class="admin-akce">
          <a class="tl tl-obrys tl-mala" href="${odkaz("index")}">${ikona("externi")}${t("admin.zpetNaWeb")}</a>
          <button type="button" class="tl tl-obrys tl-mala" data-odhlasit>${t("admin.odhlasit")}</button>
        </div>
      </div>

      <div class="hlaska hlaska-info">${ikona("info")}<span>${t("admin.demoUpozorneni")}</span></div>

      <div class="admin-zalozky" role="tablist">
        ${zalozka("texty", t("admin.zalozky.texty"), "upravit")}
        ${zalozka("realizace", t("admin.zalozky.realizace"), "montaz")}
        ${zalozka("data", t("admin.zalozky.data"), "ulozit")}
      </div>

      <div class="admin-panel" data-panel="texty">
        <div class="admin-nastroje">
          <label class="hledani" style="flex:1;min-width:220px">
            <span class="vizualne-skryto">${t("admin.texty.hledat")}</span>
            ${ikona("lupa")}
            <input type="search" data-admin-hledani placeholder="${t("admin.texty.hledat")}…">
          </label>
          <label class="admin-jazyk">
            <span>${t("admin.texty.jazyk")}</span>
            <select data-admin-jazyk>
              ${site.jazyky.map((j) => `<option value="${j.kod}">${j.nazev}</option>`).join("")}
            </select>
          </label>
        </div>
        <p class="lead" style="font-size:.95rem">${t("admin.texty.lead")}</p>
        <div data-admin-texty></div>
        <p data-admin-texty-prazdno hidden class="lead" style="text-align:center;padding:2rem">${t("admin.texty.zadnyVysledek")}</p>
      </div>

      <div class="admin-panel" data-panel="realizace" hidden>
        <div class="admin-nastroje">
          <p class="lead" style="font-size:.95rem;flex:1">${t("admin.realizace.lead")}</p>
          <button type="button" class="tl tl-hlavni tl-mala" data-pridat-realizaci>${ikona("plus")}${t("admin.realizace.pridat")}</button>
        </div>
        <div data-admin-realizace></div>
      </div>

      <div class="admin-panel" data-panel="data" hidden>
        <p class="lead" style="font-size:.95rem">${t("admin.data.lead")}</p>
        <p class="admin-cas" data-admin-cas></p>
        <div class="tlacitka" style="margin-top:1.4rem">
          <button type="button" class="tl tl-obrys" data-export>${ikona("stahnout")}${t("admin.data.stahnout")}</button>
          <label class="tl tl-obrys" style="cursor:pointer">
            ${ikona("nahrat")}${t("admin.data.nahrat")}
            <input type="file" accept="application/json" data-import hidden>
          </label>
          <button type="button" class="tl tl-obrys" data-reset style="border-color:#e0b4b0;color:#b32b22">${ikona("kos")}${t("admin.data.vymazat")}</button>
        </div>
      </div>
    </div>
  </div>

  <dialog class="admin-dialog" data-dialog>
    <form method="dialog" data-realizace-form>
      <h2 data-dialog-titulek>${t("admin.realizace.pridat")}</h2>
      <div class="formular-dvojice">
        <div class="pole"><label for="r-nazev">${t("admin.realizace.nazev")}</label><input type="text" id="r-nazev" name="nazev" required></div>
        <div class="pole"><label for="r-misto">${t("admin.realizace.misto")}</label><input type="text" id="r-misto" name="misto"></div>
        <div class="pole"><label for="r-datum">${t("admin.realizace.datum")}</label><input type="date" id="r-datum" name="datum"></div>
        <div class="pole"><label for="r-plocha">${t("admin.realizace.plocha")}</label><input type="text" id="r-plocha" name="plocha"></div>
      </div>
      <div class="pole">
        <label>${t("admin.realizace.kategorie")}</label>
        <div class="admin-kategorie">${Object.entries(data.kategorie)
          .map(
            ([k, v]) =>
              `<label class="zaskrtavatko"><input type="checkbox" name="kategorie" value="${k}"><span>${v}</span></label>`
          )
          .join("")}</div>
      </div>
      <div class="pole"><label for="r-perex">${t("admin.realizace.perex")}</label><textarea id="r-perex" name="perex" style="min-height:70px"></textarea></div>
      <div class="pole"><label for="r-zadani">${t("admin.realizace.zadani")}</label><textarea id="r-zadani" name="zadani" style="min-height:70px"></textarea></div>
      <div class="pole"><label for="r-rozsah">${t("admin.realizace.rozsah")}</label><textarea id="r-rozsah" name="rozsah" style="min-height:110px"></textarea></div>
      <div class="pole"><label for="r-technologie">${t("admin.realizace.technologie")}</label><input type="text" id="r-technologie" name="technologie"></div>
      <div class="pole"><label for="r-vysledek">${t("admin.realizace.vysledek")}</label><textarea id="r-vysledek" name="vysledek" style="min-height:90px"></textarea></div>
      <div class="pole"><label for="r-doba">${t("admin.realizace.doba")}</label><input type="text" id="r-doba" name="doba"></div>
      <input type="hidden" name="id">
      <div class="tlacitka" style="justify-content:flex-end;margin-top:1rem">
        <button type="button" class="tl tl-obrys tl-mala" data-zavrit-dialog>${t("admin.realizace.zrusit")}</button>
        <button type="submit" class="tl tl-hlavni tl-mala">${ikona("ulozit")}${t("admin.realizace.ulozit")}</button>
      </div>
    </form>
  </dialog>
</section>

<script type="application/json" data-admin-data>${JSON.stringify(data)}</script>
<script type="application/json" data-admin-texty-slovnik>${JSON.stringify({
    skupiny: SKUPINY,
    popisky: {
      puvodni: t("admin.texty.puvodni"),
      zmeneno: t("admin.texty.zmeneno"),
      vratit: t("admin.texty.vratit"),
      ulozit: t("admin.texty.ulozit"),
      ulozeno: t("admin.texty.ulozeno"),
      upravit: t("admin.realizace.upravit"),
      smazat: t("admin.realizace.smazat"),
      smazatPotvrzeni: t("admin.realizace.smazatPotvrzeni"),
      vlastni: t("admin.realizace.vlastni"),
      upravena: t("admin.realizace.upravena"),
      prazdne: t("admin.realizace.prazdne"),
      pridat: t("admin.realizace.pridat"),
      posledniZmena: t("admin.data.posledniZmena"),
      zadnaZmena: t("admin.data.zadnaZmena"),
      chybaImportu: t("admin.data.chybaImportu"),
      vymazatPotvrzeni: t("admin.data.vymazatPotvrzeni"),
    },
  })}</script>`;
}
