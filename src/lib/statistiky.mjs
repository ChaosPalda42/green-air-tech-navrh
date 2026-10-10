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

  // Základní úroveň návštěvnosti a plynulý mírný růst (ne skok).
  const zaklad = 260 + Math.floor(nahoda() * 120); // 260–380
  const rust = 0.004 + nahoda() * 0.006; // ~0,4–1,0 % denně

  let cas = 150 + nahondaKrok(nahoda, 40); // 150–190, pak procházka
  let opusteni = 38 + nahondaKrok(nahoda, 8); // 38–46, pak procházka

  const data = [];
  for (let i = n - 1; i >= 0; i--) {
    const den = new Date(dnes.getFullYear(), dnes.getMonth(), dnes.getDate() - i);
    const vikend = den.getDay() === 0 || den.getDay() === 6;

    // Plynulá trendová hladina všedního dne.
    const hladina = zaklad * Math.pow(1 + rust, n - 1 - i);
    // Víkendový rytmus: 45–55 % všední hladiny.
    const vikendFaktor = 0.45 + nahoda() * 0.1;
    const cil = vikend ? hladina * vikendFaktor : hladina;

    // Klidné kolísání kolem hladiny (±12 %).
    const navstevy = Math.max(1, Math.round(cil * (0.88 + nahoda() * 0.24)));

    // Uživatelé 60–85 % návštěv.
    const uzivatele = Math.min(
      navstevy,
      Math.round(navstevy * (0.6 + nahoda() * 0.25))
    );

    // Zobrazení 2,0–4,0násobek návštěv.
    const zobrazeni = Math.round(navstevy * (2 + nahoda() * 2));

    // Poptávky: konverze nejvýš 1,5 % návštěv.
    const poptavky = Math.floor(nahoda() * Math.ceil(navstevy * 0.015));

    // Čas na stránce: malý krok od předchozího dne, držen v pásmu 100–260.
    cas = Math.min(260, Math.max(100, cas + nahondaKrok(nahoda, 12)));
    cas = Math.round(cas);

    // Míra okamžitého opuštění: malý krok, držená v pásmu 30–55.
    opusteni = Math.min(55, Math.max(30, opusteni + nahondaKrok(nahoda, 2.5)));
    opusteni = Math.round(opusteni);

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

// Náhodný krok v rozmezí [-amplituda, +amplituda].
function nahondaKrok(nahonda, amplituda) {
  return (nahonda() * 2 - 1) * amplituda;
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
  const nahonda = vytvorLcg(hashRetezce(String(seminko)));
  const vahy = polozky.map(() => 0.2 + nahonda() * 0.8);
  const soucetVah = vahy.reduce((a, b) => a + b, 0);
  const podily = vahy.map((v) => Math.floor((v / soucetVah) * 100));
  let zbytek = 100 - podily.reduce((a, b) => a + b, 0);
  // Každá položka musí mít podíl > 0; doplníme nuly a zbytek jde k první.
  for (let i = 0; i < podily.length && zbytek > 0; i++) {
    if (podily[i] === 0) {
      podily[i] = 1;
      zbytek -= 1;
    }
  }
  podily[0] += zbytek;
  return polozky.map((nazev, i) => ({ nazev, podil: podily[i] }));
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
