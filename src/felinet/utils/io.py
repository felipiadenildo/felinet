"""Helpers de leitura/gravacao consistentes (JSON, CSV, NPZ).

Convencoes:
- UTF-8 com newline final
- ``indent=2, ensure_ascii=False`` para JSON
- ``cria pasta-pai`` antes de gravar
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


def gravar_json(dados: Any, caminho: Path) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, indent=2, ensure_ascii=False) + "\n"
    caminho.write_text(texto, encoding="utf-8")


def ler_json(caminho: Path) -> Any:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def gravar_csv(linhas: list[dict[str, Any]], caminho: Path, colunas: list[str]) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        for linha in linhas:
            writer.writerow(linha)


def gravar_npz(caminho: Path, **arrays: np.ndarray) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(caminho, **arrays)


def ler_npz(caminho: Path) -> dict[str, np.ndarray]:
    with np.load(Path(caminho), allow_pickle=False) as z:
        return {chave: z[chave] for chave in z.files}
