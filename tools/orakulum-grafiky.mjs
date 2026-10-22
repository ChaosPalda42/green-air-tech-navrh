/* Orákulum pro ikony, motivy a hero schéma: co vrací ukázka pro každou ikonu
   a každý motiv, včetně přístupnostních atributů. */
import { writeFile } from "node:fs/promises";
import { ikona, nazvyIkon } from "../src/templates/ikony.mjs";
import { motivRealizace } from "../src/templates/motivy.mjs";
import { heroSchema } from "../src/templates/grafika.mjs";

const data = { ikona: [], motivRealizace: [], heroSchema: [] };

for (const n of nazvyIkon) {
  data.ikona.push({ args: [n, {}], out: ikona(n, {}) });
}
for (const volby of [{ trida: "ikona-velka" }, { velikost: 18 }, { popis: "Vzduchotechnika" },
                     { trida: "a b", velikost: 32, popis: "Servis" }]) {
  data.ikona.push({ args: ["sip", volby], out: ikona("sip", volby) });
}
for (let i = 1; i <= 10; i++) {
  data.motivRealizace.push({ args: [i, {}], out: motivRealizace(i, {}) });
}
data.motivRealizace.push({ args: [3, { popis: "Poliklinika Písek" }], out: motivRealizace(3, { popis: "Poliklinika Písek" }) });
data.motivRealizace.push({ args: [0, {}], out: motivRealizace(0, {}) });
data.heroSchema.push({ args: [], out: heroSchema() });

await writeFile(new URL("../tests/orakulum/grafika.json", import.meta.url), JSON.stringify(data, null, 1));
console.log(`grafika.json: ${data.ikona.length} ikon, ${data.motivRealizace.length} motivů, hero schéma`);
