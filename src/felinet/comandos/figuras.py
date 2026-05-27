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


@app.command("comparativo-fontes")
def comparativo_fontes(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fontes: str = typer.Option(
        None,
        "--fontes",
        help="Lista separada por virgula (ex.: 'kaggle_cats,felidae'). "
        "Default: todas as fontes do perfil.",
    ),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Figura comparativa multifonte (Bloco 7).

    Gera PNG 300 DPI com dois painéis verticais. O painel superior mostra
    contagens absolutas (entradas, animais detectados, felis_catus) em
    escala simétrico-log; o painel inferior mostra as taxas relativas
    (animal/entradas e felis/animais) em percentual. Saída em
    ``artifacts/figuras/operacional/_global/comparativo_fontes.png``.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from felinet.comandos.tabelas import _latest_por_fase

    cfg = carregar_perfil(perfil)
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")

    if fontes:
        lista_fontes = [s.strip() for s in fontes.split(",") if s.strip()]
    else:
        lista_fontes = sorted((cfg.extras.get("fontes") or {}).keys())

    nomes: list[str] = []
    n_entradas: list[int] = []
    n_animais: list[int] = []
    n_felis: list[int] = []
    taxa_animal: list[float] = []
    taxa_felis: list[float] = []

    for fonte in lista_fontes:
        man_ing = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="ingestao"
        )
        man_det = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="deteccao"
        )
        man_cls = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="classificacao"
        )
        if man_ing is None and man_det is None and man_cls is None:
            LOG.warning(f"Fonte '{fonte}': sem runs operacionais (skip).")
            continue

        m_ing = (man_ing or {}).get("metricas_resumo") or {}
        m_det = (man_det or {}).get("metricas_resumo") or {}
        m_cls = (man_cls or {}).get("metricas_resumo") or {}
        ne = int(m_ing.get("n_entradas", 0) or 0)
        na = int(m_det.get("n_animais_detectados", 0) or 0)
        nc = int(m_cls.get("n_felis_catus", 0) or 0)
        nomes.append(fonte)
        n_entradas.append(ne)
        n_animais.append(na)
        n_felis.append(nc)
        taxa_animal.append(100.0 * na / ne if ne else 0.0)
        taxa_felis.append(100.0 * nc / na if na else 0.0)

    if not nomes:
        LOG.error("Nenhuma fonte com runs operacionais encontrada.")
        raise typer.Exit(code=1)

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True, dpi=300)
    x = np.arange(len(nomes))
    largura = 0.27

    ax_top.bar(x - largura, n_entradas, largura, label="entradas")
    ax_top.bar(x, n_animais, largura, label="animais detectados")
    ax_top.bar(x + largura, n_felis, largura, label="felis_catus")
    ax_top.set_yscale("symlog")
    ax_top.set_xticks(x, nomes, rotation=15)
    ax_top.set_ylabel("contagem (symlog)")
    ax_top.set_title("Volumes absolutos por fonte e fase")
    ax_top.legend(loc="upper right", fontsize=8)
    ax_top.grid(True, alpha=0.3, axis="y")

    ax_bot.bar(x - largura / 2, taxa_animal, largura, label="taxa animal (%)")
    ax_bot.bar(x + largura / 2, taxa_felis, largura, label="taxa felis_catus (%)")
    ax_bot.set_xticks(x, nomes, rotation=15)
    ax_bot.set_ylabel("taxa (%)")
    ax_bot.set_title("Taxas relativas (eficiência do filtro)")
    ax_bot.legend(loc="upper right", fontsize=8)
    ax_bot.grid(True, alpha=0.3, axis="y")
    ax_bot.set_ylim(0, 110)

    fig.suptitle("Comparativo entre fontes — pipeline operacional", fontsize=12)

    pasta = _pasta_artifacts(cfg, "operacional", "_global")
    pasta.mkdir(parents=True, exist_ok=True)
    saida_arq = saida or (pasta / "comparativo_fontes.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq}")


@app.command("matriz-confusao-fontes")
def matriz_confusao_fontes(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fontes: list[str] = typer.Option(
        None,
        "--fonte",
        help="Restringir a um subconjunto de fontes (default: todas com ground truth).",
    ),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Bloco 9: matriz de confusão Felis-vs-resto por fonte.

    Para cada fonte operacional, cruza as predições do classificador de
    espécie (fase 3) com o rótulo verdadeiro derivado de
    :mod:`felinet.datasets.labels_proxy`. Fontes monocategoria usam
    label-proxy de fonte (e.g. kaggle_cats ≈ Felis catus); fontes
    multicategoria (e.g. felidae) usam ``classe_origem`` registrada na
    ingestão. Imagens sem ground truth são contadas separadamente e
    excluídas da matriz.

    Saída: heatmap PNG 300 DPI em
    ``artifacts/figuras/operacional/_global/matriz_confusao_fontes.png``
    com painel por fonte (TP/FP/TN/FN normalizados) e tabela lateral com
    precisão, revocação e F1.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from felinet.comandos.tabelas import _latest_por_fase
    from felinet.datasets.labels_proxy import fontes_com_ground_truth
    from felinet.metricas.confusao_especie import (
        calcular_matriz,
        ler_classe_origem_de_run,
        ler_predicoes_de_run,
    )

    cfg = carregar_perfil(perfil)
    raiz_runs = getattr(cfg, "raiz_runs", raiz_projeto() / "runs")
    fontes_disponiveis = list((cfg.fontes or {}).keys()) if hasattr(cfg, "fontes") else []
    if not fontes:
        fontes = fontes_com_ground_truth(fontes_disponiveis) or [
            "kaggle_cats",
            "felidae",
        ]

    matrizes = []
    avisos: list[str] = []
    for f in fontes:
        run_cls_manifest = _latest_por_fase(
            raiz_runs, fonte=f, perfil_nome=perfil, prefixo_comando="classificacao"
        )
        run_ing_manifest = _latest_por_fase(
            raiz_runs, fonte=f, perfil_nome=perfil, prefixo_comando="ingestao"
        )
        if not run_cls_manifest:
            avisos.append(f"{f}: sem run de classificação")
            continue
        # Caminho da run: usa 'latest' como referencial estável
        run_dir = raiz_runs / "operacional" / f / perfil / "_" / "latest"
        predicoes = ler_predicoes_de_run(run_dir)
        if not predicoes:
            avisos.append(f"{f}: nenhuma predição lida em {run_dir}")
            continue
        classe_origem: dict[str, str] = {}
        if run_ing_manifest:
            classe_origem = ler_classe_origem_de_run(run_dir)
        matriz = calcular_matriz(f, predicoes, classe_origem)
        if matriz.total == 0:
            avisos.append(
                f"{f}: total=0 após cruzamento (todas as predições "
                f"ficaram sem ground truth — {matriz.sem_ground_truth} imagens)."
            )
            continue
        matrizes.append(matriz)

    if not matrizes:
        for av in avisos:
            LOG.warning(av)
        typer.echo(
            "matriz-confusao-fontes: nenhuma fonte com dados suficientes. "
            "Rode primeiro felinet pipeline executar nas fontes desejadas."
        )
        for av in avisos:
            typer.echo(f"  - {av}")
        return

    # ----- plotagem -----
    n = len(matrizes)
    fig, axes = plt.subplots(1, n, figsize=(3.4 * n + 1.6, 3.6), constrained_layout=True)
    if n == 1:
        axes = [axes]
    for ax, m in zip(axes, matrizes, strict=True):
        cm = np.array([[m.tp, m.fn], [m.fp, m.tn]], dtype=float)
        # normalizar por linha (taxa por classe verdadeira)
        soma_linhas = cm.sum(axis=1, keepdims=True)
        soma_linhas[soma_linhas == 0] = 1.0
        cm_norm = cm / soma_linhas
        im = ax.imshow(cm_norm, vmin=0, vmax=1, cmap="Blues")
        ax.set_xticks([0, 1], ["pred felis", "pred outros"], fontsize=9)
        ax.set_yticks([0, 1], ["verd felis", "verd outros"], fontsize=9)
        for i in range(2):
            for j in range(2):
                cor = "white" if cm_norm[i, j] > 0.5 else "black"
                ax.text(
                    j,
                    i,
                    f"{int(cm[i, j])}\n({cm_norm[i, j] * 100:.1f}%)",
                    ha="center",
                    va="center",
                    color=cor,
                    fontsize=9,
                )
        ax.set_title(
            f"{m.fonte}\n"
            f"P={m.precisao:.2f}  R={m.revocacao:.2f}  F1={m.f1:.2f}\n"
            f"n={m.total} (s/GT={m.sem_ground_truth})",
            fontsize=10,
        )
    fig.suptitle(
        "Matriz de confusão Felis catus vs. outros — por fonte",
        fontsize=12,
    )
    fig.colorbar(im, ax=axes, shrink=0.7, label="taxa por classe verdadeira")

    pasta = (
        cfg.artifacts_figuras_raiz / "operacional" / "_global"
        if hasattr(cfg, "artifacts_figuras_raiz")
        else raiz_projeto() / "artifacts" / "figuras" / "operacional" / "_global"
    )
    pasta.mkdir(parents=True, exist_ok=True)
    saida_arq = saida or (pasta / "matriz_confusao_fontes.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # também grava CSV com as métricas (útil para LaTeX)
    csv_arq = saida_arq.with_suffix(".csv")
    import csv as _csv

    with csv_arq.open("w", newline="", encoding="utf-8") as f:
        cabecalho = [
            "fonte",
            "tp",
            "fp",
            "tn",
            "fn",
            "sem_ground_truth",
            "total",
            "precisao",
            "revocacao",
            "f1",
            "acuracia",
        ]
        w = _csv.DictWriter(f, fieldnames=cabecalho)
        w.writeheader()
        for m in matrizes:
            w.writerow(m.como_dict())

    typer.echo(f"OK: {saida_arq}")
    typer.echo(f"     {csv_arq}")
    for av in avisos:
        typer.echo(f"aviso: {av}")


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


@app.command("galeria-erros")
def galeria_erros(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    n: int = typer.Option(200, "--n"),
    top_n_piores: int = typer.Option(
        5, "--piores", help="Quantas queries com erro mostrar (linhas)."
    ),
    top_k: int = typer.Option(3, "--top-k", help="Quantos candidatos por query (colunas)."),
    run: Path = typer.Option(None, "--run"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Galeria qualitativa de erros: queries com Top-1 errado + top-K candidatos.

    Mostra grade <top_n_piores> linhas x (1 + top_k) colunas:
        coluna 0 = query (borda azul);
        colunas 1..K = candidatos mais similares (borda verde se ID bater,
        vermelha se nao). Ordenadas pelas queries com Top-1 errado de maior
        similaridade (i.e., erros "mais confiantes" do modelo).
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

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
    vetores = dados["vetores"]
    ids = dados["ids"]
    splits = dados["splits"]
    if "caminhos" not in dados.files:
        LOG.error(
            "embeddings.npz nao contem 'caminhos'. Re-rode o pipeline (felinet reid extrair)"
            " para registrar os caminhos das imagens originais."
        )
        raise typer.Exit(code=2)
    caminhos = dados["caminhos"]

    mask_q = splits == "query"
    mask_g = splits == "gallery"
    eq, ig, iq = vetores[mask_q], ids[mask_g], ids[mask_q]
    eg = vetores[mask_g]
    cam_q, cam_g = caminhos[mask_q], caminhos[mask_g]

    if len(eq) == 0 or len(eg) == 0:
        LOG.error("Query ou galeria vazia.")
        raise typer.Exit(code=1)

    sim = eq @ eg.T  # (Nq, Ng)
    # Ordena galeria por similaridade decrescente para cada query
    ordem = np.argsort(-sim, axis=1)
    top1_ids = ig[ordem[:, 0]]
    top1_sim = np.take_along_axis(sim, ordem[:, :1], axis=1).ravel()
    acertou_top1 = top1_ids == iq

    # Queries com Top-1 errado, ordenadas por similaridade DECRESCENTE (erros confiantes)
    idx_errados = np.where(~acertou_top1)[0]
    if len(idx_errados) == 0:
        LOG.warning("Nenhum erro de Top-1 -- modelo acertou tudo. Galeria nao gerada.")
        raise typer.Exit(code=0)

    ordem_piores = idx_errados[np.argsort(-top1_sim[idx_errados])]
    selecionados = ordem_piores[:top_n_piores]
    n_linhas = len(selecionados)
    n_colunas = 1 + top_k

    fig, axes = plt.subplots(
        n_linhas,
        n_colunas,
        figsize=(2.2 * n_colunas, 2.4 * n_linhas),
        dpi=200,
    )
    if n_linhas == 1:
        axes = axes.reshape(1, -1)

    def _carregar(p: str) -> np.ndarray | None:
        try:
            return np.asarray(Image.open(p).convert("RGB"))
        except (OSError, ValueError) as exc:
            LOG.warning(f"Falha ao abrir {p}: {exc}")
            return None

    def _box(ax, cor: str) -> None:
        for spine in ax.spines.values():
            spine.set_edgecolor(cor)
            spine.set_linewidth(3.0)
        ax.set_xticks([])
        ax.set_yticks([])

    for linha, idx_q in enumerate(selecionados):
        # Coluna 0: query
        ax_q = axes[linha, 0]
        img_q = _carregar(str(cam_q[idx_q]))
        if img_q is not None:
            ax_q.imshow(img_q)
        ax_q.set_title(f"Query ID={iq[idx_q]}", fontsize=8)
        _box(ax_q, "#1f4e8a")  # azul

        # Colunas 1..K: candidatos
        for col, idx_g in enumerate(ordem[idx_q, :top_k], start=1):
            ax_c = axes[linha, col]
            img_c = _carregar(str(cam_g[idx_g]))
            if img_c is not None:
                ax_c.imshow(img_c)
            acerto = ig[idx_g] == iq[idx_q]
            cor = "#2a8a3e" if acerto else "#b13030"  # verde/vermelha
            ax_c.set_title(
                f"#{col} ID={ig[idx_g]} sim={sim[idx_q, idx_g]:.2f}",
                fontsize=7,
                color=cor,
            )
            _box(ax_c, cor)

    fig.suptitle(
        f"Galeria de erros - {fonte_efetiva} (N={n}) - {n_linhas} piores Top-1",
        fontsize=10,
        y=1.0,
    )
    fig.tight_layout()

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva, protocolo)
    saida_arq = saida or (pasta / "reid_galeria_erros.png")
    saida_arq.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida_arq, dpi=200, bbox_inches="tight")
    plt.close(fig)
    typer.echo(f"OK: {saida_arq} ({n_linhas} linhas x {n_colunas} cols)")
