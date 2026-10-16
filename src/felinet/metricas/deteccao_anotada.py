"""Fase II contra anotações de referência: o gato foi achado, achado com a classe errada ou perdido?

Cruza as caixas gravadas num run com as anotações do próprio dataset (formato YOLO: ``classe cx cy
w h`` normalizados, um ``.txt`` por imagem, como no ``samuelayman/cat-dataset``). Para cada animal
anotado, a melhor caixa por IoU define o desfecho:

* ``animal``: há caixa da classe animal com IoU >= limiar;
* ``classe_errada``: não há caixa animal, mas há caixa de pessoa ou veículo com IoU >= limiar;
* ``perdido``: nenhuma caixa cobre o animal.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path


def ler_yolo(caminho: Path) -> list[dict]:
    caixas = []
    for linha in Path(caminho).read_text(encoding="utf-8").split("\n"):
        partes = linha.split()
        if len(partes) == 5:
            cx, cy, w, h = map(float, partes[1:])
            caixas.append({"x": cx - w / 2, "y": cy - h / 2, "w": w, "h": h})
    return caixas


def iou(a: dict, b: dict) -> float:
    x0, y0 = max(a["x"], b["x"]), max(a["y"], b["y"])
    x1 = min(a["x"] + a["w"], b["x"] + b["w"])
    y1 = min(a["y"] + a["h"], b["y"] + b["h"])
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    uniao = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / uniao if uniao > 0 else 0.0


def desfecho(anotada: dict, caixas: list[dict], limiar: float = 0.5) -> str:
    def melhor(categorias: set[str]) -> float:
        return max(
            (iou(anotada, c["bbox"]) for c in caixas if c["categoria"] in categorias), default=0
        )

    if melhor({"animal"}) >= limiar:
        return "animal"
    if melhor({"person", "vehicle"}) >= limiar:
        return "classe_errada"
    return "perdido"


def cruzar(imagens: dict[str, dict], pasta_anotacoes: Path, limiar: float = 0.5) -> dict:
    """``imagens``: saída de ``figuras_exemplos.imagens_do_run``. Conta por animal anotado e por imagem."""
    por_animal, por_imagem = Counter(), Counter()
    for midia, r in imagens.items():
        rotulo = Path(pasta_anotacoes) / (Path(midia).stem + ".txt")
        if not rotulo.exists():
            por_imagem["sem_anotacao"] += 1
            continue
        desfechos = [desfecho(a, r["caixas"], limiar) for a in ler_yolo(rotulo)]
        por_animal.update(desfechos)
        sem_animal = not any(c["categoria"] == "animal" for c in r["caixas"])
        if sem_animal:
            por_imagem["sem_caixa_animal"] += 1
            if "classe_errada" in desfechos:
                por_imagem["sem_caixa_animal_com_gato_em_classe_errada"] += 1
    return {"limiar_iou": limiar, "por_animal": dict(por_animal), "por_imagem": dict(por_imagem)}
