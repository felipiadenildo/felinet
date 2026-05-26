"""Galeria visual didática para o modo ``--dev`` do pipeline.

A intenção do modo ``--dev`` é permitir inspeção humana do que cada fase do
pipeline aceitou, descartou e por quê. Esta implementação é deliberadamente
leve: cria a estrutura de subpastas e os CSVs de motivos por fase, e expõe
helpers (``desenhar_bbox``) que as fases podem usar opcionalmente para
salvar miniaturas com bbox sobreposta.

Layout produzido em ``run.raiz/dev_visualizacao/``::

    01_ingestao/motivos.csv
    02_deteccao/deteccoes.csv
    03_classificacao/classificacoes.csv

Cada CSV usa cabeçalho explícito e é seguro de gerar mesmo sem GPU/modelos
pesados (as fases que falharem por falta de modelo simplesmente não
adicionam linhas, mas o arquivo persiste).
"""

from __future__ import annotations

import csv
from pathlib import Path

CABECALHO_INGESTAO = ["nome_arq", "motivo", "detalhe"]
CABECALHO_DETECCAO = ["nome_arq", "n_bbox", "max_score", "decisao"]
CABECALHO_CLASSIFICACAO = ["nome_arq", "idx_crop", "classe", "score"]


def preparar_estrutura(raiz_run: Path) -> Path:
    """Cria ``raiz_run/dev_visualizacao/`` com subpastas e CSVs vazios.

    Retorna o ``Path`` da raiz da galeria.
    """
    base = raiz_run / "dev_visualizacao"
    subpastas = {
        "01_ingestao": CABECALHO_INGESTAO,
        "02_deteccao": CABECALHO_DETECCAO,
        "03_classificacao": CABECALHO_CLASSIFICACAO,
    }
    nomes_csv = {
        "01_ingestao": "motivos.csv",
        "02_deteccao": "deteccoes.csv",
        "03_classificacao": "classificacoes.csv",
    }
    base.mkdir(parents=True, exist_ok=True)
    for sub, header in subpastas.items():
        (base / sub).mkdir(parents=True, exist_ok=True)
        arq = base / sub / nomes_csv[sub]
        if not arq.exists():
            with arq.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)
    return base


def registrar_ingestao(
    base: Path, nome_arq: str, motivo: str, detalhe: str = ""
) -> None:
    """Acrescenta uma linha em ``01_ingestao/motivos.csv``.

    ``motivo`` é um slug curto (``aceita``, ``hash_dup``, ``formato_invalido``,
    ``corrompida``); ``detalhe`` é texto livre opcional.
    """
    arq = base / "01_ingestao" / "motivos.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, motivo, detalhe])


def registrar_deteccao(
    base: Path,
    nome_arq: str,
    n_bbox: int,
    max_score: float,
    decisao: str,
) -> None:
    """Acrescenta uma linha em ``02_deteccao/deteccoes.csv``.

    ``decisao`` ∈ {``com_animal``, ``sem_animal``, ``abaixo_limiar``}.
    """
    arq = base / "02_deteccao" / "deteccoes.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, n_bbox, f"{max_score:.3f}", decisao])


def registrar_classificacao(
    base: Path,
    nome_arq: str,
    idx_crop: int,
    classe: str,
    score: float,
) -> None:
    """Acrescenta uma linha em ``03_classificacao/classificacoes.csv``."""
    arq = base / "03_classificacao" / "classificacoes.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, idx_crop, classe, f"{score:.3f}"])


def desenhar_bbox(
    img_path: Path,
    bboxes: list[tuple[float, float, float, float]],
    scores: list[float],
    limiar: float,
    saida: Path,
    cor_aceita: str = "green",
    cor_recusa: str = "red",
) -> None:
    """Desenha bboxes em uma imagem e grava em ``saida``.

    Bboxes com ``score >= limiar`` saem em verde; abaixo do limiar em
    vermelho. Útil para popular ``02_deteccao/com_animal`` e
    ``02_deteccao/abaixo_limiar``.
    """
    from PIL import Image, ImageDraw

    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for (x1, y1, x2, y2), s in zip(bboxes, scores, strict=False):
        cor = cor_aceita if s >= limiar else cor_recusa
        draw.rectangle([x1, y1, x2, y2], outline=cor, width=3)
        draw.text((x1, max(0, y1 - 12)), f"{s:.2f}", fill=cor)
    saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, quality=85)
