"""Akceptační test C-003 — src/lib/cms-store.mjs (demo administrace)."""
from __future__ import annotations

import pytest

FAKE_STORAGE = """
const store = new Map(Object.entries(A.seed || {}));
const storage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => { store.set(k, String(v)); },
  removeItem: (k) => { store.delete(k); },
};
"""

BASE = [
    {"id": "bytovy-dum-praha", "nazev": "Bytový dům Praha", "datum": "2026-04-01", "kategorie": "vzt"},
    {"id": "hala-milevsko", "nazev": "Hala Milevsko", "datum": "2025-06-01", "kategorie": "chlazeni"},
]


@pytest.fixture()
def js():
    from tests.jsmod import run_js

    def call(body, **args):
        return run_js("cms-store.mjs", FAKE_STORAGE + body, args={"base": BASE, **args})

    return call


def test_load_state_vraci_prazdny_stav_bez_dat(js):
    stav = js('out(m.loadState(storage));')
    assert stav["texts"] == {}
    assert stav["realizace"] == {"added": [], "edited": {}, "removed": []}


def test_load_state_prezije_rozbite_json(js):
    stav = js('out(m.loadState(storage));', seed={"gat-cms-v1": "{tohle není json"})
    assert stav["texts"] == {}


def test_save_a_load_prenesou_stav(js):
    hodnota = js(
        """
        let s = m.emptyState();
        s = m.setText(s, "cs", "hero.title", "Nový nadpis");
        m.saveState(storage, s);
        out(m.getText(m.loadState(storage), "cs", "hero.title"));
        """
    )
    assert hodnota == "Nový nadpis"


def test_set_text_prazdnou_hodnotou_maze_prepis(js):
    stav = js(
        """
        let s = m.setText(m.emptyState(), "cs", "a.b", "X");
        s = m.setText(s, "cs", "a.b", "");
        out(s.texts);
        """
    )
    assert stav == {"cs": {}}


def test_set_text_nemeni_puvodni_objekt(js):
    assert js(
        """
        const s0 = m.emptyState();
        m.setText(s0, "cs", "a", "X");
        out(s0.texts.cs === undefined || Object.keys(s0.texts.cs || {}).length === 0);
        """
    ) is True


def test_merge_texts_prepise_jen_zmenene_klice(js):
    vysledek = js(
        """
        const s = m.setText(m.emptyState(), "cs", "hero.title", "Přepsáno");
        out(m.mergeTexts(s, "cs", { "hero.title": "Původní", "hero.lead": "Zůstává" }));
        """
    )
    assert vysledek == {"hero.title": "Přepsáno", "hero.lead": "Zůstává"}


def test_merge_texts_ignoruje_jiny_jazyk(js):
    vysledek = js(
        """
        const s = m.setText(m.emptyState(), "en", "hero.title", "Overwritten");
        out(m.mergeTexts(s, "cs", { "hero.title": "Původní" }));
        """
    )
    assert vysledek == {"hero.title": "Původní"}


def test_slugify_prevede_cestinu_na_url(js):
    assert js('out(m.slugify("Výměna VZT — Školka Příbram 3"));') == "vymena-vzt-skolka-pribram-3"


def test_upsert_prideli_id_z_nazvu(js):
    polozka = js('out(m.upsertRealizace(m.emptyState(), { nazev: "Nová hala" }).realizace.added[0]);')
    assert polozka["id"] == "nova-hala"


def test_upsert_nove_id_nekoliduje(js):
    ids = js(
        """
        let s = m.upsertRealizace(m.emptyState(), { nazev: "Nová hala" });
        s = m.upsertRealizace(s, { nazev: "Nová hala" });
        out(s.realizace.added.map((r) => r.id));
        """
    )
    assert ids == ["nova-hala", "nova-hala-2"]


def test_upsert_existujiciho_id_ho_upravi_na_miste(js):
    added = js(
        """
        let s = m.upsertRealizace(m.emptyState(), { nazev: "Hala" });
        s = m.upsertRealizace(s, { id: "hala", nazev: "Hala – etapa 2" });
        out(s.realizace.added);
        """
    )
    assert len(added) == 1
    assert added[0]["nazev"] == "Hala – etapa 2"


def test_upsert_polozky_ze_zakladu_jde_do_edited(js):
    stav = js('out(m.upsertRealizace(m.emptyState(), { id: "hala-milevsko", nazev: "Jinak" }, A.base));')
    assert stav["realizace"]["added"] == []
    assert stav["realizace"]["edited"]["hala-milevsko"]["nazev"] == "Jinak"


def test_merge_realizace_radi_od_nejnovejsi_a_pridane_nahoru(js):
    ids = js(
        """
        let s = m.upsertRealizace(m.emptyState(), { nazev: "Nová", datum: "2026-09-01" });
        out(m.mergeRealizace(s, A.base).map((r) => r.id));
        """
    )
    assert ids == ["nova", "bytovy-dum-praha", "hala-milevsko"]


def test_merge_realizace_aplikuje_upravy_a_smazani(js):
    vysledek = js(
        """
        let s = m.upsertRealizace(m.emptyState(), { id: "bytovy-dum-praha", nazev: "Přejmenováno" }, A.base);
        s = m.removeRealizace(s, "hala-milevsko");
        out(m.mergeRealizace(s, A.base));
        """
    )
    assert [r["id"] for r in vysledek] == ["bytovy-dum-praha"]
    assert vysledek[0]["nazev"] == "Přejmenováno"
    assert vysledek[0]["kategorie"] == "vzt"


def test_remove_pridane_polozky_ji_vyhodi_z_added(js):
    stav = js(
        """
        let s = m.upsertRealizace(m.emptyState(), { nazev: "Dočasná" });
        s = m.removeRealizace(s, "docasna");
        out(s.realizace);
        """
    )
    assert stav["added"] == []
    assert stav["removed"] == []


def test_export_a_import_prenesou_stav(js):
    vysledek = js(
        """
        const s = m.setText(m.emptyState(), "cs", "hero.title", "Export");
        const vysledek = m.importJson(m.emptyState(), m.exportJson(s));
        out(vysledek);
        """
    )
    assert vysledek["ok"] is True
    assert vysledek["state"]["texts"]["cs"]["hero.title"] == "Export"


def test_import_rozbiteho_json_vrati_chybu(js):
    vysledek = js('out(m.importJson(m.emptyState(), "{{"));')
    assert vysledek["ok"] is False
    assert vysledek["error"]


def test_reset_state_smaze_ulozeny_klic(js):
    zbylo = js(
        """
        m.saveState(storage, m.setText(m.emptyState(), "cs", "a", "b"));
        m.resetState(storage);
        out(storage.getItem(m.STORAGE_KEY));
        """
    )
    assert zbylo is None


def test_save_state_zapisuje_cas_zmeny(js):
    assert js(
        """
        const s = m.saveState(storage, m.emptyState());
        out(typeof m.loadState(storage).updatedAt === "string");
        """
    ) is True
