"""Akceptační test C-006 — tools/optimize_images.py (responzivní obrázky)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def tool():
    sys.path.insert(0, str(ROOT))
    from tools import optimize_images

    return optimize_images


@pytest.fixture()
def zdroje(tmp_path):
    from PIL import Image

    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (1600, 900), (40, 120, 30)).save(src / "hala.jpg", quality=95)
    Image.new("RGB", (480, 320), (200, 200, 200)).save(src / "maly.jpg", quality=95)
    Image.new("RGBA", (300, 300), (0, 0, 0, 0)).save(src / "odznak.png")
    return src


def test_plan_sizes_nenafukuje_original(tool):
    assert tool.plan_sizes(1600, [480, 960, 1440, 1920]) == [480, 960, 1440, 1600]


def test_plan_sizes_maleho_obrazku(tool):
    assert tool.plan_sizes(400, [480, 960]) == [400]


def test_plan_sizes_nevraci_duplicity(tool):
    assert tool.plan_sizes(960, [480, 960, 1440]) == [480, 960]


def test_process_image_zapise_webp_i_zalozni_jpg(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    zaznam = tool.process_image(zdroje / "hala.jpg", out, [480, 960])
    soubory = sorted(p.name for p in out.iterdir())
    assert soubory == ["hala-480.jpg", "hala-480.webp", "hala-960.jpg", "hala-960.webp"]
    assert zaznam["name"] == "hala"
    assert [v["w"] for v in zaznam["varianty"]] == [480, 960]
    assert zaznam["pomer"] == pytest.approx(1600 / 900, rel=1e-3)


def test_process_image_zachova_pomer_stran(tool, zdroje, tmp_path):
    from PIL import Image

    out = tmp_path / "out"
    tool.process_image(zdroje / "hala.jpg", out, [960])
    assert Image.open(out / "hala-960.webp").size == (960, 540)


def test_process_image_pruhledne_png_zustane_png(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    zaznam = tool.process_image(zdroje / "odznak.png", out, [300])
    assert (out / "odznak-300.png").exists()
    assert (out / "odznak-300.webp").exists()
    assert zaznam["zaloha"] == "png"


def test_webp_je_mensi_nez_zaloha(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    tool.process_image(zdroje / "hala.jpg", out, [960])
    assert (out / "hala-960.webp").stat().st_size <= (out / "hala-960.jpg").stat().st_size


def test_build_manifest_zpracuje_celou_slozku(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    manifest = tool.build_manifest(zdroje, out, [480, 960])
    assert sorted(manifest) == ["hala", "maly", "odznak"]
    assert [v["w"] for v in manifest["maly"]["varianty"]] == [480]


def test_build_manifest_neprepisuje_uz_hotove(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    tool.build_manifest(zdroje, out, [480])
    razitko = (out / "hala-480.webp").stat().st_mtime_ns
    tool.build_manifest(zdroje, out, [480])
    assert (out / "hala-480.webp").stat().st_mtime_ns == razitko


def test_srcset_slozi_atribut(tool, zdroje, tmp_path):
    out = tmp_path / "out"
    zaznam = tool.process_image(zdroje / "hala.jpg", out, [480, 960])
    assert tool.srcset(zaznam, "webp", "img/") == "img/hala-480.webp 480w, img/hala-960.webp 960w"
    assert tool.srcset(zaznam, "zaloha", "img/") == "img/hala-480.jpg 480w, img/hala-960.jpg 960w"
