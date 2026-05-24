"""Baixa imagens-amostra de gatos para validação manual do detector.

URLs do Wikimedia Commons (CC-BY-SA). Usa URLs originais (sem /thumb/)
pois a Wikimedia bloqueia thumbnails arbitrários desde 2025.

Uso:
    python 03_codigo/scripts/baixar_amostras.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

AMOSTRAS = [
    (
        "gato_01_externo.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/4/4d/Cat_November_2010-1a.jpg",
    ),
    (
        "gato_02_rua.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg",
    ),
    (
        "gato_03_grama.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/2/25/Siam_lilacpoint.jpg",
    ),
]


def baixar() -> None:
    raiz = Path(__file__).resolve().parents[2]
    destino = raiz / "04_dados" / "raw" / "amostras_dev"
    destino.mkdir(parents=True, exist_ok=True)

    for nome, url in AMOSTRAS:
        alvo = destino / nome
        if alvo.exists():
            print(f"[skip] {nome} já existe")
            continue
        print(f"[baixando] {nome}")
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "tcc-gatos-campus2/0.1 "
                    "(https://github.com/felipiadenildo; "
                    "felipiadenildo@gmail.com)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp, alvo.open("wb") as f:
            f.write(resp.read())
        print(f"   ok ({alvo.stat().st_size // 1024} KiB)")

    print(f"\nAmostras em: {destino}")


if __name__ == "__main__":
    try:
        baixar()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
