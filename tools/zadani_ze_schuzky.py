"""C-008: Extrakce požadavků na web z přepisu schůzky (lokální model)."""
from __future__ import annotations

import logging
import os
import re
import sys
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LocalClient
# ---------------------------------------------------------------------------

class LocalClient:
    """HTTP klient pro lokální modelový server (pouze loopback)."""

    def __init__(self, base_url: str, model: str, timeout: float = 600.0) -> None:
        # Ověření loopback
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        host = parsed.hostname or ""
        if host not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError(
                f"base_url host '{host}' není loopback. "
                "Citlivý přepis nesmí opustit tento stroj."
            )
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str, **kwargs: Any) -> str:
        import httpx

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Odpověď neobsahuje žádné volby")
        return choices[0]["message"]["content"]


# ---------------------------------------------------------------------------
# rozdel_prepis
# ---------------------------------------------------------------------------

def rozdel_prepis(text: str, max_znaku: int) -> list[str]:
    """Rozdělí přepis na části podle řádků, žádná část nepřesáhne max_znaku."""
    if not text or not text.strip():
        return []

    casti: list[str] = []
    aktualni: list[str] = []
    aktualni_délka = 0

    for radek in text.splitlines():
        if aktualni and aktualni_délka + 1 + len(radek) > max_znaku:
            casti.append("\n".join(aktualni))
            aktualni = []
            aktualni_délka = 0
        if aktualni:
            aktualni_délka += 1 + len(radek)
        else:
            aktualni_délka = len(radek)
        aktualni.append(radek)

    if aktualni:
        casti.append("\n".join(aktualni))

    return casti


# ---------------------------------------------------------------------------
# sestav_prompt
# ---------------------------------------------------------------------------

def sestav_prompt(cast: str, poradi: int, celkem: int) -> str:
    """Sestaví český prompt pro extrakci požadavků na web."""
    return (
        "Jsi asistent, který z přepisu schůzky vytahuje požadavky na web.\n"
        f"Zpracovávám část {poradi} z {celkem} přepisu schůzky.\n\n"
        "Vypiš POUZE konkrétní požadavky na web, každý na samostatném řádku "
        "jako odrážku začínající '- '.\n"
        "Zákaz uvádět jména osob (jméno, příjmení), telefonní čísla, e-maily "
        "a jakékoli jiné osobní nebo kontaktní údaje.\n"
        "Pokud v této části žádný požadavek na web není, odpovìz prázdným řádkem.\n\n"
        "Text přepisu:\n"
        f"{cast}"
    )


# ---------------------------------------------------------------------------
# posbirej_body / sluc_body
# ---------------------------------------------------------------------------

def _odstrani_odrazku(radek: str) -> str:
    """Odstraní značku odrážky a následující mezery; vráti '' pokud není odrážka."""
    radek = radek.strip()
    if not radek:
        return ""
    if radek[0] in ("-", "*", "•"):
        return radek[1:].lstrip()
    m = re.match(r"^\d+\.\s*", radek)
    if m:
        return radek[m.end():].lstrip()
    return ""


def posbirej_body(odpoved: str) -> list[str]:
    """Vytáhne odrážky z odpovědi modelu; zahodí prázdné a duplicity."""
    body: list[str] = []
    videne: set[str] = set()
    for radek in odpoved.splitlines():
        text = _odstrani_odrazku(radek)
        if not text:
            continue
        klic = text.strip().lower()
        if klic in videne:
            continue
        videne.add(klic)
        body.append(text)
    return body


def sluc_body(seznamy: list[list[str]]) -> list[str]:
    """Spojí seznamy a odstraní duplicity (case-insensitive, první výskyt)."""
    slouceno: list[str] = []
    videne: set[str] = set()
    for seznam in seznamy:
        for bod in seznam:
            klic = bod.strip().lower()
            if klic in videne:
                continue
            videne.add(klic)
            slouceno.append(bod)
    return slouceno


# ---------------------------------------------------------------------------
# obsahuje_kontaktni_udaj
# ---------------------------------------------------------------------------

def obsahuje_kontaktni_udaj(radek: str) -> bool:
    """Pojistka: True, pokud řádek obsahuje e-mail, telefon nebo dlouhé číslo."""
    # e-mail
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", radek):
        return True
    # telefon v českém tvaru: +420/00420 + devět číslic (mezery povoleny)
    if re.search(r"(?:\+420|00420)[\s]?[0-9](?:[\s]?[0-9]){8}", radek):
        return True
    # samostatná skupina devíti a více číslic
    if re.search(r"(?<!\d)\d{9,}(?!\d)", radek):
        return True
    return False


# ---------------------------------------------------------------------------
# zpracuj
# ---------------------------------------------------------------------------

def zpracuj(text: str, client: Any, max_znaku: int = 6000, pokusy: int = 2) -> dict:
    """Zpracuje přepis: rozdělení, volání modelu, sběr a filtrace bodů."""
    if not text or not text.strip():
        return {"body": [], "vyrazeno": []}

    casti = rozdel_prepis(text, max_znaku)
    seznamy: list[list[str]] = []

    for i, cast in enumerate(casti, start=1):
        prompt = sestav_prompt(cast, i, len(casti))
        odpoved: str | None = None
        for _pokus in range(max(1, pokusy)):
            try:
                odpoved = client.complete(prompt)
                break
            except Exception:
                logger.exception(
                    "Volání modelu selhalo pro část %d/%d; zkusím znovu.",
                    i,
                    len(casti),
                )
                odpoved = None
        if odpoved is None:
            continue  # část přeskočena
        seznamy.append(posbirej_body(odpoved))

    slouceno = sluc_body(seznamy)
    bezpecne = [b for b in slouceno if not obsahuje_kontaktni_udaj(b)]
    vyrazeno = [b for b in slouceno if obsahuje_kontaktni_udaj(b)]
    return {"body": bezpecne, "vyrazeno": vyrazeno}


# ---------------------------------------------------------------------------
# zapis_markdown
# ---------------------------------------------------------------------------

def zapis_markdown(vysledek: dict, datum: str) -> str:
    """Sestaví markdown dokument s požadavky."""
    radeky: list[str] = []
    radeky.append(f"# Požadavky na web — {datum}")
    radeky.append("")
    radeky.append(
        "Požadavky vytažené z přepisu schůzky lokálním modelem."
    )
    radeky.append("")
    for bod in vysledek.get("body", []):
        radeky.append(f"- {bod}")
    vyrazeno = vysledek.get("vyrazeno", [])
    if vyrazeno:
        radeky.append("")
        radeky.append(
            f"Poznámka: {len(vyrazeno)} bod(ů) bylo vyřazeno, "
            "protože obsahovaly osobní nebo kontaktní údaje."
        )
    return "\n".join(radeky) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print(
            f"Usage: {sys.argv[0]} <prepis.md> <vystup.md> [datum]",
            file=sys.stderr,
        )
        sys.exit(1)

    vstup, vystup = sys.argv[1], sys.argv[2]
    datum = sys.argv[3] if len(sys.argv) == 4 else date.today().isoformat()

    with open(vstup, "r", encoding="utf-8") as f:
        text = f.read()

    base_url = os.environ.get("FACTORY_BASE_URL", "http://127.0.0.1:8080/v1")
    model = os.environ.get("FACTORY_MODEL", "qwen3.8-flash-next")
    klient = LocalClient(base_url=base_url, model=model)

    vysledek = zpracuj(text, klient)
    dokument = zapis_markdown(vysledek, datum)

    with open(vystup, "w", encoding="utf-8") as f:
        f.write(dokument)

    print(f"Vytaženo {len(vysledek['body'])} požadavků -> {vystup}")
