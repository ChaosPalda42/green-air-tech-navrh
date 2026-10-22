<?php
/* Technická grafika místo stockových fotek: schéma pod hero obrázkem a osm
   náhledů realizací.

   VYGENEROVÁNO z src/templates/motivy.mjs a grafika.mjs skriptem
   tools/prevod-grafiky.mjs. Je to dekorace, která nezávisí na obsahu — proto
   se nepočítá znovu v PHP, ale přenáší se hotová. Needitovat ručně. */

declare(strict_types=1);

namespace App\Sablony;

final class Grafika
{
    private const HERO = '<svg class="hero-schema" viewBox="0 0 520 150" aria-hidden="true" focusable="false" fill="none">
  <defs>
    <linearGradient id="gs-proud" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7bd13f" stop-opacity="0"/>
      <stop offset="45%" stop-color="#7bd13f" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#7bd13f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g stroke="var(--plocha-kresba)" stroke-width="1.4">
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
  <g fill="#7bd13f" opacity=".9">
    <circle cx="66" cy="75" r="2.4"/><circle cx="470" cy="75" r="2.4"/>
  </g>
</svg>';

    /** @var list<string> osm schémat; %A11Y% je místo pro přístupnostní atributy */
    private const MOTIVY = [
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m1s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m1p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m1t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7bd13f" stop-opacity="0"/>
      <stop offset="35%" stop-color="#7bd13f" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#7bd13f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m1p)"/>
  <rect width="640" height="400" fill="url(#m1s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <path d="M30 120h440M30 166h440"/><path d="M68 115v56M106 115v56M144 115v56M182 115v56M220 115v56M258 115v56M296 115v56M334 115v56M372 115v56M410 115v56M448 115v56" opacity=".55"/>
    <path d="M120 166v78M240 166v110M360 166v62"/>
    <path d="M103 244l8 20h18l8 -20z"/><path d="M112 256h16" opacity=".6"/><path d="M223 276l8 20h18l8 -20z"/><path d="M232 288h16" opacity=".6"/><path d="M343 228l8 20h18l8 -20z"/><path d="M352 240h16" opacity=".6"/>
    <g stroke="#7bd13f"><rect x="470" y="96" width="140" height="94" rx="6"/><path d="M516.6666666666666 96v94M563.3333333333334 96v94" opacity=".6"/><g stroke="#7bd13f"><circle cx="540" cy="143" r="26"/><path d="M540 143L566.0 143.0M540 143L553.0 165.5M540 143L527.0 165.5M540 143L514.0 143.0M540 143L527.0 120.5M540 143L553.0 120.5" opacity=".8"/><circle cx="540" cy="143" r="5.7"/></g></g>
  </g>
  <g fill="none" stroke="url(#m1t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m2s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m2p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m2t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#9a8de0" stop-opacity="0"/>
      <stop offset="35%" stop-color="#9a8de0" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#9a8de0" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m2p)"/>
  <rect width="640" height="400" fill="url(#m2s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <g><rect x="30" y="150" width="210" height="116" rx="6"/><path d="M82.5 150v116M135 150v116M187.5 150v116" opacity=".6"/></g>
    <g stroke="#9a8de0"><rect x="48" y="170" width="48" height="76" rx="3"/><path d="M60 170v76M72 170v76M84 170v76" opacity=".75"/></g>
    <g stroke="#9a8de0"><circle cx="196" cy="208" r="32"/><path d="M196 208L228.0 208.0M196 208L212.0 235.7M196 208L180.0 235.7M196 208L164.0 208.0M196 208L180.0 180.3M196 208L212.0 180.3" opacity=".8"/><circle cx="196" cy="208" r="7.0"/></g>
    <path d="M240 180h230M240 236h230"/><path d="M278 175v66M316 175v66M354 175v66M392 175v66M430 175v66" opacity=".55"/>
    <path d="M470 180H480A24 24 0 0 0 504 156V96"/><path d="M470 236H480A80 80 0 0 0 560 156V96"/>
    <path d="M490 96l14 -20h56l14 20z"/><path d="M502 87h60" opacity=".55"/>
  </g>
  <g fill="none" stroke="url(#m2t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m3s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m3p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m3t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7bd13f" stop-opacity="0"/>
      <stop offset="35%" stop-color="#7bd13f" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#7bd13f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m3p)"/>
  <rect width="640" height="400" fill="url(#m3s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <path d="M288 40v320M336 40v320"/><path d="M283 84h58M283 128h58M283 172h58M283 216h58M283 260h58M283 304h58M283 348h58" opacity=".55"/>
    <path d="M336 96h120M336 186h150M336 286h120"/>
    <path d="M336 78h120v36h-120M336 168h150v36h-150M336 268h120v36h-120"/>
    <g stroke="#7bd13f"><g><rect x="470" y="78" width="64" height="26" rx="5"/><path d="M480 104l-4 10M496 104l-4 10M512 104l-4 10M528 104l-4 10" stroke="#7bd13f"/></g><g><rect x="500" y="168" width="64" height="26" rx="5"/><path d="M510 194l-4 10M526 194l-4 10M542 194l-4 10M558 194l-4 10" stroke="#7bd13f"/></g><g><rect x="470" y="268" width="64" height="26" rx="5"/><path d="M480 294l-4 10M496 294l-4 10M512 294l-4 10M528 294l-4 10" stroke="#7bd13f"/></g></g>
  </g>
  <g fill="none" stroke="url(#m3t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m4s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m4p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m4t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#9a8de0" stop-opacity="0"/>
      <stop offset="35%" stop-color="#9a8de0" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#9a8de0" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m4p)"/>
  <rect width="640" height="400" fill="url(#m4s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <path d="M90 92h460a44 44 0 0 1 44 44v128a44 44 0 0 1-44 44H90a44 44 0 0 1-44-44V136a44 44 0 0 1 44-44z"/>
    <path d="M90 136h460a0 0 0 0 1 0 0v88a0 0 0 0 1 0 0H90" opacity=".35"/>
    <g stroke="#9a8de0"><circle cx="150" cy="180" r="40"/><path d="M150 180L190.0 180.0M150 180L170.0 214.6M150 180L130.0 214.6M150 180L110.0 180.0M150 180L130.0 145.4M150 180L170.0 145.4" opacity=".8"/><circle cx="150" cy="180" r="8.8"/></g>
    <g stroke="#9a8de0"><rect x="360" y="130" width="130" height="100" rx="4"/><path d="M376.25 130l-16.25 100M392.5 130l-16.25 100M408.75 130l-16.25 100M425 130l-16.25 100M441.25 130l-16.25 100M457.5 130l-16.25 100M473.75 130l-16.25 100" opacity=".6" clip-path="inset(0)"/></g>
    <path d="M300 92v-34M300 314v34" opacity=".5"/>
  </g>
  <g fill="none" stroke="url(#m4t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m5s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m5p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m5t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7bd13f" stop-opacity="0"/>
      <stop offset="35%" stop-color="#7bd13f" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#7bd13f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m5p)"/>
  <rect width="640" height="400" fill="url(#m5s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <g><rect x="30" y="120" width="130" height="120" rx="6"/><path d="M73.33333333333334 120v120M116.66666666666667 120v120" opacity=".6"/></g>
    <g stroke="#7bd13f"><circle cx="95" cy="180" r="34"/><path d="M95 180L129.0 180.0M95 180L112.0 209.4M95 180L78.0 209.4M95 180L61.0 180.0M95 180L78.0 150.6M95 180L112.0 150.6" opacity=".8"/><circle cx="95" cy="180" r="7.5"/></g>
    <path d="M160 152h420M160 208h420"/>
    <path d="M280 152v-46M280 208v46M420 152v-46M420 208v46M540 152v-46M540 208v46" opacity=".8"/>
    <g stroke="#7bd13f"><g><rect x="248" y="62" width="64" height="26" rx="5"/><path d="M258 88l-4 10M274 88l-4 10M290 88l-4 10M306 88l-4 10" stroke="#7bd13f"/></g><g><rect x="388" y="62" width="64" height="26" rx="5"/><path d="M398 88l-4 10M414 88l-4 10M430 88l-4 10M446 88l-4 10" stroke="#7bd13f"/></g><g><rect x="508" y="62" width="64" height="26" rx="5"/><path d="M518 88l-4 10M534 88l-4 10M550 88l-4 10M566 88l-4 10" stroke="#7bd13f"/></g></g>
    <g><path d="M263 254l8 20h18l8 -20z"/><path d="M272 266h16" opacity=".6"/><path d="M403 254l8 20h18l8 -20z"/><path d="M412 266h16" opacity=".6"/><path d="M523 254l8 20h18l8 -20z"/><path d="M532 266h16" opacity=".6"/></g>
  </g>
  <g fill="none" stroke="url(#m5t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m6s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m6p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m6t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#9a8de0" stop-opacity="0"/>
      <stop offset="35%" stop-color="#9a8de0" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#9a8de0" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m6p)"/>
  <rect width="640" height="400" fill="url(#m6s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <g><rect x="34" y="96" width="150" height="124" rx="6"/><path d="M34 112h150" opacity=".5"/><g stroke="#9a8de0"><circle cx="109" cy="166" r="38.75"/><path d="M109 166L147.8 166.0M109 166L128.4 199.6M109 166L89.6 199.6M109 166L70.3 166.0M109 166L89.6 132.4M109 166L128.4 132.4" opacity=".8"/><circle cx="109" cy="166" r="8.5"/></g></g>
    <path d="M184 136h86M184 180h86"/>
    <g><g><rect x="270" y="62" width="110" height="190" rx="55"/><path d="M282 84q43 14 86 0M282 113.2q43 14 86 0M282 142.4q43 14 86 0M282 171.6q43 14 86 0M282 200.8q43 14 86 0" stroke="#9a8de0" opacity=".85"/></g></g>
    <path d="M380 108h140v156"/>
    <g stroke="#9a8de0">
      <path d="M520 264H150a17 17 0 0 0 0 34h370a17 17 0 0 1 0 34H150"/>
    </g>
    <path d="M150 332h-46V148h-70" opacity=".6"/>
  </g>
  <g fill="none" stroke="url(#m6t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m7s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m7p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m7t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7bd13f" stop-opacity="0"/>
      <stop offset="35%" stop-color="#7bd13f" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#7bd13f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m7p)"/>
  <rect width="640" height="400" fill="url(#m7s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <path d="M30 150h90M30 238h90"/><path d="M74 145v98" opacity=".55"/>
    <g><rect x="120" y="130" width="330" height="128" rx="6"/><path d="" opacity=".6"/></g>
    <g stroke="rgba(255,255,255,.46)"><rect x="142" y="150" width="52" height="88" rx="3"/><path d="M159.33333333333334 150v88M176.66666666666666 150v88" opacity=".75"/></g>
    <g stroke="#7bd13f"><rect x="240" y="150" width="66" height="88" rx="3"/><path d="M251 150v88M262 150v88M273 150v88M284 150v88M295 150v88" opacity=".75"/></g>
    <g stroke="#7bd13f"><rect x="352" y="150" width="78" height="88" rx="3"/><path d="M360.6666666666667 150v88M369.3333333333333 150v88M378 150v88M386.6666666666667 150v88M395.3333333333333 150v88M404 150v88M412.6666666666667 150v88M421.3333333333333 150v88" opacity=".75"/></g>
    <path d="M450 150h160M450 238h160"/><path d="M494 145v98M538 145v98M582 145v98" opacity=".55"/>
    <path d="M142 268v26M240 268v26M352 268v26" opacity=".45"/>
    <path d="M120 294h340" opacity=".45"/>
  </g>
  <g fill="none" stroke="url(#m7t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
        '<svg class="motiv" %A11Y% viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="m8s" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0v32" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="m8p" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0%" stop-color="#17271b"/><stop offset="100%" stop-color="#0b130d"/>
    </linearGradient>
    <linearGradient id="m8t" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#9a8de0" stop-opacity="0"/>
      <stop offset="35%" stop-color="#9a8de0" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#9a8de0" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" fill="url(#m8p)"/>
  <rect width="640" height="400" fill="url(#m8s)"/>
  <g fill="none" stroke="rgba(255,255,255,.46)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    
    <g stroke="#9a8de0"><rect x="190" y="106" width="260" height="190" rx="4"/><path d="M222.5 106l-32.5 190M255 106l-32.5 190M287.5 106l-32.5 190M320 106l-32.5 190M352.5 106l-32.5 190M385 106l-32.5 190M417.5 106l-32.5 190" opacity=".6" clip-path="inset(0)"/></g>
    <path d="M30 130h160M30 170h160"/><path d="M70 125v50M110 125v50M150 125v50" opacity=".55"/>
    <path d="M450 130h160M450 170h160"/><path d="M490 125v50M530 125v50M570 125v50" opacity=".55"/>
    <path d="M30 232h160M30 272h160"/><path d="M70 227v50M110 227v50M150 227v50" opacity=".55"/>
    <path d="M450 232h160M450 272h160"/><path d="M490 227v50M530 227v50M570 227v50" opacity=".55"/>
    <path d="M190 106l-22-22M450 106l22-22M190 296l-22 22M450 296l22 22" opacity=".5"/>
  </g>
  <g fill="none" stroke="url(#m8t)" stroke-width="3" stroke-linecap="round">
    <path d="M0 372h640" stroke-dasharray="26 18">
      <animate attributeName="stroke-dashoffset" values="88;0" dur="3.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.4">
    <path d="M24 356h592M24 350v12M616 350v12"/>
  </g>
</svg>',
    ];

    public static function heroSchema(): string
    {
        return self::HERO;
    }

    /** Náhled realizace. Číslo motivu se cyklicky zarovná do rozsahu 1..8. */
    public static function motivRealizace(mixed $motiv = 1, array $volby = []): string
    {
        $cislo = (int) round(is_numeric($motiv) ? (float) $motiv : 1);
        $cislo = ((max(1, $cislo) - 1) % count(self::MOTIVY)) + 1;
        $popis = (string) ($volby['popis'] ?? '');
        $a11y = $popis !== ''
            ? 'role="img" aria-label="' . htmlspecialchars($popis, ENT_QUOTES, 'UTF-8') . '"'
            : 'aria-hidden="true" focusable="false"';

        return str_replace('%A11Y%', $a11y, self::MOTIVY[$cislo - 1]);
    }
}
