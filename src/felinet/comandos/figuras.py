"""Subcomandos: felinet figuras ...

Gera figuras 300 DPI para inclusao na monografia. Le dados do run latest
identificado por (modo, fonte, perfil, protocolo) em ``runs/latest/`` e
escreve PNG/PDF em ``artifacts/figuras/<modo>/<fonte>/<protocolo>/``.

Para forcar uma figura a partir de um run especifico (nao o latest),
use ``--run <caminho>``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, raiz_projeto
from felinet.logging_setup import obter_logger
from felinet.runs import resolver_latest

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.figuras")


def _resolver_run_metodologico(
    *,
    cfg,
    fonte: str | None,
    n: int,
    openset: bool,
    run: Path | None,
) -> tuple[Path, str, str]:
    """Retorna (caminho_run, fonte, protocolo)."""
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    protocolo = f"openset_n{n:04d}" if openset else f"n{n:04d}"
    if run:
        return Path(run), fonte_efetiva, protocolo
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    alvo = resolver_latest(
        modo="metodologico",
        fonte=fonte_efetiva,
        perfil=cfg.nome,
        protocolo=protocolo,
        raiz_runs=raiz_runs,
    )
    if alvo is None:
        raise typer.BadParameter(
            f"Nenhum run latest para metodologico/{fonte_efetiva}/{cfg.nome}/{protocolo}."
        )
    return alvo, fonte_efetiva, protocolo


def _pasta_artifacts(cfg, modo: str, fonte: str, protocolo: str | None = None) -> Path:
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_figuras_raiz") or "artifacts/figuras")
    partes = [modo, fonte]
    if protocolo:
        partes.append(protocolo)
    return raiz.joinpath(*partes)


@app.command("reid-cmc")
def reid_cmc(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    run: Path = typer.Option(None, "--run", help="Caminho explicito de um run."),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Curva CMC (Top-K vs K) a partir do run metodologico latest."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    raiz_run, fonte_efetiva, protocolo = _resolver_run_metodologico(
        cfg=cfg,
        fonte=fonte,
        n=n,
        openset=False,
        run=run,
    )
    arquivo = raiz_run / "metricas.json"
    if not arquivo.exists():
        LOG.error(f"metricas.json ausente em {raiz_run}")
        raise typer.Exit(code=1)

    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    cmc = payload["relatorio"]["cmc"]
    ks = np.arange(1, len(cmc) + 1)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    ax.plot(ks, np.asarray(cmc) * 100, marker="o", linewidth=1.5)
    ax.set_xlabel("Rank K")
    ax.set_ylabel("Acerto cumulativo (%)")
    ax.set_title(f"Curva CMC - {fonte_efetiva} (N={n})")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_cmc.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("matriz-similaridade")
def matriz_similaridade(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(50, "--n"),
    run: Path = typer.Option(None, "--run"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Heatmap de similaridade cosseno (query x galeria) do run latest."""
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    raiz_run, fonte_efetiva, protocolo = _resolver_run_metodologico(
        cfg=cfg,
        fonte=fonte,
        n=n,
        openset=False,
        run=run,
    )
    arquivo_emb = raiz_run / "07_embeddings.npz"
    if not arquivo_emb.exists():
        arquivo_emb = raiz_run / "embeddings.npz"
    if not arquivo_emb.exists():
        LOG.error(f"embeddings.npz ausente em {raiz_run}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, splits = dados["vetores"], dados["splits"]
    q = vetores[splits == "query"]
    g = vetores[splits == "gallery"]
    sim = q @ g.T

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    im = ax.imshow(sim, cmap="viridis", aspect="auto")
    ax.set_xlabel("Galeria (i)")
    ax.set_ylabel("Query (j)")
    ax.set_title(f"Similaridade cosseno - {fonte_efetiva} (N={n})")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_matriz_sim.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("cmc-comparativo")
def cmc_comparativo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    ns: str = typer.Option("50,200,500", "--ns", help="Lista CSV de Ns a sobrepor."),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Sobrepõe curvas CMC de múltiplos N em um único gráfico.

    Cada N gera uma curva colorida; eixo X = rank K, eixo Y = acerto (%).
    Le metricas.json do run latest de cada n{NNNN}.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    valores_n = [int(s) for s in ns.split(",")]

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    cores = plt.cm.viridis(np.linspace(0.15, 0.85, len(valores_n)))
    plotados = 0
    for n, cor in zip(valores_n, cores, strict=True):
        protocolo = f"n{n:04d}"
        alvo = resolver_latest(
            modo="metodologico",
            fonte=fonte_efetiva,
            perfil=cfg.nome,
            protocolo=protocolo,
            raiz_runs=raiz_runs,
        )
        if alvo is None:
            LOG.warning(f"N={n}: run latest ausente")
            continue
        arq = alvo / "metricas.json"
        if not arq.exists():
            LOG.warning(f"N={n}: metricas.json ausente em {alvo}")
            continue
        payload = json.loads(arq.read_text(encoding="utf-8"))
        cmc = payload["relatorio"]["cmc"]
        rel = payload["relatorio"]
        top1 = rel.get("top_k", {}).get("1", cmc[0] if cmc else 0.0)
        ks = np.arange(1, len(cmc) + 1)
        ax.plot(
            ks,
            np.asarray(cmc) * 100,
            marker="o",
            markersize=4,
            linewidth=1.5,
            color=cor,
            label=f"N={n} (Top-1={float(top1) * 100:.1f}%)",
        )
        plotados += 1

    if plotados == 0:
        LOG.error("Nenhum run encontrado para os Ns informados.")
        raise typer.Exit(code=1)

    ax.set_xlabel("Rank K")
    ax.set_ylabel("Acerto cumulativo (%)")
    ax.set_title(f"CMC comparativa - {fonte_efetiva}")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva)
    saida_arq = saida or (pasta / "reid_cmc_comparativo.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq} ({plotados} curvas)")


@app.command("dist-intra-inter")
def dist_intra_inter(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    run: Path = typer.Option(None, "--run"),
    saida: Path = typer.Option(None, "--saida"),
    bins: int = typer.Option(40, "--bins"),
) -> None:
    """Histograma de similaridades intra-classe vs inter-classe.

    Mostra a separação que o embedding consegue criar entre pares do
    mesmo gato (intra) e gatos diferentes (inter). Inclui linha vertical
    no EER, se disponível.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    raiz_run, fonte_efetiva, protocolo = _resolver_run_metodologico(
        cfg=cfg,
        fonte=fonte,
        n=n,
        openset=False,
        run=run,
    )
    arquivo_emb = raiz_run / "embeddings.npz"
    if not arquivo_emb.exists():
        arquivo_emb = raiz_run / "07_embeddings.npz"
    if not arquivo_emb.exists():
        LOG.error(f"embeddings.npz ausente em {raiz_run}")
        raise typer.Exit(code=1)

    dados = np.load(arquivo_emb, allow_pickle=True)
    vetores, ids, splits = dados["vetores"], dados["ids"], dados["splits"]
    q = vetores[splits == "query"]
    g = vetores[splits == "gallery"]
    ids_q = ids[splits == "query"]
    ids_g = ids[splits == "gallery"]

    if len(q) == 0 or len(g) == 0:
        LOG.error("Query ou galeria vazia.")
        raise typer.Exit(code=1)

    sim = q @ g.T  # (Nq, Ng)
    mascara_intra = ids_q[:, None] == ids_g[None, :]
    intra = sim[mascara_intra]
    inter = sim[~mascara_intra]

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    ax.hist(
        inter,
        bins=bins,
        alpha=0.55,
        color="#d96b6b",
        label=f"Inter-classe (n={len(inter)})",
        density=True,
        edgecolor="#7a3535",
        linewidth=0.3,
    )
    ax.hist(
        intra,
        bins=bins,
        alpha=0.65,
        color="#5b8def",
        label=f"Intra-classe (n={len(intra)})",
        density=True,
        edgecolor="#2c4d99",
        linewidth=0.3,
    )

    # Linha do EER, se houver run openset correspondente
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    alvo_os = resolver_latest(
        modo="metodologico",
        fonte=fonte_efetiva,
        perfil=cfg.nome,
        protocolo=f"openset_n{n:04d}",
        raiz_runs=raiz_runs,
    )
    if alvo_os and (alvo_os / "metricas.json").exists():
        os_pl = json.loads((alvo_os / "metricas.json").read_text(encoding="utf-8"))
        por_seed = os_pl.get("por_seed", [])
        if por_seed:
            taus = [float(s["relatorio"].get("tau_eer", 0.0)) for s in por_seed]
            tau_eer_medio = float(np.mean(taus))
            ax.axvline(
                tau_eer_medio,
                color="black",
                linestyle="--",
                linewidth=1.2,
                label=f"\u03c4 @ EER = {tau_eer_medio:.3f}",
            )

    ax.set_xlabel("Similaridade cosseno")
    ax.set_ylabel("Densidade")
    ax.set_title(f"Distribui\u00e7\u00e3o intra vs inter - {fonte_efetiva} (N={n})")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_dist_intra_inter.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("roc-openset")
def roc_openset(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Curva ROC open-set com banda de variação entre seeds.

    Le metricas.json do run latest openset_n<NNNN>; sobrepõe a curva
    de cada seed e desenha a média em destaque.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    protocolo = f"openset_n{n:04d}"
    alvo = resolver_latest(
        modo="metodologico",
        fonte=fonte_efetiva,
        perfil=cfg.nome,
        protocolo=protocolo,
        raiz_runs=raiz_runs,
    )
    if alvo is None or not (alvo / "metricas.json").exists():
        LOG.error(f"metricas.json openset ausente para N={n}")
        raise typer.Exit(code=1)

    payload = json.loads((alvo / "metricas.json").read_text(encoding="utf-8"))
    por_seed = payload.get("por_seed", [])
    if not por_seed:
        LOG.error("por_seed vazio no payload openset.")
        raise typer.Exit(code=1)

    # Interpola TPR em grade comum de FPR para poder calcular média/banda
    fpr_grid = np.linspace(0, 1, 200)
    tprs_interp = []
    fig, ax = plt.subplots(figsize=(6.0, 4.5), dpi=300)
    for s in por_seed:
        rel = s["relatorio"]
        fpr = np.asarray(rel.get("fpr_curve", []))
        tpr = np.asarray(rel.get("tpr_curve", []))
        if len(fpr) == 0:
            continue
        # garantir monotonia para interp
        ordem = np.argsort(fpr)
        fpr_o, tpr_o = fpr[ordem], tpr[ordem]
        tpr_int = np.interp(fpr_grid, fpr_o, tpr_o)
        tprs_interp.append(tpr_int)
        ax.plot(fpr, tpr, color="steelblue", alpha=0.25, linewidth=1.0)

    if not tprs_interp:
        LOG.error("Sem curvas ROC nos relatorios por_seed.")
        raise typer.Exit(code=1)

    tprs_arr = np.vstack(tprs_interp)
    tpr_media = tprs_arr.mean(axis=0)
    tpr_std = tprs_arr.std(axis=0)

    auc_media = float(payload.get("auc_media", 0.0))
    auc_desvio = float(payload.get("auc_desvio", 0.0))

    ax.fill_between(
        fpr_grid,
        tpr_media - tpr_std,
        tpr_media + tpr_std,
        alpha=0.20,
        color="steelblue",
        label="\u00b11 \u03c3 entre seeds",
    )
    ax.plot(
        fpr_grid,
        tpr_media,
        color="navy",
        linewidth=1.8,
        label=f"M\u00e9dia (AUC={auc_media:.3f}\u00b1{auc_desvio:.3f})",
    )
    ax.plot([0, 1], [0, 1], color="gray", linestyle=":", linewidth=0.8, label="Acaso")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_title(f"ROC open-set - {fonte_efetiva} (N={n}, seeds={len(tprs_interp)})")
    ax.legend(loc="lower right", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_roc_openset.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")
