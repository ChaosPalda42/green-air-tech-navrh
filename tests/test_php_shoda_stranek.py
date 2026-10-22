"""Brána: PHP verze webu musí vyrobit tytéž bajty jako ukázka.

Ukázka v out/web je orákulum — 138 stránek ve třech jazycích, které Michael
viděl a schválil. Tohle je ta nejpřísnější možná odpověď na „bude to fungovat
jako v ukázce": ne „vypadá to podobně", ale shoda bajt na bajt.

Administrace je z diffu VYNECHANÁ záměrně: v ukázce je to nákres, který si
pamatuje změny v prohlížeči, na ostrém webu je to přihlášení, server a skutečná
data z Analytics. Má proto svoje vlastní testy, ne tenhle.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from tests import shoda

MIMO_DIFF = {"administrace.html"}


def stranky_k_diffu() -> list[str]:
    return [s for s in shoda.stranky() if s not in MIMO_DIFF]


def test_je_co_merit():
    """Kdyby se ukázka nepostavila, diff by byl zeleně prázdný — to nechceme."""
    seznam = stranky_k_diffu()
    assert len(seznam) == 138, f"čekal jsem 138 stránek k diffu, je jich {len(seznam)}"
    chybi = [s for s in seznam if not (shoda.UKAZKA / s).exists()]
    assert not chybi, f"ukázka není postavená (chybí {len(chybi)}): {chybi[:5]} — spusť `node build.mjs`"


def test_php_vyrobi_tytez_bajty():
    rozdily = shoda.rozdily(stranky_k_diffu())
    if rozdily:
        pytest.fail(
            f"{len(rozdily)} z 138 stránek se neshoduje s ukázkou:\n\n" + "\n\n".join(rozdily[:6]),
            pytrace=False,
        )


def test_administrace_se_vykresli():
    """Administrace se nediffuje, ale spadnout taky nesmí."""
    hotovo = subprocess.run(
        ["php", str(shoda.KOREN / "tools" / "vykresli.php"), "administrace.html"],
        cwd=shoda.KOREN,
        capture_output=True,
        text=True,
    )
    assert hotovo.returncode == 0, f"administrace.html se nevykreslila:\n{hotovo.stderr[:800]}"
    assert hotovo.stdout.startswith("<!doctype html>")
