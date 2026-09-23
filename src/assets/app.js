/* Runtime webu Green Air Tech. Klasický skript (žádné ESM) — web musí fungovat i z file://.
   Logika je v GAT.* (sestaveno z src/lib/*.mjs). Tady je jen DOM. */
(function () {
  "use strict";

  var $ = function (s, k) { return (k || document).querySelector(s); };
  var $$ = function (s, k) { return Array.prototype.slice.call((k || document).querySelectorAll(s)); };
  var mene = window.matchMedia("(prefers-reduced-motion: reduce)");
  var dotykove = window.matchMedia("(hover: none)");

  /* ============================================================ navigace */
  function navigace() {
    var lista = $("#lista");
    var hamburger = $("[data-hamburger]");
    var panel = $("[data-panel]");

    if (lista) {
      var prahHlidac = function () {
        lista.classList.toggle("je-odscrollovana", window.scrollY > 8);
      };
      prahHlidac();
      window.addEventListener("scroll", prahHlidac, { passive: true });
    }

    if (hamburger && panel) {
      var prepni = function (otevrit) {
        document.body.classList.toggle("menu-otevreno", otevrit);
        hamburger.setAttribute("aria-expanded", String(otevrit));
        document.body.style.overflow = otevrit ? "hidden" : "";
      };
      hamburger.addEventListener("click", function () {
        prepni(!document.body.classList.contains("menu-otevreno"));
      });
      $$("a", panel).forEach(function (a) {
        a.addEventListener("click", function () { prepni(false); });
      });
      window.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && document.body.classList.contains("menu-otevreno")) prepni(false);
      });
    }

    var jazyky = $("[data-jazyky]");
    if (jazyky) {
      var tl = $(".jazyky-tl", jazyky);
      tl.addEventListener("click", function (e) {
        e.stopPropagation();
        var otevreno = jazyky.getAttribute("data-otevreno") === "1";
        jazyky.setAttribute("data-otevreno", otevreno ? "0" : "1");
        tl.setAttribute("aria-expanded", String(!otevreno));
      });
      document.addEventListener("click", function () {
        jazyky.setAttribute("data-otevreno", "0");
        tl.setAttribute("aria-expanded", "false");
      });
    }

    var nahoru = $("[data-nahoru]");
    if (nahoru) {
      nahoru.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: mene.matches ? "auto" : "smooth" });
      });
      var hlidac = function () {
        nahoru.setAttribute("data-viditelne", window.scrollY > 700 ? "1" : "0");
      };
      hlidac();
      window.addEventListener("scroll", hlidac, { passive: true });
    }
  }

  /* ======================================================= proudění vzduchu
     Laminární proudnice: každá částice je krátký pruh, který plyne zleva
     doprava a jemně se vlní podle sinusového pole. Kreslí se přímo přes
     CSS gradient pod plátnem, takže se každý snímek maže celé plátno. */
  function vitr(platno) {
    var ctx = platno.getContext("2d", { alpha: true });
    if (!ctx) return;

    var klid = platno.getAttribute("data-vitr") === "klid";
    var sirka = 0, vyska = 0, dpr = 1;
    var castice = [];
    var bezi = false, viditelne = true, zaklad = 0;

    function rozmer() {
      var r = platno.getBoundingClientRect();
      if (!r.width || !r.height) return false;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      sirka = r.width;
      vyska = r.height;
      platno.width = Math.round(sirka * dpr);
      platno.height = Math.round(vyska * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return true;
    }

    function pocetCastic() {
      var plocha = sirka * vyska;
      var zaklad2 = Math.round(plocha / 9000);
      var max = sirka < 640 ? 46 : sirka < 1100 ? 90 : 150;
      return Math.max(14, Math.min(klid ? Math.round(max * 0.45) : max, zaklad2));
    }

    function novaCastice(nahodneX) {
      return {
        x: nahodneX ? Math.random() * sirka : -Math.random() * 180,
        y: Math.random() * vyska,
        rychlost: 22 + Math.random() * 78,       // px za sekundu
        delka: 16 + Math.random() * 64,
        sila: 0.06 + Math.random() * 0.3,
        faze: Math.random() * Math.PI * 2,
        vlna: 4 + Math.random() * 16,
        jasna: Math.random() < 0.12,
      };
    }

    function naplnit() {
      var n = pocetCastic();
      castice = [];
      for (var i = 0; i < n; i++) castice.push(novaCastice(true));
    }

    function kresli(cas) {
      ctx.clearRect(0, 0, sirka, vyska);
      ctx.lineCap = "round";
      for (var i = 0; i < castice.length; i++) {
        var c = castice[i];
        var posun = Math.sin(cas * 0.0006 + c.faze + c.x * 0.006) * c.vlna;
        var y = c.y + posun;
        var x0 = c.x - c.delka;
        var g = ctx.createLinearGradient(x0, y, c.x, y);
        var barva = c.jasna ? "123, 209, 63" : "88, 172, 37";
        g.addColorStop(0, "rgba(" + barva + ", 0)");
        g.addColorStop(1, "rgba(" + barva + ", " + c.sila.toFixed(3) + ")");
        ctx.strokeStyle = g;
        ctx.lineWidth = c.jasna ? 1.8 : 1.1;
        ctx.beginPath();
        ctx.moveTo(x0, y);
        ctx.lineTo(c.x, y);
        ctx.stroke();
      }
    }

    // poloha kurzoru nad plátnem — proudění se za ním ohne a zrychlí
    var mysX = -9999, mysY = -9999, mysAktivni = false;
    platno.parentNode.addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      var r = platno.getBoundingClientRect();
      mysX = e.clientX - r.left;
      mysY = e.clientY - r.top;
      mysAktivni = true;
    }, { passive: true });
    platno.parentNode.addEventListener("pointerleave", function () { mysAktivni = false; }, { passive: true });

    var DOSAH = 170;

    function krok(cas) {
      if (!bezi) return;
      var dt = Math.min((cas - zaklad) / 1000, 0.05);
      zaklad = cas;
      for (var i = 0; i < castice.length; i++) {
        var c = castice[i];
        var zrychleni = 1;
        if (mysAktivni) {
          var dx = c.x - mysX;
          var dy = c.y - mysY;
          var vzdalenost = Math.sqrt(dx * dx + dy * dy);
          if (vzdalenost < DOSAH) {
            var sila = 1 - vzdalenost / DOSAH;      // 0..1
            zrychleni = 1 + sila * 2.6;              // proud se u kurzoru rozjede
            c.y += (dy / (vzdalenost || 1)) * sila * 46 * dt; // a uhne mu z cesty
            c.y = Math.max(-40, Math.min(vyska + 40, c.y));
          }
        }
        c.x += c.rychlost * zrychleni * dt;
        if (c.x - c.delka > sirka) castice[i] = novaCastice(false);
      }
      kresli(cas);
      requestAnimationFrame(krok);
    }

    function spustit() {
      if (bezi || !viditelne || document.hidden) return;
      bezi = true;
      zaklad = performance.now();
      requestAnimationFrame(krok);
    }
    function zastavit() { bezi = false; }

    if (!rozmer()) return;
    naplnit();
    kresli(performance.now()); // první snímek hned — hero nikdy nesvítí prázdnotou

    if (mene.matches) return;

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (zaznamy) {
        viditelne = zaznamy[0].isIntersecting;
        if (viditelne) spustit(); else zastavit();
      }, { threshold: 0 }).observe(platno);
    }
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) zastavit(); else spustit();
    });

    var casovac;
    window.addEventListener("resize", function () {
      clearTimeout(casovac);
      casovac = setTimeout(function () {
        if (rozmer()) naplnit();
      }, 180);
    }, { passive: true });

    spustit();
  }

  /* ======================================================= vysvětlivky zkratek */
  function zkratky() {
    var zkratkyNaStrance = $$("abbr.zkratka");
    if (!zkratkyNaStrance.length) return;

    var data = window.GAT_SLOVNIK || {};
    var bublina = null;
    var aktivni = null;

    function vytvor() {
      if (bublina) return bublina;
      bublina = document.createElement("div");
      bublina.className = "bublina";
      bublina.setAttribute("role", "tooltip");
      bublina.innerHTML = '<span class="sipka" aria-hidden="true"></span><div data-telo></div>' +
        '<button type="button" class="bublina-zavrit" data-zavrit>' + (data.zavrit || "Zavřít") + "</button>";
      document.body.appendChild(bublina);
      $("[data-zavrit]", bublina).addEventListener("click", skryj);
      return bublina;
    }

    function umisti(cil) {
      var r = cil.getBoundingClientRect();
      var b = bublina.getBoundingClientRect();
      var mezera = 12;
      var nad = r.top > b.height + mezera + 8;
      var top = nad ? r.top - b.height - mezera : r.bottom + mezera;
      var left = r.left + r.width / 2 - b.width / 2;
      left = Math.max(10, Math.min(left, window.innerWidth - b.width - 10));
      bublina.style.top = Math.round(top) + "px";
      bublina.style.left = Math.round(left) + "px";
      var sipka = $(".sipka", bublina);
      var sx = r.left + r.width / 2 - left - 6;
      sipka.style.left = Math.max(10, Math.min(sx, b.width - 22)) + "px";
      if (nad) {
        sipka.style.top = b.height - 6 + "px";
        sipka.style.transform = "rotate(225deg)";
      } else {
        sipka.style.top = "-6px";
        sipka.style.transform = "rotate(45deg)";
      }
    }

    function ukaz(cil) {
      var klic = cil.getAttribute("data-abbr");
      var t = data.terminy && data.terminy[klic];
      if (!t) return;
      vytvor();
      $("[data-telo]", bublina).innerHTML =
        "<b>" + klic + "</b><i>" + t.full + "</i>" + t.popis;
      bublina.setAttribute("data-viditelna", "1");
      aktivni = cil;
      cil.setAttribute("aria-describedby", "gat-bublina");
      bublina.id = "gat-bublina";
      umisti(cil);
    }

    function skryj() {
      if (!bublina) return;
      bublina.removeAttribute("data-viditelna");
      if (aktivni) aktivni.removeAttribute("aria-describedby");
      aktivni = null;
    }

    zkratkyNaStrance.forEach(function (el) {
      if (dotykove.matches) {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          if (aktivni === el) skryj(); else ukaz(el);
        });
      } else {
        el.addEventListener("mouseenter", function () { ukaz(el); });
        el.addEventListener("mouseleave", skryj);
      }
      el.addEventListener("focus", function () { ukaz(el); });
      el.addEventListener("blur", skryj);
    });

    document.addEventListener("click", function (e) {
      if (bublina && !bublina.contains(e.target) && e.target !== aktivni) skryj();
    });
    window.addEventListener("keydown", function (e) { if (e.key === "Escape") skryj(); });
    window.addEventListener("scroll", function () { if (aktivni) umisti(aktivni); }, { passive: true });
    window.addEventListener("resize", skryj, { passive: true });
  }

  /* ============================================================ formuláře */
  function formulare() {
    $$("[data-formular]").forEach(function (form) {
      var hlasky = window.GAT_CHYBY || {};

      function vycisti() {
        $$(".pole[data-chyba]", form).forEach(function (p) {
          p.removeAttribute("data-chyba");
          var ch = $(".chyba", p);
          if (ch) ch.remove();
        });
      }

      form.addEventListener("submit", function (e) {
        e.preventDefault();
        vycisti();
        if (form.elements.vebsajt && form.elements.vebsajt.value) return; // medová past

        var hodnoty = {
          jmeno: (form.elements.jmeno || {}).value || "",
          email: (form.elements.email || {}).value || "",
          telefon: (form.elements.telefon || {}).value || "",
          typ: (form.elements.typ || {}).value || "",
          zprava: (form.elements.zprava || {}).value || "",
          souhlas: !!(form.elements.souhlas && form.elements.souhlas.checked),
        };

        var vysledek = GAT.formValidate.validateContact(hodnoty, hlasky);
        if (!vysledek.ok) {
          var prvni = null;
          Object.keys(vysledek.errors).forEach(function (pole) {
            var vstup = form.elements[pole];
            if (!vstup) return;
            var obal = vstup.closest(".pole");
            if (!obal) return;
            obal.setAttribute("data-chyba", vysledek.errors[pole]);
            var zprava = document.createElement("span");
            zprava.className = "chyba";
            zprava.innerHTML =
              '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5h.01"/></svg>' +
              vysledek.messages[pole];
            obal.appendChild(zprava);
            if (!prvni) prvni = vstup;
          });
          if (prvni) {
            prvni.focus();
            prvni.scrollIntoView({ block: "center", behavior: mene.matches ? "auto" : "smooth" });
          }
          return;
        }

        var hotovo = document.createElement("div");
        hotovo.className = "hlaska";
        hotovo.setAttribute("role", "status");
        hotovo.innerHTML =
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.7 2.6L16 9.6"/></svg><span>' +
          (window.GAT_TEXTY ? window.GAT_TEXTY.odeslano : "Děkujeme.") + "</span>";
        form.innerHTML = "";
        form.appendChild(hotovo);
        hotovo.scrollIntoView({ block: "center", behavior: mene.matches ? "auto" : "smooth" });
      });
    });
  }

  /* ========================================================= výpis realizací */
  function vypisRealizaci() {
    var uzel = $("[data-vypis-realizaci]");
    var jsonEl = $("[data-realizace-data]");
    if (!uzel || !jsonEl) return;

    var data;
    try { data = JSON.parse(jsonEl.textContent); } catch (e) { return; }

    var stav = GAT.cmsStore.loadState(bezpecneUloziste());
    var vsechny = GAT.cmsStore.mergeRealizace(stav, data.polozky);
    var filtr = { kategorie: "vse", dotaz: "" };

    var prazdno = $("[data-prazdno]");
    var pocet = $("[data-pocet]");
    var hledani = $("[data-hledani]");

    // motivy posbírané z původního výpisu — ať se přidaná realizace nekreslí naprázdno
    var motivy = {};
    var poradi = [];
    $$(".karta-nahled[data-motiv]", uzel).forEach(function (el) {
      var cislo = el.getAttribute("data-motiv");
      var svg = el.querySelector("svg");
      if (svg && !motivy[cislo]) { motivy[cislo] = svg.outerHTML; poradi.push(cislo); }
    });

    function motiv(m) {
      if (m != null && motivy[m]) return motivy[m];
      if (!poradi.length) return "";
      var n = 0;
      var text = String(m == null ? "" : m);
      for (var i = 0; i < text.length; i++) n = (n * 31 + text.charCodeAt(i)) % 997;
      return motivy[poradi[n % poradi.length]];
    }

    function karta(r) {
      var stitky = (r.kategorie || []).slice(0, 2).map(function (k) {
        return '<span class="odznak">' + (data.kategorie[k] || k) + "</span>";
      }).join("");
      var href = r.odkaz || (data.detailSablona + "?id=" + encodeURIComponent(r.id));
      var datum = formatDatum(r.datum);
      return '<a class="karta-realizace" href="' + href + '">' +
        '<span class="karta-nahled">' + motiv(r.motiv != null ? r.motiv : r.id) + '<span class="stitky">' + stitky + "</span></span>" +
        '<span class="telo"><h3>' + uklid(r.nazev) + "</h3>" +
        '<span class="karta-meta"><span>' + uklid(r.misto || "") + "</span><span>" + datum + "</span></span>" +
        "<p>" + uklid(r.perex || "") + "</p>" +
        '<span class="odkaz-sip">' + data.texty.vice + "</span></span></a>";
    }

    function prekresli() {
      var vysledek = GAT.realizaceFilter.filterItems(vsechny, filtr);
      vysledek = GAT.realizaceFilter.sortItems(vysledek, "nejnovejsi");
      uzel.innerHTML = vysledek.map(karta).join("");
      uzel.hidden = vysledek.length === 0;
      if (prazdno) prazdno.hidden = vysledek.length !== 0;
      if (pocet) pocet.textContent = vysledek.length + " / " + vsechny.length;
    }

    $$("[data-kategorie]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        filtr.kategorie = chip.getAttribute("data-kategorie");
        $$("[data-kategorie]").forEach(function (c) {
          c.setAttribute("aria-pressed", String(c === chip));
        });
        prekresli();
      });
    });

    if (hledani) {
      var casovac;
      hledani.addEventListener("input", function () {
        clearTimeout(casovac);
        casovac = setTimeout(function () {
          filtr.dotaz = hledani.value;
          prekresli();
        }, 160);
      });
    }

    prekresli();
  }

  /* ================================================= detail přidané realizace */
  function detailZeSablony() {
    var jsonEl = $("[data-sablona-data]");
    if (!jsonEl) return;
    var data;
    try { data = JSON.parse(jsonEl.textContent); } catch (e) { return; }

    var id = new URLSearchParams(window.location.search).get("id");
    var stav = GAT.cmsStore.loadState(bezpecneUloziste());
    var polozka = null;
    var pridane = (stav.realizace && stav.realizace.added) || [];
    for (var i = 0; i < pridane.length; i++) if (pridane[i].id === id) polozka = pridane[i];

    if (!polozka) {
      var zaklad = data.zakladni.filter(function (z) { return z.id === id; })[0];
      if (zaklad) { window.location.replace(zaklad.odkaz); return; }
      $('[data-sablona="nazev"]').textContent = document.title;
      return;
    }

    var nastav = function (klic, text) {
      var el = $('[data-sablona="' + klic + '"]');
      if (el) el.textContent = text || "";
    };
    nastav("nazev", polozka.nazev);
    nastav("perex", polozka.perex);
    nastav("zadani", polozka.zadani);
    nastav("vysledek", polozka.vysledek);
    document.title = polozka.nazev + " — Green Air Tech";

    var rozsah = $('[data-sablona="rozsah"]');
    if (rozsah) {
      rozsah.innerHTML = (polozka.rozsah || []).map(function (r) {
        return '<li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.7 2.6L16 9.6"/></svg><span>' + uklid(r) + "</span></li>";
      }).join("");
    }
    var tech = $('[data-sablona="technologie"]');
    if (tech) {
      tech.innerHTML = (polozka.technologie || []).map(function (x) {
        return '<span class="odznak odznak-zeleny">' + uklid(x) + "</span>";
      }).join(" ");
    }
    var par = $('[data-sablona="parametry"]');
    if (par) {
      var radky = [
        [data.popisky.kraj, polozka.misto],
        [data.popisky.dokonceno, polozka.datum ? formatDatum(polozka.datum) : ""],
        [data.popisky.plocha, polozka.plocha],
        [data.popisky.doba, polozka.doba],
        [data.popisky.kategorie, (polozka.kategorie || []).map(function (k) { return data.kategorie[k] || k; }).join(", ")],
      ].filter(function (r) { return r[1]; });
      par.innerHTML = radky.map(function (r) {
        return "<div><dt>" + r[0] + "</dt><dd>" + uklid(r[1]) + "</dd></div>";
      }).join("");
    }
    var nahled = $('[data-sablona="nahled"]');
    if (nahled && window.GAT_MOTIV) nahled.innerHTML = window.GAT_MOTIV;
  }

  /* ================================================================ slovník */
  function slovnikHledani() {
    var vstup = $("[data-hledani-slovnik]");
    if (!vstup) return;
    var prazdno = $("[data-slovnik-prazdno]");
    vstup.addEventListener("input", function () {
      var dotaz = GAT.realizaceFilter.normalizeText(vstup.value.trim());
      var nalezeno = 0;
      $$(".slovnik-skupina").forEach(function (skupina) {
        var viditelnych = 0;
        $$("[data-zkratka]", skupina).forEach(function (karta) {
          var sedi = !dotaz || GAT.realizaceFilter.normalizeText(karta.getAttribute("data-zkratka") + " " + karta.textContent).indexOf(dotaz) !== -1;
          karta.hidden = !sedi;
          if (sedi) viditelnych++;
        });
        skupina.hidden = viditelnych === 0;
        nalezeno += viditelnych;
      });
      if (prazdno) prazdno.hidden = nalezeno !== 0;
    });
  }

  /* ========================================================== CMS náhledy */
  function cmsPrepisy() {
    var uloziste = bezpecneUloziste();
    var stav = GAT.cmsStore.loadState(uloziste);
    var lang = document.documentElement.lang || "cs";
    var prepisy = (stav.texts && stav.texts[lang]) || {};
    var klice = Object.keys(prepisy);
    if (!klice.length) return;
    klice.forEach(function (klic) {
      $$('[data-cms="' + klic.replace(/"/g, '\\"') + '"]').forEach(function (el) {
        el.innerHTML = prepisy[klic];
      });
    });
  }

  /* ================================================================ pomocné */
  /* ============================================================ pás teček
     Do každé světlé sekce vložíme vrstvu s rastrem. Leží pod obsahem
     a maska ji drží v levém pásu, takže přes celou výšku stránky vzniká
     jeden souvislý okraj — stejný jako kolem loga v hlavičce. */
  function pasTecek() {
    var vrstvy = [];

    $$(".sekce:not(.sekce-tmava)").forEach(function (sekce) {
      var vrstva = document.createElement("span");
      vrstva.className = "rastr";
      vrstva.setAttribute("aria-hidden", "true");
      vrstva.innerHTML = "<i></i>";
      sekce.insertBefore(vrstva, sekce.firstChild);
      vrstvy.push(vrstva);
    });
    if (!vrstvy.length) return;

    // Každá sekce má vlastní počátek souřadnic, takže by na sebe mřížky
    // nenavazovaly. Posuneme je tak, aby všechny sedly na jednu mřížku
    // vedenou od horního okraje dokumentu.
    function zarovnej() {
      var krok = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--tecka-krok")) || 41;
      var odsun = window.scrollY || window.pageYOffset || 0;
      for (var i = 0; i < vrstvy.length; i++) {
        var vrchol = vrstvy[i].getBoundingClientRect().top + odsun;
        var posun = -(((vrchol % krok) + krok) % krok);
        vrstvy[i].querySelector("i").style.setProperty("--posun", posun.toFixed(2) + "px");
      }
    }

    zarovnej();
    window.addEventListener("load", zarovnej);
    window.addEventListener("resize", function () {
      clearTimeout(pasTecek.casovac);
      pasTecek.casovac = setTimeout(zarovnej, 150);
    }, { passive: true });
    if ("ResizeObserver" in window) {
      new ResizeObserver(function () { zarovnej(); }).observe(document.body);
    }
  }

  /* ======================================================= zaměřovací kurzor
     Kroužek s ryskami, který se veze za myší s mírným zpožděním. Nad odkazy
     se rozevře, nad textem stáhne, na tmavých sekcích se rozsvítí zeleně. */
  function zamerovac() {
    if (mene.matches || dotykove.matches) return;
    if (!window.matchMedia("(pointer: fine)").matches) return;

    var znacka = document.createElement("div");
    znacka.className = "zamerovac";
    znacka.setAttribute("aria-hidden", "true");
    znacka.innerHTML = '<span class="stred"></span>';
    document.body.appendChild(znacka);

    var cilX = -200, cilY = -200, x = -200, y = -200;
    var bezi = false, tik = 0;
    var AKCE = 'a, button, [role="button"], summary, label.zaskrtavatko, .chip, input[type="submit"]';
    var TEXT = "p, li, h1, h2, h3, h4, dd, dt, address, span.lead, td, th, blockquote";
    var TMAVE = ".hero, .podhlavi, .sekce-tmava, .paticka, .vyzva, .karta-nahled, .karta-kontakt.zvyrazneny";

    function krok() {
      // plynulé dohánění — kroužek se veze za šipkou
      x += (cilX - x) * 0.22;
      y += (cilY - y) * 0.22;
      znacka.style.transform = "translate3d(" + x.toFixed(1) + "px," + y.toFixed(1) + "px,0)";
      if (Math.abs(cilX - x) > 0.4 || Math.abs(cilY - y) > 0.4) {
        requestAnimationFrame(krok);
      } else {
        bezi = false;
      }
    }

    document.addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      cilX = e.clientX;
      cilY = e.clientY;
      znacka.setAttribute("data-zive", "1");

      if ((tik++ & 3) === 0) {
        var pod = e.target;
        var jeAkce = pod.closest && pod.closest(AKCE);
        var jeText = !jeAkce && pod.closest && pod.closest(TEXT);
        if (jeAkce) znacka.setAttribute("data-cil", "akce");
        else if (jeText) znacka.setAttribute("data-cil", "text");
        else znacka.removeAttribute("data-cil");

        var tmavy = pod.closest && pod.closest(TMAVE);
        if (tmavy) znacka.setAttribute("data-podklad", "tmavy");
        else znacka.removeAttribute("data-podklad");
      }

      if (!bezi) { bezi = true; requestAnimationFrame(krok); }
    }, { passive: true });

    document.addEventListener("pointerleave", function () { znacka.removeAttribute("data-zive"); }, { passive: true });
    document.addEventListener("pointerdown", function () { znacka.setAttribute("data-cil", "akce"); }, { passive: true });
  }

  /* ====================================================== karty pod kurzorem
     Po povrchu karty putuje měkký proud světla podle polohy kurzoru a karta
     se o zlomek stupně nakloní — jako plech nastavený do proudu vzduchu.
     Efekt nikdy neopustí kartu, takže nekříží text. */
  function kartyPodKurzorem() {
    if (mene.matches || dotykove.matches) return;

    var VYBER = ".karta-sluzba, .karta-realizace, .karta-clanek, .karta-kontakt, .karta-clovek, .slovnik-karta";
    var aktivni = null, x = 0, y = 0, ceka = false;

    function prekresli() {
      ceka = false;
      if (!aktivni) return;
      var r = aktivni.getBoundingClientRect();
      if (!r.width || !r.height) return;
      var px = (x - r.left) / r.width;
      var py = (y - r.top) / r.height;
      aktivni.style.setProperty("--cx", (px * 100).toFixed(1) + "%");
      aktivni.style.setProperty("--cy", (py * 100).toFixed(1) + "%");
    }

    function opust(karta) {
      if (!karta) return;
      karta.removeAttribute("data-kurzor");
      karta.style.removeProperty("--cx");
      karta.style.removeProperty("--cy");
    }

    document.addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      var karta = e.target.closest ? e.target.closest(VYBER) : null;
      if (karta && karta.classList.contains("privane")) karta = null;
      if (karta !== aktivni) {
        opust(aktivni);
        aktivni = karta;
        if (aktivni) aktivni.setAttribute("data-kurzor", "1");
      }
      if (!aktivni) return;
      x = e.clientX;
      y = e.clientY;
      if (!ceka) { ceka = true; requestAnimationFrame(prekresli); }
    }, { passive: true });

    document.addEventListener("pointerleave", function () { opust(aktivni); aktivni = null; }, { passive: true });
    window.addEventListener("scroll", function () { opust(aktivni); aktivni = null; }, { passive: true });
  }

  /* ============================================== závan při příchodu na stránku */
  function zavanPriPrichodu() {
    if (mene.matches) return;
    var obal = document.createElement("div");
    obal.className = "zavan";
    obal.setAttribute("aria-hidden", "true");
    var html = "";
    for (var i = 0; i < 7; i++) {
      var top = (8 + Math.random() * 84).toFixed(1);
      var doba = (620 + Math.random() * 520).toFixed(0);
      var zpozdeni = (i * 42).toFixed(0);
      var sirka = (22 + Math.random() * 26).toFixed(0);
      html += '<i style="top:' + top + "%;width:" + sirka + "vw;--doba:" + doba + "ms;--zpozdeni:" + zpozdeni + 'ms"></i>';
    }
    obal.innerHTML = html;
    document.body.appendChild(obal);
    setTimeout(function () { obal.remove(); }, 1800);
  }

  /* ============================================== příchod obsahu při scrollu
     Nadpisy přijedou zleva k pásu teček, karty se vynoří zespodu jedna po
     druhé. Pojistka na konci zaručí, že nic nezůstane neviditelné. */
  function prichodObsahu() {
    if (mene.matches || !("IntersectionObserver" in window)) return;

    var cekajici = [];

    // poryv: tři zelené pruhy, které sekcí prolétnou ve chvíli příletu obsahu
    function vlozPoryv(sekce) {
      if (sekce.querySelector(":scope > .pruvan")) return;
      var pruvan = document.createElement("span");
      pruvan.className = "pruvan";
      pruvan.setAttribute("aria-hidden", "true");
      var html = "";
      for (var i = 0; i < 3; i++) {
        var top = (14 + i * 30 + Math.random() * 16).toFixed(1);
        var doba = (620 + Math.random() * 360).toFixed(0);
        var zpozdeni = (i * 90).toFixed(0);
        html += '<i style="top:' + top + "%;--doba:" + doba + "ms;--zpozdeni:" + zpozdeni + 'ms"></i>';
      }
      pruvan.innerHTML = html;
      sekce.appendChild(pruvan);
    }

    function spustPoryv(prvek) {
      var sekce = prvek.closest(".sekce, .vyzva");
      if (!sekce || sekce.dataset.poryvBezel === "1") return;
      sekce.dataset.poryvBezel = "1";
      vlozPoryv(sekce);
      requestAnimationFrame(function () {
        sekce.classList.add("je-zavan");
        setTimeout(function () { sekce.classList.remove("je-zavan"); }, 1600);
      });
    }

    function uklid(prvek) {
      prvek.classList.remove("privane", "privane-karta", "privane-nadpis", "je-videt");
      prvek.style.transitionDelay = "";
    }

    function odkryj(prvek) {
      if (document.hidden) {
        uklid(prvek);
      } else {
        spustPoryv(prvek);
        prvek.classList.add("je-videt");
        // až animace doběhne, třídy zmizí — jinak by jejich transform
        // kolidoval s nakloněním karty pod kurzorem
        var zpozdeni = parseFloat(prvek.style.transitionDelay) || 0;
        setTimeout(function () { uklid(prvek); }, 1200 + zpozdeni);
      }
      var i = cekajici.indexOf(prvek);
      if (i !== -1) cekajici.splice(i, 1);
      pozorovatel.unobserve(prvek);
    }

    var pozorovatel = new IntersectionObserver(function (zaznamy) {
      zaznamy.forEach(function (z) { if (z.isIntersecting) odkryj(z.target); });
    }, { rootMargin: "0px 0px -14% 0px", threshold: 0 });

    function pocetSloupcu(skupina, deti) {
      if (!deti.length) return 1;
      var prvniTop = Math.round(deti[0].getBoundingClientRect().top);
      var n = 0;
      for (var i = 0; i < deti.length; i++) {
        if (Math.abs(Math.round(deti[i].getBoundingClientRect().top) - prvniTop) > 4) break;
        n++;
      }
      return Math.max(1, n);
    }

    function priprav(prvek, trida, zpozdeni) {
      if (!prvek || prvek.classList.contains("privane")) return;
      if (prvek.getBoundingClientRect().top < window.innerHeight * 0.86) return;
      prvek.classList.add("privane");
      if (trida) prvek.classList.add(trida);
      prvek.style.transitionDelay = zpozdeni + "ms";
      cekajici.push(prvek);
      pozorovatel.observe(prvek);
    }

    $$(".sekce, .vyzva").forEach(function (sekce) {
      priprav($(".hlavicka-sekce", sekce), "privane-nadpis", 0);

      // mřížky a postupy nastupují po položkách
      var skupiny = $$(".mrizka, .postup, .slovnik-polozky", sekce);
      if (skupiny.length) {
        skupiny.forEach(function (skupina) {
          var deti = Array.prototype.slice.call(skupina.children);
          var sloupcu = pocetSloupcu(skupina, deti);
          deti.forEach(function (dite, i) {
            var sloupec = i % sloupcu;
            var rada = Math.floor(i / sloupcu);
            priprav(dite, "privane-karta", sloupec * 115 + Math.min(rada, 3) * 60);
          });
        });
      }

      // ostatní přímé bloky sekce (text, formulář, obrázek)
      var obal = $(".obal", sekce);
      if (obal) {
        Array.prototype.slice.call(obal.children).forEach(function (dite, i) {
          if (dite.classList.contains("hlavicka-sekce")) return;
          if ($(".mrizka, .postup, .slovnik-polozky", dite) || dite.classList.contains("mrizka")) return;
          priprav(dite, "", i * 60);
        });
      }
    });

    priprav($(".hero-pruh"), "", 0);

    function dorovnej() {
      cekajici.slice().forEach(function (prvek) {
        if (prvek.getBoundingClientRect().top < window.innerHeight * 0.86) odkryj(prvek);
      });
    }
    window.addEventListener("scroll", dorovnej, { passive: true });
    window.addEventListener("resize", dorovnej, { passive: true });
    document.addEventListener("visibilitychange", dorovnej);
    window.addEventListener("load", dorovnej);
    setTimeout(dorovnej, 1500);
  }

  /* ========================================================== počítadla v hero */
  function pocitadla() {
    if (mene.matches || !("IntersectionObserver" in window)) return;
    var cisla = $$(".hero-pruh b").filter(function (el) {
      return /^\d+\s*[^\d\/]*$/.test(el.textContent.trim());
    });
    if (!cisla.length) return;

    var pozorovatel = new IntersectionObserver(function (zaznamy) {
      zaznamy.forEach(function (z) {
        if (!z.isIntersecting) return;
        var el = z.target;
        pozorovatel.unobserve(el);
        var text = el.textContent.trim();
        var shoda = text.match(/^(\d+)(.*)$/);
        if (!shoda) return;
        var cil = parseInt(shoda[1], 10);
        var pripona = shoda[2];
        var doba = 900;

        function dokonci() { el.textContent = cil + pripona; }
        if (document.hidden) { dokonci(); return; }

        var zacatek = performance.now();
        var hotovo = false;
        (function tik(cas) {
          if (hotovo) return;
          if (document.hidden) { hotovo = true; dokonci(); return; }
          var podil = Math.min(1, (cas - zacatek) / doba);
          var krivka = 1 - Math.pow(1 - podil, 3);
          el.textContent = Math.round(cil * krivka) + pripona;
          if (podil < 1) requestAnimationFrame(tik);
          else hotovo = true;
        })(zacatek);
        // pojistka: rAF se ve skryté záložce zastaví, časovač ne
        setTimeout(function () { if (!hotovo) { hotovo = true; dokonci(); } }, doba + 600);
      });
    }, { threshold: 0.4 });

    cisla.forEach(function (el) { pozorovatel.observe(el); });
  }

  function formatDatum(iso) {
    if (!iso) return "";
    try {
      return new Date(iso + "T12:00:00Z").toLocaleDateString(document.documentElement.lang || "cs", {
        month: "long", year: "numeric", timeZone: "UTC",
      });
    } catch (e) { return iso; }
  }

  function uklid(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function bezpecneUloziste() {
    try {
      window.localStorage.setItem("gat-test", "1");
      window.localStorage.removeItem("gat-test");
      return window.localStorage;
    } catch (e) {
      var pamet = {};
      return {
        getItem: function (k) { return Object.prototype.hasOwnProperty.call(pamet, k) ? pamet[k] : null; },
        setItem: function (k, v) { pamet[k] = String(v); },
        removeItem: function (k) { delete pamet[k]; },
      };
    }
  }
  window.GAT_ULOZISTE = bezpecneUloziste;

  /* ================================================================== start */
  function start() {
    navigace();
    $$("[data-vitr]").forEach(vitr);
    cmsPrepisy();
    zkratky();
    formulare();
    vypisRealizaci();
    detailZeSablony();
    slovnikHledani();
    pasTecek();
    kartyPodKurzorem();
    zamerovac();
    zavanPriPrichodu();
    prichodObsahu();
    pocitadla();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
