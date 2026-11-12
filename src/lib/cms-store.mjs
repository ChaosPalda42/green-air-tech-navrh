export const STORAGE_KEY = "gat-cms-v1";

export function emptyState() {
  return { texts: {}, realizace: { added: [], edited: {}, removed: [] }, portrety: {}, lide: { added: [], edited: {}, removed: [] }, updatedAt: null };
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
  if (!s.portrety || typeof s.portrety !== "object" || Array.isArray(s.portrety)) s.portrety = {};
  if (!s.lide || typeof s.lide !== "object" || Array.isArray(s.lide)) s.lide = { added: [], edited: {}, removed: [] };
  if (!Array.isArray(s.lide.added)) s.lide.added = [];
  if (!s.lide.edited || typeof s.lide.edited !== "object" || Array.isArray(s.lide.edited)) s.lide.edited = {};
  if (!Array.isArray(s.lide.removed)) s.lide.removed = [];
  return s;
}

export function loadState(storage) {
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

export function saveState(storage, state) {
  const s = _deepClone(state);
  s.updatedAt = new Date().toISOString();
  storage.setItem(STORAGE_KEY, JSON.stringify(s));
  return s;
}

export function resetState(storage) {
  storage.removeItem(STORAGE_KEY);
}

export function setText(state, lang, key, value) {
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

export function getText(state, lang, key) {
  const texts = state.texts && state.texts[lang];
  if (texts === undefined || texts === null) return null;
  return texts[key] !== undefined ? texts[key] : null;
}

export function mergeTexts(state, lang, baseFlatDict) {
  const result = _deepClone(baseFlatDict);
  const overrides = state.texts && state.texts[lang];
  if (overrides) {
    for (const k of Object.keys(overrides)) {
      result[k] = overrides[k];
    }
  }
  return result;
}

export function slugify(text) {
  let s = text.toLowerCase();
  s = s.normalize("NFD").replace(/[\u0300-\u036F]/g, "");
  s = s.replace(/[^a-z0-9]+/g, "-");
  s = s.replace(/^-+|-+$/g, "");
  return s;
}

export function upsertRealizace(state, item, baseList) {
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

export function removeRealizace(state, id) {
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

export function mergeRealizace(state, baseList) {
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

/* ------------------------------------------------------------ portréty */
/* Výřez portrétu v kolečku týmu: `zoom` je přiblížení v procentech (100 =
   celá fotka), `x`/`y` je posun fotky v procentech šířky kolečka. Posun
   nesmí odkrýt okraj, takže je omezený přiblížením: při zoomu 100 nejde
   posunout nic, při 160 je po každé straně navíc 30 %. Hodnoty se zarovnají
   na celá procenta — stejný výřez musí v PHP i v JS vyjít na stejné bajty. */
export const VYREZ_VYCHOZI = { zoom: 100, x: 0, y: 0 };
export const VYREZ_MAX_ZOOM = 250;

function _cislo(hodnota, vychozi) {
  const n = typeof hodnota === "number" ? hodnota : Number(hodnota);
  return Number.isFinite(n) ? n : vychozi;
}

/** Hodnoty v mezích a na celá procenta; posun zkrácený podle přiblížení. */
export function normalizeVyrez(vyrez) {
  const v = vyrez && typeof vyrez === "object" && !Array.isArray(vyrez) ? vyrez : {};
  let zoom = Math.round(_cislo(v.zoom, 100));
  if (zoom < 100) zoom = 100;
  if (zoom > VYREZ_MAX_ZOOM) zoom = VYREZ_MAX_ZOOM;
  const mez = (zoom - 100) / 2;
  const omez = (hodnota) => {
    let n = Math.round(_cislo(hodnota, 0));
    if (n > mez) n = Math.floor(mez);
    if (n < -mez) n = -Math.floor(mez);
    return n;
  };
  return { zoom, x: omez(v.x), y: omez(v.y) };
}

export function jeVychoziVyrez(vyrez) {
  const v = normalizeVyrez(vyrez);
  return v.zoom === VYREZ_VYCHOZI.zoom && v.x === VYREZ_VYCHOZI.x && v.y === VYREZ_VYCHOZI.y;
}

/** Nastaví výřez jednoho člověka; `null` záznam ze stavu SMAŽE.

   Mazat i výřez 100/0/0 by se zdálo úsporné, ale vzalo by správci možnost
   fotku vrátit na celou: soubor site.json u některých lidí přiblížení vozí
   (ZdrojDb ho stavem jen přepisuje), takže smazaný záznam znamená „nech
   dodané", ne „nepřibližuj". Prázdno se proto ukládá taky. */
export function setVyrez(state, id, vyrez) {
  const s = _ensureState(state);
  if (vyrez === null || vyrez === undefined) {
    delete s.portrety[id];
  } else {
    s.portrety[id] = normalizeVyrez(vyrez);
  }
  return s;
}

export function getVyrez(state, id) {
  const ulozeny = state && state.portrety ? state.portrety[id] : undefined;
  if (ulozeny === undefined || ulozeny === null) return null;
  return normalizeVyrez(ulozeny);
}

/* Výřez jako hodnota atributu style. Dvě desetinná místa u přiblížení
   proto, aby PHP a JS napsaly tytéž znaky — "1.6" proti "1.60" by rozhodilo
   bajtovou shodu ostrého webu s ukázkou. */
export function stylVyrezu(vyrez) {
  if (vyrez === undefined || vyrez === null || jeVychoziVyrez(vyrez)) return "";
  const v = normalizeVyrez(vyrez);
  return `--vz:${(v.zoom / 100).toFixed(2)};--vx:${v.x}%;--vy:${v.y}%`;
}

/* ------------------------------------------------------------------- lidé
   Tým se dá v administraci doplnit, upravit i zkrátit. Zrcadlí
   web/app/Obsah/StavLidi.php — co jedno složí, musí složit i druhé, jinak
   se ostrý web rozejde s ukázkou.

   Role člověka se tady neukládá: je to text jako každý jiný, klíč
   `lide.<id>` v části texts. */

/** Pole, která o člověku držíme. */
export const POLE_CLOVEKA = ["id", "jmeno", "telefon", "telefonHref", "email", "inicialy", "fotka"];

/** Kolik lidí smí administrace přidat. Tým není adresář. */
export const MAX_PRIDANYCH_LIDI = 30;

function _ocistiClovek(osoba) {
  const ven = {};
  for (const pole of POLE_CLOVEKA) {
    if (!Object.prototype.hasOwnProperty.call(osoba, pole)) continue;
    if (typeof osoba[pole] !== "string") continue;
    ven[pole] = osoba[pole].trim();
  }
  return ven;
}

/** Zkratka ze jména: první písmena prvních dvou slov, velká. */
export function inicialyZJmena(jmeno) {
  const slova = String(jmeno).trim().split(/\s+/);
  let zkratka = "";
  for (const slovo of slova) {
    if (slovo === "") continue;
    zkratka += slovo.slice(0, 1);
    if (zkratka.length >= 2) break;
  }
  return zkratka.toUpperCase();
}

/** Telefon do odkazu tel:: jen číslice a jedno plus na začátku. */
export function telefonHref(telefon) {
  const text = String(telefon);
  const cisla = text.replace(/[^0-9]/g, "");
  const plus = text.replace(/^\s+/, "").startsWith("+") ? "+" : "";
  return cisla === "" ? "" : plus + cisla;
}

/** Doplní zkratku a telefon do odkazu, pokud chybí. */
export function doplnenyClovek(osoba) {
  const o = Object.assign({}, osoba);
  if (!o.inicialy) o.inicialy = inicialyZJmena(o.jmeno || "");
  if (!o.telefonHref) o.telefonHref = telefonHref(o.telefon || "");
  return o;
}

/**
 * Přidá nebo změní jednoho člověka. Bez id se id vyrobí ze jména (slug);
 * při kolizi se připojuje -2, -3, … Id ze souborů jde do edited (sloučeno
 * s předchozí změnou) a vybere se z removed, jinak do added.
 */
export function upsertClovek(state, osoba, baseList) {
  if (baseList === undefined) baseList = [];
  const s = _ensureState(state);
  const baseIds = new Set(baseList.map((b) => String(b.id)));
  const addedIds = new Set(s.lide.added.map((a) => String(a.id)));

  let id = osoba.id;
  if (!id) {
    const zaklad = slugify(osoba.jmeno || "");
    id = zaklad;
    let suffix = 2;
    while (baseIds.has(id) || addedIds.has(id) || Object.prototype.hasOwnProperty.call(s.lide.edited, id)) {
      id = zaklad + "-" + suffix;
      suffix++;
    }
  }
  id = String(id);

  const zapis = _ocistiClovek(osoba);
  delete zapis.id;

  // Zkratka a odkaz na telefon se odvozují ze jména a z čísla. Když se
  // zdroj změní a odvozené pole nepřijde, přepočítá se — jinak by po
  // opravě čísla zůstal odkaz `tel:` na to staré.
  if ("jmeno" in zapis && !("inicialy" in zapis)) zapis.inicialy = inicialyZJmena(String(zapis.jmeno));
  if ("telefon" in zapis && !("telefonHref" in zapis)) zapis.telefonHref = telefonHref(String(zapis.telefon));

  // Nejdřív `added`: administrace na ostrém webu dostává do stránky
  // sloučený seznam, takže `baseList` už přidané lidi obsahuje. Kdyby
  // rozhodoval základ, oprava přidaného člověka by skončila v `edited` —
  // a tu spojení zahodí, protože v site.json to id není.
  const kde = s.lide.added.findIndex((p) => String(p.id) === id);
  if (kde !== -1) {
    s.lide.added[kde] = doplnenyClovek(Object.assign({}, s.lide.added[kde], zapis, { id }));
  } else if (baseIds.has(id)) {
    const drive = s.lide.edited[id] || {};
    s.lide.edited[id] = Object.assign({}, drive, zapis);
    s.lide.removed = s.lide.removed.filter((odebrane) => odebrane !== id);
  } else {
    s.lide.added.push(doplnenyClovek(Object.assign({}, zapis, { id })));
  }

  return s;
}

/**
 * Odebere člověka. Přidaný zmizí z added (nebyl nikdy v souborech), ten ze
 * souborů se zapíše do removed. Výřez fotky jde s ním — jinak by v datech
 * zůstal záznam, ke kterému už nikdo nepatří.
 */
export function removeClovek(state, id) {
  const s = _ensureState(state);
  const kde = s.lide.added.findIndex((p) => String(p.id) === id);
  if (kde !== -1) {
    s.lide.added.splice(kde, 1);
  } else {
    if (!s.lide.removed.includes(id)) s.lide.removed.push(id);
    delete s.lide.edited[id];
  }
  delete s.portrety[id];
  return s;
}

/**
 * Lidé ze souborů se změnami administrace: odebraní vypadnou, změněným se
 * přelepí pole, přidaní se připojí na konec.
 */
export function mergeLide(state, baseList) {
  const lide = (state && state.lide) || {};
  const added = Array.isArray(lide.added) ? lide.added : [];
  const edited = lide.edited && typeof lide.edited === "object" ? lide.edited : {};
  const removed = new Set(Array.isArray(lide.removed) ? lide.removed.map(String) : []);

  const vysledek = [];
  for (const osoba of baseList) {
    if (!osoba || typeof osoba !== "object") continue;
    const id = String(osoba.id === undefined ? "" : osoba.id);
    if (removed.has(id)) continue;
    const zmena = edited[id];
    vysledek.push(
      zmena && typeof zmena === "object"
        ? doplnenyClovek(Object.assign({}, osoba, _ocistiClovek(zmena), { id }))
        : Object.assign({}, osoba)
    );
  }
  for (const osoba of added) {
    if (!osoba || typeof osoba !== "object" || !osoba.id) continue;
    vysledek.push(doplnenyClovek(_ocistiClovek(osoba)));
  }

  return vysledek;
}

/** Lidé ze souborů přelepení výřezy z administrace. */
export function mergeVyrezy(state, baseList) {
  const prepisy = (state && state.portrety) || {};
  return baseList.map((osoba) => {
    const prepis = prepisy[osoba.id];
    if (prepis === undefined || prepis === null) return Object.assign({}, osoba);
    return Object.assign({}, osoba, { vyrez: normalizeVyrez(prepis) });
  });
}

export function exportJson(state) {
  return JSON.stringify(state, null, 2);
}

export function importJson(state, text) {
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
