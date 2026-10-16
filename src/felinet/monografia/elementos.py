"""Registro de tudo o que a monografia recebe do felinet.

Cada ``Elemento`` liga um rótulo do LaTeX (``\\label``) a um arquivo em
``<monografia>/elementos/gerados/`` e à função que o produz. ``felinet monografia gerar``
percorre esta lista; ``felinet monografia verificar`` confere se o ``.tex`` usa exatamente
estes arquivos; ``felinet monografia listar`` mostra o mapa. Desenhos (TikZ e drawio) não
vêm de dados e ficam na monografia (``elementos/diagramas/``).

Requisitos de cada elemento (o que precisa estar disponível para gerá-lo):

* ``runs``: runs da execução final (``runs/operacional``, ``metodologico``, ``complementar``);
* ``imagens``: as imagens que os runs referenciam (no ambiente original, nos caminhos
  gravados; em outra máquina, reconstruídas com ``felinet datasets reconstruir-run`` e
  mapeadas por ``substituir``);
* ``fotos``: as 36 fotos do iNaturalist (``scripts/baixar_exemplos_inat.py``);
* ``petface``: as imagens do PetFace referenciadas nos embeddings (ambiente original);
* ``umap``: o run de ``felinet experimentos visualizacao-exploratoria`` (ambiente original).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from felinet.monografia import dados as d
from felinet.monografia import exemplos as fx
from felinet.monografia import graficos as g
from felinet.monografia import tabelas as t

RAIZ_FELINET = Path(__file__).resolve().parents[3]
EXEMPLOS = RAIZ_FELINET / "docs" / "exemplos"
FONTES_CASCATA = ("kaggle_cats", "felidae")
NS = g.NS


@dataclass(frozen=True)
class Entradas:
    """Onde estão os dados nesta máquina."""

    runs: Path | None = None
    fotos: Path | None = None
    # Prefixo gravado nos runs -> pasta local (vazio no ambiente original).
    substituir: tuple[tuple[str, str], ...] = ()

    def caminho(self, gravado: str) -> Path:
        return fx.remapear(str(gravado), list(self.substituir))


def _tem_runs(en: Entradas) -> bool:
    return en.runs is not None and (en.runs / "operacional").is_dir()


def _primeira_imagem_do_run(en: Entradas) -> Path:
    pasta = d.pasta_run_cascata(en.runs, "kaggle_cats")
    det = json.loads((pasta / "03_deteccoes" / "deteccoes.json").read_text(encoding="utf-8"))
    return en.caminho(det["resultados"][0]["media_path"])


def _primeira_imagem_petface(en: Entradas) -> Path:
    z = _embeddings_npz(en, 100)
    return en.caminho(str(z["caminhos"][0]))


def _ok(teste: Callable[[Entradas], bool]) -> Callable[[Entradas], bool]:
    def seguro(en: Entradas) -> bool:
        try:
            return bool(teste(en))
        except (OSError, KeyError, IndexError, d.DadosAusentesError):
            return False

    return seguro


REQUISITOS: dict[str, tuple[str, Callable[[Entradas], bool]]] = {
    "runs": ("runs da execução final (--runs)", _ok(_tem_runs)),
    "imagens": (
        "imagens dos runs (ambiente original, ou reconstruídas + --substituir)",
        _ok(lambda en: _tem_runs(en) and _primeira_imagem_do_run(en).is_file()),
    ),
    "fotos": (
        "36 fotos do iNaturalist (scripts/baixar_exemplos_inat.py; --fotos)",
        _ok(lambda en: en.fotos is not None and any(Path(en.fotos).glob("*.jpg"))),
    ),
    "petface": (
        "imagens do PetFace (ambiente original)",
        _ok(lambda en: _tem_runs(en) and _primeira_imagem_petface(en).is_file()),
    ),
    "umap": (
        "run de `felinet experimentos visualizacao-exploratoria` (ambiente original)",
        _ok(
            lambda en: any(
                (en.runs / "complementar" / "visualizacao_exploratoria").glob("*/resultados.csv")
            )
        ),
    ),
}


@dataclass(frozen=True)
class Elemento:
    rotulo: str  # \label do LaTeX ao qual o arquivo pertence
    arquivo: str  # relativo a <monografia>/elementos/gerados/
    descricao: str
    funcao: Callable  # função que desenha a figura ou escreve a tabela
    dados: Callable[[Entradas], tuple]  # argumentos de ``funcao`` lidos das entradas
    requer: tuple[str, ...] = ("runs",)
    extras: dict = field(default_factory=dict)  # argumentos fixos de ``funcao``

    @property
    def tipo(self) -> str:
        return "tabela" if self.arquivo.endswith(".tex") else "figura"

    @property
    def codigo(self) -> str:
        """Onde está a função, relativo à raiz do felinet (para o mapa e o manifesto)."""
        modulo = self.funcao.__module__.replace(".", "/")
        return f"src/{modulo}.py::{self.funcao.__qualname__}"

    def produzir(self, en: Entradas):
        return self.funcao(*self.dados(en), **self.extras)


# ----------------------------------------------------------------------------
# Leitura das entradas de cada elemento
# ----------------------------------------------------------------------------


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _selecao() -> dict:
    return _json(EXEMPLOS / "fauna_campus2" / "selecao.json")


def _resultados_fotos() -> dict[str, dict]:
    return fx.carregar(EXEMPLOS / "fauna_campus2" / "resultados.json")


def _grade_fotos(en: Entradas) -> tuple:
    sel = _selecao()
    nomes = {e["prefixo"]: (e["comum"], e["cientifico"]) for e in sel["especies"]}
    itens = [(a, *nomes[a.rsplit("_", 1)[0]]) for a in sel["grade"]]
    return (_resultados_fotos(), Path(en.fotos), itens)


def _exemplo_fronteira(en: Entradas) -> d.CaixaClassificada | None:
    """A caixa do Felidae aceita como F. catus (caso de fronteira do Cap. 5), se houver recorte."""
    aceitas = [c for c in d.carregar_caixas(en.runs, "felidae") if c.status == "felis_catus"]
    return next((c for c in aceitas if c.recorte is not None), None)


def _cascata(en: Entradas) -> tuple:
    return (
        [d.carregar_cascata_operacional(en.runs, f) for f in FONTES_CASCATA],
        {f: d.carregar_caixas(en.runs, f) for f in FONTES_CASCATA},
    )


def _trajetorias(fonte: str) -> Callable[[Entradas], tuple]:
    def ler(en: Entradas) -> tuple:
        casos = _json(EXEMPLOS / "trajetorias" / f"{fonte}.json")
        return (casos, {fonte: d.pasta_run_cascata(en.runs, fonte)}, list(en.substituir))

    return ler


def _amostras(en: Entradas) -> tuple:
    """As imagens de cada run operacional, nos caminhos desta máquina."""
    pastas = {}
    for fonte, nome in (("kaggle_cats", r"$\mathtt{kaggle\_cats}$"), ("felidae", "Felidae")):
        imagens = fx.imagens_do_run(d.pasta_run_cascata(en.runs, fonte))
        pastas[nome] = sorted(en.caminho(p) for p in imagens)
    return (pastas,)


def _embeddings_npz(en: Entradas, n: int):
    pasta = d._pasta_metodologica(en.runs, f"n{n:04d}", "petface", "prod")
    return np.load(sorted(pasta.glob("*/embeddings.npz"))[0], allow_pickle=False)


def _reid_exemplos(en: Entradas) -> tuple:
    z = _embeddings_npz(en, 100)
    return (z["vetores"], z["ids"], z["splits"], z["caminhos"], list(en.substituir))


def _tau_eer_medio(en: Entradas, n: int) -> float:
    os_ = d.carregar_openset(en.runs, n)
    return float(np.mean([s["relatorio"]["tau_eer"] for s in os_["por_seed"]]))


# ----------------------------------------------------------------------------
# O registro, na ordem em que os elementos aparecem na monografia
# ----------------------------------------------------------------------------

ELEMENTOS: list[Elemento] = [
    # ---- Cap. 3: exemplos da cascata em fotos do iNaturalist ----
    Elemento(
        "fig:exemplos-cascata",
        "cap3/exemplos_cascata.pdf",
        "Grade de exemplos das Fases II e III em fauna que pode ocorrer no Campus 2",
        fx.exemplos_cascata,
        _grade_fotos,
        requer=("fotos",),
    ),
    Elemento(
        "fig:exemplos-cascata",
        "cap3/exemplos_cascata_creditos.tex",
        "Autor e licença das fotos da grade, na ordem da grade",
        t.creditos_fotos,
        lambda en: (_json(EXEMPLOS / "fauna_campus2" / "registro.json"), _selecao()["grade"]),
        requer=(),
    ),
    Elemento(
        "tab:exemplos-cascata",
        "cap3/tab_exemplos_cascata.tex",
        "Desfecho da cascata nas 36 fotos, por espécie",
        t.exemplos_cascata,
        lambda en: (_resultados_fotos(), _selecao()["especies"]),
        requer=(),
    ),
    # ---- Cap. 4: amostras das fontes operacionais ----
    Elemento(
        "fig:amostras-fontes",
        "cap4/amostras_fontes.pdf",
        "Amostras sorteadas (semente 42) das imagens dos dois runs operacionais",
        fx.amostras_datasets,
        _amostras,
        requer=("runs", "imagens"),
    ),
    # ---- Cap. 5: cascata operacional ----
    Elemento(
        "tab:cap5-comparativo-fontes",
        "cap5/tab_comparativo_fontes.tex",
        "Totais das Fases II e III por fonte operacional",
        t.comparativo_fontes,
        lambda en: ([d.carregar_cascata_operacional(en.runs, f) for f in FONTES_CASCATA],),
    ),
    Elemento(
        "fig:cap5-comparativo-fontes",
        "cap5/cascata_operacional.pdf",
        "Fases II e III sobrepostas por fonte, com o caso aceito do Felidae",
        g.cascata_operacional,
        lambda en: (*_cascata(en), _exemplo_fronteira(en)),
        # revisão visual do quadro (reconstruído do LILA, rótulo "puma"): traseira de um felídeo
        # de costas junto a uma árvore, à noite; a outra caixa do quadro (um tronco) saiu do
        # SpeciesNet como "vazio" (0,99)
        extras={"nota_exemplo": "puma de costas, à noite\n(rótulo do LILA: puma)"},
    ),
    Elemento(
        "fig:cap5-trajetorias-kaggle",
        "cap5/trajetorias_kaggle_cats.pdf",
        "Quatro fotos do kaggle_cats pelas Fases I a III (casos em docs/exemplos/trajetorias)",
        fx.trajetorias,
        _trajetorias("kaggle_cats"),
        requer=("runs", "imagens"),
    ),
    Elemento(
        "fig:cap5-trajetorias-felidae",
        "cap5/trajetorias_felidae.pdf",
        "Quatro quadros do Felidae pelas Fases I a III (casos em docs/exemplos/trajetorias)",
        fx.trajetorias,
        _trajetorias("felidae"),
        requer=("runs", "imagens"),
    ),
    # ---- Cap. 5: experimentos complementares ----
    Elemento(
        "fig:cap5-multifonte",
        "cap5/cascatas_multifonte.pdf",
        "Cascatas Multifonte (YOLOv8n + CLIP) em quatro fontes",
        g.cascatas_multifonte,
        lambda en: (d.carregar_complementar(en.runs, "cascatas_multifonte"),),
    ),
    Elemento(
        "fig:cap5-sensibilidade",
        "cap5/sensibilidade_limiar.pdf",
        "Taxa de imagens com animal e confiança média versus limiar do detector",
        g.sensibilidade_limiar,
        lambda en: (d.carregar_complementar(en.runs, "sensibilidade_limiar"),),
    ),
    # ---- Cap. 5: re-ID ----
    Elemento(
        "tab:cap5-reid-closed",
        "cap5/tab_reid_closed.tex",
        "Métricas closed-set no PetFace (N = 50, 100, 200)",
        t.closed_set,
        lambda en: ({n: d.carregar_closed(en.runs, n) for n in NS},),
    ),
    Elemento(
        "fig:cap5-cmc-comparativo",
        "cap5/reid_cmc.pdf",
        "Curvas CMC closed-set (N = 50, 100, 200)",
        g.curvas_cmc,
        lambda en: ({n: d.carregar_closed(en.runs, n) for n in NS},),
    ),
    Elemento(
        "fig:cap5-exemplos-reid",
        "cap5/exemplos_reid.pdf",
        "Duas consultas do closed-set N = 100 e o top-5 da galeria (um acerto, um erro)",
        fx.exemplos_reid,
        _reid_exemplos,
        requer=("runs", "petface"),
    ),
    Elemento(
        "tab:cap5-reid-openset",
        "cap5/tab_reid_openset.tex",
        "Métricas open-set no PetFace, médias de três sementes",
        t.open_set,
        lambda en: ({n: d.carregar_openset(en.runs, n) for n in NS},),
    ),
    Elemento(
        "fig:cap5-roc-openset",
        "cap5/reid_roc_openset.pdf",
        "Curvas ROC open-set (N = 50, 100, 200)",
        g.curvas_roc_openset,
        lambda en: ({n: d.carregar_openset(en.runs, n) for n in NS},),
    ),
    # ---- Apêndice E: resultados complementares ----
    Elemento(
        "fig:cap5-distribuicoes",
        "apendice_e/distribuicoes_cascata.pdf",
        "Distribuição da confiança do detector e da probabilidade de gato, por fonte",
        g.distribuicoes_cascata,
        lambda en: ({f: d.carregar_caixas(en.runs, f) for f in FONTES_CASCATA},),
    ),
    Elemento(
        "tab:cap5-multifonte",
        "apendice_e/tab_cascatas_multifonte.tex",
        "Totais do experimento de Cascatas Multifonte",
        t.cascatas_multifonte,
        lambda en: (d.carregar_complementar(en.runs, "cascatas_multifonte"),),
    ),
    Elemento(
        "tab:cap5-sensibilidade",
        "apendice_e/tab_sensibilidade_limiar.tex",
        "Totais do experimento de Sensibilidade ao Limiar",
        t.sensibilidade_limiar,
        lambda en: (d.carregar_complementar(en.runs, "sensibilidade_limiar"),),
    ),
    Elemento(
        "fig:cap5-matriz-sim-n100",
        "apendice_e/reid_matriz_similaridade_n100.pdf",
        "Matriz de similaridade consultas x galeria (N = 100)",
        g.matriz_similaridade,
        lambda en: (d.carregar_embeddings(en.runs, 100),),
    ),
    Elemento(
        "fig:cap5-dist-intra-inter-n100",
        "apendice_e/reid_intra_inter_n100.pdf",
        "Similaridades intra e inter identidades (N = 100) e o limiar do EER",
        g.distribuicao_intra_inter,
        lambda en: (d.carregar_embeddings(en.runs, 100), _tau_eer_medio(en, 100)),
    ),
    Elemento(
        "fig:cap5-umap",
        "apendice_e/reid_umap.pdf",
        "Projeção UMAP dos embeddings de corpo do CatIndividualImages",
        g.projecao_umap,
        lambda en: (d.carregar_complementar(en.runs, "visualizacao_exploratoria"),),
        requer=("runs", "umap"),
    ),
]


def por_arquivo() -> dict[str, Elemento]:
    return {el.arquivo: el for el in ELEMENTOS}


def faltando(el: Elemento, en: Entradas) -> list[str]:
    """Requisitos do elemento que não estão disponíveis nesta máquina."""
    return [REQUISITOS[r][0] for r in el.requer if not REQUISITOS[r][1](en)]
