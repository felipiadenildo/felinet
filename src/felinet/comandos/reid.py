"""Subcomandos: felinet reid ...

Avaliacao METODOLOGICA (Fase IV isolada sobre dataset com identidade rotulada)
que gera as metricas reportadas na monografia.

Fluxo:
    1. felinet reid extrair-embeddings --fonte petface --n 200
       -> runs/metodologico/petface/<perfil>/n0200/<gitsha>/embeddings.npz

    2. felinet reid avaliar-closed --fonte petface --n 200
       -> runs/metodologico/petface/<perfil>/n0200/<gitsha>/metricas.json

    3. felinet reid avaliar-openset --fonte petface --n 200
       -> runs/metodologico/petface/<perfil>/openset_n0200/<gitsha>/metricas.json

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


def _achar_embeddings(raiz_run: Path) -> Path | None:  # type: ignore[name-defined]
    """Aceita tanto embeddings.npz (novo) quanto 07_embeddings.npz (legado)."""
    from pathlib import Path
    for nome in ("embeddings.npz", "07_embeddings.npz"):
        p = Path(raiz_run) / nome
        if p.exists():
            return p
    return None


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
        
        def _extrair(caminho: Path) -> np.ndarray:
            img = Image.open(caminho).convert("RGB")
            emb = extrator.extrair_de_pil(
                media_path=caminho, bbox_indice=0, crop_img=img,
            )
            return emb.vetor
        
        for reg in registros:
            id_str = f"{reg.id_individuo:06d}"
            # 1 query por individuo
            vetores.append(_extrair(reg.query))
            ids.append(id_str)
            splits.append("query")
            # N galeria por individuo
            for caminho_g in reg.galeria:
                vetores.append(_extrair(caminho_g))
                ids.append(id_str)
                splits.append("gallery")

        matriz = np.stack(vetores).astype(np.float32)
        # Grava como embeddings.npz (nome canonico do layout runs/)
        np.savez(
            run.raiz / "embeddings.npz",
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
        {"run_path": str(run.raiz),
         "embeddings": str(run.raiz / "embeddings.npz"),
         "n_embeddings": len(vetores)},
        indent=2, ensure_ascii=False,
    ))


@app.command("avaliar-closed")
def avaliar_closed(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    k_max: int = typer.Option(10, "--k-max"),
    tag: str = typer.Option(None, "--tag", "-t"),
) -> None:
    """Avaliacao closed-set Re-ID (Top-K + CMC).

    Le embeddings.npz do run latest de
    ``metodologico/<fonte>/<perfil>/n<NNNN>/`` e escreve metricas.json
    em um novo run no mesmo protocolo.
    """
    import numpy as np

    from felinet.config import raiz_projeto
    from felinet.pipeline.fase4_reid.avaliacao import (
        avaliar_top_k,
        matriz_similaridade_cosseno,
    )

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
    arquivo_emb = _achar_embeddings(latest)
    if arquivo_emb is None:
        LOG.error(f"embeddings.npz nao encontrado em {latest}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]
    mascara_q = splits == "query"
    mascara_g = splits == "gallery"

    extras = {"comando": "reid avaliar-closed", "n": n, "k_max": k_max}
    run = criar_run(
        perfil=cfg, modo="metodologico", fonte=fonte_efetiva,
        protocolo=protocolo, tag=tag, extras=extras,
    )

    try:
        sim = matriz_similaridade_cosseno(vetores[mascara_q], vetores[mascara_g])
        relatorio = avaliar_top_k(
            similaridade=sim,
            ids_query=ids[mascara_q],
            ids_galeria=ids[mascara_g],
            k_max=k_max,
        )
        payload = {
            "n_individuos": int(n),
            "n_query": int(mascara_q.sum()),
            "n_galeria": int(mascara_g.sum()),
            "relatorio": relatorio.como_dicionario(),
        }
        run.metricas_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        top_1 = relatorio.top_k.get(1, 0.0)
        top_5 = relatorio.top_k.get(5, 0.0)
    except Exception as exc:  # noqa: BLE001
        finalizar_run(run, sucesso=False, mensagem=str(exc))
        raise

    finalizar_run(
        run, sucesso=True,
        metricas_resumo={"top_1": top_1, "top_5": top_5, "n": n},
    )
    typer.echo(json.dumps(
        {"run_path": str(run.raiz),
         "top_1": top_1, "top_5": top_5,
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
    arquivo_emb = _achar_embeddings(latest)
    if arquivo_emb is None:
        LOG.error(f"embeddings.npz nao encontrado em {latest}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]
    embeddings_q = vetores[splits == "query"]
    ids_q = ids[splits == "query"]
    embeddings_g_full = vetores[splits == "gallery"]
    ids_g_full = ids[splits == "gallery"]

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
            # particionar_ids_open_set: retorna (ids_catalogo, ids_novos)
            # avaliar_open_set espera APENAS ids_novos; a galeria deve ser
            # filtrada para excluir ids_novos do catalogo.
            _, ids_novos = particionar_ids_open_set(
                np.unique(ids), frac_novos=frac_novos, random_state=seed,
            )
            mascara_galeria_catalogo = np.array(
                [g not in ids_novos for g in ids_g_full]
            )
            rel = avaliar_open_set(
                embeddings_query=embeddings_q,
                embeddings_galeria=embeddings_g_full[mascara_galeria_catalogo],
                ids_query=ids_q,
                ids_galeria=ids_g_full[mascara_galeria_catalogo],
                ids_novos=ids_novos,
            )
            por_seed.append({"seed": seed, "relatorio": asdict(rel)})

        aucs = [s["relatorio"]["auc_roc"] for s in por_seed]
        tprs_01 = [s["relatorio"]["tpr_at_fpr_01"] for s in por_seed]
        tprs_05 = [s["relatorio"]["tpr_at_fpr_05"] for s in por_seed]
        payload = {
            "n_individuos": int(n), "frac_novos": frac_novos, "seeds": seed_list,
            "auc_media": float(np.mean(aucs)),
            "auc_desvio": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0,
            "tpr_at_fpr_01_media": float(np.mean(tprs_01)),
            "tpr_at_fpr_05_media": float(np.mean(tprs_05)),
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
            "tpr_at_fpr_01_media": payload["tpr_at_fpr_01_media"],
        },
    )
    typer.echo(json.dumps(
        {"run_path": str(run.raiz),
         "auc_media": payload["auc_media"], "auc_desvio": payload["auc_desvio"],
         "tpr_at_fpr_01_media": payload["tpr_at_fpr_01_media"]},
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
        if isinstance(resumo.get("top_1"), (int, float)):
            metrica = f"top1={resumo['top_1']:.3f}"
        elif isinstance(resumo.get("auc_media"), (int, float)):
            metrica = f"auc={resumo['auc_media']:.3f}"
        else:
            metrica = "?"
        typer.echo(
            f"[{sucesso}] {m.get('data_inicio', '?')} "
            f"{m.get('fonte', '?'):15s} {m.get('protocolo', '_'):12s} "
            f"git={m.get('git_sha', '?')} {metrica} -> {r.raiz}"
        )
