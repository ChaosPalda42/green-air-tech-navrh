// C-004 — validace kontaktního formuláře (co nejkratší, po schůzce 9. 10. 2026).

export function isEmail(value) {
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

export function normalizePhone(value) {
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

export function isPhoneCz(value) {
  if (typeof value !== "string" || value === "") return false;
  const v = normalizePhone(value);
  if (!/^\+420\d{9}$/.test(v)) return false;
  return "672359".includes(v[4]);
}

export function validateContact(values, messages = {}) {
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
