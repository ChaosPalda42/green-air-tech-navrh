"""Responzivní obrázky – WebP + záložní formát."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def plan_sizes(width: int, targets: list[int]) -> list[int]:
    """Výběr cílových šířek pro daný obrázek.

    Z `targets` vezme ty, které jsou menší než `width`, a přidá `width`,
    pokud je menší nebo roven největšímu targetu; výsledek je vzestupně
    a bez duplicit.
    """
    result = sorted({t for t in targets if t < width})
    if width <= max(targets):
        result.append(width)
    return sorted(set(result))


def _has_transparency(img: Image.Image) -> bool:
    """Zjistí, zda obrázek obsahuje průhlednost."""
    if img.mode in ("RGBA", "LA"):
        return True
    if isinstance(img.info.get("transparency"), (bytes, str, int)):
        return True
    return False


def process_image(
    src: Path,
    out_dir: Path,
    widths: list[int],
    quality: int = 82,
) -> dict:
    """Zpracuje obrázek do všech požadovaných šířek."""
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(src)

    orig = Image.open(src)
    orig_w, orig_h = orig.size
    jmeno = src.stem
    zaloha = "png" if _has_transparency(orig) else "jpg"

    varianty = []
    for w in widths:
        h = round(w * orig_h / orig_w)
        resized = orig.resize((w, h), Image.LANCZOS)

        # WebP verze
        webp_name = f"{jmeno}-{w}.webp"
        resized.save(out_dir / webp_name, "WEBP", quality=quality, method=6)

        # Záložní verze
        if zaloha == "jpg":
            backup = resized.convert("RGB")
            backup_name = f"{jmeno}-{w}.jpg"
            backup.save(out_dir / backup_name, "JPEG", quality=quality, optimize=True)
        else:
            backup_name = f"{jmeno}-{w}.png"
            resized.save(out_dir / backup_name, "PNG", optimize=True)

        varianty.append({
            "w": w,
            "h": h,
            "webp": webp_name,
            "zaloha": backup_name,
        })

    orig.close()

    return {
        "name": jmeno,
        "zdroj": src.name,
        "zaloha": zaloha,
        "pomer": orig_w / orig_h,
        "varianty": varianty,
    }


def build_manifest(
    src_dir: Path,
    out_dir: Path,
    targets: list[int],
) -> dict:
    """Projde všechny obrázky ve src_dir a vygeneruje manifest."""
    src_dir = Path(src_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Najdi všechny podporované soubory (bez rekurze), seřazené podle jména
    files = sorted(
        f for f in src_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    manifest: dict[str, dict] = {}

    for src in files:
        jmeno = src.stem
        img = Image.open(src)
        orig_w = img.size[0]
        img.close()

        widths = plan_sizes(orig_w, targets)

        # Zkontroluj, zda už existují všechny varianty a jsou novější než zdroj
        skip = False
        if out_dir.exists():
            all_exist = True
            for v in widths:
                webp_path = out_dir / f"{jmeno}-{v}.webp"
                if not webp_path.exists() or webp_path.stat().st_mtime_ns <= src.stat().st_mtime_ns:
                    all_exist = False
                    break
            if all_exist:
                skip = True

        if skip:
            # Doplníme záznam ze skutečných rozměrů existujících souborů
            zaloha = "png"
            varianty = []
            for v in widths:
                webp_path = out_dir / f"{jmeno}-{v}.webp"
                backup_path = out_dir / f"{jmeno}-{v}.png"
                if not backup_path.exists():
                    backup_path = out_dir / f"{jmeno}-{v}.jpg"
                    zaloha = "jpg"
                if backup_path.exists():
                    backup_img = Image.open(backup_path)
                    h = backup_img.size[1]
                    backup_img.close()
                else:
                    h = round(v * img.size[1] / img.size[0])
                varianty.append({
                    "w": v,
                    "h": h,
                    "webp": f"{jmeno}-{v}.webp",
                    "zaloha": f"{jmeno}-{v}.{zaloha}",
                })
            manifest[jmeno] = {
                "name": jmeno,
                "zdroj": src.name,
                "zaloha": zaloha,
                "pomer": img.size[0] / img.size[1],
                "varianty": varianty,
            }
        else:
            zaznam = process_image(src, out_dir, widths, quality=82)
            manifest[jmeno] = zaznam

    return manifest


def srcset(zaznam: dict, druh: str, prefix: str = "") -> str:
    """Vygeneruje srcset atribut."""
    parts = []
    for v in zaznam["varianty"]:
        if druh == "webp":
            file = v["webp"]
        else:
            file = v["zaloha"]
        parts.append(f"{prefix}{file} {v['w']}w")
    return ", ".join(parts)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Použití: {sys.argv[0]} <src_dir> <out_dir>", file=sys.stderr)
        sys.exit(1)
    src_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    targets = [480, 960, 1440, 1920]
    manifest = build_manifest(src_dir, out_dir, targets)
    print(json.dumps(manifest, indent=2))
