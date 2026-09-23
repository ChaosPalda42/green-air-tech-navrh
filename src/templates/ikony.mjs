/* Sada SVG ikon. Vše 24×24, tah 1.8, dědí currentColor. */

const T = {
  /* --- služby ---------------------------------------------------- */
  // projekce: výkres s potrubím a kótou
  projekce:
    '<path d="M3 4.5h18v15H3z"/><path d="M3 9h18M8 4.5v15"/><path d="M12 12.5h4.5a1.5 1.5 0 0 1 0 3H12z"/><path d="M12 12.5v3"/>',
  // montáž: potrubní koleno s přírubami
  montaz:
    '<path d="M3 7.5h7.5a3 3 0 0 1 3 3V21"/><path d="M3 5v5M13.5 21h-4M13.5 21h4"/><path d="M20 4.2l1 1.8-1 1.8-2 .2-1.4-1.4.2-2z"/><path d="M17.8 6.4l-3.2 3.2"/>',
  // servis: klíč a hodiny
  servis:
    '<circle cx="8" cy="8" r="5"/><path d="M8 5.4V8l1.8 1"/><path d="M14.5 13.5l6 6M13 17l4-4"/><path d="M12.6 15.4a2.6 2.6 0 0 1 3.4-3.4"/>',
  // energetika: list a ručička měřidla
  energetika:
    '<path d="M4 18.5a8.5 8.5 0 0 1 16 0"/><path d="M12 18.5l4-5"/><circle cx="12" cy="18.5" r="1.2"/><path d="M12 8.5c0-2.6 2-4.5 4.5-5-0 3-1.6 5-4.5 5z"/>',
  // klimatizace: sněhová vločka a vlna tepla
  klimatizace:
    '<path d="M12 3v10M12 3l-2 2M12 3l2 2"/><path d="M7.7 5.6l8.6 5M7.7 5.6l.3 2.8M7.7 5.6l2.8-.4"/><path d="M16.3 5.6l-8.6 5M16.3 5.6l-2.8-.4M16.3 5.6l-.3 2.8"/><path d="M4 18c1.6 0 1.6-1.6 3.2-1.6S8.8 18 10.4 18s1.6-1.6 3.2-1.6S15.2 18 16.8 18s1.6-1.6 3.2-1.6"/>',
  // filtr: mřížka filtru
  filtr:
    '<rect x="3.5" y="4.5" width="17" height="15" rx="1.5"/><path d="M8 4.5v15M12 4.5v15M16 4.5v15"/><path d="M3.5 9.5h17M3.5 14.5h17"/>',
  // výměník: lamely a trubky
  vymenik:
    '<rect x="3.5" y="5.5" width="17" height="13" rx="1.5"/><path d="M7 5.5v13M10.3 5.5v13M13.7 5.5v13M17 5.5v13"/><path d="M1.5 9h2M1.5 15h2M20.5 9h2M20.5 15h2"/>',

  /* --- rozhraní -------------------------------------------------- */
  sip: '<path d="M4 12h15"/><path d="M13 6l6 6-6 6"/>',
  sipZpet: '<path d="M20 12H5"/><path d="M11 6l-6 6 6 6"/>',
  sipNahoru: '<path d="M12 20V5"/><path d="M6 11l6-6 6 6"/>',
  sipDolu: '<path d="M6 9l6 6 6-6"/>',
  telefon:
    '<path d="M6.5 3.5h3l1.5 4-2 1.5a12 12 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2.2 2C11.6 19 5 12.4 4.5 5.7A2 2 0 0 1 6.5 3.5z"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5l8.5 6 8.5-6"/>',
  hodiny: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5.3l3.4 2"/>',
  fajfka: '<circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.7 2.6L16 9.6"/>',
  fajfkaProsta: '<path d="M4.5 12.8l4.7 4.5L19.5 6.8"/>',
  lupa: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  krizek: '<path d="M6 6l12 12M18 6L6 18"/>',
  misto: '<path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/>',
  kalendar: '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  varovani: '<path d="M12 3.5l9 16H3l9-16z"/><path d="M12 9.5v4.5M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  externi: '<path d="M14 4h6v6"/><path d="M20 4l-8.5 8.5"/><path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
  stahnout: '<path d="M12 3.5v11"/><path d="M7.5 10l4.5 4.5 4.5-4.5"/><path d="M4.5 19.5h15"/>',
  nahrat: '<path d="M12 20V9"/><path d="M7.5 13.5L12 9l4.5 4.5"/><path d="M4.5 4.5h15"/>',
  upravit: '<path d="M4 20h4.5L19 9.5a2.1 2.1 0 0 0-3-3L5.5 17 4 20z"/>',
  kos: '<path d="M4.5 6.5h15"/><path d="M9.5 6.5V4.5h5v2"/><path d="M6.5 6.5l1 13h9l1-13"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  ulozit: '<path d="M5 4.5h11l3 3v12a1.5 1.5 0 0 1-1.5 1.5h-12A1.5 1.5 0 0 1 4 19.5V6a1.5 1.5 0 0 1 1-1.5z"/><path d="M8 4.5v5h7"/><rect x="8" y="13" width="8" height="6.5"/>',
  vitr: '<path d="M3 8h9.5a2.5 2.5 0 1 0-2.5-2.5"/><path d="M3 12h13a2.5 2.5 0 1 1-2.5 2.5"/><path d="M3 16h6.5a2 2 0 1 1-2 2"/>',
  dokument: '<path d="M6 3.5h7.5L19 9v11.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1z"/><path d="M13.5 3.5V9H19"/><path d="M8.5 13h7M8.5 16.5h7"/>',
  lide: '<circle cx="9" cy="8" r="3.4"/><path d="M3.5 19.5a5.5 5.5 0 0 1 11 0"/><path d="M16 5.2a3.4 3.4 0 0 1 0 5.6"/><path d="M17 14.6a5.5 5.5 0 0 1 3.5 4.9"/>',
  stit: '<path d="M12 3l7.5 3v6c0 4.5-3.2 7.7-7.5 9-4.3-1.3-7.5-4.5-7.5-9V6L12 3z"/><path d="M8.8 12.2l2.2 2.2 4.2-4.4"/>',
  list: '<path d="M4.5 19.5C4.5 11 9.5 5 20 4.5c.5 9.5-4.5 15-12 15h-3.5z"/><path d="M4.5 19.5C7 15 10.5 11.8 15 10"/>',
  kolecko: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7"/>',
};

export function ikona(nazev, { trida = "", velikost = 24, popis = "" } = {}) {
  const cesta = T[nazev];
  if (!cesta) throw new Error(`Neznámá ikona: ${nazev}`);
  const a11y = popis ? `role="img" aria-label="${popis}"` : 'aria-hidden="true" focusable="false"';
  return (
    `<svg ${a11y} class="${trida}" width="${velikost}" height="${velikost}" viewBox="0 0 24 24" ` +
    `fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${cesta}</svg>`
  );
}

export const nazvyIkon = Object.keys(T);
