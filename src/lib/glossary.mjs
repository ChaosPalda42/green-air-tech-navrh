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
export function annotate(html, terms, options = {}) {
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
export function findTerm(terms, abbr) {
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
export function sortTerms(terms) {
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
export function groupTerms(terms) {
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
