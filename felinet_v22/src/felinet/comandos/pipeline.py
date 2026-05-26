"""Subcomandos: felinet pipeline ...

Modo OPERACIONAL (cascata I -> II -> III -> IV) sobre as imagens brutas do
perfil ativo. Equivalente, em ``dev``, a executar manualmente:

    felinet ingestao executar --perfil dev
    felinet deteccao executar --perfil dev
    felinet classificacao executar --perfil dev
    felinet classificacao recortar --perfil dev
    felinet reid extrair-embeddings-cascata --perfil dev

Mas em uma chamada unica, com relatorio agregado.
"""
from __future__ import annotations

import json

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.pipeline")


@app.command("executar")
def executar(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
    confianca_deteccao: float = typer.Option(
        0.20, "--confianca-deteccao",
        help="Threshold do MegaDetector (default 0.20).",
    ),
) -> None:
    """Roda a cascata completa I -> II -> III -> IV usando o perfil ativo.

    Cada fase grava seu artefato no caminho configurado em ``paths.yaml``.
    Ao final, imprime um relatorio com contagens por fase.
    """
    from felinet.pipeline.orquestrador import executar_cascata

    cfg = carregar_perfil(perfil)
    LOG.info(f"Cascata iniciada (perfil={perfil})")
    relatorio = executar_cascata(cfg, confianca_min_deteccao=confianca_deteccao)

    typer.echo(json.dumps(relatorio.como_dicionario(), indent=2, ensure_ascii=False))
    if not relatorio.sucesso:
        raise typer.Exit(code=1)


@app.command("resumir")
def resumir(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
) -> None:
    """Imprime um resumo dos artefatos existentes no perfil ativo.

    Util para diagnosticar a partir de qual fase a cascata pode ser
    reexecutada.
    """
    cfg = carregar_perfil(perfil)
    checagens = [
        ("manifesto", cfg.saida_manifesto / "manifesto.csv"),
        ("deteccoes", cfg.saida_deteccoes / "deteccoes.json"),
        ("classificacoes", cfg.saida_classificacoes / "classificacoes.json"),
        ("crops", cfg.saida_crops),
        ("anotacao_identidade", cfg.anotacao_identidade),
        ("embeddings", cfg.saida_embeddings),
        ("avaliacao_pipeline", cfg.saida_avaliacao_pipeline),
    ]
    for nome, caminho in checagens:
        existe = caminho.exists()
        marca = "OK" if existe else "--"
        typer.echo(f"[{marca}] {nome:24s} {caminho}")
