/**
 * C-005: Filtrování, řazení a stránkování referencí
 * Čistý JavaScript — žádné importy, žádné externí závislosti.
 */

/**
 * normalizeText(value) → string
 * Malá písmena, bez diakritiky (odstraní kombinující znaky U+0300–U+036F).
 */
export function normalizeText(value) {
  return String(value)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * filterItems(items, { kategorie, dotaz, rok } = {}) → nové pole
 * Filtry se kombinují logickým A. Vstup se nemutuje.
 */
export function filterItems(items, { kategorie, dotaz, rok } = {}) {
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
export function collectKategorie(items) {
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
export function collectRoky(items) {
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
export function sortItems(items, mode) {
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
export function paginate(items, page, perPage) {
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
