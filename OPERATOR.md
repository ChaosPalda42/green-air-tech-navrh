# OPERATOR — green-air-tech

## Co a proč
Návrh nového webu pro Green Air Tech s.r.o. (TZB) – statický vícejazyčný web CZ/EN/DE s animovanou grafikou proudění vzduchu, slovníkem zkratek, sekcí realizací a demo administrací

## Kde jsme
Viz STATE.md (generuje harness). Poslední shrnutí operátora: —

## Rozhodnutí
- 2026-09-23: projekt založen.

## Pravidla projektu
- Stack: python
- Testy: `uv run pytest -q`
- Nic nad rámec harnessu; obecná pravidla jsou v ~/factory/docs.

## Jak spustit
- `factory run` — spustí běh (kontrakty → workeři → brány → checkpointy)
- `factory status` — stav, otevřené balíčky
- `factory packets` — balíčky čekající na rozhodnutí; `factory answer <id> …`
