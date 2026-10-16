"""Gráficos dos resultados (Cap. 5 e Apêndice E), no estilo único de ``estilo.py``.

Cada função recebe os dados já carregados e devolve a ``Figure``. Qual figura da
monografia cada função produz, e com quais dados, está em ``elementos.py``.
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import LinearSegmentedColormap, PowerNorm
from matplotlib.figure import Figure

from felinet.monografia import dados as d
from felinet.monografia import estilo as e

NS = (50, 100, 200)
# Nome de cada fonte como aparece no texto da monografia.
NOME_FONTE = {"felidae": "Felidae"}


def _inteiro(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


# ----------------------------------------------------------------------------
# Fases II e III
# ----------------------------------------------------------------------------


# Nomes em português das espécies que aparecem nos exemplos (rótulos do SpeciesNet).
ESPECIE_PT = {
    "domestic cat": "gato doméstico",
    "coyote": "coiote",
    "blank": "vazio",
    "northern raccoon": "guaxinim",
    "mammal": "mamífero",
    "bobcat": "lince-pardo",
    "puma": "puma",
    "grey fox": "raposa-cinzenta",
}

_LEGENDA_CASCATA = [
    ("Imagem com animal detectado", e.COR["animal"]),
    ("Imagem sem animal", e.COR["sem"]),
    (f"Caixa aceita como {e.FELIS}", e.COR["felis"]),
    ("Caixa para validação humana", e.COR["validacao"]),
    ("Caixa de outra espécie", e.COR["outra"]),
]


def _pct(v: float) -> str:
    return f"{e.numero(100 * v, 1)}%"


def _legenda_patches(ax, itens: list[tuple[str, str]], ncol: int) -> None:
    from matplotlib.patches import Patch

    ax.legend(
        handles=[Patch(facecolor=cor, label=rot) for rot, cor in itens],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=ncol,
        handlelength=1.0,
        columnspacing=1.2,
    )


def cascata_operacional(
    fontes: list[d.CascataOperacional],
    caixas: dict[str, list[d.CaixaClassificada]],
    exemplo: d.CaixaClassificada | None = None,
    nota_exemplo: str | None = None,
) -> Figure:
    """Fases II e III sobrepostas por fonte, na mesma escala de 0 a 100%.

    Para cada fonte, a linha da Fase II divide as imagens em com/sem animal e a
    da Fase III divide as caixas detectadas pela decisão do classificador
    (gato, validação humana, outra espécie). Lidas juntas, mostram a inversão:
    o Felidae tem animal em quase todas as imagens, mas quase nenhuma caixa vira
    gato. ``exemplo`` (opcional) é uma caixa mostrada ao lado, ligada à sua fatia;
    ``nota_exemplo``, o resultado da revisão visual dessa caixa.
    """
    fig = e.figura_vazia(altura_cm=7.6)
    com_exemplo = exemplo is not None and exemplo.recorte is not None
    grade = (
        fig.add_gridspec(1, 2, width_ratios=[2.3, 1.0]) if com_exemplo else fig.add_gridspec(1, 1)
    )
    ax = fig.add_subplot(grade[0, 0])
    linhas, cabecalhos = [], []
    y = 0.0
    pos_exemplo = None
    for f in fontes:
        cx = caixas[f.fonte]
        n_val = sum(c.status == "validacao_humana" for c in cx)
        n_out = sum(c.status == "outra_especie" for c in cx)
        nome = NOME_FONTE.get(f.fonte, f.fonte)
        cabecalhos.append((y + 0.62, nome))
        linhas.append(
            (
                y,
                f"Fase II: {f.midias} imagens",
                [
                    (f.imagens_com_animal, e.COR["animal"]),
                    (f.midias - f.imagens_com_animal, e.COR["sem"]),
                ],
                f"{_pct(f.taxa_animal)} com animal",
            )
        )
        linhas.append(
            (
                y - 0.8,
                f"Fase III: {f.caixas} caixas",
                [
                    (f.caixas_felis, e.COR["felis"]),
                    (n_val, e.COR["validacao"]),
                    (n_out, e.COR["outra"]),
                ],
                f"{_pct(f.taxa_felis)} aceitas como gato"
                + (f" ({f.caixas_felis} caixa)" if f.caixas_felis == 1 else ""),
            )
        )
        if com_exemplo and f.fonte == "felidae":
            pos_exemplo = y - 0.8
        y -= 2.3
    e.barras_empilhadas(ax, linhas)
    for yy, nome in cabecalhos:
        ax.text(0, yy, nome, fontsize=9, fontweight="bold", va="bottom", ha="left")
    if pos_exemplo is not None:
        # A fatia de uma caixa tem largura invisível; um marcador a torna visível.
        ax.plot([0.004], [pos_exemplo], marker="o", markersize=5, color=e.COR["felis"],
                markeredgecolor=e.FUNDO, markeredgewidth=0.8, clip_on=False, zorder=5)  # fmt: skip
    ax.set_ylim(y + 2.3 - 1.3, 1.1)
    _legenda_patches(ax, _LEGENDA_CASCATA, ncol=2)

    if com_exemplo:
        from matplotlib.patches import ConnectionPatch

        im_ax = fig.add_subplot(grade[0, 1])
        from PIL import Image

        from felinet.monografia.exemplos import realcar

        with Image.open(exemplo.recorte) as bruto:
            recorte, realcado = realcar(bruto.convert("RGB"))
        im_ax.imshow(recorte)
        im_ax.set_xticks([])
        im_ax.set_yticks([])
        im_ax.grid(False)
        for lado in im_ax.spines.values():
            lado.set_visible(True)
            lado.set_color(e.COR["felis"])
            lado.set_linewidth(1.5)
        top = "\n".join(
            f"{ESPECIE_PT.get(esp, esp)}: {e.numero(p, 2)}" for esp, p in exemplo.top_k[:3]
        )
        im_ax.set_title("Única caixa do Felidae\naceita como gato", fontsize=8, pad=4)
        nota = nota_exemplo or f"pasta de origem: {exemplo.classe_origem}"
        if realcado:
            nota += "\n(contraste realçado)"
        im_ax.set_xlabel(
            f"{nota}\nSpeciesNet, top-3:\n{top}",
            fontsize=7,
            labelpad=4,
        )
        if pos_exemplo is not None:
            fig.add_artist(
                ConnectionPatch(
                    # começa logo após o rótulo "(1 caixa)", à direita da barra
                    xyA=(1.67, pos_exemplo), coordsA=ax.get_yaxis_transform(), xyB=(-0.04, 0.5),
                    coordsB=im_ax.transAxes, arrowstyle="->", color=e.TINTA_SECUNDARIA,
                    linewidth=0.7,
                )
            )  # fmt: skip
    return fig


def cascatas_multifonte(linhas: list[dict]) -> Figure:
    """YOLOv8n + CLIP em quatro fontes, no mesmo desenho da cascata operacional.

    Fase II: imagens com/sem animal; Fase III: das imagens com animal, quantas
    foram aceitas como F. catus (definição da "Taxa gato", Tab. 9).
    """
    fig, (ax,) = e.nova_figura(altura_cm=10.0)
    barras, cabecalhos = [], []
    y = 0.0
    for r in linhas:
        n, animal, gato = (
            int(float(r[k])) for k in ("n_images", "n_images_with_animal", "n_classified_cat")
        )
        cabecalhos.append((y + 0.62, r["source"]))
        barras.append(
            (y, f"Fase II: {n} imagens", [(animal, e.COR["animal"]), (n - animal, e.COR["sem"])],
             f"{_pct(animal / n)} com animal")
        )  # fmt: skip
        barras.append(
            (y - 0.8, f"Fase III: {animal} com animal",
             [(gato, e.COR["felis"]), (animal - gato, e.COR["outra"])],
             f"{_pct(gato / animal if animal else 0)} aceitas como gato")
        )  # fmt: skip
        y -= 2.3
    e.barras_empilhadas(ax, barras)
    for yy, nome in cabecalhos:
        ax.text(0, yy, nome, fontsize=9, fontweight="bold", va="bottom", ha="left")
    ax.set_ylim(y + 2.3 - 1.3, 1.1)
    _legenda_patches(
        ax,
        [
            ("Imagem com animal detectado", e.COR["animal"]),
            ("Imagem sem animal", e.COR["sem"]),
            (f"Imagem aceita como {e.FELIS}", e.COR["felis"]),
            ("Imagem com animal não aceita", e.COR["outra"]),
        ],
        ncol=2,
    )
    return fig


def distribuicoes_cascata(
    caixas: dict[str, list[d.CaixaClassificada]], limiar: float = 0.5
) -> Figure:
    """Distribuição, por caixa, da confiança do detector e da probabilidade de gato doméstico.

    (a) confiança do MegaDetector nas caixas aceitas (limiar 0,2); (b) probabilidade
    de "gato doméstico" atribuída pelo SpeciesNet, com o limiar de aceitação do
    decisor (top-1 >= 0,5). Eixo y em fração das caixas de cada fonte.
    """
    fig, (a, b) = e.nova_figura(altura_cm=6.2, ncols=2)
    bordas_det = np.linspace(0.2, 1.0, 17)
    bordas_p = np.linspace(0.0, 1.0, 21)
    for fonte, cx in caixas.items():
        cor = e.COR_FONTE.get(fonte, e.COR["neutra"])
        nome = f"{NOME_FONTE.get(fonte, fonte)} ({len(cx)} caixas)"
        pesos = np.full(len(cx), 1 / len(cx))
        for ax, valores, bordas in (
            (a, [c.confianca_deteccao for c in cx], bordas_det),
            (b, [c.p_gato for c in cx], bordas_p),
        ):
            ax.hist(valores, bins=bordas, weights=pesos, color=cor, alpha=0.18)
            ax.hist(valores, bins=bordas, weights=pesos, histtype="step", color=cor, linewidth=1.2,
                    label=nome)  # fmt: skip
    b.axvline(limiar, color=e.TINTA_SECUNDARIA, linestyle=(0, (1, 2)), linewidth=0.7)
    b.annotate("limiar de aceitação", (limiar, b.get_ylim()[1] * 0.92), xytext=(4, 0),
               textcoords="offset points", fontsize=7, color=e.TINTA_SECUNDARIA)  # fmt: skip
    a.set_xlabel("Confiança do detector na caixa")
    b.set_xlabel("Probabilidade de gato doméstico (SpeciesNet)")
    a.set_ylabel("Fração das caixas")
    for ax in (a, b):
        e.eixo_virgula(ax.xaxis, 1)
        e.eixo_virgula(ax.yaxis, 2)
    a.legend(loc="upper left")
    e.titulo_painel(a, "(a)")
    e.titulo_painel(b, "(b)")
    return fig


def sensibilidade_limiar(linhas: list[dict], limiar_adotado: float = 0.2) -> Figure:
    """(a) taxa de imagens com animal e (b) confiança média, ambos contra o limiar."""
    fig, (a, b) = e.nova_figura(altura_cm=5.8, ncols=2)
    limiar = [float(r["threshold"]) for r in linhas]
    for ax, coluna, rotulo, faixa in (
        (a, "rate_animal", "Taxa de imagens com animal", (0.70, 1.0)),
        (b, "mean_score", "Confiança média das caixas aceitas", (0.65, 0.90)),
    ):
        valores = [float(r[coluna]) for r in linhas]
        ax.axvline(limiar_adotado, color=e.TINTA_SECUNDARIA, linestyle=(0, (1, 2)), linewidth=0.6)
        ax.plot(limiar, valores, marker="o", color=e.COR["animal"])
        ax.set_xlabel("Limiar de confiança do detector")
        ax.set_ylabel(rotulo)
        ax.set_ylim(*faixa)
        ax.set_xticks(limiar)
        e.eixo_virgula(ax.xaxis, 1)
        e.eixo_virgula(ax.yaxis, 2)
    a.annotate(
        f"limiar adotado ({e.numero(limiar_adotado, 1)})",
        (limiar_adotado, 0.72),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=7,
        color=e.TINTA_SECUNDARIA,
    )
    e.titulo_painel(a, "(a)")
    e.titulo_painel(b, "(b)")
    return fig


# ----------------------------------------------------------------------------
# Fase IV
# ----------------------------------------------------------------------------


def curvas_cmc(closed: dict[int, dict]) -> Figure:
    """acerto acumulado até o rank k para cada tamanho de catálogo."""
    fig, (ax,) = e.nova_figura(largura_cm=12.0, altura_cm=7.0)
    for n in sorted(closed):
        cmc = closed[n]["cmc"]
        ks = list(range(1, len(cmc) + 1))
        ax.plot(
            ks,
            cmc,
            marker="o",
            color=e.RAMPA_N[n],
            label=f"N = {n} (Top-1 = {e.numero(100 * cmc[0], 1)}%)",
        )
    ax.set_xlabel("Rank $k$")
    ax.set_ylabel("Acerto acumulado")
    ax.set_xticks(ks)
    ax.set_ylim(0.5, 0.9)
    e.eixo_virgula(ax.yaxis, 2)
    ax.legend(loc="lower right")
    return fig


def _cmap_sequencial() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("felinet_azul", e.SEQUENCIAL)


def matriz_similaridade(emb: d.EmbeddingsReid) -> Figure:
    """similaridade cosseno entre consultas (linhas) e galeria (colunas)."""
    q, _, g, _ = emb.consulta_galeria()
    sim = q @ g.T
    fig, (ax,) = e.nova_figura(largura_cm=13.0, altura_cm=8.0)
    # Potência 3 reserva os tons escuros para similaridades altas, onde está a diagonal.
    im = ax.imshow(
        sim, cmap=_cmap_sequencial(), norm=PowerNorm(gamma=3.0, vmin=0.0, vmax=1.0),
        aspect="auto", interpolation="nearest",
    )  # fmt: skip
    im.set_rasterized(True)
    ax.grid(False)
    ax.set_xlabel("Itens da galeria")
    ax.set_ylabel("Consultas")
    barra = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02)
    barra.set_label("Similaridade cosseno")
    barra.outline.set_visible(False)
    barra.set_ticks([0.0, 0.5, 0.7, 0.8, 0.9, 1.0])
    e.eixo_virgula(barra.ax.yaxis, 1)
    return fig


def similaridades_intra_inter(emb: d.EmbeddingsReid) -> tuple[np.ndarray, np.ndarray]:
    q, ids_q, g, ids_g = emb.consulta_galeria()
    sim = q @ g.T
    mesma = ids_q[:, None] == ids_g[None, :]
    return sim[mesma], sim[~mesma]


def distribuicao_intra_inter(
    emb: d.EmbeddingsReid, tau_eer: float | None = None, bins: int = 40
) -> Figure:
    """densidade das similaridades intra-identidade e inter-identidades."""
    intra, inter = similaridades_intra_inter(emb)
    fig, (ax,) = e.nova_figura(largura_cm=12.0, altura_cm=7.0)
    bordas = np.linspace(min(intra.min(), inter.min()), max(intra.max(), inter.max()), bins + 1)
    for valores, chave, rotulo in (
        (inter, "inter", f"Inter-identidades (n = {_inteiro(len(inter))})"),
        (intra, "intra", f"Intra-identidade (n = {_inteiro(len(intra))})"),
    ):
        ax.hist(valores, bins=bordas, density=True, color=e.COR[chave], alpha=0.22)
        ax.hist(
            valores, bins=bordas, density=True, histtype="step", color=e.COR[chave],
            linewidth=1.2, label=rotulo,
        )  # fmt: skip
    if tau_eer is not None:
        ax.axvline(
            tau_eer,
            color=e.COR["neutra"],
            linestyle=(0, (3, 2)),
            linewidth=0.9,
            label=rf"Limiar no EER ($\tau$ = {e.numero(tau_eer, 3)})",
        )
    ax.set_xlabel("Similaridade cosseno")
    ax.set_ylabel("Densidade")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.3)  # espaço para a legenda acima das barras
    e.eixo_virgula(ax.xaxis, 1)
    e.eixo_virgula(ax.yaxis, 1)
    ax.legend(loc="upper left", ncol=1)
    return fig


def curvas_roc_openset(openset: dict[int, dict]) -> Figure:
    """ROC open-set média entre sementes, uma curva por escala de catálogo.

    Uma só área de plotagem para comparar as escalas diretamente; o desvio-padrão
    entre sementes aparece na legenda (AUC média ± σ) e os pontos de operação
    (TPR a FPR = 1% e 5%) ficam na Tab. 12.
    """
    fig, (ax,) = e.nova_figura(largura_cm=11.0, altura_cm=9.0)
    grade = np.linspace(0, 1, 401)
    for n in sorted(openset):
        dados_n = openset[n]
        tprs = []
        for semente in dados_n["por_seed"]:
            rel = semente["relatorio"]
            fpr, tpr = np.asarray(rel["fpr_curve"]), np.asarray(rel["tpr_curve"])
            ordem = np.argsort(fpr, kind="stable")
            tprs.append(np.interp(grade, fpr[ordem], tpr[ordem]))
        ax.plot(
            grade,
            np.vstack(tprs).mean(axis=0),
            color=e.RAMPA_N[n],
            label=f"N = {n} (AUC = {e.numero(dados_n['auc_media'], 3)} ± "
            f"{e.numero(dados_n['auc_desvio'], 3)})",
        )
    ax.plot([0, 1], [0, 1], color=e.COR["neutra"], linestyle=(0, (1, 2)), linewidth=0.8,
            label="Acaso")  # fmt: skip
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.grid(True, axis="both")
    e.eixo_virgula(ax.xaxis, 1)
    e.eixo_virgula(ax.yaxis, 1)
    ax.set_xlabel("Taxa de falsos positivos (FPR)")
    ax.set_ylabel("Taxa de verdadeiros positivos (TPR)")
    ax.legend(loc="lower right")
    return fig


# Destaques do UMAP: 3 cores (separáveis em todos os pares) x 2 marcadores = 6 identidades.
_DESTAQUES = [(cor, m) for m in ("o", "^") for cor in ("#2a78d6", "#eb6834", "#1baf7a")]


def projecao_umap(linhas: list[dict]) -> Figure:
    """UMAP 2D por recorte; seis identidades destacadas por cor e forma, demais em cinza.

    Um gráfico de dispersão não comporta 20 cores distinguíveis (inclusive para daltonismo); as
    identidades destacadas são as de mais recortes (desempate pelo nome) e as demais ficam em cinza.
    """
    from collections import Counter

    contagem = Counter(r["identity"] for r in linhas)
    destaque = [i for i, _ in sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))][
        : len(_DESTAQUES)
    ]
    fig, (ax,) = e.nova_figura(largura_cm=12.0, altura_cm=9.0)
    outras = [r for r in linhas if r["identity"] not in destaque]
    ax.scatter(
        [float(r["x"]) for r in outras], [float(r["y"]) for r in outras], s=10, color="#c9c8c3",
        linewidths=0, label=f"Demais identidades ({len({r['identity'] for r in outras})})",
    )  # fmt: skip
    for (cor, marcador), ident in zip(_DESTAQUES, destaque, strict=False):
        pts = [r for r in linhas if r["identity"] == ident]
        ax.scatter(
            [float(r["x"]) for r in pts], [float(r["y"]) for r in pts], s=26, color=cor, marker=marcador,
            edgecolors=e.FUNDO, linewidths=0.6, label=f"Identidade {ident}",
        )  # fmt: skip
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=7)
    return fig
