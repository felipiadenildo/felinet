"""Subcomandos: felinet reid ...

Avaliacao METODOLOGICA (Fase IV isolada sobre PetFace) que gera as metricas
reportadas na monografia.

Para a cascata operacional, use ``felinet pipeline executar``.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.reid")


@app.command("extrair-embeddings")
def extrair_embeddings(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    n: int = typer.Option(200, "--n", help="Numero maximo de individuos do PetFace."),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Extrai embeddings MegaDescriptor para subset do PetFace.

    Saida default: ``<interim>/embeddings_petface_n{N:04d}.npz``.
    """
    import numpy as np
    from PIL import Image

    from felinet.datasets.petface import carregar_reidentification
    from felinet.pipeline.fase4_reid.megadescriptor import ExtratorMegaDescriptor

    cfg = carregar_perfil(perfil)
    arquivo_saida = saida or (cfg.interim / f"embeddings_petface_n{n:04d}.npz")

    registros = carregar_reidentification(cfg.raw_petface, max_individuos=n)
    LOG.info(f"PetFace: {len(registros)} registros (n={n})")
    extrator = ExtratorMegaDescriptor()

    vetores: list[np.ndarray] = []
    ids: list[str] = []
    splits: list[str] = []
    for reg in registros:
        img = Image.open(reg.caminho).convert("RGB")
        emb = extrator.extrair_de_pil(
            media_path=reg.caminho, bbox_indice=0, crop_img=img,
        )
        vetores.append(emb.vetor)
        ids.append(reg.individuo)
        splits.append(reg.split)

    matriz = np.stack(vetores).astype(np.float32)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        arquivo_saida,
        vetores=matriz,
        ids=np.array(ids),
        splits=np.array(splits),
    )
    typer.echo(f"OK: {len(vetores)} embeddings -> {arquivo_saida}")


@app.command("avaliar-closed")
def avaliar_closed(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    n: int = typer.Option(200, "--n"),
    saida: Path | None = typer.Option(None, "--saida"),
) -> None:
    """Avaliacao closed-set Re-ID (Top-K + CMC) sobre PetFace.

    Le o cache de embeddings (gerado por ``extrair-embeddings``) e
    escreve ``avaliacao_reid_petface_n{N:04d}_<timestamp>.json``.
    """
    import numpy as np

    from felinet.pipeline.fase4_reid.avaliacao import avaliar_closed_set

    cfg = carregar_perfil(perfil)
    arquivo_emb = cfg.interim / f"embeddings_petface_n{n:04d}.npz"
    if not arquivo_emb.exists():
        LOG.error(f"Cache de embeddings ausente: {arquivo_emb}")
        LOG.error("Rode antes: felinet reid extrair-embeddings --n %d", n)
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores = dados["vetores"]
    ids = dados["ids"]
    splits = dados["splits"]

    mascara_q = splits == "query"
    mascara_g = splits == "gallery"
    relatorio = avaliar_closed_set(
        embeddings_query=vetores[mascara_q],
        ids_query=ids[mascara_q],
        embeddings_galeria=vetores[mascara_g],
        ids_galeria=ids[mascara_g],
    )

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    arquivo_saida = saida or (
        cfg.processed / f"avaliacao_reid_petface_n{n:04d}_{timestamp}.json"
    )
    payload = {
        "n_individuos": int(n),
        "n_query": int(mascara_q.sum()),
        "n_galeria": int(mascara_g.sum()),
        "relatorio": asdict(relatorio),
        "timestamp": timestamp,
    }
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_saida.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # symlink latest
    latest = cfg.processed / "avaliacao_reid_petface_latest.json"
    latest.unlink(missing_ok=True)
    latest.symlink_to(arquivo_saida.name)
    typer.echo(f"OK: Top-1={relatorio.top_1:.3f} -> {arquivo_saida}")


@app.command("avaliar-openset")
def avaliar_openset(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    n: int = typer.Option(200, "--n"),
    frac_novos: float = typer.Option(0.50, "--frac-novos"),
    seeds: str = typer.Option("42,7,123", "--seeds"),
) -> None:
    """Avaliacao open-set Re-ID (AUC + thresholds) com multiplas seeds."""
    import numpy as np

    from felinet.pipeline.fase4_reid.avaliacao import (
        avaliar_open_set,
        particionar_ids_open_set,
    )

    cfg = carregar_perfil(perfil)
    arquivo_emb = cfg.interim / f"embeddings_petface_n{n:04d}.npz"
    if not arquivo_emb.exists():
        LOG.error(f"Cache de embeddings ausente: {arquivo_emb}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]

    seed_list = [int(s) for s in seeds.split(",")]
    por_seed = []
    for seed in seed_list:
        ids_conhecidos, ids_novos = particionar_ids_open_set(
            ids, frac_novos=frac_novos, seed=seed,
        )
        rel = avaliar_open_set(
            embeddings_query=vetores[splits == "query"],
            ids_query=ids[splits == "query"],
            embeddings_galeria=vetores[splits == "gallery"],
            ids_galeria=ids[splits == "gallery"],
            ids_conhecidos=ids_conhecidos,
            ids_novos=ids_novos,
        )
        por_seed.append({"seed": seed, "relatorio": asdict(rel)})

    aucs = [s["relatorio"]["auc"] for s in por_seed]
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    arquivo_saida = (
        cfg.processed / f"avaliacao_openset_petface_n{n:04d}_{timestamp}.json"
    )
    payload = {
        "n_individuos": int(n),
        "frac_novos": frac_novos,
        "seeds": seed_list,
        "auc_media": float(np.mean(aucs)),
        "auc_desvio": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0,
        "por_seed": por_seed,
        "timestamp": timestamp,
    }
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_saida.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    latest = cfg.processed / "avaliacao_openset_petface_latest.json"
    latest.unlink(missing_ok=True)
    latest.symlink_to(arquivo_saida.name)
    typer.echo(
        f"OK: AUC={np.mean(aucs):.3f}+/-{np.std(aucs, ddof=1):.3f} -> {arquivo_saida}"
    )
