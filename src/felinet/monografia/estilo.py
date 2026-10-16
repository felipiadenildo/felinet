"""Estilo único das figuras da monografia.

Toda figura do relatório passa por aqui: mesma fonte do corpo do texto
(Latin Modern, embutida no PDF), tamanho físico igual ao de impressão
(a figura entra no LaTeX sem reescala), paleta fixa por papel, vírgula
decimal e rótulos em português. As figuras não têm título interno; a
legenda fica no LaTeX.

Paleta validada (validador da skill de visualização, modo claro):
categórica de 3 cores com todos os pares separáveis para daltonismo
(pior ΔE 9,2) e rampa ordinal azul de 3 passos.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

PASTA_FONTES = Path(__file__).parent / "fontes"
FAMILIA = "Latin Modern Roman"

CM = 1 / 2.54
# Largura útil do texto na USPSC (A4, margens 3 cm + 2 cm) e largura padrão
# das figuras de página inteira.
LARGURA_TEXTO_CM = 16.0
LARGURA_CHEIA_CM = 15.5

TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e3e2de"
FUNDO = "#ffffff"

# Cor por papel: a mesma entidade tem a mesma cor em todas as figuras.
COR = {
    "midias": "#2a78d6",  # mídias ingeridas (Fase I)
    "animal": "#eb6834",  # animal detectado (Fase II)
    "felis": "#1baf7a",  # aceito como F. catus (Fase III)
    "intra": "#2a78d6",  # pares da mesma identidade
    "inter": "#eb6834",  # pares de identidades diferentes
    "neutra": "#52514e",  # séries únicas, referência de acaso
    "validacao": "#eda100",  # caixa enviada à validação humana (Fase III)
    "outra": "#a3a29c",  # caixa de outra espécie (descartada na Fase III)
    "sem": "#ebeae6",  # imagem sem animal detectado (descartada na Fase II)
}
# Fontes comparadas lado a lado (azul x vermelho: separáveis para daltonismo).
COR_FONTE = {"kaggle_cats": "#2a78d6", "felidae": "#e34948"}
# Tamanho de catálogo é ordinal: rampa de um só matiz, clara -> escura.
RAMPA_N = {50: "#86b6ef", 100: "#2a78d6", 200: "#104281"}
# Rampa sequencial (mapa de calor), passos 100 -> 700 do azul de referência.
SEQUENCIAL = [
    "#ffffff", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
    "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]  # fmt: skip

FELIS = r"$\mathit{F.\,catus}$"

_configurado = False


def configurar() -> None:
    """Registra as fontes embutidas e aplica os parâmetros globais (idempotente)."""
    global _configurado
    if _configurado:
        return
    for arquivo in sorted(PASTA_FONTES.glob("*.otf")):
        font_manager.fontManager.addfont(str(arquivo))
    plt.rcParams.update(
        {
            "font.family": FAMILIA,
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "mathtext.fontset": "custom",
            "mathtext.rm": FAMILIA,
            "mathtext.it": f"{FAMILIA}:italic",
            "mathtext.bf": f"{FAMILIA}:bold",
            "mathtext.cal": FAMILIA,
            "text.color": TINTA,
            "axes.labelcolor": TINTA,
            "axes.edgecolor": TINTA_SECUNDARIA,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "grid.color": GRADE,
            "grid.linewidth": 0.5,
            "xtick.color": TINTA_SECUNDARIA,
            "ytick.color": TINTA_SECUNDARIA,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "lines.linewidth": 1.5,
            "lines.markersize": 4,
            "legend.frameon": False,
            "figure.facecolor": FUNDO,
            "axes.facecolor": FUNDO,
            "savefig.facecolor": FUNDO,
            # Type 3: contornos da Latin Modern (OTF/CFF) embutidos de forma que
            # qualquer leitor de PDF e o pdflatex aceitam (Type 42 declara CFF como TrueType).
            "pdf.fonttype": 3,
            "axes.unicode_minus": True,
        }
    )
    _configurado = True


def nova_figura(
    largura_cm: float = LARGURA_CHEIA_CM, altura_cm: float = 6.0, ncols: int = 1, nrows: int = 1
) -> tuple[Figure, list[Axes]]:
    """Cria figura no tamanho físico final; devolve sempre uma lista plana de eixos."""
    configurar()
    fig, eixos = plt.subplots(
        nrows,
        ncols,
        figsize=(largura_cm * CM, altura_cm * CM),
        layout="constrained",
        squeeze=False,
    )
    return fig, list(eixos.ravel())


def figura_vazia(largura_cm: float = LARGURA_CHEIA_CM, altura_cm: float = 6.0) -> Figure:
    """Figura no tamanho físico final, sem eixos (para grades não uniformes)."""
    configurar()
    return plt.figure(figsize=(largura_cm * CM, altura_cm * CM), layout="constrained")


def numero(valor: float, casas: int = 1) -> str:
    """Formata número em pt-BR (vírgula decimal, sem separador de milhar)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def eixo_virgula(eixo, casas: int = 1) -> None:
    """Aplica vírgula decimal aos rótulos de um eixo (``ax.xaxis`` ou ``ax.yaxis``)."""
    eixo.set_major_formatter(FuncFormatter(lambda v, _pos: numero(v, casas)))


def rotular_painel(ax: Axes, rotulo: str) -> None:
    """Escreve o rótulo do painel, ex.: ``(a)``, no canto superior esquerdo."""
    ax.text(-0.02, 1.02, rotulo, transform=ax.transAxes, ha="right", va="bottom", fontsize=9)


def barras_empilhadas(
    ax: Axes,
    linhas: list[tuple[float, str, list[tuple[float, str]], str]],
    rotulo_minimo: float = 0.07,
) -> None:
    """Barras horizontais de 100%: cada linha é um todo dividido em categorias.

    ``linhas``: ``(y, rótulo do eixo, [(contagem, cor), ...], texto à direita)``.
    As fatias têm um respiro branco entre si; a contagem é escrita dentro da
    fatia quando ela tem pelo menos ``rotulo_minimo`` da largura.
    """
    for y, _rotulo, segmentos, direita in linhas:
        total = sum(v for v, _ in segmentos) or 1.0
        inicio = 0.0
        for valor, cor in segmentos:
            frac = valor / total
            ax.barh(y, frac, left=inicio, height=0.62, color=cor, edgecolor=FUNDO, linewidth=1.0)
            if frac >= rotulo_minimo:
                ax.text(inicio + frac / 2, y, str(int(valor)), ha="center", va="center",
                        fontsize=7, color=TINTA)  # fmt: skip
            inicio += frac
        ax.text(1.015, y, direita, va="center", ha="left", fontsize=7.5, color=TINTA,
                transform=ax.get_yaxis_transform())  # fmt: skip
    ax.set_yticks([y for y, *_ in linhas], [r for _, r, *_ in linhas])
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{int(round(100 * v))}%"))
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)


def titulo_painel(ax: Axes, texto: str) -> None:
    """Título curto de painel, alinhado à esquerda (ex.: ``(a) Fase II: ...``)."""
    ax.set_title(texto, loc="left", fontsize=9, pad=4)


def salvar(fig: Figure, destino: Path) -> Path:
    """Salva em PDF vetorial reprodutível (sem data de criação nos metadados)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        destino,
        format="pdf",
        metadata={"Creator": "felinet", "Producer": "felinet", "CreationDate": None},
    )
    plt.close(fig)
    return destino
