"""Subcomandos: felinet reid ...

Avaliacao METODOLOGICA (Fase IV isolada sobre dataset com identidade rotulada)
que gera as metricas reportadas na monografia.

Fluxo:
    1. felinet reid extrair-embeddings --fonte petface --n 200
       -> runs/metodologico/petface/<perfil>/n0200/<gitsha>/{embeddings.npz, manifest.json}

    2. felinet reid avaliar-closed --fonte petface --n 200
       -> mesmo run (ou novo se gitsha mudou): metricas.json, splits.json

    3. felinet reid avaliar-openset --fonte petface --n 200
       -> protocolo openset_n0200/<gitsha>/: metricas.json com auc, tpr@fpr.

Para a cascata operacional, use ``felinet pipeline executar``.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, resolver_fonte
from felinet.logging_setup import obter_logger
from felinet.runs import (
    criar_run,
    finalizar_run,
    listar_runs,
    resolver_latest,
)

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.reid")


def _protocolo_closed(n: int) -> str:
    return f"n{n:04d}"


def _protocolo_openset(n: int) -> str:
    return f"openset_n{n:04d}"


@app.command("extrair-embeddings")
def extrair_embeddings(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n", help="Numero maximo de individuos."),
    tag: str = typer.Option(None, "--tag", "-t"),
) -> None:
    """Extrai embeddings MegaDescriptor para subset N de uma fonte de Re-ID.

    Saida: ``runs/metodologico/<fonte>/<perfil>/n<NNNN>/<gitsha>[__<tag>]/embeddings.npz``.
    """
    import numpy as np
    from PIL import Image

    from felinet.datasets.petface import carregar_reidentification
    from felinet.pipeline.fase4_reid.megadescriptor import ExtratorMegaDescriptor

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_fonte = resolver_fonte(cfg, fonte_efetiva)

    extras = {"comando": "reid extrair-embeddings", "n": n}
    run = criar_run(
        perfil=cfg, modo="metodologico", fonte=fonte_efetiva,
        protocolo=_protocolo_closed(n), tag=tag, extras=extras,
    )
    LOG.info(f"Run: {run.raiz}")

    try:
        registros = carregar_reidentification(raiz_fonte, max_individuos=n)
        LOG.info(f"{fonte_efetiva}: {len(registros)} registros (n={n})")
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
        np.savez(
            run.embeddings_path,
            vetores=matriz, ids=np.array(ids), splits=np.array(splits),
        )
        n_query = int((np.array(splits) == "query").sum())
        n_gallery = int((np.array(splits) == "gallery").sum())
        run.splits_path.write_text(
            json.dumps(
                {"n_total": len(registros), "n_query": n_query, "n_galeria": n_gallery},
                indent=2, ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise

    finalizar_run(
        run, sucesso=True,
        metricas_resumo={
            "n_embeddings": len(vetores), "n_query": n_query, "n_galeria": n_gallery,
        },
    )
    typer.echo(json.dumps(
        {"run_path": str(run.raiz), "embeddings": str(run.embeddings_path),
         "n_embeddings": len(vetores)},
        indent=2, ensure_ascii=False,
    ))


@app.command("avaliar-closed")
def avaliar_closed(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    tag: str = typer.Option(None, "--tag", "-t"),
) -> None:
    """Avaliacao closed-set Re-ID (Top-K + CMC).

    Le ``embeddings.npz`` do run latest de
    ``metodologico/<fonte>/<perfil>/n<NNNN>/`` e escreve metricas.json
    no MESMO run (ou cria run novo se o gitsha mudou).
    """
    import numpy as np

    from felinet.config import raiz_projeto
    from felinet.pipeline.fase4_reid.avaliacao import avaliar_closed_set

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    protocolo = _protocolo_closed(n)

    latest = resolver_latest(
        modo="metodologico", fonte=fonte_efetiva, perfil=cfg.nome,
        protocolo=protocolo, raiz_runs=raiz_runs,
    )
    if latest is None:
        LOG.error(
            f"Embeddings ausentes para {fonte_efetiva}/{cfg.nome}/{protocolo}. "
            f"Rode antes: felinet reid extrair-embeddings --fonte {fonte_efetiva} --n {n}"
        )
        raise typer.Exit(code=1)
    arquivo_emb = latest / "07_embeddings.npz"
    if not arquivo_emb.exists():
        # compat: tambem aceita nome simples 'embeddings.npz'
        arquivo_emb = latest / "embeddings.npz"
    if not arquivo_emb.exists():
        LOG.error(f"embeddings.npz nao encontrado em {latest}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]
    mascara_q = splits == "query"
    mascara_g = splits == "gallery"

    extras = {"comando": "reid avaliar-closed", "n": n}
    run = criar_run(
        perfil=cfg, modo="metodologico", fonte=fonte_efetiva,
        protocolo=protocolo, tag=tag, extras=extras,
    )

    try:
        relatorio = avaliar_closed_set(
            embeddings_query=vetores[mascara_q], ids_query=ids[mascara_q],
            embeddings_galeria=vetores[mascara_g], ids_galeria=ids[mascara_g],
        )
        payload = {
            "n_individuos": int(n),
            "n_query": int(mascara_q.sum()),
            "n_galeria": int(mascara_g.sum()),
            "relatorio": asdict(relatorio),
        }
        run.metricas_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise

    finalizar_run(
        run, sucesso=True,
        metricas_resumo={"top_1": relatorio.top_1, "n": n},
    )
    typer.echo(json.dumps(
        {"run_path": str(run.raiz), "top_1": relatorio.top_1,
         "metricas": str(run.metricas_path)},
        indent=2, ensure_ascii=False,
    ))


@app.command("avaliar-openset")
def avaliar_openset(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    frac_novos: float = typer.Option(0.50, "--frac-novos"),
    seeds: str = typer.Option("42,7,123", "--seeds"),
    tag: str = typer.Option(None, "--tag", "-t"),
) -> None:
    """Avaliacao open-set Re-ID (AUC + thresholds) com multiplas seeds."""
    import numpy as np

    from felinet.config import raiz_projeto
    from felinet.pipeline.fase4_reid.avaliacao import (
        avaliar_open_set,
        particionar_ids_open_set,
    )

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    protocolo_closed = _protocolo_closed(n)

    latest = resolver_latest(
        modo="metodologico", fonte=fonte_efetiva, perfil=cfg.nome,
        protocolo=protocolo_closed, raiz_runs=raiz_runs,
    )
    if latest is None:
        LOG.error(
            f"Embeddings ausentes. Rode: felinet reid extrair-embeddings "
            f"--fonte {fonte_efetiva} --n {n}"
        )
        raise typer.Exit(code=1)
    arquivo_emb = latest / "07_embeddings.npz"
    if not arquivo_emb.exists():
        arquivo_emb = latest / "embeddings.npz"
    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]

    seed_list = [int(s) for s in seeds.split(",")]
    extras = {
        "comando": "reid avaliar-openset", "n": n,
        "frac_novos": frac_novos, "seeds": seed_list,
    }
    run = criar_run(
        perfil=cfg, modo="metodologico", fonte=fonte_efetiva,
        protocolo=_protocolo_openset(n), tag=tag, extras=extras,
    )

    try:
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
                ids_conhecidos=ids_conhecidos, ids_novos=ids_novos,
            )
            por_seed.append({"seed": seed, "relatorio": asdict(rel)})

        aucs = [s["relatorio"]["auc"] for s in por_seed]
        payload = {
            "n_individuos": int(n), "frac_novos": frac_novos, "seeds": seed_list,
            "auc_media": float(np.mean(aucs)),
            "auc_desvio": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0,
            "por_seed": por_seed,
        }
        run.metricas_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise

    finalizar_run(
        run, sucesso=True,
        metricas_resumo={
            "auc_media": payload["auc_media"], "auc_desvio": payload["auc_desvio"],
        },
    )
    typer.echo(json.dumps(
        {"run_path": str(run.raiz),
         "auc_media": payload["auc_media"], "auc_desvio": payload["auc_desvio"]},
        indent=2, ensure_ascii=False,
    ))


@app.command("listar")
def listar(
    perfil: str = typer.Option(None, "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    protocolo: str = typer.Option(None, "--protocolo"),
) -> None:
    """Lista runs metodologicos existentes em ``runs/``."""
    from felinet.config import raiz_projeto
    cfg = carregar_perfil(perfil) if perfil else None
    raiz_runs = raiz_projeto() / (
        (cfg.extras.get("raiz_runs") if cfg else None) or "runs"
    )
    registros = listar_runs(
        raiz_runs, modo="metodologico", fonte=fonte,
        perfil=cfg.nome if cfg else None, protocolo=protocolo,
    )
    if not registros:
        typer.echo("(nenhum run metodologico encontrado)")
        return
    for r in registros:
        m = r.manifest
        sucesso = "OK" if m.get("sucesso") else ("--" if m.get("sucesso") is None else "X")
        resumo = m.get("metricas_resumo") or {}
        metrica = (
            f"top1={resumo.get('top_1', '?'):.3f}"
            if isinstance(resumo.get("top_1"), (int, float))
            else f"auc={resumo.get('auc_media', '?')}"
        )
        typer.echo(
            f"[{sucesso}] {m.get('data_inicio', '?')} "
            f"{m.get('fonte', '?'):15s} {m.get('protocolo', '_'):12s} "
            f"git={m.get('git_sha', '?')} {metrica} -> {r.raiz}"
        )
