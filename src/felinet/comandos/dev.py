"""Subcomandos: felinet dev ...

Utilitarios de desenvolvimento. Nao usados na execucao oficial; servem
apenas para preparar/validar o ambiente dev.
"""
from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.dev")


@app.command("preparar-petface-mini")
def preparar_petface_mini(
    origem: Path = typer.Option(
        ..., "--origem",
        help="Caminho para o PetFace completo (e.g. /mnt/ssd/petface).",
    ),
    individuos: int = typer.Option(5, "--individuos", help="N de IDs a amostrar."),
    imagens_por_id: int = typer.Option(
        3, "--imagens-por-id", help="Imagens por individuo.",
    ),
) -> None:
    """Cria ``data/dev/petface_mini/`` com subset aleatorio do PetFace.

    Util para validar a Fase IV em ~10s sem acessar o SSD externo.
    """
    import shutil
    from random import Random

    cfg = carregar_perfil("dev")
    destino = cfg.raw_petface
    destino.mkdir(parents=True, exist_ok=True)

    if not origem.exists():
        LOG.error(f"Origem inexistente: {origem}")
        raise typer.Exit(code=1)

    rng = Random(42)
    ids = sorted(p for p in origem.iterdir() if p.is_dir())
    ids = rng.sample(ids, min(individuos, len(ids)))

    n_copiadas = 0
    for id_dir in ids:
        imgs = sorted(p for p in id_dir.glob("*") if p.suffix.lower() in {".jpg", ".png"})
        imgs = rng.sample(imgs, min(imagens_por_id, len(imgs)))
        dest_id = destino / id_dir.name
        dest_id.mkdir(exist_ok=True)
        for img in imgs:
            shutil.copy2(img, dest_id / img.name)
            n_copiadas += 1
    typer.echo(f"OK: {len(ids)} IDs x ~{imagens_por_id} imgs = {n_copiadas} -> {destino}")


@app.command("validar-ambiente")
def validar_ambiente() -> None:
    """Sanity check: verifica imports, modelos, perfis e GPU."""
    import importlib

    typer.echo("== felinet: validacao de ambiente ==")
    pacotes = ["torch", "numpy", "PIL", "yaml", "typer", "matplotlib"]
    for pkg in pacotes:
        try:
            mod = importlib.import_module(pkg)
            versao = getattr(mod, "__version__", "?")
            typer.echo(f"  [OK] {pkg:12s} {versao}")
        except ImportError as exc:
            typer.echo(f"  [!!] {pkg:12s} {exc}")

    try:
        import torch
        cuda = torch.cuda.is_available()
        dispositivo = torch.cuda.get_device_name(0) if cuda else "CPU"
        typer.echo(f"  [OK] CUDA disponivel: {cuda} ({dispositivo})")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"  [!!] torch/CUDA: {exc}")

    cfg_dev = carregar_perfil("dev")
    typer.echo(f"  [OK] Perfil dev raiz: {cfg_dev.raw_camera_trap.parent}")


@app.command("limpar-saidas-dev")
def limpar_saidas_dev(
    confirmar: bool = typer.Option(False, "--confirmar", help="Confirmacao explicita."),
) -> None:
    """Remove artefatos gerados pela cascata em ``data/dev/pipeline/0[2-8]_*``.

    NAO apaga ``01_brutas/`` (origem da cascata dev).
    """
    import shutil

    if not confirmar:
        typer.echo("Use --confirmar para prosseguir.")
        raise typer.Exit(code=0)

    cfg = carregar_perfil("dev")
    alvos = [
        cfg.saida_manifesto,
        cfg.saida_deteccoes,
        cfg.saida_classificacoes,
        cfg.saida_crops,
        cfg.saida_embeddings,
        cfg.saida_avaliacao_pipeline,
    ]
    for alvo in alvos:
        if alvo.is_dir():
            shutil.rmtree(alvo)
            typer.echo(f"removido: {alvo}/")
        elif alvo.is_file():
            alvo.unlink()
            typer.echo(f"removido: {alvo}")
    typer.echo("OK: saidas dev limpas (01_brutas preservada).")
