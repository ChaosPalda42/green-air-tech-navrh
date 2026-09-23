/**
 * Validace kontaktního formuláře — čistý ESM, žádné importy.
 */

/**
 * @param {string} value
 * @returns {boolean}
 */
export function isEmail(value) {
  if (value == null || typeof value !== 'string') return false;
  if (value.includes(' ')) return false;
  // exactly one @
  const atIdx = value.indexOf('@');
  if (atIdx <= 0 || value.indexOf('@', atIdx + 1) !== -1) return false;
  const local = value.slice(0, atIdx);
  const domain = value.slice(atIdx + 1);
  if (local === '') return false;
  // domain must have at least one dot, no empty parts around dots
  const parts = domain.split('.');
  if (parts.length < 2) return false;
  for (const p of parts) {
    if (p === '') return false;
  }
  // TLD must be at least 2 letters
  const tld = parts[parts.length - 1];
  if (!/^[a-zA-Z]{2,}$/.test(tld)) return false;
  return true;
}

/**
 * @param {string} value
 * @returns {string}
 */
export function normalizePhone(value) {
  if (value == null || typeof value !== 'string') return '';
  // Remove spaces, parentheses, dashes
  let cleaned = value.replace(/[\s()\-]/g, '');

  // Strip leading '+' if present
  let noPlus = cleaned;
  if (noPlus.startsWith('+')) {
    noPlus = noPlus.slice(1);
  }

  // Check for leading "00420" → replace with +420
  if (noPlus.startsWith('00420')) {
    return '+420' + noPlus.slice(5);
  }

  // Check for leading "420" with total 12 digits (420 + 9 digits)
  if (noPlus.startsWith('420') && noPlus.length === 12) {
    return '+420' + noPlus.slice(3);
  }

  // 9-digit number without prefix → prepend +420
  if (/^\d{9}$/.test(noPlus)) {
    return '+420' + noPlus;
  }

  return cleaned;
}

/**
 * @param {string} value
 * @returns {boolean}
 */
export function isPhoneCz(value) {
  if (value == null || typeof value !== 'string' || value.trim() === '') return false;
  const normalized = normalizePhone(value);
  if (!normalized.startsWith('+420')) return false;
  const digits = normalized.slice(4);
  if (digits.length !== 9) return false;
  if (!/^\d{9}$/.test(digits)) return false;
  const first = digits[0];
  return ['6', '7', '2', '3', '5', '9'].includes(first);
}

/**
 * @param {object} values
 * @param {object} [messages]
 * @returns {{ ok: boolean, errors: object, messages: object }}
 */
export function validateContact(values, messages = {}) {
  const errors = {};
  const msgs = {};

  const jmeno = values.jmeno;
  if (jmeno == null || String(jmeno).trim() === '') {
    errors.jmeno = 'required';
    msgs.jmeno = resolveMessage('jmeno', 'required', messages);
  }

  const email = values.email;
  if (email == null || String(email).trim() === '') {
    errors.email = 'required';
    msgs.email = resolveMessage('email', 'required', messages);
  } else if (!isEmail(String(email))) {
    errors.email = 'email';
    msgs.email = resolveMessage('email', 'email', messages);
  }

  const telefon = values.telefon;
  if (telefon != null && String(telefon).trim() !== '' && !isPhoneCz(String(telefon))) {
    errors.telefon = 'telefon';
    msgs.telefon = resolveMessage('telefon', 'telefon', messages);
  }

  // typ: never errors

  const zprava = values.zprava;
  if (zprava == null || String(zprava).trim() === '') {
    errors.zprava = 'required';
    msgs.zprava = resolveMessage('zprava', 'required', messages);
  } else if (String(zprava).trim().length < 10) {
    errors.zprava = 'zprava-kratka';
    msgs.zprava = resolveMessage('zprava', 'zprava-kratka', messages);
  }

  const souhlas = values.souhlas;
  if (souhlas !== true) {
    errors.souhlas = 'souhlas';
    msgs.souhlas = resolveMessage('souhlas', 'souhlas', messages);
  }

  return {
    ok: Object.keys(errors).length === 0,
    errors,
    messages: msgs,
  };
}

/**
 * Resolve a human-readable message for a field.
 * Priority: messages[field] > messages[code] > code
 * @param {string} field
 * @param {string} code
 * @param {object} messages
 * @returns {string}
 */
function resolveMessage(field, code, messages) {
  if (messages[field] !== undefined) return messages[field];
  if (messages[code] !== undefined) return messages[code];
  return code;
}
