"""Subcomandos: felinet classificacao ..."""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.classificacao")


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    deteccoes: Path | None = typer.Option(
        None, "--deteccoes", help="JSON com deteccoes (default: <saida_deteccoes>/deteccoes.json)."
    ),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Roda SpeciesNet sobre cada bbox 'animal' das deteccoes da Fase II.

    Mapeia o processo P4 do DFD. Para cada bbox, gera um item de
    classificacao com status (felis_catus / nao_felis_catus / indecidivel).
    """
    from felinet.pipeline.fase2_deteccao.schema import (
        ResultadoDeteccao,
    )
    from felinet.pipeline.fase2_deteccao.schema import (
        carregar_resultados_json as carregar_deteccoes,
    )
    from felinet.pipeline.fase3_classificacao.decisor import ConfigDecisor
    from felinet.pipeline.fase3_classificacao.schema import salvar_resultados_json
    from felinet.pipeline.fase3_classificacao.speciesnet import (
        ClassificadorSpeciesNet,
        CropEntrada,
    )

    cfg = carregar_perfil(perfil)
    arquivo_det = deteccoes or (cfg.saida_deteccoes / "deteccoes.json")
    arquivo_saida = saida or (cfg.saida_classificacoes / "classificacoes.json")

    if not arquivo_det.exists():
        LOG.error(f"Deteccoes nao encontradas: {arquivo_det}")
        raise typer.Exit(code=1)

    resultados: list[ResultadoDeteccao] = carregar_deteccoes(arquivo_det)
    classificador = ClassificadorSpeciesNet(config_decisor=ConfigDecisor())

    classificacoes = []
    for r in resultados:
        for i, det in enumerate(r.deteccoes):
            if det.categoria != "animal":
                continue
            entrada = CropEntrada(
                media_path=Path(r.media_path),
                bbox=det.bbox,
                indice=i,
            )
            classificacoes.append(classificador.classificar(entrada))

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    salvar_resultados_json(classificacoes, arquivo_saida)
    typer.echo(f"OK: {len(classificacoes)} classificacoes -> {arquivo_saida}")


@app.command("recortar")
def recortar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Persiste crops de bboxes classificadas como felis_catus.

    Le ``classificacoes.json`` e ``deteccoes.json`` do perfil ativo e
    grava arquivos PNG em ``<saida_crops>/``. As demais classificacoes
    sao movidas para ``rejeitadas_<motivo>/`` (apenas marcadores .txt).
    """
    from felinet.pipeline.fase2_deteccao.schema import (
        carregar_resultados_json as carregar_deteccoes,
    )
    from felinet.pipeline.fase3_classificacao.crops import persistir_crops_felis_catus
    from felinet.pipeline.fase3_classificacao.schema import (
        carregar_resultados_json as carregar_classificacoes,
    )

    cfg = carregar_perfil(perfil)
    arquivo_clf = cfg.saida_classificacoes / "classificacoes.json"
    arquivo_det = cfg.saida_deteccoes / "deteccoes.json"
    pasta_saida = saida or cfg.saida_crops

    classificacoes = carregar_classificacoes(arquivo_clf)
    resultados_det = carregar_deteccoes(arquivo_det)
    deteccoes_por_imagem = {
        str(r.media_path): [d.bbox for d in r.deteccoes] for r in resultados_det
    }

    crops = persistir_crops_felis_catus(
        classificacoes,
        deteccoes_por_imagem,
        pasta_saida,
    )
    typer.echo(f"OK: {len(crops)} crops persistidos -> {pasta_saida}")
