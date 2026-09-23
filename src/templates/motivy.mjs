/* Osm technických schémat místo stockových fotek.
   Plátno 640×400, kresba drží v ploše 30..610 × 55..350. */

const ZELENA = "#7bd13f";
const FIALOVA = "#9a8de0";
const LINKA = "rgba(255,255,255,.46)";
const SLABA = "rgba(255,255,255,.2)";

/* -------------------------------------------------------------- prvky */

/** Vodorovné potrubí s přírubami. */
function potrubiH(x1, x2, y, h = 44, krok = 38) {
  let priruby = "";
  for (let x = x1 + krok; x < x2 - 4; x += krok) priruby += `M${x} ${y - 5}v${h + 10}`;
  return `<path d="M${x1} ${y}h${x2 - x1}M${x1} ${y + h}h${x2 - x1}"/><path d="${priruby}" opacity=".55"/>`;
}

/** Svislé potrubí s přírubami. */
function potrubiV(y1, y2, x, w = 44, krok = 38) {
  let priruby = "";
  for (let y = y1 + krok; y < y2 - 4; y += krok) priruby += `M${x - 5} ${y}h${w + 10}`;
  return `<path d="M${x} ${y1}v${y2 - y1}M${x + w} ${y1}v${y2 - y1}"/><path d="${priruby}" opacity=".55"/>`;
}

/** Koncentrické koleno 90°: vodorovné potrubí (konec x, pás y..y+h) se stáčí nahoru k hladině cy. */
function kolenoNahoru(x, y, h, cy) {
  const rVnitrni = 24;
  const rVnejsi = rVnitrni + h;
  const svislyX = x + 34;              // levá stěna svislé větve
  const zlom = svislyX - rVnitrni;     // obě stěny se lámou ve stejném místě
  return (
    `<path d="M${x} ${y}H${zlom}A${rVnitrni} ${rVnitrni} 0 0 0 ${svislyX} ${y - rVnitrni}V${cy}"/>` +
    `<path d="M${x} ${y + h}H${zlom}A${rVnejsi} ${rVnejsi} 0 0 0 ${svislyX + h} ${y + h - rVnejsi}V${cy}"/>`
  );
}

/** Střešní výfuková hlavice nad svislým potrubím. */
function hlavice(x, w, y) {
  return `<path d="M${x - 14} ${y}l14 -20h${w}l14 20z"/><path d="M${x - 2} ${y - 9}h${w + 4}" opacity=".55"/>`;
}

/** Vzduchotechnická jednotka — skříň s komorami. */
function jednotka(x, y, w, h, komory = 4) {
  let deleni = "";
  for (let i = 1; i < komory; i++) deleni += `M${x + (w / komory) * i} ${y}v${h}`;
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6"/><path d="${deleni}" opacity=".6"/>`;
}

/** Ventilátor s lopatkami. */
function ventilator(cx, cy, r, barva) {
  let lopatky = "";
  for (let i = 0; i < 6; i++) {
    const a = (i * Math.PI) / 3;
    lopatky += `M${cx} ${cy}L${(cx + Math.cos(a) * r).toFixed(1)} ${(cy + Math.sin(a) * r).toFixed(1)}`;
  }
  return `<g stroke="${barva}"><circle cx="${cx}" cy="${cy}" r="${r}"/><path d="${lopatky}" opacity=".8"/><circle cx="${cx}" cy="${cy}" r="${(r * 0.22).toFixed(1)}"/></g>`;
}

/** Filtrační vložka — svislé lamely. */
function filtr(x, y, w, h, barva, lamel = 6) {
  let lamely = "";
  for (let i = 1; i < lamel; i++) lamely += `M${x + (w / lamel) * i} ${y}v${h}`;
  return `<g stroke="${barva}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3"/><path d="${lamely}" opacity=".75"/></g>`;
}

/** Deskový výměník — kosočtvercová skříň s žebry. */
function vymenik(x, y, w, h, barva) {
  let zebra = "";
  for (let i = 1; i < 8; i++) zebra += `M${x + (w / 8) * i} ${y}l${-w / 8} ${h}`;
  return `<g stroke="${barva}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4"/><path d="${zebra}" opacity=".6" clip-path="inset(0)"/></g>`;
}

/** Výustka / anemostat. */
function vyust(x, y, smer = 1) {
  const h = 20 * smer;
  return `<path d="M${x - 17} ${y}l8 ${h}h18l8 ${-h}z"/><path d="M${x - 8} ${y + h * 0.6}h16" opacity=".6"/>`;
}

/** Venkovní jednotka tepelného čerpadla. */
function venkovniJednotka(x, y, w, h, barva) {
  return (
    `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6"/>` +
    `<path d="M${x} ${y + 16}h${w}" opacity=".5"/>` +
    ventilator(x + w / 2, y + h / 2 + 8, Math.min(w, h) / 3.2, barva)
  );
}

/** Zásobník / akumulace se spirálou. */
function zasobnik(x, y, w, h, barva) {
  let spirala = "";
  const kroku = 5;
  for (let i = 0; i < kroku; i++) {
    const yy = y + 22 + (i * (h - 44)) / kroku;
    spirala += `M${x + 12} ${yy}q${w / 2 - 12} 14 ${w - 24} 0`;
  }
  return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${w / 2}"/><path d="${spirala}" stroke="${barva}" opacity=".85"/></g>`;
}

/** Fan-coil / vnitřní jednotka. */
function fanCoil(x, y, barva) {
  return `<g><rect x="${x}" y="${y}" width="64" height="26" rx="5"/><path d="M${x + 10} ${y + 26}l-4 10M${x + 26} ${y + 26}l-4 10M${x + 42} ${y + 26}l-4 10M${x + 58} ${y + 26}l-4 10" stroke="${barva}"/></g>`;
}

/* --------------------------------------------------------- kompozice */

const ROZVRHY = [
  // 1 — hlavní rozvod VZT s výustkami a jednotkou
  (a) => `
    ${potrubiH(30, 470, 120, 46)}
    <path d="M120 166v78M240 166v110M360 166v62"/>
    ${vyust(120, 244)}${vyust(240, 276)}${vyust(360, 228)}
    <g stroke="${a}">${jednotka(470, 96, 140, 94, 3)}${ventilator(540, 143, 26, a)}</g>`,

  // 2 — strojovna: jednotka, koleno nahoru, střešní výfuk
  (a) => `
    <g>${jednotka(30, 150, 210, 116, 4)}</g>
    ${filtr(48, 170, 48, 76, a, 4)}
    ${ventilator(196, 208, 32, a)}
    ${potrubiH(240, 470, 180, 56, 38)}
    ${kolenoNahoru(470, 180, 56, 96)}
    ${hlavice(504, 56, 96)}`,

  // 3 — stoupačka s patry
  (a) => `
    ${potrubiV(40, 360, 288, 48, 44)}
    <path d="M336 96h120M336 186h150M336 286h120"/>
    <path d="M336 78h120v36h-120M336 168h150v36h-150M336 268h120v36h-120"/>
    <g stroke="${a}">${fanCoil(470, 78, a)}${fanCoil(500, 168, a)}${fanCoil(470, 268, a)}</g>`,

  // 4 — uzavřený okruh s ventilátorem a rekuperací
  (a) => `
    <path d="M90 92h460a44 44 0 0 1 44 44v128a44 44 0 0 1-44 44H90a44 44 0 0 1-44-44V136a44 44 0 0 1 44-44z"/>
    <path d="M90 136h460a0 0 0 0 1 0 0v88a0 0 0 0 1 0 0H90" opacity=".35"/>
    ${ventilator(150, 180, 40, a)}
    ${vymenik(360, 130, 130, 100, a)}
    <path d="M300 92v-34M300 314v34" opacity=".5"/>`,

  // 5 — chlazení: zdroj chladu, dvě větve, fan-coily
  (a) => `
    <g>${jednotka(30, 120, 130, 120, 3)}</g>
    ${ventilator(95, 180, 34, a)}
    <path d="M160 152h420M160 208h420"/>
    <path d="M280 152v-46M280 208v46M420 152v-46M420 208v46M540 152v-46M540 208v46" opacity=".8"/>
    <g stroke="${a}">${fanCoil(248, 62, a)}${fanCoil(388, 62, a)}${fanCoil(508, 62, a)}</g>
    <g>${vyust(280, 254)}${vyust(420, 254)}${vyust(540, 254)}</g>`,

  // 6 — tepelné čerpadlo: venkovní jednotka, akumulace, podlahový okruh
  (a) => `
    <g>${venkovniJednotka(34, 96, 150, 124, a)}</g>
    <path d="M184 136h86M184 180h86"/>
    <g>${zasobnik(270, 62, 110, 190, a)}</g>
    <path d="M380 108h140v156"/>
    <g stroke="${a}">
      <path d="M520 264H150a17 17 0 0 0 0 34h370a17 17 0 0 1 0 34H150"/>
    </g>
    <path d="M150 332h-46V148h-70" opacity=".6"/>`,

  // 7 — filtrace ve třech stupních
  (a) => `
    ${potrubiH(30, 120, 150, 88, 44)}
    <g>${jednotka(120, 130, 330, 128, 1)}</g>
    ${filtr(142, 150, 52, 88, LINKA, 3)}
    ${filtr(240, 150, 66, 88, a, 6)}
    ${filtr(352, 150, 78, 88, a, 9)}
    ${potrubiH(450, 610, 150, 88, 44)}
    <path d="M142 268v26M240 268v26M352 268v26" opacity=".45"/>
    <path d="M120 294h340" opacity=".45"/>`,

  // 8 — opravy výměníků: výměník a čtyři hrdla
  (a) => `
    ${vymenik(190, 106, 260, 190, a)}
    ${potrubiH(30, 190, 130, 40, 40)}
    ${potrubiH(450, 610, 130, 40, 40)}
    ${potrubiH(30, 190, 232, 40, 40)}
    ${potrubiH(450, 610, 232, 40, 40)}
    <path d="M190 106l-22-22M450 106l22-22M190 296l-22 22M450 296l22 22" opacity=".5"/>`,
];

/**
 * Náhled realizace — technický výkres místo fotky.
 * @param {number} motiv 1..8
 */
export function motivRealizace(motiv = 1, { popis = "" } = {}) {
  const cislo = ((Math.max(1, Math.round(motiv)) - 1) % ROZVRHY.length) + 1;
  const akcent = cislo % 2 === 1 ? ZELENA : FIALOVA;
  const id = `m${cislo}`;
  const a11y = popis ? `role="img" aria-label="${popis}"` : 'aria-hidden="true" focusable="false"';

  return `<svg class="motiv" ${a11y} viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="${id}s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="${id}p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="${id}t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${akcent}" stop-opacity="0"/>
      <stop offset="35%" stop-color="${akcent}" stop-opacity=".85"/>
      <stop offset="100%" stop-color="${akcent}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#${id}p)"/>
  <rect width="640" height="400" fill="url(#${id}s)"/>
  <g fill="none" stroke="${LINKA}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    ${ROZVRHY[cislo - 1](akcent)}
  </g>
  <g fill="none" stroke="url(#${id}t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="${SLABA}" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>`;
}
