/* Demo administrace. Stav drží GAT.cmsStore, ukládá se do localStorage prohlížeče. */
(function () {
  "use strict";

  var korenAdmin = document.querySelector("[data-admin]");
  if (!korenAdmin || !window.GAT || !window.GAT.cmsStore) return;

  var $ = function (s, k) { return (k || document).querySelector(s); };
  var $$ = function (s, k) { return Array.prototype.slice.call((k || document).querySelectorAll(s)); };

  var data = JSON.parse($("[data-admin-data]").textContent);
  var slovnikUI = JSON.parse($("[data-admin-texty-slovnik]").textContent);
  var P = slovnikUI.popisky;

  var uloziste = window.GAT_ULOZISTE ? window.GAT_ULOZISTE() : window.localStorage;
  var stav = GAT.cmsStore.loadState(uloziste);
  var jazyk = "cs";

  function uloz() {
    stav = GAT.cmsStore.saveState(uloziste, stav);
    obnovCas();
  }

  function uklid(t) {
    return String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* -------------------------------------------------------- přihlášení */
  var PRIHLASEN = "gat-admin-prihlasen";
  function prihlasit(ano) {
    try { ano ? sessionStorage.setItem(PRIHLASEN, "1") : sessionStorage.removeItem(PRIHLASEN); } catch (e) {}
    $("[data-prihlaseni]").hidden = ano;
    $("[data-app]").hidden = !ano;
    if (ano) { vykresliNastenku(); vykresliTexty(); vykresliRealizace(); vykresliUzivatele(); obnovCas(); }
  }
  $("[data-vstoupit]").addEventListener("click", function () { prihlasit(true); });
  $("[data-odhlasit]").addEventListener("click", function () { prihlasit(false); });

  /* ------------------------------------------------------------ záložky */
  $$("[data-zalozka]").forEach(function (tl) {
    tl.addEventListener("click", function () {
      var id = tl.getAttribute("data-zalozka");
      $$("[data-zalozka]").forEach(function (x) {
        x.setAttribute("aria-selected", String(x === tl));
      });
      $$("[data-panel]", korenAdmin).forEach(function (p) {
        p.hidden = p.getAttribute("data-panel") !== id;
      });
    });
  });
  $$("[data-zalozka]")[0].setAttribute("aria-selected", "true");

  /* -------------------------------------------------------------- texty */
  var hledani = $("[data-admin-hledani]");
  var vyberJazyka = $("[data-admin-jazyk]");
  var kontejnerTextu = $("[data-admin-texty]");
  var prazdnoTextu = $("[data-admin-texty-prazdno]");

  vyberJazyka.addEventListener("change", function () {
    jazyk = vyberJazyka.value;
    vykresliTexty();
  });
  var casovac;
  hledani.addEventListener("input", function () {
    clearTimeout(casovac);
    casovac = setTimeout(vykresliTexty, 160);
  });

  function normalizuj(t) {
    return String(t).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function vykresliTexty() {
    var zaklad = data.slovniky[jazyk] || {};
    var prepisy = (stav.texts && stav.texts[jazyk]) || {};
    var dotaz = normalizuj(hledani.value.trim());

    var skupiny = {};
    data.klice.forEach(function (klic) {
      if (!(klic in zaklad)) return;
      var hodnota = klic in prepisy ? prepisy[klic] : zaklad[klic];
      if (dotaz && normalizuj(klic + " " + hodnota + " " + zaklad[klic]).indexOf(dotaz) === -1) return;
      var skupina = klic.split(".")[0];
      (skupiny[skupina] = skupiny[skupina] || []).push(klic);
    });

    var poradi = Object.keys(slovnikUI.skupiny).filter(function (s) { return skupiny[s]; });
    Object.keys(skupiny).forEach(function (s) { if (poradi.indexOf(s) === -1) poradi.push(s); });

    if (!poradi.length) {
      kontejnerTextu.innerHTML = "";
      prazdnoTextu.hidden = false;
      return;
    }
    prazdnoTextu.hidden = true;

    kontejnerTextu.innerHTML = poradi
      .map(function (s, i) {
        var polozky = skupiny[s]
          .map(function (klic) {
            var zmeneno = klic in prepisy;
            var hodnota = zmeneno ? prepisy[klic] : zaklad[klic];
            return (
              '<div class="admin-polozka" data-klic="' + uklid(klic) + '">' +
              '<div class="admin-klic">' + uklid(klic) +
              (zmeneno ? '<span class="admin-znacka">' + P.zmeneno + "</span>" : "") +
              "</div>" +
              '<textarea data-hodnota rows="2">' + uklid(hodnota) + "</textarea>" +
              '<div class="radek">' +
              '<button type="button" class="tl tl-hlavni tl-mala" data-uloz-text>' + P.ulozit + "</button>" +
              (zmeneno ? '<button type="button" class="tl tl-obrys tl-mala" data-vrat-text>' + P.vratit + "</button>" : "") +
              '<span class="puvodni">' + P.puvodni + ": " + uklid(zaklad[klic]) + "</span>" +
              "</div></div>"
            );
          })
          .join("");
        return (
          '<details class="admin-skupina"' + (i === 0 || dotaz ? " open" : "") + ">" +
          "<summary>" + uklid(slovnikUI.skupiny[s] || s) +
          '<span class="pocet">' + skupiny[s].length + "</span></summary>" +
          '<div class="admin-skupina-telo">' + polozky + "</div></details>"
        );
      })
      .join("");

    $$("[data-uloz-text]", kontejnerTextu).forEach(function (tl) {
      tl.addEventListener("click", function () {
        var polozka = tl.closest(".admin-polozka");
        var klic = polozka.getAttribute("data-klic");
        var hodnota = $("[data-hodnota]", polozka).value;
        var zaklad2 = data.slovniky[jazyk][klic];
        stav = GAT.cmsStore.setText(stav, jazyk, klic, hodnota === zaklad2 ? "" : hodnota);
        uloz();
        potvrd(tl);
        vykresliTexty();
      });
    });
    $$("[data-vrat-text]", kontejnerTextu).forEach(function (tl) {
      tl.addEventListener("click", function () {
        var klic = tl.closest(".admin-polozka").getAttribute("data-klic");
        stav = GAT.cmsStore.setText(stav, jazyk, klic, "");
        uloz();
        vykresliTexty();
      });
    });
  }

  function potvrd(tl) {
    var puvodni = tl.textContent;
    tl.textContent = P.ulozeno;
    setTimeout(function () { tl.textContent = puvodni; }, 1400);
  }

  /* --------------------------------------------------------- realizace */
  var kontejnerRealizaci = $("[data-admin-realizace]");
  var dialog = $("[data-dialog]");
  var formRealizace = $("[data-realizace-form]");

  var filtrVetve = "vse";

  function nazevVetve(id) {
    var v = (data.vetve || []).filter(function (x) { return x.id === id; })[0];
    return v ? v.nazev : "";
  }

  function vychoziVetev() {
    return (data.vetve && data.vetve[0] && data.vetve[0].id) || "";
  }

  function vykresliRealizace() {
    var vse = GAT.cmsStore.mergeRealizace(stav, data.realizace);
    if (filtrVetve !== "vse") {
      vse = vse.filter(function (r) { return (r.vetev || vychoziVetev()) === filtrVetve; });
    }
    var pridana = ((stav.realizace && stav.realizace.added) || []).map(function (r) { return r.id; });
    var upravena = Object.keys((stav.realizace && stav.realizace.edited) || {});

    if (!vse.length) {
      kontejnerRealizaci.innerHTML = '<p class="lead">' + P.prazdne + "</p>";
      return;
    }

    kontejnerRealizaci.innerHTML = vse
      .map(function (r) {
        var znacka = pridana.indexOf(r.id) !== -1
          ? '<span class="admin-znacka">' + P.vlastni + "</span>"
          : upravena.indexOf(r.id) !== -1
          ? '<span class="admin-znacka">' + P.upravena + "</span>"
          : "";
        return (
          '<div class="admin-karta-realizace" data-id="' + uklid(r.id) + '">' +
          '<div class="info"><div class="nazev">' + uklid(r.nazev) + " " + znacka + "</div>" +
          '<div class="meta"><span class="admin-vetev">' + uklid(nazevVetve(r.vetev || vychoziVetev())) +
          "</span> " + uklid(r.misto || "") + " · " + uklid(r.datum || "") + "</div></div>" +
          '<div class="tlacitka">' +
          '<button type="button" class="tl tl-obrys tl-mala" data-upravit>' + P.upravit + "</button>" +
          '<button type="button" class="tl tl-obrys tl-mala" data-smazat>' + P.smazat + "</button>" +
          "</div></div>"
        );
      })
      .join("");

    $$("[data-upravit]", kontejnerRealizaci).forEach(function (tl) {
      tl.addEventListener("click", function () {
        var id = tl.closest("[data-id]").getAttribute("data-id");
        var polozka = GAT.cmsStore.mergeRealizace(stav, data.realizace).filter(function (r) { return r.id === id; })[0];
        otevriDialog(polozka);
      });
    });
    $$("[data-smazat]", kontejnerRealizaci).forEach(function (tl) {
      tl.addEventListener("click", function () {
        var id = tl.closest("[data-id]").getAttribute("data-id");
        if (!window.confirm(P.smazatPotvrzeni)) return;
        stav = GAT.cmsStore.removeRealizace(stav, id);
        uloz();
        vykresliRealizace();
      });
    });
  }

  function otevriDialog(polozka) {
    var p = polozka || {};
    formRealizace.elements.id.value = p.id || "";
    formRealizace.elements.vetev.value = p.vetev || vychoziVetev();
    formRealizace.elements.nazev.value = p.nazev || "";
    formRealizace.elements.misto.value = p.misto || "";
    formRealizace.elements.datum.value = p.datum || new Date().toISOString().slice(0, 10);
    formRealizace.elements.plocha.value = p.plocha || "";
    formRealizace.elements.perex.value = p.perex || "";
    formRealizace.elements.zadani.value = p.zadani || "";
    formRealizace.elements.doba.value = p.doba || "";
    formRealizace.elements.vysledek.value = p.vysledek || "";
    formRealizace.elements.rozsah.value = (p.rozsah || []).join("\n");
    formRealizace.elements.technologie.value = (p.technologie || []).join(", ");
    var kat = p.kategorie || [];
    $$('input[name="kategorie"]', formRealizace).forEach(function (ch) {
      ch.checked = kat.indexOf(ch.value) !== -1;
    });
    $("[data-dialog-titulek]").textContent = p.id ? P.upravit : P.pridat;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  $("[data-pridat-realizaci]").addEventListener("click", function () { otevriDialog(null); });
  $$("[data-filtr-vetev]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      filtrVetve = chip.getAttribute("data-filtr-vetev");
      $$("[data-filtr-vetev]").forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      vykresliRealizace();
    });
  });
  $("[data-zavrit-dialog]").addEventListener("click", function () { dialog.close(); });

  formRealizace.addEventListener("submit", function () {
    var f = formRealizace.elements;
    var polozka = {
      vetev: f.vetev.value,
      nazev: f.nazev.value.trim(),
      misto: f.misto.value.trim(),
      datum: f.datum.value,
      plocha: f.plocha.value.trim(),
      doba: f.doba.value.trim(),
      perex: f.perex.value.trim(),
      zadani: f.zadani.value.trim(),
      vysledek: f.vysledek.value.trim(),
      rozsah: f.rozsah.value.split("\n").map(function (x) { return x.trim(); }).filter(Boolean),
      technologie: f.technologie.value.split(",").map(function (x) { return x.trim(); }).filter(Boolean),
      kategorie: $$('input[name="kategorie"]:checked', formRealizace).map(function (ch) { return ch.value; }),
    };
    if (f.id.value) polozka.id = f.id.value;
    if (!polozka.nazev) return;
    stav = GAT.cmsStore.upsertRealizace(stav, polozka, data.realizace);
    uloz();
    vykresliRealizace();
  });

  /* ---------------------------------------------------------- nástěnka
     Ukázková analytika. Data generuje GAT.statistiky deterministicky, aby
     náhled vypadal pokaždé stejně — na ostrém webu je nahradí Analytics. */
  var obdobi = 30;

  function vykresliNastenku() {
    if (!window.GAT || !GAT.statistiky) return;
    var S = GAT.statistiky;
    var vsechna = S.vygenerujData("green-air-tech", obdobi * 2);
    var ted = S.filtrujObdobi(vsechna, obdobi);
    var drive = vsechna.slice(0, vsechna.length - ted.length);
    var a = S.souhrn(ted);
    var b = S.souhrn(drive);

    var format = {
      navstevy: S.formatCislo, uzivatele: S.formatCislo,
      zobrazeni: S.formatCislo, poptavky: S.formatCislo,
      cas: S.formatCas, opusteni: S.formatProcenta,
    };
    Object.keys(format).forEach(function (klic) {
      var karta = $('[data-metrika="' + klic + '"]');
      if (!karta) return;
      $("[data-hodnota]", karta).textContent = format[klic](a[klic]);
      var zmena = S.zmenaProti(a[klic], b[klic]);
      var el = $("[data-zmena]", karta);
      el.textContent = S.formatZmena(zmena);
      // u míry opuštění je pokles dobrá zpráva
      var dobre = klic === "opusteni" ? zmena < 0 : zmena > 0;
      el.setAttribute("data-smer", zmena === null || zmena === 0 ? "nic" : dobre ? "nahoru" : "dolu");
    });

    nakresliGraf(S, ted);
    vykresliRozpady(S);
  }

  function nakresliGraf(S, data2) {
    var cil = $("[data-graf]");
    if (!cil) return;
    var osa = S.osaGrafu(data2, "navstevy");
    if (!osa.body.length) { cil.innerHTML = ""; return; }
    var body = osa.body.map(function (b) { return b.x.toFixed(2) + "," + (100 - b.y).toFixed(2); });
    var plocha = "0,100 " + body.join(" ") + " 100,100";
    cil.innerHTML =
      '<svg viewBox="0 0 100 100" preserveAspectRatio="none" class="admin-sparkline" aria-hidden="true">' +
      '<polygon points="' + plocha + '" class="admin-sparkline-plocha"/>' +
      '<polyline points="' + body.join(" ") + '" class="admin-sparkline-cara"/>' +
      "</svg>" +
      '<div class="admin-graf-osa"><span>' + uklid(data2[0].datum) + "</span><span>" +
      uklid(data2[data2.length - 1].datum) + "</span></div>" +
      '<div class="admin-graf-rozsah">' + S.formatCislo(osa.min) + " – " + S.formatCislo(osa.max) + "</div>";
  }

  function vykresliRozpady(S) {
    Object.keys(slovnikUI.rozpady || {}).forEach(function (klic) {
      var cil = $('[data-rozpad="' + klic + '"]');
      if (!cil) return;
      var radky = S.rozdeleni("gat-" + klic + "-" + obdobi, slovnikUI.rozpady[klic]);
      cil.innerHTML = radky
        .map(function (r) {
          return '<div class="admin-radek"><span>' + uklid(r.nazev) + "</span>" +
            '<span class="admin-pruh"><i style="width:' + r.podil + '%"></i></span>' +
            "<b>" + r.podil + " %</b></div>";
        })
        .join("");
    });
  }

  $$("[data-obdobi]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      obdobi = Number(chip.getAttribute("data-obdobi"));
      $$("[data-obdobi]").forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      vykresliNastenku();
    });
  });

  /* -------------------------------------------------------- uživatelé */
  var KLIC_UZIVATELE = "gat-admin-uzivatele";
  var VYCHOZI_UZIVATELE = [
    { jmeno: "Pavel Janda", email: "pavel.janda@greenairtech.cz", role: "spravce" },
    { jmeno: "Martina Mašindová", email: "martina.masindova@greenairtech.cz", role: "editor" },
  ];

  function nactiUzivatele() {
    try {
      var syrove = uloziste.getItem(KLIC_UZIVATELE);
      if (!syrove) return VYCHOZI_UZIVATELE.slice();
      var ulozeni = JSON.parse(syrove);
      return Array.isArray(ulozeni) ? ulozeni : VYCHOZI_UZIVATELE.slice();
    } catch (e) { return VYCHOZI_UZIVATELE.slice(); }
  }
  function ulozUzivatele(seznam) { uloziste.setItem(KLIC_UZIVATELE, JSON.stringify(seznam)); }

  function vykresliUzivatele() {
    var cil = $("[data-admin-uzivatele]");
    if (!cil) return;
    var seznam = nactiUzivatele();
    if (!seznam.length) { cil.innerHTML = '<p class="lead">' + P.uzivateleprazdne + "</p>"; return; }
    cil.innerHTML = seznam
      .map(function (u, i) {
        var role = (slovnikUI.role || {})[u.role] || { nazev: u.role, prava: "" };
        return '<div class="admin-karta-realizace" data-uzivatel="' + i + '">' +
          '<div class="info"><div class="nazev">' + uklid(u.jmeno) + "</div>" +
          '<div class="meta">' + uklid(u.email || "") + "</div></div>" +
          '<div class="info"><div class="nazev">' + uklid(role.nazev) + "</div>" +
          '<div class="meta">' + uklid(role.prava) + "</div></div>" +
          '<div class="tlacitka"><button type="button" class="tl tl-obrys tl-mala" data-odebrat-uzivatele>' +
          P.odebrat + "</button></div></div>";
      })
      .join("");
    $$("[data-odebrat-uzivatele]", cil).forEach(function (tl) {
      tl.addEventListener("click", function () {
        if (!window.confirm(P.odebratPotvrzeni)) return;
        var i = Number(tl.closest("[data-uzivatel]").getAttribute("data-uzivatel"));
        var seznam2 = nactiUzivatele();
        seznam2.splice(i, 1);
        ulozUzivatele(seznam2);
        vykresliUzivatele();
      });
    });
  }

  var dialogUzivatel = $("[data-dialog-uzivatel]");
  var formUzivatel = $("[data-uzivatel-form]");
  $("[data-pridat-uzivatele]").addEventListener("click", function () {
    formUzivatel.reset();
    if (typeof dialogUzivatel.showModal === "function") dialogUzivatel.showModal();
    else dialogUzivatel.setAttribute("open", "");
  });
  $("[data-zavrit-uzivatel]").addEventListener("click", function () { dialogUzivatel.close(); });
  formUzivatel.addEventListener("submit", function () {
    var f = formUzivatel.elements;
    if (!f.jmeno.value.trim()) return;
    var seznam = nactiUzivatele();
    seznam.push({ jmeno: f.jmeno.value.trim(), email: f.email.value.trim(), role: f.role.value });
    ulozUzivatele(seznam);
    vykresliUzivatele();
  });

  /* -------------------------------------------------------------- data */
  function obnovCas() {
    var el = $("[data-admin-cas]");
    if (!el) return;
    el.textContent = stav.updatedAt
      ? P.posledniZmena + ": " + new Date(stav.updatedAt).toLocaleString(document.documentElement.lang)
      : P.zadnaZmena;
  }

  $("[data-export]").addEventListener("click", function () {
    var blob = new Blob([GAT.cmsStore.exportJson(stav)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "green-air-tech-zmeny.json";
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  });

  $("[data-import]").addEventListener("change", function (e) {
    var soubor = e.target.files && e.target.files[0];
    if (!soubor) return;
    var ctecka = new FileReader();
    ctecka.onload = function () {
      var vysledek = GAT.cmsStore.importJson(stav, String(ctecka.result));
      if (!vysledek.ok) { window.alert(P.chybaImportu + " " + vysledek.error); return; }
      stav = vysledek.state;
      uloz();
      vykresliTexty();
      vykresliRealizace();
      vykresliUzivatele();
    };
    ctecka.readAsText(soubor);
    e.target.value = "";
  });

  $("[data-reset]").addEventListener("click", function () {
    if (!window.confirm(P.vymazatPotvrzeni)) return;
    GAT.cmsStore.resetState(uloziste);
    stav = GAT.cmsStore.emptyState();
    vykresliTexty();
    vykresliRealizace();
    obnovCas();
  });

  /* Až úplně na konec: do téhle chvíle musí existovat všechny proměnné,
     které vykreslovací funkce používají (jinak to padá na hledani.value). */
  var jePrihlasen = false;
  try { jePrihlasen = sessionStorage.getItem(PRIHLASEN) === "1"; } catch (e) {}
  prihlasit(jePrihlasen);
})();
