// Galerie fotek u realizace — čistá logika (C-010).
// Fotka = { id, nazev, typ, sirka, vyska, bajty, dataUrl }.
// První fotka v poli je titulní.

export const LIMITY = {
  maxFotek: 8,
  maxBajtuGalerie: 1500000,
  maxHrana: 1600,
  povoleneTypy: ["image/jpeg", "image/png", "image/webp"],
};

// Doplní chybějící/neúplné limity z LIMITY (mělké sloučení).
function doplnLimity(limity) {
  const v =
    limity && typeof limity === "object" && !Array.isArray(limity) ? limity : {};
  return {
    maxFotek: Number.isFinite(v.maxFotek) ? v.maxFotek : LIMITY.maxFotek,
    maxBajtuGalerie: Number.isFinite(v.maxBajtuGalerie)
      ? v.maxBajtuGalerie
      : LIMITY.maxBajtuGalerie,
    maxHrana: Number.isFinite(v.maxHrana) ? v.maxHrana : LIMITY.maxHrana,
    povoleneTypy:
      Array.isArray(v.povoleneTypy) && v.povoleneTypy.length > 0
        ? v.povoleneTypy
        : LIMITY.povoleneTypy,
  };
}

function jePlatnyText(hodnota) {
  return typeof hodnota === "string" && hodnota.length > 0;
}

function jePlatneCislo(hodnota) {
  return typeof hodnota === "number" && Number.isFinite(hodnota);
}

// ---------------------------------------------------------------- normalizace

export function normalizujGalerie(cokoli) {
  if (!Array.isArray(cokoli)) return [];
  const vysledek = [];
  const videne = new Set();
  for (const z of cokoli) {
    if (z === null || typeof z !== "object" || Array.isArray(z)) continue;
    if (!jePlatnyText(z.id)) continue;
    if (!jePlatnyText(z.dataUrl) || !z.dataUrl.startsWith("data:image/")) continue;
    if (videne.has(z.id)) continue;
    videne.add(z.id);
    vysledek.push({
      id: z.id,
      nazev: jePlatnyText(z.nazev) ? z.nazev : "",
      typ: jePlatnyText(z.typ) ? z.typ : "",
      sirka: jePlatneCislo(z.sirka) ? z.sirka : 0,
      vyska: jePlatneCislo(z.vyska) ? z.vyska : 0,
      bajty: jePlatneCislo(z.bajty) ? z.bajty : 0,
      dataUrl: z.dataUrl,
    });
  }
  return vysledek;
}

// ---------------------------------------------------------------- kontrola

export function zkontrolujSoubor(soubor, limity) {
  const l = doplnLimity(limity);
  const s = soubor && typeof soubor === "object" ? soubor : {};
  if (!l.povoleneTypy.includes(s.typ)) return { ok: false, chyba: "typ" };
  if (jePlatneCislo(s.velikost) && s.velikost > 12 * 1024 * 1024) {
    return { ok: false, chyba: "velikost" };
  }
  return { ok: true, chyba: null };
}

// ---------------------------------------------------------------- rozměry

export function cilovyRozmer(sirka, vyska, maxHrana) {
  const hrana = Number.isFinite(maxHrana) ? maxHrana : LIMITY.maxHrana;
  if (!jePlatneCislo(sirka) || !jePlatneCislo(vyska) || sirka <= 0 || vyska <= 0) {
    return { sirka: 0, vyska: 0 };
  }
  const m = Math.max(sirka, vyska);
  if (m <= hrana) return { sirka: Math.round(sirka), vyska: Math.round(vyska) };
  const faktor = hrana / m;
  return {
    sirka: Math.max(1, Math.round(sirka * faktor)),
    vyska: Math.max(1, Math.round(vyska * faktor)),
  };
}

// ---------------------------------------------------------------- odhad bajtů

export function odhadniBajty(dataUrl) {
  if (typeof dataUrl !== "string") return 0;
  const m = dataUrl.match(/^data:[^,]*;base64,(.*)$/s);
  if (!m) return 0;
  const payload = m[1];
  const rovnitka = (payload.match(/=+$/) || [""])[0].length;
  return Math.floor((payload.length * 3) / 4) - rovnitka;
}

// ---------------------------------------------------------------- přidávání

export function pridejFotky(galerie, nove, limity) {
  const l = doplnLimity(limity);
  const zaklad = Array.isArray(galerie) ? galerie : [];
  const davka = Array.isArray(nove) ? nove : [];

  const vysledek = [];
  const dataUrls = new Set();
  let bajty = 0;
  const pouzitaId = new Set();
  for (const f of zaklad) {
    if (f === null || typeof f !== "object" || Array.isArray(f)) continue;
    vysledek.push({ ...f });
    if (typeof f.dataUrl === "string") dataUrls.add(f.dataUrl);
    if (jePlatnyText(f.id)) pouzitaId.add(f.id);
    if (jePlatneCislo(f.bajty)) bajty += f.bajty;
  }

  const odmitnuto = [];
  let pridano = 0;

  for (const f of davka) {
    if (f === null || typeof f !== "object" || Array.isArray(f)) {
      odmitnuto.push({ nazev: "", duvod: "duplikat" });
      continue;
    }
    const nazev = jePlatnyText(f.nazev) ? f.nazev : "";
    const fBajty = jePlatneCislo(f.bajty) ? f.bajty : 0;

    if (typeof f.dataUrl === "string" && dataUrls.has(f.dataUrl)) {
      odmitnuto.push({ nazev, duvod: "duplikat" });
      continue;
    }
    if (vysledek.length >= l.maxFotek) {
      odmitnuto.push({ nazev, duvod: "pocet" });
      continue;
    }
    if (bajty + fBajty > l.maxBajtuGalerie) {
      odmitnuto.push({ nazev, duvod: "misto" });
      continue;
    }

    let id = jePlatnyText(f.id) ? f.id : "";
    if (!id || pouzitaId.has(id)) {
      let n = 1;
      do {
        id = "f" + n;
        n += 1;
      } while (pouzitaId.has(id));
    }
    pouzitaId.add(id);
    if (typeof f.dataUrl === "string") dataUrls.add(f.dataUrl);
    bajty += fBajty;
    vysledek.push({ ...f, id });
    pridano += 1;
  }

  return { galerie: vysledek, pridano, odmitnuto };
}

// ---------------------------------------------------------------- pořadí a mazání

export function odeberFotku(galerie, id) {
  const g = Array.isArray(galerie) ? galerie : [];
  return g.filter((f) => !(f && f.id === id));
}

export function presunFotku(galerie, id, smer) {
  const g = Array.isArray(galerie) ? galerie : [];
  const i = g.findIndex((f) => f && f.id === id);
  if (i < 0 || !smer || smer === 0) return g.slice();
  const j = smer < 0 ? i - 1 : i + 1;
  if (j < 0 || j >= g.length) return g.slice();
  const kopie = g.slice();
  [kopie[i], kopie[j]] = [kopie[j], kopie[i]];
  return kopie;
}

export function nastavTitulni(galerie, id) {
  const g = Array.isArray(galerie) ? galerie : [];
  const i = g.findIndex((f) => f && f.id === id);
  if (i < 0) return g.slice();
  const kopie = g.slice();
  const [fotka] = kopie.splice(i, 1);
  kopie.unshift(fotka);
  return kopie;
}

export function titulni(galerie) {
  if (!Array.isArray(galerie) || galerie.length === 0) return null;
  const f = galerie[0];
  return f && typeof f === "object" && !Array.isArray(f) ? f : null;
}

// ---------------------------------------------------------------- souhrn

export function souhrn(galerie) {
  const g = Array.isArray(galerie) ? galerie : [];
  let bajty = 0;
  for (const f of g) {
    if (f && typeof f === "object" && jePlatneCislo(f.bajty)) bajty += f.bajty;
  }
  return { pocet: g.length, bajty };
}

// ---------------------------------------------------------------- formátování

export function formatVelikost(bajty) {
  if (!jePlatneCislo(bajty) || bajty < 0) return "0 kB";
  if (bajty < 1048576) {
    return `${Math.round(bajty / 1024)} kB`;
  }
  const mb = bajty / 1048576;
  const cel = Math.floor(mb);
  const desetiny = Math.round((mb - cel) * 10);
  const cislo = desetiny === 10 ? `${cel + 1},0` : `${cel},${desetiny}`;
  return `${cislo} MB`;
}
