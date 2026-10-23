export function isEmail(value) {
  if (typeof value !== "string" || value.length === 0) return false;
  if (/\s/.test(value)) return false;
  if (value.includes("..")) return false;
  const at = value.indexOf("@");
  if (at === -1 || at !== value.lastIndexOf("@")) return false;
  const local = value.slice(0, at);
  const domain = value.slice(at + 1);
  if (local.length === 0) return false;
  if (domain.length === 0) return false;
  const parts = domain.split(".");
  if (parts.length < 2) return false;
  for (const part of parts) {
    if (part.length === 0) return false;
  }
  const tld = parts[parts.length - 1];
  if (tld.length < 2) return false;
  if (!/^[A-Za-z]{2,}$/.test(tld)) return false;
  return true;
}

export function normalizePhone(value) {
  if (typeof value !== "string") return "";
  const cleaned = value.replace(/[\s()\-]/g, "");
  if (/^00\d{9,15}$/.test(cleaned)) {
    return "+" + cleaned.slice(2);
  }
  if (/^420\d{9}$/.test(cleaned)) {
    return "+" + cleaned;
  }
  if (/^\d{9}$/.test(cleaned)) {
    return "+420" + cleaned;
  }
  return cleaned;
}

export function isPhoneCz(value) {
  if (value === null || value === undefined || value === "") return false;
  const v = normalizePhone(value);
  return /^\+420[2-79]\d{8}$/.test(v);
}

export function isPhone(value) {
  if (value === null || value === undefined || value === "") return false;
  const v = normalizePhone(value);
  if (v.startsWith("+420")) {
    return isPhoneCz(value);
  }
  return /^\+[1-9]\d{8,14}$/.test(v);
}

export function validateContact(values, messages = {}) {
  const v = values || {};
  const errors = {};

  const typ = typeof v.typ === "string" ? v.typ.trim() : "";
  if (typ === "") errors.typ = "required";

  const jmeno = typeof v.jmeno === "string" ? v.jmeno.trim() : "";
  if (jmeno === "") errors.jmeno = "required";

  const email = typeof v.email === "string" ? v.email.trim() : "";
  if (email !== "" && !isEmail(email)) errors.email = "email";

  const telefon = typeof v.telefon === "string" ? v.telefon.trim() : "";
  if (telefon !== "" && !isPhone(telefon)) errors.telefon = "telefon";

  if (telefon === "" && email === "") errors.kontakt = "kontakt";

  const zprava = typeof v.zprava === "string" ? v.zprava.trim() : "";
  if (zprava !== "" && zprava.length < 10) errors.zprava = "zprava-kratka";

  if (v.souhlas !== true) errors.souhlas = "souhlas";

  const outMessages = {};
  for (const key of Object.keys(errors)) {
    const code = errors[key];
    if (messages && Object.prototype.hasOwnProperty.call(messages, key)) {
      outMessages[key] = messages[key];
    } else if (messages && Object.prototype.hasOwnProperty.call(messages, code)) {
      outMessages[key] = messages[code];
    } else {
      outMessages[key] = code;
    }
  }

  return { ok: Object.keys(errors).length === 0, errors, messages: outMessages };
}
