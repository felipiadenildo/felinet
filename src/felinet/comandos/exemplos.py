"""Subcomandos: felinet exemplos ...

Execuções ilustrativas, fora dos experimentos da monografia, para mostrar o
funcionamento da cascata em imagens escolhidas (ex.: fauna do Campus 2).

* ``cascata``: roda as Fases II e III (MegaDetector v6 + SpeciesNet + decisor),
  com os mesmos wrappers e limiares dos experimentos, sobre uma pasta de
  imagens e grava ``resultados.json``. Requer o extra ``[modelos]``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.exemplos")

EXTENSOES = {".jpg", ".jpeg", ".png"}


@app.command("cascata")
def cascata(
    imagens: Path = typer.Option(..., "--imagens", help="Pasta com as imagens de entrada."),
    saida: Path = typer.Option(..., "--saida", help="Arquivo resultados.json a gravar."),
    confianca_deteccao: float = typer.Option(0.2, "--confianca-deteccao"),
    dispositivo: str = typer.Option("auto", "--dispositivo"),
    pais: str = typer.Option(
        None, "--pais", help="Filtro geográfico do SpeciesNet (ISO alfa-3, ex.: BRA)."
    ),
) -> None:
    """Fases II e III em cada imagem: caixas, top-5 do SpeciesNet e decisão."""
    from felinet.pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6
    from felinet.pipeline.fase3_classificacao.speciesnet import (
        ClassificadorSpeciesNet,
        crops_de_deteccao,
    )

    detector = DetectorMegaDetectorV6(dispositivo=dispositivo)
    from felinet.pipeline.fase3_classificacao.decisor import ConfigDecisor

    # Com filtro geográfico, rótulos como "cat family" vão para validação em vez de descarte.
    classificador = ClassificadorSpeciesNet(
        dispositivo=dispositivo,
        pais=pais,
        config_decisor=ConfigDecisor(ancestrais_para_validacao=bool(pais)),
    )
    arquivos = sorted(p for p in imagens.iterdir() if p.suffix.lower() in EXTENSOES)
    resultados = []
    for i, arq in enumerate(arquivos, 1):
        det = detector.detectar(arq, limite_confianca=confianca_deteccao)
        classes = {c.bbox_indice: c for c in map(classificador.classificar, crops_de_deteccao(det))}
        caixas = []
        for j, caixa in enumerate(det.deteccoes):
            cls = classes.get(j)
            caixas.append(
                {
                    "categoria": caixa.categoria,
                    "confianca": round(float(caixa.confianca), 4),
                    "bbox": {k: round(float(getattr(caixa.bbox, k)), 5) for k in "xywh"},
                    "status": cls.status if cls else None,
                    "top_k": [
                        {"especie": p.especie, "probabilidade": round(float(p.probabilidade), 4)}
                        for p in (cls.top_k if cls else [])
                    ],
                }
            )
        resultados.append(
            {"arquivo": arq.name, "largura": det.largura, "altura": det.altura, "caixas": caixas}
        )
        LOG.info("[%d/%d] %s: %d caixa(s)", i, len(arquivos), arq.name, len(caixas))
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        json.dumps(
            {
                "modelos": {
                    "deteccao": det.modelo if arquivos else None,
                    "classificacao": "SpeciesNet",
                },
                "confianca_deteccao": confianca_deteccao,
                "pais": pais,
                "resultados": resultados,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    typer.echo(f"OK: {len(resultados)} imagens -> {saida}")
