// Ukázková analytika pro nástěnku v administraci (C-009).
// Data se generují deterministicky ze semínka, aby náhled vypadal pokaždé stejně.

// ------------------------------------------------------------- náhodnost

function hashRetezce(text) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

// Lineární kongruentní generátor; vrací čísla v [0, 1).
function vytvorLcg(seed) {
  let stav = (seed >>> 0) || 1;
  return function () {
    stav = (Math.imul(stav, 1664525) + 1013904223) >>> 0;
    return stav / 4294967296;
  };
}

function celoe(v, min, max) {
  return min + Math.floor(v * (max - min + 1));
}

// ------------------------------------------------------------------ data

function formatDatum(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

export function vygenerujData(seminko, dnu) {
  const n = Math.floor(dnu);
  if (!Number.isFinite(n) || n <= 0) return [];
  const nahoda = vytvorLcg(hashRetezce(String(seminko)));
  const dnes = new Date();
  const data = [];
  for (let i = n - 1; i >= 0; i--) {
    const den = new Date(dnes.getFullYear(), dnes.getMonth(), dnes.getDate() - i);
    const vikend = den.getDay() === 0 || den.getDay() === 6;
    const zaklad = vikend ? 120 : 400;
    const navstevy = celoe(nahoda(), Math.round(zaklad * 0.7), Math.round(zaklad * 1.3));
    const uzivatele = celoe(nahoda(), Math.round(navstevy * 0.5), navstevy);
    const zobrazeni = navstevy + celoe(nahoda(), Math.round(navstevy * 0.5), Math.round(navstevy * 2));
    const poptavky = celoe(nahoda(), 0, Math.max(1, Math.round(navstevy / 100)));
    const cas = celoe(nahoda(), 60, 300);
    const opusteni = celoe(nahoda(), 15, 70);
    data.push({
      datum: formatDatum(den),
      navstevy,
      uzivatele,
      zobrazeni,
      poptavky,
      cas,
      opusteni,
    });
  }
  return data;
}

// ------------------------------------------------------------- výběr období

export function filtrujObdobi(data, dni) {
  const n = Math.floor(dni);
  if (!Number.isFinite(n) || n <= 0) return [];
  return data.slice(-n);
}

// ------------------------------------------------------------------ souhrn

export function souhrn(data) {
  let navstevy = 0, uzivatele = 0, zobrazeni = 0, poptavky = 0;
  let casVazene = 0, opusteniVazene = 0;
  for (const den of data) {
    navstevy += den.navstevy;
    uzivatele += den.uzivatele;
    zobrazeni += den.zobrazeni;
    poptavky += den.poptavky;
    casVazene += den.cas * den.navstevy;
    opusteniVazene += den.opusteni * den.navstevy;
  }
  if (navstevy === 0) {
    return { navstevy: 0, uzivatele: 0, zobrazeni: 0, poptavky: 0, cas: 0, opusteni: 0 };
  }
  return {
    navstevy,
    uzivatele,
    zobrazeni,
    poptavky,
    cas: casVazene / navstevy,
    opusteni: opusteniVazene / navstevy,
  };
}

// ------------------------------------------------------------------ změna

export function zmenaProti(aktualni, predchozi) {
  if (!predchozi) return null;
  return Math.round(((aktualni - predchozi) / predchozi) * 100);
}

// ---------------------------------------------------------------- rozdělení

export function rozdeleni(seminko, polozky) {
  if (!Array.isArray(polozky) || polozky.length === 0) return [];
  if (polozky.length === 1) return [{ nazev: polozky[0], podil: 100 }];
  const nahoda = vytvorLcg(hashRetezce(String(seminko)));
  const vahy = polozky.map(() => nahonda(nahoda));
  const soucetVah = vahy.reduce((a, b) => a + b, 0);
  const podily = vahy.map((v) => Math.floor((v / soucetVah) * 100));
  let zbytek = 100 - podily.reduce((a, b) => a + b, 0);
  // Každá položka musí mít podíl > 0; zbytek doplníme k první položce.
  for (let i = 0; i < podily.length && zbytek > 0; i++) {
    if (podily[i] === 0) {
      podily[i] = 1;
      zbytek -= 1;
    }
  }
  podily[0] += zbytek;
  return polozky.map((nazev, i) => ({ nazev, podil: podily[i] }));
}

function nahonda(nahoda) {
  return 0.2 + nahonda2(nahoda);
}

function nahonda2(nahoda) {
  return nahoda() * 0.8;
}

// ------------------------------------------------------------- formátování

export function formatCislo(n) {
  const cel = Math.round(n);
  const znamenko = cel < 0 ? "-" : "";
  const cisla = String(Math.abs(cel));
  let vysledek = "";
  for (let i = 0; i < cisla.length; i++) {
    if (i > 0 && (cisla.length - i) % 3 === 0) vysledek += " ";
    vysledek += cisla[i];
  }
  return znamenko + vysledek;
}

export function formatCas(sekundy) {
  const s = Math.round(sekundy);
  const minuty = Math.floor(s / 60);
  const zbytek = s % 60;
  return `${minuty}:${String(zbytek).padStart(2, "0")}`;
}

export function formatProcenta(n) {
  return `${Math.round(n)} %`;
}

export function formatZmena(n) {
  if (n === null || n === undefined) return "—";
  if (n > 0) return `+${n} %`;
  if (n < 0) return `\u2212${Math.abs(n)} %`;
  return "0 %";
}

// -------------------------------------------------------------------- graf

export function osaGrafu(data, klic) {
  if (!Array.isArray(data) || data.length === 0) {
    return { body: [], min: 0, max: 0 };
  }
  const hodnoty = data.map((den) => den[klic]);
  const min = Math.min(...hodnoty);
  const max = Math.max(...hodnoty);
  const body = data.map((den, i) => {
    const x = data.length === 1 ? 0 : (i / (data.length - 1)) * 100;
    const y = min === max ? 50 : ((den[klic] - min) / (max - min)) * 100;
    return { x, y };
  });
  return { body, min, max };
}
