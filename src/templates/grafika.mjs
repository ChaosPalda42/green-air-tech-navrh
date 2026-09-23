/* Vlastní technická grafika: dělič z potrubí, schéma v hero a náhledy realizací.
   Všechno je inline SVG — ostré na retině, laditelné barvou, bez jediného kB fotky. */

const ZELENA = "#58ac25";
const ZELENA_SV = "#7bd13f";
const FIALOVA = "#8a7ecd";

/* ------------------------------------------------------------- hero schéma */
/** Podélný řez vzduchotechnickou jednotkou s proudnicemi — dekorace pod hero obrázkem. */
export function heroSchema() {
  return `<svg class="hero-schema" viewBox="0 0 520 150" aria-hidden="true" focusable="false" fill="none">
  <defs>
    <linearGradient id="gs-proud" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${ZELENA_SV}" stop-opacity="0"/>
      <stop offset="45%" stop-color="${ZELENA_SV}" stop-opacity=".85"/>
      <stop offset="100%" stop-color="${ZELENA_SV}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g stroke="rgba(255,255,255,.22)" stroke-width="1.4">
    <rect x="94" y="34" width="150" height="82" rx="8"/>
    <path d="M94 56h150M94 94h150"/>
    <path d="M124 34v82M154 34v82M184 34v82M214 34v82"/>
    <rect x="288" y="46" width="104" height="58" rx="6"/>
    <circle cx="340" cy="75" r="19"/>
    <path d="M340 56v38M321 75h38M326.6 61.6l26.8 26.8M326.6 88.4l26.8-26.8"/>
    <path d="M244 62h44M244 88h44M392 62h56M392 88h56"/>
    <path d="M40 62h54M40 88h54"/>
  </g>
  <g stroke="url(#gs-proud)" stroke-width="2.2" stroke-linecap="round" fill="none">
    <path d="M8 75h48"><animate attributeName="stroke-dasharray" values="0 60;28 60;0 60" dur="3.2s" repeatCount="indefinite"/></path>
    <path d="M452 75h60"><animate attributeName="stroke-dasharray" values="0 70;34 70;0 70" dur="3.2s" begin="1.1s" repeatCount="indefinite"/></path>
  </g>
  <g fill="${ZELENA_SV}" opacity=".9">
    <circle cx="66" cy="75" r="2.4"/><circle cx="470" cy="75" r="2.4"/>
  </g>
</svg>`;
}

/* ------------------------------------------------------------- náhledy realizací */
export { motivRealizace } from "./motivy.mjs";

/* ------------------------------------------------------------- favicon */
/** Kruhový motiv z loga zjednodušený do faviconu (zelená G-kružnice s paprsky). */
export function favicon() {
  let paprsky = "";
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4;
    const x1 = 32 + Math.cos(a) * 25;
    const y1 = 32 + Math.sin(a) * 25;
    const x2 = 32 + Math.cos(a) * 30;
    const y2 = 32 + Math.sin(a) * 30;
    const barva = i % 2 === 0 ? ZELENA : "#584a95";
    paprsky += `<path d="M${x1.toFixed(1)} ${y1.toFixed(1)}L${x2.toFixed(1)} ${y2.toFixed(1)}" stroke="${barva}" stroke-width="5" stroke-linecap="round"/>`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="13" fill="#101a12"/>
  ${paprsky}
  <path d="M32 14a18 18 0 1 0 18 18H32" fill="none" stroke="${ZELENA}" stroke-width="6" stroke-linecap="round"/>
</svg>`;
}

/* ------------------------------------------------------------- sdílecí obrázek */
export function ogObrazek(titulek) {
  const bezpecny = String(titulek).replace(/[<>&]/g, "");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
  <defs><linearGradient id="og" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#16251a"/><stop offset="100%" stop-color="#0b130d"/>
  </linearGradient></defs>
  <rect width="1200" height="630" fill="url(#og)"/>
  <g stroke="rgba(255,255,255,.14)" stroke-width="2" fill="none">
    <rect x="80" y="380" width="700" height="70" rx="8"/>
    <path d="M220 380v70M360 380v70M500 380v70M640 380v70"/>
    <path d="M780 400h200M780 430h200"/>
  </g>
  <path d="M80 300h140" stroke="${ZELENA}" stroke-width="6" stroke-linecap="round"/>
  <text x="80" y="230" fill="#ffffff" font-family="Barlow, Arial, sans-serif" font-size="76" font-weight="700">Green Air Tech</text>
  <text x="80" y="356" fill="#9fc98a" font-family="Inter, Arial, sans-serif" font-size="34">${bezpecny}</text>
</svg>`;
}
