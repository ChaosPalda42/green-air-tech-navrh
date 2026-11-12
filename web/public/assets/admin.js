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

  /* ------------------------------------------------- ukázka / ostrý web
     V ukázce je pravda v localStorage prohlížeče. Na ostrém webu je na
     serveru: PHP vloží do stránky window.GAT_STAV a window.GAT_UZIVATELE,
     každý zápis jde do /api/*. Rozhraní je schválně stejné jako Storage,
     aby zbytek téhle administrace nemusel vědět, kam vlastně ukládá. */
  var SERVER = !!window.GAT_SERVER;
  var HLASKY = {
    ulozeni: "Změnu se nepovedlo uložit na server. Stránku raději obnovte.",
    prava: "Na tuhle změnu nemáte právo.",
    odhlasen: "Přihlášení vypršelo. Přihlaste se znovu.",
    fotka: "Fotku se nepovedlo nahrát na server.",
    fotkaVelka: "Fotka má moc pixelů, než aby ji server rozbalil. Zmenšete ji a nahrajte znovu.",
    souborVelky: "Soubor je větší, než server přijímá. Zmenšete fotku a nahrajte znovu.",
    nahraniPreruseno: "Nahrávání se přerušilo. Zkuste to prosím ještě jednou.",
    statistiky: "Statistiky se nepovedlo načíst, ukazuje se ukázkový náhled.",
  };

  /* Hosting u klienta nepouští PUT ani DELETE: Apache je odmítne 403 dřív,
     než se spustí PHP, takže by se z administrace neuložilo nic. Posílá se
     proto POST a skutečná metoda jde v hlavičce — tu cizí stránka nenastaví
     (prohlížeč by si napřed vyžádal CORS preflight), takže se tím nic
     neotvírá. Na serveru ji přečte App\Jadro\Metoda. */
  function api(metoda, cil, telo, soubor) {
    var prestrojena = metoda === "PUT" || metoda === "DELETE";
    var volby = {
      method: prestrojena ? "POST" : metoda,
      credentials: "same-origin",
      headers: { "X-CSRF": window.GAT_CSRF || "" },
    };
    if (prestrojena) volby.headers["X-HTTP-Method-Override"] = metoda;
    if (soubor) {
      var fd = new FormData();
      fd.append("fotka", soubor);
      volby.body = fd;
    } else if (telo !== undefined) {
      volby.headers["Content-Type"] = "application/json";
      volby.body = JSON.stringify(telo);
    }
    return fetch((window.GAT_API || "api/") + cil, volby).then(function (r) {
      return r
        .json()
        .catch(function () { return {}; })
        .then(function (d) {
          if (r.ok) return d;
          var e = new Error(d.chyba || "http-" + r.status);
          e.stav = r.status;
          e.data = d;
          throw e;
        });
    });
  }

  function hlaskaChyby(e) {
    if (e && e.stav === 401) return HLASKY.odhlasen;
    if (e && e.stav === 403) return HLASKY.prava;
    /* Odpovědi od nahrávání fotek: obecné „Změnu se nepovedlo uložit" by
       správce poslalo obnovovat stránku, místo aby fotku zmenšil. */
    var kod = e && e.data ? e.data.chyba : "";
    if (kod === "fotka-moc-velka") return HLASKY.fotkaVelka;
    if (kod === "soubor-moc-velky") return HLASKY.souborVelky;
    if (kod === "nahrani-preruseno") return HLASKY.nahraniPreruseno;
    return HLASKY.ulozeni;
  }

  /** Storage nad serverem: čte z toho, co vložilo PHP, zapisuje do API. */
  function serverUloziste() {
    var pamet = {};
    pamet["gat-cms-v1"] = JSON.stringify(window.GAT_STAV || GAT.cmsStore.emptyState());
    pamet["gat-admin-uzivatele"] = JSON.stringify(window.GAT_UZIVATELE || []);
    function nestaraSe(e) {
      window.alert(hlaskaChyby(e));
      if (e && (e.stav === 401 || e.stav === 403)) return;
      window.location.reload();
    }
    return {
      getItem: function (k) {
        return Object.prototype.hasOwnProperty.call(pamet, k) ? pamet[k] : null;
      },
      setItem: function (k, v) {
        var drive = pamet[k];
        pamet[k] = v;
        if (k === "gat-cms-v1") {
          api("PUT", "stav", JSON.parse(v)).catch(function (e) {
            pamet[k] = drive;
            nestaraSe(e);
          });
          return;
        }
        if (k === "gat-admin-uzivatele") {
          var stari = JSON.parse(drive || "[]");
          var novi = JSON.parse(v);
          var ids = novi.map(function (u) { return u.id; });
          var prace = stari
            .filter(function (u) { return u.id != null && ids.indexOf(u.id) === -1; })
            .map(function (u) { return function () { return api("DELETE", "uzivatele?id=" + encodeURIComponent(u.id)); }; })
            .concat(
              novi
                .filter(function (u) { return u.id == null; })
                .map(function (u) {
                  return function () {
                    return api("POST", "uzivatele", { jmeno: u.jmeno, email: u.email, role: u.role })
                      .then(function (d) {
                        /* Server vrátí pozvánku s tokenem; bez ní by nový
                           uživatel neměl jak heslo nastavit, tak si ji
                           schováme a po překreslení ukážeme odkaz. */
                        if (d && d.pozvanka && d.pozvanka.token) {
                          cekaPozvanka = { jmeno: u.jmeno, email: u.email, token: d.pozvanka.token };
                        }
                        return d;
                      });
                  };
                })
            );
          prace
            .reduce(function (retez, krok) { return retez.then(krok); }, Promise.resolve())
            .then(function () { return api("GET", "uzivatele"); })
            .then(function (d) {
              pamet[k] = JSON.stringify(d.uzivatele || []);
              vykresliUzivatele();
              if (cekaPozvanka) { ukazPozvanku(cekaPozvanka); cekaPozvanka = null; }
            })
            .catch(function (e) { pamet[k] = drive; nestaraSe(e); });
        }
      },
      removeItem: function (k) {
        if (k === "gat-cms-v1") {
          var prazdny = GAT.cmsStore.emptyState();
          pamet[k] = JSON.stringify(prazdny);
          api("PUT", "stav", prazdny).catch(nestaraSe);
          return;
        }
        delete pamet[k];
      },
    };
  }

  var uloziste = SERVER
    ? serverUloziste()
    : window.GAT_ULOZISTE
      ? window.GAT_ULOZISTE()
      : window.localStorage;
  var stav = GAT.cmsStore.loadState(uloziste);
  var jazyk = "cs";

  function uloz() {
    // Fotky se ukládají jako data URL, takže se dá narazit na strop
    // localStorage. Když to nevyjde, vrátíme stav zpátky a řekneme to.
    var predtim = stav;
    try {
      stav = GAT.cmsStore.saveState(uloziste, stav);
    } catch (e) {
      stav = predtim;
      window.alert(P.fotkyPlno);
      return false;
    }
    obnovCas();
    return true;
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
    if (ano) { vykresliNastenku(); vykresliTexty(); vykresliRealizace(); vykresliPortrety(); vykresliUzivatele(); obnovCas(); }
  }
  if (SERVER) {
    // tlačítko „Vstoupit" je na ostrém webu submit skutečného formuláře,
    // odhlášení musí projít serverem, aby zanikla session
    $("[data-odhlasit]").addEventListener("click", function () {
      var f = document.createElement("form");
      f.method = "post";
      f.action = window.location.pathname;
      f.innerHTML =
        '<input type="hidden" name="akce" value="odhlasit">' +
        '<input type="hidden" name="csrf" value="' + uklid(window.GAT_CSRF || "") + '">';
      document.body.appendChild(f);
      f.submit();
    });
  } else {
    $("[data-vstoupit]").addEventListener("click", function () { prihlasit(true); });
    $("[data-odhlasit]").addEventListener("click", function () { prihlasit(false); });
  }

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
      // Na mobilu se lišta záložek posouvá do strany; vybraná musí být
      // vidět celá. scrollIntoView({inline:"nearest"}) tu nestačí — nechával
      // ji o pár pixelů za hranou, tak si posun spočítáme sami.
      var lista = tl.parentNode;
      if (lista && lista.scrollWidth > lista.clientWidth) {
        // offsetLeft tu neposlouží — lišta není pozicovaná, takže se počítá
        // od jiného předka. Rozdíly obdélníků jsou spolehlivější.
        var rezerva = 12;
        var oL = lista.getBoundingClientRect();
        var oT = tl.getBoundingClientRect();
        if (oT.left < oL.left + rezerva) lista.scrollLeft -= oL.left + rezerva - oT.left;
        else if (oT.right > oL.right - rezerva) lista.scrollLeft += oT.right - oL.right + rezerva;
      }
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

  function nahledRealizace(r) {
    var fotky = F ? F.normalizujGalerie(r.fotky) : [];
    if (!fotky.length) return '<span class="admin-nahled admin-nahled-prazdny" aria-hidden="true"></span>';
    return '<span class="admin-nahled"><img src="' + F.zdrojFotky(fotky[0], window.GAT_KOREN) + '" alt=""></span>' +
      (fotky.length > 1 ? '<span class="admin-nahled-pocet">+' + (fotky.length - 1) + "</span>" : "");
  }

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
          nahledRealizace(r) +
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

  /* ------------------------------------------------------------- fotky
     Obrázek se před uložením zmenší na dlouhou hranu LIMITY.maxHrana a
     překlopí do JPEG — bez toho by se do localStorage vešly dvě fotky.
     Pořadí, limity a formátování velikostí řeší GAT.fotky (kontrakt C-010). */
  var galerieVDialogu = [];
  var F = window.GAT && GAT.fotky;

  function zonaFotek() { return $("[data-fotky-zona]", formRealizace); }

  function ukazChybyFotek(seznam) {
    var cil = $("[data-fotky-chyby]", formRealizace);
    if (!cil) return;
    cil.hidden = !seznam.length;
    cil.innerHTML = seznam
      .map(function (ch) { return '<p class="chyba">' + uklid(ch) + "</p>"; })
      .join("");
  }

  function hlaskaOdmitnuti(o) {
    var vzor = (P.fotkyChyba || {})[o.duvod] || "{soubor}";
    return vzor.replace("{soubor}", o.nazev || "");
  }

  /** Načte soubor, zmenší ho přes canvas a vrátí záznam fotky. */
  function zpracujSoubor(soubor) {
    // Na ostrém webu fotku zmenší a uloží server (webp v public/media),
    // v prohlížeči zůstane jen odkaz. V ukázce se nese jako data URL.
    if (SERVER) {
      return api("POST", "fotka", undefined, soubor).then(function (d) {
        var f = d.fotka || {};
        return {
          id: f.id || "f" + Date.now().toString(36),
          nazev: soubor.name,
          typ: f.typ || "image/webp",
          sirka: f.sirka || 0,
          vyska: f.vyska || 0,
          bajty: f.bajty || soubor.size,
          /* Ve stavu je jen cesta do media — kořen si při kreslení doplní
              každá stránka sama (v /en/ je o adresář výš). */
          dataUrl: f.soubor || "",
        };
      });
    }
    return new Promise(function (hotovo, chyba) {
      var ctecka = new FileReader();
      ctecka.onerror = function () { chyba(new Error("cteni")); };
      ctecka.onload = function () {
        var obr = new Image();
        obr.onerror = function () { chyba(new Error("obrazek")); };
        obr.onload = function () {
          var cil = F.cilovyRozmer(obr.naturalWidth, obr.naturalHeight, F.LIMITY.maxHrana);
          var platno = document.createElement("canvas");
          platno.width = cil.sirka;
          platno.height = cil.vyska;
          var ctx = platno.getContext("2d");
          ctx.drawImage(obr, 0, 0, cil.sirka, cil.vyska);
          var dataUrl = platno.toDataURL("image/jpeg", 0.82);
          hotovo({
            id: "f" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
            nazev: soubor.name,
            typ: "image/jpeg",
            sirka: cil.sirka,
            vyska: cil.vyska,
            bajty: F.odhadniBajty(dataUrl),
            dataUrl: dataUrl,
          });
        };
        obr.src = ctecka.result;
      };
      ctecka.readAsDataURL(soubor);
    });
  }

  function nactiSoubory(soubory) {
    if (!F || !soubory || !soubory.length) return;
    var zona = zonaFotek();
    if (zona) zona.setAttribute("data-nacitam", "1");
    var chyby = [];
    var pripravene = [];
    var fronta = Array.prototype.slice.call(soubory).reduce(function (retez, soubor) {
      return retez.then(function () {
        var kontrola = F.zkontrolujSoubor({ nazev: soubor.name, typ: soubor.type, velikost: soubor.size });
        if (!kontrola.ok) {
          chyby.push(hlaskaOdmitnuti({ nazev: soubor.name, duvod: kontrola.chyba }));
          return null;
        }
        return zpracujSoubor(soubor).then(
          function (f) { pripravene.push(f); },
          function (e) {
            /* Server umí říct, CO bylo špatně. Dosud se to zahodilo a správce
               se dozvěděl jen „obrázek se nepodařilo otevřít". */
            var kod = e && e.data ? e.data.chyba : "";
            if (kod === "fotka-moc-velka" || kod === "soubor-moc-velky"
                || kod === "nahrani-preruseno") {
              chyby.push(soubor.name + ": " + hlaskaChyby(e));
              return;
            }
            chyby.push(hlaskaOdmitnuti({ nazev: soubor.name, duvod: "nacteni" }));
          }
        );
      });
    }, Promise.resolve());

    fronta.then(function () {
      var vysledek = F.pridejFotky(galerieVDialogu, pripravene);
      galerieVDialogu = vysledek.galerie;
      vysledek.odmitnuto.forEach(function (o) { chyby.push(hlaskaOdmitnuti(o)); });
      if (zona) zona.removeAttribute("data-nacitam");
      ukazChybyFotek(chyby);
      vykresliGalerii();
    });
  }

  function vykresliGalerii() {
    var cil = $("[data-fotky-seznam]", formRealizace);
    var souhrnEl = $("[data-fotky-souhrn]", formRealizace);
    if (!cil || !F) return;
    if (!galerieVDialogu.length) {
      cil.innerHTML = '<p class="napoveda">' + uklid(P.fotkyPrazdno) + "</p>";
    } else {
      cil.innerHTML = galerieVDialogu
        .map(function (f, i) {
          return '<figure class="admin-fotka" data-fotka="' + uklid(f.id) + '">' +
            '<img src="' + F.zdrojFotky(f, window.GAT_KOREN) + '" alt="' + uklid(f.nazev) + '" loading="lazy">' +
            (i === 0 ? '<span class="admin-fotka-titulni">' + uklid(P.fotkyTitulni) + "</span>" : "") +
            '<figcaption>' + uklid(F.formatVelikost(f.bajty)) + " · " + f.sirka + "×" + f.vyska + "</figcaption>" +
            '<div class="admin-fotka-akce">' +
            '<button type="button" data-fotka-doleva aria-label="' + uklid(P.fotkyDoleva) + '" title="' + uklid(P.fotkyDoleva) + '"' + (i === 0 ? " disabled" : "") + ">&#8592;</button>" +
            '<button type="button" data-fotka-titulni aria-label="' + uklid(P.fotkyNastavTitulni) + '" title="' + uklid(P.fotkyNastavTitulni) + '"' + (i === 0 ? " disabled" : "") + ">&#9733;</button>" +
            '<button type="button" data-fotka-doprava aria-label="' + uklid(P.fotkyDoprava) + '" title="' + uklid(P.fotkyDoprava) + '"' + (i === galerieVDialogu.length - 1 ? " disabled" : "") + ">&#8594;</button>" +
            '<button type="button" data-fotka-pryc aria-label="' + uklid(P.fotkyOdebrat) + '" title="' + uklid(P.fotkyOdebrat) + '">&#10005;</button>' +
            "</div></figure>";
        })
        .join("");
    }
    if (souhrnEl) {
      var souhrn = F.souhrn(galerieVDialogu);
      souhrnEl.textContent = String(P.fotkySouhrn || "")
        .replace("{pocet}", souhrn.pocet)
        .replace("{velikost}", F.formatVelikost(souhrn.bajty));
    }
  }

  // akce nad dlaždicemi řešíme delegováním — mřížka se překresluje
  $("[data-fotky-seznam]", formRealizace).addEventListener("click", function (e) {
    var tl = e.target.closest("button");
    if (!tl) return;
    var id = tl.closest("[data-fotka]").getAttribute("data-fotka");
    if (tl.hasAttribute("data-fotka-pryc")) galerieVDialogu = F.odeberFotku(galerieVDialogu, id);
    else if (tl.hasAttribute("data-fotka-doleva")) galerieVDialogu = F.presunFotku(galerieVDialogu, id, -1);
    else if (tl.hasAttribute("data-fotka-doprava")) galerieVDialogu = F.presunFotku(galerieVDialogu, id, 1);
    else if (tl.hasAttribute("data-fotka-titulni")) galerieVDialogu = F.nastavTitulni(galerieVDialogu, id);
    vykresliGalerii();
  });

  var vstupFotek = $("[data-fotky-vstup]", formRealizace);
  $("[data-fotky-vybrat]", formRealizace).addEventListener("click", function () { vstupFotek.click(); });
  vstupFotek.addEventListener("change", function () {
    nactiSoubory(vstupFotek.files);
    vstupFotek.value = "";
  });

  (function pretahovani() {
    var zona = zonaFotek();
    if (!zona) return;
    ["dragenter", "dragover"].forEach(function (udalost) {
      zona.addEventListener(udalost, function (e) {
        e.preventDefault();
        zona.setAttribute("data-nad", "1");
      });
    });
    ["dragleave", "drop"].forEach(function (udalost) {
      zona.addEventListener(udalost, function (e) {
        e.preventDefault();
        zona.removeAttribute("data-nad");
      });
    });
    zona.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files) nactiSoubory(e.dataTransfer.files);
    });
  })();

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
    galerieVDialogu = F ? F.normalizujGalerie(p.fotky) : [];
    ukazChybyFotek([]);
    vykresliGalerii();
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
    polozka.fotky = galerieVDialogu;
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

  // na ostrém webu sem teče Google Analytics: data z /api/statistiky se
  // uloží sem a nástěnka se překreslí. Formátování a graf zůstávají stejné.
  var zeServeru = null;

  function nactiStatistiky() {
    api("GET", "statistiky?dni=" + obdobi * 2)
      .then(function (d) {
        zeServeru = { dny: d.dny || [], rozpady: d.rozpady || {} };
        vykresliNastenku();
      })
      .catch(function () {
        // Na ostrém webu se čísla nedotáhla. Prázdná nástěnka je poctivější než
        // vygenerovaná — a kdyby tu zůstalo null, vykresliNastenku by si o data
        // řekla znovu a pořád dokola.
        zeServeru = { dny: [], rozpady: {} };
        vykresliNastenku();
      });
  }

  function vykresliNastenku() {
    if (!window.GAT || !GAT.statistiky) return;
    var S = GAT.statistiky;
    if (SERVER && zeServeru === null) { nactiStatistiky(); return; }
    var vsechna = SERVER
      ? zeServeru.dny
      : S.vygenerujData("green-air-tech", obdobi * 2);

    // Upozornění "čísla se zatím nenačetla" patří jen k prázdné nástěnce.
    // Pozor: .hlaska má display:flex, který atribut hidden přebije — schovává
    // se proto stylem, ne atributem.
    var upozorneni = document.querySelector("[data-nastenka-upozorneni]");
    if (upozorneni && SERVER) upozorneni.style.display = vsechna.length > 0 ? "none" : "";
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
      var radky = SERVER
        ? zeServeru.rozpady[klic] || []
        : S.rozdeleni("gat-" + klic + "-" + obdobi, slovnikUI.rozpady[klic]);
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
      if (SERVER) zeServeru = null;
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
          '<div class="tlacitka">' +
          (SERVER && u.id != null
            ? '<button type="button" class="tl tl-obrys tl-mala" data-pozvat-uzivatele>' +
              POZVANKY.vystavit + "</button>"
            : "") +
          '<button type="button" class="tl tl-obrys tl-mala" data-odebrat-uzivatele>' +
          P.odebrat + "</button></div></div>";
      })
      .join("");
    $$("[data-pozvat-uzivatele]", cil).forEach(function (tl) {
      tl.addEventListener("click", function () {
        var u = seznam[Number(tl.closest("[data-uzivatel]").getAttribute("data-uzivatel"))];
        if (!u || u.id == null) return;
        if (!window.confirm(POZVANKY.potvrzeni.replace("{jmeno}", u.jmeno))) return;
        api("POST", "pozvanka", { id: Number(u.id) })
          .then(function (d) {
            ukazPozvanku({ jmeno: u.jmeno, email: u.email, token: (d.pozvanka || {}).token });
          })
          .catch(function (e) {
            window.alert(e && e.data && e.data.chyba === "nelze-sam-sebe"
              ? POZVANKY.sobe
              : hlaskaChyby(e));
          });
      });
    });
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

  /* ------------------------------------- pozvánky a vlastní heslo
     Jen na ostrém webu. Nový uživatel nemá heslo — dostane odkaz
     administrace.html?pozvanka=<token>, kterým si ho nastaví. Vlastní heslo
     si mění každý sám přes POST /api/heslo; správce cizí heslo nezadává,
     jen vystaví novou pozvánku. */
  var POZVANKY = {
    vystavit: "Pozvánka",
    potvrzeni: "Vystavit novou pozvánku pro {jmeno}? Dosavadní heslo tím přestane platit.",
    sobe: "Pozvánku si sám sobě nevystavíte — zrušila by vám heslo. Použijte Změnit heslo.",
    zkopirovano: "Odkaz je zkopírovaný.",
    nezkopirovano: "Odkaz se nepovedlo zkopírovat, vyberte ho prosím ručně.",
    komu: "Pozvánka pro {jmeno} ({email}).",
    hesloHotovo: "Heslo je změněné.",
    hesloStare: "Současné heslo nesouhlasí.",
    hesloNesouhlasi: "Nová hesla se neshodují.",
    hesloKratke: "Nové heslo musí mít aspoň 12 znaků.",
    hesloPrazdne: "Heslo nemůže být prázdné.",
  };
  var cekaPozvanka = null;

  function otevri(dialog) {
    if (!dialog) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function odkazPozvanky(token) {
    return window.location.origin + window.location.pathname +
      "?pozvanka=" + encodeURIComponent(token);
  }

  var dialogPozvanka = $("[data-dialog-pozvanka]");

  function ukazPozvanku(kdo) {
    if (!kdo || !kdo.token) return;
    var odkaz = odkazPozvanky(kdo.token);
    if (!dialogPozvanka) { window.prompt(POZVANKY.komu, odkaz); return; }
    $("[data-pozvanka-komu]", dialogPozvanka).textContent = POZVANKY.komu
      .replace("{jmeno}", kdo.jmeno || "")
      .replace("{email}", kdo.email || "");
    var pole = $("[data-pozvanka-odkaz]", dialogPozvanka);
    pole.value = odkaz;
    otevri(dialogPozvanka);
    pole.select();
  }

  if (dialogPozvanka) {
    $("[data-kopirovat-pozvanku]", dialogPozvanka).addEventListener("click", function () {
      var pole = $("[data-pozvanka-odkaz]", dialogPozvanka);
      pole.select();
      var hotovo = function () { window.alert(POZVANKY.zkopirovano); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(pole.value).then(hotovo, function () {
          window.alert(POZVANKY.nezkopirovano);
        });
        return;
      }
      try { document.execCommand("copy"); hotovo(); }
      catch (e) { window.alert(POZVANKY.nezkopirovano); }
    });
  }

  var dialogHeslo = $("[data-dialog-heslo]");
  var tlacitkoHeslo = $("[data-moje-heslo]");
  if (dialogHeslo && tlacitkoHeslo) {
    var formHeslo = $("[data-heslo-form]", dialogHeslo);
    tlacitkoHeslo.addEventListener("click", function () {
      formHeslo.reset();
      otevri(dialogHeslo);
    });
    $("[data-zavrit-heslo]", dialogHeslo).addEventListener("click", function () {
      dialogHeslo.close();
    });
    formHeslo.addEventListener("submit", function () {
      var f = formHeslo.elements;
      var stare = f.stare.value;
      var nove = f.nove.value;
      if (nove !== f.nove2.value) { window.alert(POZVANKY.hesloNesouhlasi); return; }
      api("POST", "heslo", { stare: stare, nove: nove })
        .then(function () { window.alert(POZVANKY.hesloHotovo); })
        .catch(function (e) {
          var chyba = e && e.data ? e.data.chyba : "";
          if (chyba === "spatne-stare-heslo") { window.alert(POZVANKY.hesloStare); return; }
          if (chyba === "vadne-heslo") {
            window.alert(e.data.duvod === "prazdne" ? POZVANKY.hesloPrazdne : POZVANKY.hesloKratke);
            return;
          }
          window.alert(hlaskaChyby(e));
        });
    });
  }

  /* ------------------------------------------------------- práva rolí
     Matice je stejná jako na serveru (App\Auth\Uzivatele::MATICE) —
     tady jen zhasíná záložky, aby se uživatel nedobýval do něčeho, co mu
     API stejně odmítne. Rozhoduje server, tohle je slušnost k uživateli. */
  var PANELY = {
    nastenka: "statistiky",
    texty: "texty",
    realizace: "realizace",
    portrety: "texty",
    uzivatele: "uzivatele",
    data: "uzivatele",
  };
  var MATICE = {
    spravce: ["texty", "realizace", "novinky", "uzivatele", "statistiky"],
    editor: ["texty", "realizace", "novinky"],
    autor: ["novinky"],
  };

  function omezPodleRole(role) {
    var smi = MATICE[role] || [];
    var prvni = null;
    $$("[data-zalozka]").forEach(function (tl) {
      var panel = tl.getAttribute("data-zalozka");
      var oblast = PANELY[panel] || panel;
      // „novinky" se v téhle administraci upravují mezi texty
      var povoleno = smi.indexOf(oblast) !== -1 || (panel === "texty" && smi.indexOf("novinky") !== -1);
      tl.hidden = !povoleno;
      var cil = $('[data-panel="' + panel + '"]', korenAdmin);
      if (!povoleno && cil) cil.hidden = true;
      if (povoleno && !prvni) prvni = tl;
    });
    if (prvni && prvni.getAttribute("aria-selected") !== "true") prvni.click();
  }

  /* ---------------------------------------------------------- portréty
     Hlava sedí na každé fotce jinak, tak si správce posune fotku v
     kolečku sám a hned vidí, co se na webu ukáže. Posun se drží
     v procentech šířky kolečka, takže platí ve velkém editoru i
     v náhledu 72 px — a stejná čísla pak vykreslí PHP (StavVyrezu). */
  var PORTRETY = data.portrety || [];
  /* Co web ukazuje teď, ve chvíli otevření stránky. Tlačítko „vrátit jak
     bylo" se vrací sem; soubor site.json u některých lidí přiblížení vozí
     a prohlížeč ho nezná, takže „žádný výřez" by nebylo totéž. */
  var VYREZ_PRI_OTEVRENI = {};
  PORTRETY.forEach(function (o) {
    VYREZ_PRI_OTEVRENI[o.id] = GAT.cmsStore.normalizeVyrez(o.vyrez);
  });

  function vyrezOsoby(id) {
    return GAT.cmsStore.getVyrez(stav, id) || VYREZ_PRI_OTEVRENI[id] || { zoom: 100, x: 0, y: 0 };
  }

  function stejnyVyrez(a, b) {
    return !!a && !!b && a.zoom === b.zoom && a.x === b.x && a.y === b.y;
  }

  function promenneVyrezu(prvek, v) {
    if (!prvek) return;
    prvek.style.setProperty("--vz", (v.zoom / 100).toFixed(2));
    prvek.style.setProperty("--vx", v.x + "%");
    prvek.style.setProperty("--vy", v.y + "%");
  }

  /** Překreslí jeden řádek; `jenObraz` při tahání, ať se nepřepisuje posuvník. */
  function ukazVyrez(radek, v, jenObraz) {
    promenneVyrezu($(".vyrez-fotka", radek), v);
    promenneVyrezu($("[data-vyrez-nahled] .portret", radek), v);
    var cislo = $("[data-vyrez-cislo]", radek);
    if (cislo) cislo.textContent = v.zoom + " %";
    if (jenObraz) return;
    var id = radek.getAttribute("data-vyrez");
    var posuvnik = $("[data-vyrez-zoom]", radek);
    if (posuvnik && Number(posuvnik.value) !== v.zoom) posuvnik.value = String(v.zoom);
    var znacka = $("[data-vyrez-zmeneno]", radek);
    if (znacka) znacka.hidden = !GAT.cmsStore.getVyrez(stav, id);
    var vratit = $("[data-vyrez-vratit]", radek);
    if (vratit) vratit.disabled = stejnyVyrez(v, VYREZ_PRI_OTEVRENI[id]);
  }

  function ulozVyrez(radek, v) {
    var id = radek.getAttribute("data-vyrez");
    stav = GAT.cmsStore.setVyrez(stav, id, v);
    uloz();
    ukazVyrez(radek, vyrezOsoby(id));
  }

  function vykresliPortrety() {
    $$("[data-vyrez]", korenAdmin).forEach(function (radek) {
      ukazVyrez(radek, vyrezOsoby(radek.getAttribute("data-vyrez")));
    });
  }

  $$("[data-vyrez]", korenAdmin).forEach(function (radek) {
    var plocha = $("[data-vyrez-plocha]", radek);
    var fotka = $(".vyrez-fotka", radek);
    var posuvnik = $("[data-vyrez-zoom]", radek);
    var id = radek.getAttribute("data-vyrez");

    /* Posuvník: při tahání se jen ukazuje, uloží se po puštění. Posun se
       musí zkrátit podle nového přiblížení, jinak by u menšího zoomu
       vykoukl prázdný okraj — normalizeVyrez to udělá za nás. */
    if (posuvnik) {
      posuvnik.addEventListener("input", function () {
        var v = vyrezOsoby(id);
        ukazVyrez(radek, GAT.cmsStore.normalizeVyrez({ zoom: Number(posuvnik.value), x: v.x, y: v.y }), true);
      });
      posuvnik.addEventListener("change", function () {
        var v = vyrezOsoby(id);
        ulozVyrez(radek, { zoom: Number(posuvnik.value), x: v.x, y: v.y });
      });
    }

    var vratit = $("[data-vyrez-vratit]", radek);
    if (vratit) {
      vratit.addEventListener("click", function () {
        ulozVyrez(radek, VYREZ_PRI_OTEVRENI[id] || { zoom: 100, x: 0, y: 0 });
      });
    }

    if (!plocha || !fotka) return;

    /* Tahání fotky. Posun je v procentech šířky kolečka (fotka má box
       přesně toho kolečka), takže se počítá z offsetWidth — ne
       z getBoundingClientRect, do kterého se už počítá i přiblížení. */
    var tah = null;
    plocha.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      var v = vyrezOsoby(id);
      tah = { x: e.clientX, y: e.clientY, vyrez: v, sirka: fotka.offsetWidth || 1 };
      plocha.setPointerCapture(e.pointerId);
      plocha.classList.add("vyrez-taham");
      e.preventDefault();
    });
    plocha.addEventListener("pointermove", function (e) {
      if (!tah) return;
      ukazVyrez(radek, GAT.cmsStore.normalizeVyrez(posunuty(tah, e)), true);
    });
    function posunuty(t, e) {
      return {
        zoom: t.vyrez.zoom,
        x: t.vyrez.x + ((e.clientX - t.x) / t.sirka) * 100,
        y: t.vyrez.y + ((e.clientY - t.y) / t.sirka) * 100,
      };
    }
    plocha.addEventListener("pointerup", function (e) {
      if (!tah) return;
      var cil = posunuty(tah, e);
      tah = null;
      plocha.classList.remove("vyrez-taham");
      ulozVyrez(radek, cil);
    });
    plocha.addEventListener("pointercancel", function () {
      if (!tah) return;
      tah = null;
      plocha.classList.remove("vyrez-taham");
      ukazVyrez(radek, vyrezOsoby(id));
    });

    /* Klávesnicí: šipky po procentu, se Shiftem po pěti. Bez toho by se
       fotka dala posunout jen myší. */
    plocha.addEventListener("keydown", function (e) {
      var sx = 0;
      var sy = 0;
      if (e.key === "ArrowLeft") sx = -1;
      else if (e.key === "ArrowRight") sx = 1;
      else if (e.key === "ArrowUp") sy = -1;
      else if (e.key === "ArrowDown") sy = 1;
      else return;
      var krok = e.shiftKey ? 5 : 1;
      var v = vyrezOsoby(id);
      e.preventDefault();
      ulozVyrez(radek, { zoom: v.zoom, x: v.x + sx * krok, y: v.y + sy * krok });
    });
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
      vykresliPortrety();
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
    vykresliPortrety();
    obnovCas();
  });

  /* Až úplně na konec: do téhle chvíle musí existovat všechny proměnné,
     které vykreslovací funkce používají (jinak to padá na hledani.value). */
  var jePrihlasen = false;
  if (SERVER) {
    jePrihlasen = !!window.GAT_UZIVATEL;
    if (jePrihlasen) omezPodleRole(window.GAT_UZIVATEL.role);
  } else {
    try { jePrihlasen = sessionStorage.getItem(PRIHLASEN) === "1"; } catch (e) {}
  }
  prihlasit(jePrihlasen);
})();
