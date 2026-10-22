/* Sestaveno z src/lib/*.mjs – needitovat ručně. */
var GAT = window.GAT || {};
window.GAT = GAT;
GAT.cmsStore = (function () {
const STORAGE_KEY = "gat-cms-v1";

function emptyState() {
  return { texts: {}, realizace: { added: [], edited: {}, removed: [] }, updatedAt: null };
}

function _deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function _ensureState(state) {
  const s = _deepClone(state);
  if (!s.texts) s.texts = {};
  if (!s.realizace) s.realizace = { added: [], edited: {}, removed: [] };
  if (s.realizace.added === undefined) s.realizace.added = [];
  if (s.realizace.edited === undefined) s.realizace.edited = {};
  if (s.realizace.removed === undefined) s.realizace.removed = [];
  return s;
}

function loadState(storage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (raw === null || raw === undefined) return emptyState();
    const parsed = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) return emptyState();
    return _ensureState(parsed);
  } catch {
    return emptyState();
  }
}

function saveState(storage, state) {
  const s = _deepClone(state);
  s.updatedAt = new Date().toISOString();
  storage.setItem(STORAGE_KEY, JSON.stringify(s));
  return s;
}

function resetState(storage) {
  storage.removeItem(STORAGE_KEY);
}

function setText(state, lang, key, value) {
  const s = _deepClone(state);
  if (!s.texts[lang]) s.texts[lang] = {};
  if (typeof value === "string" && value.trim() === "") {
    delete s.texts[lang][key];
    // Keep the language object even if empty
  } else {
    s.texts[lang][key] = value;
  }
  return s;
}

function getText(state, lang, key) {
  const texts = state.texts && state.texts[lang];
  if (texts === undefined || texts === null) return null;
  return texts[key] !== undefined ? texts[key] : null;
}

function mergeTexts(state, lang, baseFlatDict) {
  const result = _deepClone(baseFlatDict);
  const overrides = state.texts && state.texts[lang];
  if (overrides) {
    for (const k of Object.keys(overrides)) {
      result[k] = overrides[k];
    }
  }
  return result;
}

function slugify(text) {
  let s = text.toLowerCase();
  s = s.normalize("NFD").replace(/[\u0300-\u036F]/g, "");
  s = s.replace(/[^a-z0-9]+/g, "-");
  s = s.replace(/^-+|-+$/g, "");
  return s;
}

function upsertRealizace(state, item, baseList) {
  if (baseList === undefined) baseList = [];
  const s = _deepClone(state);
  const baseIds = new Set(baseList.map(b => b.id));
  const addedIds = new Set(s.realizace.added.map(a => a.id));
  const editedIds = new Set(Object.keys(s.realizace.edited));

  let id = item.id;
  if (!id) {
    id = slugify(item.nazev);
    let suffix = 2;
    while (baseIds.has(id) || addedIds.has(id) || editedIds.has(id)) {
      id = slugify(item.nazev) + "-" + suffix;
      suffix++;
    }
  }

  if (baseIds.has(id)) {
    // Merge into edited
    const existing = s.realizace.edited[id] || {};
    s.realizace.edited[id] = Object.assign({}, existing, item);
    // Ensure id is not in removed
    s.realizace.removed = s.realizace.removed.filter(r => r !== id);
  } else {
    // Check if id already in added
    const idx = s.realizace.added.findIndex(a => a.id === id);
    if (idx !== -1) {
      s.realizace.added[idx] = Object.assign({}, s.realizace.added[idx], item);
    } else {
      const newItem = _deepClone(item);
      if (!item.id) {
        newItem.id = id;
      }
      s.realizace.added.push(newItem);
    }
  }

  return s;
}

function removeRealizace(state, id) {
  const s = _deepClone(state);
  const idx = s.realizace.added.findIndex(a => a.id === id);
  if (idx !== -1) {
    // Remove from added only, do NOT add to removed
    s.realizace.added.splice(idx, 1);
  } else {
    // Add to removed (no duplicates)
    if (!s.realizace.removed.includes(id)) {
      s.realizace.removed.push(id);
    }
    // Remove from edited if present
    delete s.realizace.edited[id];
  }
  return s;
}

function mergeRealizace(state, baseList) {
  const removedSet = new Set(state.realizace.removed);
  const result = [];

  // Process baseList
  for (const item of baseList) {
    if (removedSet.has(item.id)) continue;
    const copy = Object.assign({}, item);
    if (state.realizace.edited[item.id]) {
      Object.assign(copy, state.realizace.edited[item.id]);
    }
    copy._source = "base";
    result.push(copy);
  }

  // Add items from added
  for (const item of state.realizace.added) {
    const copy = Object.assign({}, item);
    copy._source = "added";
    result.push(copy);
  }

  // Sort by datum descending; added items come before base items with same date;
  // items without datum are oldest
  result.sort((a, b) => {
    const da = a.datum || "";
    const db = b.datum || "";
    if (da === "" && db === "") {
      // Both without datum: added before base
      return a._source === "added" ? -1 : 1;
    }
    if (da === "") return 1; // a is oldest
    if (db === "") return -1; // b is oldest
    if (da > db) return -1;
    if (da < db) return 1;
    // Same date: added before base
    if (a._source === "added" && b._source !== "added") return -1;
    if (a._source !== "added" && b._source === "added") return 1;
    return 0;
  });

  // Remove internal _source field
  return result.map(r => {
    const { _source, ...rest } = r;
    return rest;
  });
}

function exportJson(state) {
  return JSON.stringify(state, null, 2);
}

function importJson(state, text) {
  try {
    const parsed = JSON.parse(text);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { ok: false, error: "Invalid JSON structure" };
    }
    const merged = _ensureState(parsed);
    return { ok: true, state: merged };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

return { STORAGE_KEY, emptyState, loadState, saveState, resetState, setText, getText, mergeTexts, slugify, upsertRealizace, removeRealizace, mergeRealizace, exportJson, importJson };
})();

GAT.formValidate = (function () {
// C-004 — validace kontaktního formuláře (co nejkratší, po schůzce 9. 10. 2026).

function isEmail(value) {
  if (typeof value !== "string") return false;
  const v = value;
  if (v === "" || v.includes(" ")) return false;
  if (v.split("@").length !== 2) return false;
  const [local, domain] = v.split("@");
  if (local === "") return false;
  const parts = domain.split(".");
  if (parts.length < 2) return false;
  if (parts.some((p) => p === "")) return false;
  if (!/^[A-Za-z]{2,}$/.test(parts[parts.length - 1])) return false;
  return true;
}

function normalizePhone(value) {
  if (typeof value !== "string") return "";
  let v = value.replace(/[\s()\-]/g, "");
  if (v.startsWith("00420") && v.length === 14) {
    v = "+420" + v.slice(5);
  } else if (v.startsWith("420") && v.length === 12) {
    v = "+420" + v.slice(3);
  } else if (/^\d{9}$/.test(v)) {
    v = "+420" + v;
  }
  return v;
}

function isPhoneCz(value) {
  if (typeof value !== "string" || value === "") return false;
  const v = normalizePhone(value);
  if (!/^\+420\d{9}$/.test(v)) return false;
  return "672359".includes(v[4]);
}

function validateContact(values, messages = {}) {
  const v = values || {};
  const errors = {};

  if (typeof v.typ !== "string" || v.typ.trim() === "") {
    errors.typ = "required";
  }
  if (typeof v.jmeno !== "string" || v.jmeno.trim() === "") {
    errors.jmeno = "required";
  }

  const email = typeof v.email === "string" ? v.email : "";
  const telefon = typeof v.telefon === "string" ? v.telefon : "";

  if (email !== "" && !isEmail(email)) {
    errors.email = "email";
  }
  if (telefon !== "" && !isPhoneCz(telefon)) {
    errors.telefon = "telefon";
  }
  if (email.trim() === "" && telefon.trim() === "") {
    errors.kontakt = "kontakt";
  }

  const zprava = typeof v.zprava === "string" ? v.zprava : "";
  if (zprava.trim() !== "" && zprava.trim().length < 10) {
    errors.zprava = "zprava-kratka";
  }

  if (v.souhlas !== true) {
    errors.souhlas = "souhlas";
  }

  const outMessages = {};
  for (const key of Object.keys(errors)) {
    const code = errors[key];
    outMessages[key] =
      messages[key] !== undefined ? messages[key] : messages[code] !== undefined ? messages[code] : code;
  }

  return { ok: Object.keys(errors).length === 0, errors, messages: outMessages };
}

return { isEmail, normalizePhone, isPhoneCz, validateContact };
})();

GAT.fotky = (function () {
// Galerie fotek u realizace — čistá logika (C-010).
// Fotka = { id, nazev, typ, sirka, vyska, bajty, dataUrl }.
// První fotka v poli je titulní.

const LIMITY = {
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

function normalizujGalerie(cokoli) {
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

function zkontrolujSoubor(soubor, limity) {
  const l = doplnLimity(limity);
  const s = soubor && typeof soubor === "object" ? soubor : {};
  if (!l.povoleneTypy.includes(s.typ)) return { ok: false, chyba: "typ" };
  if (!jePlatneCislo(s.velikost) || s.velikost <= 0 || s.velikost > 12 * 1024 * 1024) {
    return { ok: false, chyba: "velikost" };
  }
  return { ok: true, chyba: null };
}

// ---------------------------------------------------------------- rozměry

function cilovyRozmer(sirka, vyska, maxHrana) {
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

function odhadniBajty(dataUrl) {
  if (typeof dataUrl !== "string") return 0;
  const m = dataUrl.match(/^data:[^,]*;base64,(.*)$/s);
  if (!m) return 0;
  const payload = m[1];
  const rovnitka = (payload.match(/=+$/) || [""])[0].length;
  return Math.floor((payload.length * 3) / 4) - rovnitka;
}

// ---------------------------------------------------------------- přidávání

function pridejFotky(galerie, nove, limity) {
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
    const nazev =
      f && typeof f === "object" && !Array.isArray(f) && jePlatnyText(f.nazev)
        ? f.nazev
        : "";
    if (
      f === null ||
      typeof f !== "object" ||
      Array.isArray(f) ||
      !jePlatnyText(f.dataUrl) ||
      !f.dataUrl.startsWith("data:image/")
    ) {
      odmitnuto.push({ nazev, duvod: "neplatny" });
      continue;
    }
    const fBajty = jePlatneCislo(f.bajty) ? f.bajty : 0;

    if (dataUrls.has(f.dataUrl)) {
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

function odeberFotku(galerie, id) {
  const g = Array.isArray(galerie) ? galerie : [];
  return g.filter((f) => !(f && f.id === id));
}

function presunFotku(galerie, id, smer) {
  const g = Array.isArray(galerie) ? galerie : [];
  const i = g.findIndex((f) => f && f.id === id);
  if (i < 0 || !smer || smer === 0) return g.slice();
  const j = smer < 0 ? i - 1 : i + 1;
  if (j < 0 || j >= g.length) return g.slice();
  const kopie = g.slice();
  [kopie[i], kopie[j]] = [kopie[j], kopie[i]];
  return kopie;
}

function nastavTitulni(galerie, id) {
  const g = Array.isArray(galerie) ? galerie : [];
  const i = g.findIndex((f) => f && f.id === id);
  if (i < 0) return g.slice();
  const kopie = g.slice();
  const [fotka] = kopie.splice(i, 1);
  kopie.unshift(fotka);
  return kopie;
}

function titulni(galerie) {
  if (!Array.isArray(galerie) || galerie.length === 0) return null;
  const f = galerie[0];
  return f && typeof f === "object" && !Array.isArray(f) ? f : null;
}

// ---------------------------------------------------------------- souhrn

function souhrn(galerie) {
  const g = Array.isArray(galerie) ? galerie : [];
  let bajty = 0;
  for (const f of g) {
    if (f && typeof f === "object" && jePlatneCislo(f.bajty)) bajty += f.bajty;
  }
  return { pocet: g.length, bajty };
}

// ---------------------------------------------------------------- formátování

function formatVelikost(bajty) {
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

return { LIMITY, normalizujGalerie, zkontrolujSoubor, cilovyRozmer, odhadniBajty, pridejFotky, odeberFotku, presunFotku, nastavTitulni, titulni, souhrn, formatVelikost };
})();

GAT.glossary = (function () {
/**
 * C-001: Vysvětlivky zkratek – anotace textu a řazení slovníku
 *
 * Termín = { abbr: string, full: string, popis?: string }
 */

/* ── helpers ─────────────────────────────────────────────────────── */

/**
 * Test whether a character is a word-continuation character.
 * Letters (incl. Czech diacritics), digits, underscore, hyphen.
 */
function _isWordChar(ch) {
  // Check if it's a letter (any Unicode letter), digit, underscore, or hyphen
  // We use a broad approach: check against a comprehensive string of known letters
  // plus basic ASCII letters
  const czechLetters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáàâäãåāăąěèéêëēęíìîïīįñòóôöõōőřùúûüůūűýÿźçşđňÁÀÂÄÃÅĀĂĄĚÈÉÊËĒĘÍÌÎÏĪĮÑÒÓÔÖÕŌŐŘÙÚÛÜŮŪŰÝŸŹÇŞĐŇ';
  return czechLetters.includes(ch) || /\d/.test(ch) || ch === '_' || ch === '-';
}

/* ── annotate ────────────────────────────────────────────────────── */

/**
 * Wrap occurrences of abbreviations in HTML text content.
 *
 * @param {string} html
 * @param {Array<{abbr:string, full:string, popis?:string}>} terms
 * @param {{once?: boolean}} [options]
 * @returns {string}
 */
function annotate(html, terms, options = {}) {
  if (!html) return html === undefined ? '' : html;
  if (!terms || terms.length === 0) return html;

  const once = options.once === true;

  // Sort terms by abbr length descending so longer matches win
  const sorted = terms.slice().sort((a, b) => b.abbr.length - a.abbr.length);

  // Track which abbreviations have already been wrapped (for once mode)
  const used = new Set();

  // We walk the HTML string character by character, toggling between
  // "inside tag" and "text" states.
  let result = '';
  let i = 0;
  const len = html.length;

  while (i < len) {
    // ── state: inside a tag ──────────────────────────────────────
    if (html[i] === '<') {
      // Check if this is an existing <abbr ...> tag
      const rest = html.slice(i);
      const abbrMatch = rest.match(/^<abbr[\s>]/i);
      if (abbrMatch) {
        // Find the closing </abbr> tag (case-insensitive)
        const closeTag = rest.match(/<\/abbr>/i);
        if (closeTag) {
          // Skip the entire existing abbr element
          const endPos = i + closeTag.index + closeTag[0].length;
          result += html.slice(i, endPos);
          i = endPos;
          continue;
        }
      }

      // Regular tag: find the closing '>'
      let j = i + 1;
      while (j < len && html[j] !== '>') j++;
      // Copy the whole tag verbatim
      result += html.slice(i, j + 1);
      i = j + 1;
      continue;
    }

    // ── state: text ──────────────────────────────────────────────
    // Try to match any abbreviation at position i
    let bestTerm = null;
    let bestLen = 0;

    for (const t of sorted) {
      const abbr = t.abbr;
      const alen = abbr.length;
      if (alen <= bestLen) break; // already sorted descending, but be safe

      // Check if the text at i matches the abbreviation
      if (html.slice(i, i + alen) === abbr) {
        // Check word boundary before
        const beforeOk = i === 0 || !_isWordChar(html[i - 1]);
        // Check word boundary after
        const afterPos = i + alen;
        const afterOk = afterPos >= len || !_isWordChar(html[afterPos]);

        if (beforeOk && afterOk) {
          bestTerm = t;
          bestLen = alen;
        }
      }
    }

    if (bestTerm) {
      // In once mode, skip if already used
      if (once && used.has(bestTerm.abbr)) {
        result += html[i];
        i++;
        continue;
      }

      used.add(bestTerm.abbr);

      // Wrap the abbreviation
      result += '<abbr class="zkratka" tabindex="0" data-abbr="' +
        bestTerm.abbr + '">' + bestTerm.abbr + '</abbr>';
      i += bestLen;
      continue;
    }

    // No match — copy character
    result += html[i];
    i++;
  }

  return result;
}

/* ── findTerm ────────────────────────────────────────────────────── */

/**
 * Find a term by abbreviation (case-insensitive).
 *
 * @param {Array<{abbr:string, full:string, popis?:string}>} terms
 * @param {string} abbr
 * @returns {{abbr:string, full:string, popis?:string}|null}
 */
function findTerm(terms, abbr) {
  const lower = abbr.toLowerCase();
  for (const t of terms) {
    if (t.abbr.toLowerCase() === lower) return t;
  }
  return null;
}

/* ── sortTerms ───────────────────────────────────────────────────── */

/**
 * Return a new array sorted by abbr using Czech locale.
 *
 * @param {Array<{abbr:string, full:string, popis?:string}>} terms
 * @returns {Array<{abbr:string, full:string, popis?:string}>}
 */
function sortTerms(terms) {
  return terms.slice().sort((a, b) =>
    a.abbr.localeCompare(b.abbr, 'cs')
  );
}

/* ── groupTerms ──────────────────────────────────────────────────── */

/**
 * Group sorted terms by the uppercase first letter of their abbr.
 *
 * @param {Array<{abbr:string, full:string, popis?:string}>} terms
 * @returns {{letter:string, items:Array<{abbr:string, full:string, popis?:string}>}[]}
 */
function groupTerms(terms) {
  const sorted = sortTerms(terms);
  const groups = [];
  let currentLetter = '';
  let currentItems = [];

  for (const t of sorted) {
    const letter = t.abbr.charAt(0).toUpperCase();
    if (letter !== currentLetter) {
      if (currentItems.length > 0) {
        groups.push({ letter: currentLetter, items: currentItems });
      }
      currentLetter = letter;
      currentItems = [t];
    } else {
      currentItems.push(t);
    }
  }

  if (currentItems.length > 0) {
    groups.push({ letter: currentLetter, items: currentItems });
  }

  return groups;
}

return { annotate, findTerm, sortTerms, groupTerms };
})();

GAT.i18n = (function () {
/**
 * C-002: Slovníky překladů – tečkové klíče, záskok, zplošťování
 */

/**
 * Resolve a dotted path in a nested object.
 * Returns the value at the path, or null if any intermediate key is missing
 * or not an object (except the final value which can be anything).
 */
function get(dict, path) {
  if (dict == null || typeof dict !== 'object' || Array.isArray(dict)) return null;
  const parts = path.split('.');
  let current = dict;
  for (let i = 0; i < parts.length; i++) {
    const key = parts[i];
    if (current == null || typeof current !== 'object' || Array.isArray(current)) return null;
    if (!(key in current)) return null;
    current = current[key];
  }
  return current;
}

/**
 * Translate: look up `path` in `dict`, fall back to `fallbackDict`, then to `path` itself.
 * Substitute {key} placeholders from `vars`.
 */
function t(dict, path, vars = {}, fallbackDict = null) {
  let value = get(dict, path);
  if (value != null && typeof value === 'string' && value.trim() !== '') {
    // use it
  } else if (fallbackDict != null) {
    value = get(fallbackDict, path);
    if (value != null && typeof value === 'string' && value.trim() !== '') {
      // use it
    } else {
      value = null;
    }
  } else {
    value = null;
  }

  if (value == null || typeof value !== 'string') {
    value = path;
  }

  // Substitute {key} placeholders
  return value.replace(/\{([^}]+)\}/g, (_match, key) => {
    if (key in vars) return String(vars[key]);
    return _match;
  });
}

/**
 * Flatten a nested object into dot-notation keys.
 * Arrays are indexed by number. Only leaf values appear in the result.
 */
function flatten(obj, prefix = '') {
  const result = {};
  _flatten(obj, prefix, result);
  return result;
}

function _flatten(obj, prefix, result) {
  if (obj == null || typeof obj !== 'object') return;

  if (Array.isArray(obj)) {
    for (let i = 0; i < obj.length; i++) {
      const key = prefix ? prefix + '.' + i : String(i);
      const val = obj[i];
      if (val != null && typeof val === 'object' && !Array.isArray(val)) {
        _flatten(val, key, result);
      } else if (val != null && typeof val === 'object' && Array.isArray(val)) {
        _flatten(val, key, result);
      } else {
        result[key] = val;
      }
    }
  } else {
    const keys = Object.keys(obj);
    for (const key of keys) {
      const fullKey = prefix ? prefix + '.' + key : key;
      const val = obj[key];
      if (val != null && typeof val === 'object' && !Array.isArray(val)) {
        _flatten(val, fullKey, result);
      } else if (val != null && typeof val === 'object' && Array.isArray(val)) {
        _flatten(val, fullKey, result);
      } else {
        result[fullKey] = val;
      }
    }
  }
}

/**
 * Unflatten a dot-notation map back into a nested object.
 * Segments that are non-negative integers create arrays.
 */
function unflatten(map) {
  const root = {};
  for (const key of Object.keys(map)) {
    const parts = key.split('.');
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const isNum = /^\d+$/.test(part);

      if (isLast) {
        current[part] = map[key];
      } else {
        const nextPart = parts[i + 1];
        const nextIsNum = /^\d+$/.test(nextPart);

        if (isNum) {
          // Ensure array exists
          if (!Array.isArray(current)) {
            // Convert object to array if needed
            const arr = [];
            for (const k of Object.keys(current)) {
              const nk = Number(k);
              if (Number.isInteger(nk) && nk >= 0) {
                arr[nk] = current[k];
              } else {
                arr[k] = current[k];
              }
            }
            current = arr;
          }
          const idx = Number(part);
          if (current[idx] === undefined) {
            // Decide: array or object for next level
            if (nextIsNum) {
              current[idx] = [];
            } else {
              current[idx] = {};
            }
          }
          current = current[idx];
        } else {
          if (current[part] === undefined) {
            if (nextIsNum) {
              current[part] = [];
            } else {
              current[part] = {};
            }
          }
          current = current[part];
        }
      }
    }
  }
  return root;
}

/**
 * Find keys present in `reference` (with non-empty trimmed string values)
 * but missing or empty in `dict`.
 */
function missingKeys(reference, dict) {
  const flatRef = flatten(reference);
  const result = [];
  for (const key of Object.keys(flatRef)) {
    const refVal = flatRef[key];
    // Only report if reference has a non-empty trimmed string
    if (typeof refVal === 'string' && refVal.trim() !== '') {
      const dictVal = get(dict, key);
      if (dictVal == null || (typeof dictVal === 'string' && dictVal.trim() === '')) {
        result.push(key);
      }
    }
  }
  return result;
}

return { get, t, flatten, unflatten, missingKeys };
})();

GAT.realizaceFilter = (function () {
/**
 * C-005: Filtrování, řazení a stránkování referencí
 * Čistý JavaScript — žádné importy, žádné externí závislosti.
 */

/**
 * normalizeText(value) → string
 * Malá písmena, bez diakritiky (odstraní kombinující znaky U+0300–U+036F).
 */
function normalizeText(value) {
  return String(value)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * filterItems(items, { kategorie, dotaz, rok } = {}) → nové pole
 * Filtry se kombinují logickým A. Vstup se nemutuje.
 */
function filterItems(items, { kategorie, dotaz, rok } = {}) {
  const result = [];

  for (const item of items) {
    // --- kategorie ---
    if (kategorie && kategorie !== "vse") {
      if (!item.kategorie || !item.kategorie.includes(kategorie)) {
        continue;
      }
    }

    // --- rok ---
    if (rok !== undefined && rok !== null && rok !== "") {
      const datumStr = String(item.datum ?? "");
      if (!datumStr.startsWith(String(rok))) {
        continue;
      }
    }

    // --- dotaz ---
    if (dotaz && dotaz.trim() !== "") {
      const words = dotaz.trim().split(/\s+/);
      const combined = [
        item.nazev,
        item.misto,
        item.perex,
        ...(item.kategorie || []),
      ]
        .filter((v) => v != null)
        .join(" ");
      const combinedNorm = normalizeText(combined);

      let allMatch = true;
      for (const word of words) {
        if (!combinedNorm.includes(normalizeText(word))) {
          allMatch = false;
          break;
        }
      }
      if (!allMatch) {
        continue;
      }
    }

    result.push(item);
  }

  return result;
}

/**
 * collectKategorie(items) → [{ id, count }]
 * Řazení: count sestupně, při shodě id vzestupně (localeCompare "cs").
 */
function collectKategorie(items) {
  const counts = new Map();

  for (const item of items) {
    const cats = item.kategorie || [];
    for (const cat of cats) {
      counts.set(cat, (counts.get(cat) || 0) + 1);
    }
  }

  const result = [];
  for (const [id, count] of counts) {
    result.push({ id, count });
  }

  result.sort((a, b) => {
    if (b.count !== a.count) return b.count - a.count;
    return a.id.localeCompare(b.id, "cs");
  });

  return result;
}

/**
 * collectRoky(items) → pole čísel
 * Unikátní roky z datum, sestupně. Položky bez datum se přeskočí.
 */
function collectRoky(items) {
  const rokSet = new Set();

  for (const item of items) {
    if (item.datum == null) continue;
    const year = Number(String(item.datum).slice(0, 4));
    if (!isNaN(year)) {
      rokSet.add(year);
    }
  }

  return Array.from(rokSet).sort((a, b) => b - a);
}

/**
 * sortItems(items, mode) → nové pole (vstup se nemutuje)
 * "nejnovejsi" (výchozí): datum sestupně
 * "nejstarsi": datum vzestupně
 * "nazev": nazev localeCompare "cs"
 */
function sortItems(items, mode) {
  const sorted = items.slice();

  if (mode === "nejstarsi") {
    sorted.sort((a, b) => {
      if (a.datum == null) return 1;
      if (b.datum == null) return -1;
      return a.datum < b.datum ? -1 : a.datum > b.datum ? 1 : 0;
    });
  } else if (mode === "nazev") {
    sorted.sort((a, b) => a.nazev.localeCompare(b.nazev, "cs"));
  } else {
    // "nejnovejsi" nebo neznámý mode → datum sestupně
    sorted.sort((a, b) => {
      if (a.datum == null) return 1;
      if (b.datum == null) return -1;
      return a.datum > b.datum ? -1 : a.datum < b.datum ? 1 : 0;
    });
  }

  return sorted;
}

/**
 * paginate(items, page, perPage) → { items, page, pages, total }
 */
function paginate(items, page, perPage) {
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / perPage));
  const clampedPage = Math.max(1, Math.min(page, pages));
  const start = (clampedPage - 1) * perPage;
  const end = start + perPage;

  return {
    items: items.slice(start, end),
    page: clampedPage,
    pages,
    total,
  };
}

return { normalizeText, filterItems, collectKategorie, collectRoky, sortItems, paginate };
})();

GAT.statistiky = (function () {
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

function vygenerujData(seminko, dnu) {
  const n = Math.floor(dnu);
  if (!Number.isFinite(n) || n <= 0) return [];
  const nahoda = vytvorLcg(hashRetezce(String(seminko)));
  const dnes = new Date();

  // Základní úroveň návštěvnosti a plynulý mírný růst (ne skok).
  const zaklad = 260 + Math.floor(nahoda() * 120); // 260–380
  const rust = 0.004 + nahoda() * 0.006; // ~0,4–1,0 % denně

  let cas = 150 + nahodaKrok(nahoda, 40); // 150–190, pak procházka
  let opusteni = 38 + nahodaKrok(nahoda, 8); // 38–46, pak procházka

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
    cas = Math.min(260, Math.max(100, cas + nahodaKrok(nahoda, 12)));
    cas = Math.round(cas);

    // Míra okamžitého opuštění: malý krok, držená v pásmu 30–55.
    opusteni = Math.min(55, Math.max(30, opusteni + nahodaKrok(nahoda, 2.5)));
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
function nahodaKrok(nahoda, amplituda) {
  return (nahoda() * 2 - 1) * amplituda;
}

// ------------------------------------------------------------- výběr období

function filtrujObdobi(data, dni) {
  const n = Math.floor(dni);
  if (!Number.isFinite(n) || n <= 0) return [];
  return data.slice(-n);
}

// ------------------------------------------------------------------ souhrn

function souhrn(data) {
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

function zmenaProti(aktualni, predchozi) {
  if (!predchozi) return null;
  return Math.round(((aktualni - predchozi) / predchozi) * 100);
}

// ---------------------------------------------------------------- rozdělení

function rozdeleni(seminko, polozky) {
  if (!Array.isArray(polozky) || polozky.length === 0) return [];
  if (polozky.length === 1) return [{ nazev: polozky[0], podil: 100 }];
  const nahoda = vytvorLcg(hashRetezce(String(seminko)));
  const vahy = polozky.map(() => 0.2 + nahoda() * 0.8);
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

function formatCislo(n) {
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

function formatCas(sekundy) {
  const s = Math.round(sekundy);
  const minuty = Math.floor(s / 60);
  const zbytek = s % 60;
  return `${minuty}:${String(zbytek).padStart(2, "0")}`;
}

function formatProcenta(n) {
  return `${Math.round(n)} %`;
}

function formatZmena(n) {
  if (n === null || n === undefined) return "—";
  if (n > 0) return `+${n} %`;
  if (n < 0) return `\u2212${Math.abs(n)} %`;
  return "0 %";
}

// -------------------------------------------------------------------- graf

function osaGrafu(data, klic) {
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

return { vygenerujData, filtrujObdobi, souhrn, zmenaProti, rozdeleni, formatCislo, formatCas, formatProcenta, formatZmena, osaGrafu };
})();

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
            // „kontakt" není pole formuláře — je to pravidlo přes telefon a e-mail.
            // Hlášku ukážeme u telefonu, který je v pořadí první.
            var vstup = pole === "kontakt" ? form.elements.telefon : form.elements[pole];
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

  /* ================================== fotky nahrané v administraci
     Detailní stránky jsou statické, fotky žijí v localStorage. Proto se
     dokreslují až v prohlížeči — na kartách i v hlavním náhledu detailu. */
  function galerieZeStavu(id) {
    if (!id || !window.GAT || !GAT.fotky || !GAT.cmsStore) return [];
    var stav = GAT.cmsStore.loadState(bezpecneUloziste());
    var pridane = (stav.realizace && stav.realizace.added) || [];
    for (var i = 0; i < pridane.length; i++) {
      if (pridane[i].id === id) return GAT.fotky.normalizujGalerie(pridane[i].fotky);
    }
    var upravene = (stav.realizace && stav.realizace.edited) || {};
    return GAT.fotky.normalizujGalerie(upravene[id] && upravene[id].fotky);
  }

  function fotkyNaKartach() {
    $$("[data-realizace-nahled]").forEach(function (nahled) {
      var fotky = galerieZeStavu(nahled.getAttribute("data-realizace-nahled"));
      if (!fotky.length) return;
      var svg = nahled.querySelector("svg");
      if (!svg) return;
      var obr = document.createElement("img");
      obr.src = fotky[0].dataUrl;
      obr.alt = "";
      obr.loading = "lazy";
      nahled.replaceChild(obr, svg);
    });
  }

  function vykresliGalerii(cil, fotky, popis) {
    if (!cil || !fotky.length) return;
    cil.classList.add("detail-nahled", "detail-nahled-fotky");
    var mini = fotky.length < 2 ? "" :
      '<div class="galerie-pasek">' + fotky.map(function (f, i) {
        return '<button type="button" class="galerie-mini" data-index="' + i + '"' +
          (i === 0 ? ' aria-current="true"' : "") + '><img src="' + f.dataUrl + '" alt=""></button>';
      }).join("") + "</div>";
    cil.innerHTML = '<div class="galerie-hlavni"><img src="' + fotky[0].dataUrl +
      '" alt="' + uklid(popis || "") + '"></div>' + mini;

    var hlavni = cil.querySelector(".galerie-hlavni img");
    $$(".galerie-mini", cil).forEach(function (tl) {
      tl.addEventListener("click", function () {
        hlavni.src = fotky[Number(tl.getAttribute("data-index"))].dataUrl;
        $$(".galerie-mini", cil).forEach(function (x) {
          if (x === tl) x.setAttribute("aria-current", "true");
          else x.removeAttribute("aria-current");
        });
      });
    });
  }

  function galerieNaDetailu() {
    var cil = $("[data-realizace-galerie]");
    if (!cil) return;
    var fotky = galerieZeStavu(cil.getAttribute("data-realizace-galerie"));
    var nadpis = $("h1");
    vykresliGalerii(cil, fotky, nadpis ? nadpis.textContent : "");
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
      var fotky = GAT.fotky ? GAT.fotky.normalizujGalerie(r.fotky) : [];
      var nahled = fotky.length
        ? '<img src="' + fotky[0].dataUrl + '" alt="" loading="lazy">'
        : motiv(r.motiv != null ? r.motiv : r.id);
      return '<a class="karta-realizace" href="' + href + '">' +
        '<span class="karta-nahled">' + nahled + '<span class="stitky">' + stitky + "</span></span>" +
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
    var fotky = GAT.fotky ? GAT.fotky.normalizujGalerie(polozka.fotky) : [];
    if (nahled && fotky.length) vykresliGalerii(nahled, fotky, polozka.nazev);
    else if (nahled && window.GAT_MOTIV) nahled.innerHTML = window.GAT_MOTIV;
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
    fotkyNaKartach();
    galerieNaDetailu();
    zkratky();
    formulare();
    vypisRealizaci();
    detailZeSablony();
    slovnikHledani();
    pasTecek();
    kartyPodKurzorem();
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
