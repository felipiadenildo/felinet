"""Figuras com imagens: exemplos da cascata, trajetórias, amostras e exemplos de re-ID.

As caixas do detector são desenhadas na cor da decisão da Fase III, com a confiança de cada
caixa e o destino na cascata. Qual figura da monografia cada função produz está em
``elementos.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib.patches import Patch, Rectangle

from felinet.monografia import estilo as e
from felinet.monografia.graficos import ESPECIE_PT

COR_STATUS = {
    "felis_catus": e.COR["felis"],
    "validacao_humana": e.COR["validacao"],
    "outra_especie": e.COR["outra"],
}
DESTINO = {
    "felis_catus": "aceita: segue para a Fase IV",
    "validacao_humana": "fila de validação humana",
    "outra_especie": "outra espécie: descartada",
}
ESPECIE_PT_EXTRA = {
    "white-eared opossum": "gambá-de-orelha-branca",
    "south american coati": "quati",
    "jaguarundi": "gato-mourisco",
    "southern tigrina": "gato-do-mato-pequeno",
    "oncilla": "gato-do-mato",
    "argentine black and white tegu": "teiú",
    "tegu family": "teiú (família)",
    "opossum family": "gambá (família)",
    "carnivorous mammal": "carnívoro",
    "felidae family": "felídeo",
    "animal": "animal",
    "ocelot": "jaguatirica",
    "marbled cat": "gato-marmorado",
    "virginia opossum": "gambá-da-virgínia",
    "lace monitor": "varano-rendado",
    "common water monitor": "varano-d'água",
    "asiatic golden cat": "gato-dourado-asiático",
    "crab-eating fox": "cachorro-do-mato",
    "fisher": "marta-pescadora",
    "culpeo": "raposa-culpeo",
    "andean white-eared opossum": "gambá-andino",
    "striped hyaena": "hiena-listrada",
    "human": "humano",
    "brown bear": "urso-pardo",
    "domestic dog": "cão doméstico",
    "white-tailed deer": "veado-de-cauda-branca",
    "mule deer": "cervo-mula",
    "red fox": "raposa-vermelha",
    "wild boar": "javali",
    "domestic cattle": "bovino",
    "domestic goat": "cabra",
    "bird": "ave",
    "american black bear": "urso-negro",
    "canis species": "gênero Canis",
    "felis species": "gênero Felis",
    "wild cat": "gato-selvagem",
    "island fox": "raposa-das-ilhas",
    "canada lynx": "lince-do-canadá",
    "iberian lynx": "lince-ibérico",
}


def _pt(especie: str) -> str:
    return ESPECIE_PT_EXTRA.get(especie, ESPECIE_PT.get(especie, especie))


def carregar(resultados: Path) -> dict[str, dict]:
    dados = json.loads(Path(resultados).read_text(encoding="utf-8"))
    return {r["arquivo"]: r for r in dados["resultados"]}


CATEGORIA_PT = {"animal": "animal", "person": "pessoa", "vehicle": "veículo"}


def _mesma_caixa(a: dict, b: dict, tol: float = 0.01) -> bool:
    return all(abs(a[k] - b[k]) <= tol for k in ("x", "y", "w", "h"))


def _desenhar(
    ax, img, largura: int, altura: int, caixas: list[dict], titulo: str, fonte: float = 6
) -> dict | None:
    """Imagem com as caixas na cor da decisão; devolve a caixa animal de maior confiança.

    Caixas coincidentes de classes diferentes (o detector às vezes dá ``animal`` e ``person`` ao
    mesmo objeto) são desenhadas uma vez, com os rótulos juntos, para nenhum ficar escondido.
    """
    ax.imshow(img)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for lado in ax.spines.values():
        lado.set_visible(False)
    grupos: list[list[dict]] = []
    for c in sorted(caixas, key=lambda c: (c["categoria"] != "animal", -c["confianca"])):
        for g in grupos:
            if _mesma_caixa(g[0]["bbox"], c["bbox"]):
                g.append(c)
                break
        else:
            grupos.append([c])
    principal = None
    for g in grupos:
        c, b = g[0], g[0]["bbox"]
        animal = c["categoria"] == "animal"
        cor = COR_STATUS.get(c.get("status"), e.TINTA_SECUNDARIA)
        ax.add_patch(
            Rectangle(
                (b["x"] * largura, b["y"] * altura), b["w"] * largura, b["h"] * altura,
                fill=False, edgecolor=cor, linewidth=1.6 if animal else 0.9,
                linestyle="-" if animal else (0, (3, 2)),
            )
        )  # fmt: skip
        rotulo = " · ".join(
            f"{CATEGORIA_PT.get(x['categoria'], x['categoria'])} {e.numero(x['confianca'], 2)}"
            for x in g
        )
        # rótulo dentro da caixa, no canto superior: não invade o título do painel
        ax.text(
            b["x"] * largura + 4, b["y"] * altura + 4, rotulo,
            fontsize=fonte, color=e.TINTA, va="top", ha="left",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6, "alpha": 0.85},
        )  # fmt: skip
        for x in g:
            if x["categoria"] == "animal" and (
                principal is None or x["confianca"] > principal["confianca"]
            ):
                principal = x
    ax.set_title(titulo, fontsize=8, pad=3)
    return principal


def enquadrar(img, caixas: list[dict], aspecto: float = 4 / 3):
    """Maior recorte ``aspecto`` (largura/altura) que cabe na imagem, centrado nas caixas.

    Dá a mesma moldura a todos os painéis de uma grade sem distorcer as fotos. Devolve a imagem
    recortada (PIL) e as caixas renormalizadas para o recorte (as que saem dele são descartadas).
    """
    largura, altura = img.size
    cw, ch = (largura, round(largura / aspecto))
    if ch > altura:
        cw, ch = round(altura * aspecto), altura

    def centro(cs: list[dict]) -> tuple[float, float, float, float]:
        xs = [c["bbox"]["x"] for c in cs] + [c["bbox"]["x"] + c["bbox"]["w"] for c in cs]
        ys = [c["bbox"]["y"] for c in cs] + [c["bbox"]["y"] + c["bbox"]["h"] for c in cs]
        return (
            (min(xs) + max(xs)) / 2 * largura, (min(ys) + max(ys)) / 2 * altura,
            (max(xs) - min(xs)) * largura, (max(ys) - min(ys)) * altura,
        )  # fmt: skip

    cx, cy = largura / 2, altura / 2
    if caixas:
        cx, cy, uw, uh = centro(caixas)
        if uw > cw or uh > ch:  # não cabem juntas: prioriza a de maior confiança
            cx, cy, _, _ = centro([max(caixas, key=lambda c: c["confianca"])])
    x0 = int(min(max(cx - cw / 2, 0), largura - cw))
    y0 = int(min(max(cy - ch / 2, 0), altura - ch))
    novas = []
    for c in caixas:
        b = c["bbox"]
        x1 = max(b["x"] * largura, x0)
        y1 = max(b["y"] * altura, y0)
        x2 = min((b["x"] + b["w"]) * largura, x0 + cw)
        y2 = min((b["y"] + b["h"]) * altura, y0 + ch)
        if x2 > x1 and y2 > y1:
            bb = {
                "x": (x1 - x0) / cw,
                "y": (y1 - y0) / ch,
                "w": (x2 - x1) / cw,
                "h": (y2 - y1) / ch,
            }
            novas.append({**c, "bbox": bb})
    return img.crop((x0, y0, x0 + cw, y0 + ch)), novas


def realcar(img, limiar: float = 60.0):
    """Autocontraste em recortes escuros (só para visualização); devolve ``(imagem, realçou)``."""
    import numpy as np
    from PIL import ImageOps

    if float(np.asarray(img.convert("L")).mean()) >= limiar:
        return img, False
    return ImageOps.autocontrast(img.convert("RGB"), cutoff=1), True


def _rodape(principal: dict | None) -> str:
    if principal is None:
        return "nenhuma caixa da classe animal:\ndescartada na Fase II"
    topo = principal["top_k"][0] if principal["top_k"] else {"especie": "?", "probabilidade": 0}
    return (
        f"SpeciesNet: {_pt(topo['especie'])} {e.numero(topo['probabilidade'], 2)}\n"
        f"{DESTINO.get(principal['status'], principal['status'])}"
    )


def _legenda_decisoes(fig: Figure) -> None:
    fig.legend(
        handles=[
            Patch(
                facecolor="none",
                edgecolor=e.COR["felis"],
                linewidth=1.6,
                label=f"Aceita como {e.FELIS}",
            ),
            Patch(
                facecolor="none",
                edgecolor=e.COR["validacao"],
                linewidth=1.6,
                label="Validação humana",
            ),
            Patch(facecolor="none", edgecolor=e.COR["outra"], linewidth=1.6, label="Outra espécie"),
            Patch(
                facecolor="none",
                edgecolor=e.TINTA_SECUNDARIA,
                linewidth=0.9,
                linestyle=(0, (3, 2)),
                label="Pessoa ou veículo",
            ),
        ],
        loc="outside lower center",
        ncol=4,
        handlelength=1.4,
    )


def exemplos_cascata(
    resultados: dict[str, dict],
    pasta_imagens: Path,
    selecao: list[tuple[str, str, str]],
    ncols: int = 3,
) -> Figure:
    """Grade de exemplos. ``selecao``: ``(arquivo, nome comum, nome científico)``."""
    from PIL import Image

    nrows = -(-len(selecao) // ncols)
    fig, eixos = e.nova_figura(altura_cm=5.5 * nrows, ncols=ncols, nrows=nrows)
    fig.get_layout_engine().set(h_pad=0.06, hspace=0.08)  # respiro entre rodapé e título
    for ax, (arquivo, comum, cientifico) in zip(eixos, selecao, strict=False):
        r = resultados[arquivo]
        italico = cientifico.replace(" ", r"\ ")  # espaço explícito no modo matemático
        titulo = rf"{comum} ($\mathit{{{italico}}}$)"
        with Image.open(Path(pasta_imagens) / arquivo) as bruta:
            img, caixas = enquadrar(bruta.convert("RGB"), r["caixas"])
        principal = _desenhar(ax, img, img.size[0], img.size[1], caixas, titulo)
        ax.title.set_fontsize(7.5)
        ax.set_xlabel(_rodape(principal), fontsize=7, labelpad=3)
    for ax in eixos[len(selecao) :]:
        ax.set_visible(False)
    _legenda_decisoes(fig)
    return fig


# ----------------------------------------------------------------------------
# Exemplos dos próprios experimentos (rodam onde estão os datasets originais)
# ----------------------------------------------------------------------------


def remapear(caminho: str, substituicoes: list[tuple[str, str]]) -> Path:
    """Aplica a primeira substituição de prefixo que casar (os runs guardam caminhos absolutos)."""
    for antigo, novo in substituicoes:
        if caminho.startswith(antigo):
            return Path(novo + caminho[len(antigo) :])
    return Path(caminho)


def imagens_do_run(pasta_run: Path) -> dict[str, dict]:
    """Por imagem: dimensões e todas as caixas (inclusive pessoa e veículo) com a decisão da Fase III."""
    det = json.loads((pasta_run / "03_deteccoes" / "deteccoes.json").read_text(encoding="utf-8"))
    cls = json.loads(
        (pasta_run / "04_classificacoes" / "classificacoes.json").read_text(encoding="utf-8")
    )
    decisao = {(c["media_path"], c["bbox_indice"]): c for c in cls["resultados"]}
    imagens = {}
    for r in det["resultados"]:
        caixas = []
        for i, dd in enumerate(r["deteccoes"]):
            c = decisao.get((r["media_path"], i), {})
            caixas.append({**dd, "status": c.get("status"), "top_k": c.get("top_k", [])})
        imagens[r["media_path"]] = {
            "largura": r["largura"],
            "altura": r["altura"],
            "caixas": caixas,
        }
    return imagens


def _manifesto(pasta_run: Path) -> dict[str, dict]:
    import csv

    with open(pasta_run / "02_manifesto" / "manifesto.csv", encoding="utf-8", newline="") as f:
        return {Path(r["caminho_relativo"]).name: r for r in csv.DictReader(f)}


def _sem_eixos(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for lado in ax.spines.values():
        lado.set_visible(False)


def _caixa_da_fase3(caixas: list[dict], indice: int | None) -> dict | None:
    """A caixa que decide o destino da imagem: a indicada, ou a de status mais avançado."""
    animais = [c for c in caixas if c["categoria"] == "animal"]
    if indice is not None:
        return caixas[indice]
    prioridade = {"felis_catus": 0, "validacao_humana": 1, "outra_especie": 2}
    return min(
        animais, key=lambda c: (prioridade.get(c.get("status"), 3), -c["confianca"]), default=None
    )


def trajetorias(
    casos: list[dict], pastas_run: dict[str, Path], substituicoes: list[tuple[str, str]]
) -> Figure:
    """Caminho de quadros reais de um run pelas Fases I a III, uma linha por caso.

    ``casos``: ``{"fonte", "arquivo", "rotulo"}`` e, opcional, ``"caixa"`` (índice da caixa da
    Fase III a recortar). Colunas: entrada com proveniência e triagem da Fase I; quadro com as
    caixas da Fase II (pessoas desfocadas pela anonimização); recorte enviado ao classificador;
    top-3 do SpeciesNet e destino. As decisões são as gravadas no run; só a triagem e o desfoque
    são recalculados (não estavam no run da monografia).
    """
    import numpy as np
    from PIL import Image

    from felinet.pipeline.fase1_ingestao.triagem import motivo_descarte
    from felinet.pipeline.fase2_deteccao.anonimizacao import (
        anonimizar_pessoas,
        eh_noturno_infravermelho,
    )
    from felinet.pipeline.fase2_deteccao.schema import BoundingBox, Deteccao

    runs = {f: (imagens_do_run(p), _manifesto(p)) for f, p in pastas_run.items()}
    fig = e.figura_vazia(altura_cm=3.25 * len(casos) + 1.4)
    grade = fig.add_gridspec(len(casos), 4, width_ratios=[1.0, 1.0, 0.62, 1.05])
    titulos = ["Entrada (Fase I)", "Detecção (Fase II)", "Recorte", "Classificação (Fase III)"]
    for i, caso in enumerate(casos):
        imagens, manifesto = runs[caso["fonte"]]
        midia = next(m for m in imagens if Path(m).name == caso["arquivo"])
        r, meta = imagens[midia], manifesto[caso["arquivo"]]
        img = Image.open(remapear(midia, substituicoes)).convert("RGB")
        img.thumbnail((1400, 1400))  # as caixas são normalizadas: o tamanho não importa
        img, caixas = enquadrar(img, r["caixas"])  # mesma moldura 4:3 em todas as linhas
        r = {**r, "caixas": caixas}
        largura, altura = img.size

        ax0 = fig.add_subplot(grade[i, 0])
        ax0.imshow(img)
        _sem_eixos(ax0)
        camera = (meta.get("fabricante") or "").strip().title() or "sem EXIF"
        quando = (meta.get("timestamp") or "")[:16].replace("T", " ")
        # o que a Fase II usa para escolher o limiar: quadro sem cor (NIR) ou colorido
        modo = "monocromática" if eh_noturno_infravermelho(img.reduce(4)) else "colorida"
        triagem = motivo_descarte(img) or "aceito"
        ax0.set_title(caso["rotulo"], fontsize=7.5, loc="left", pad=2, fontweight="bold")
        ax0.set_xlabel(
            f"{meta['largura']}×{meta['altura']} px · {camera}\n"
            f"{quando + chr(10) if quando else ''}triagem: {triagem} · {modo}",
            fontsize=5.5, labelpad=2,
        )  # fmt: skip

        pessoas = [
            Deteccao(c["categoria"], c["confianca"], BoundingBox(**c["bbox"]))
            for c in r["caixas"]
            if c["categoria"] == "person"
        ]
        ax1 = fig.add_subplot(grade[i, 1])
        principal = _caixa_da_fase3(r["caixas"], caso.get("caixa"))
        _desenhar(ax1, anonimizar_pessoas(img, pessoas), largura, altura, r["caixas"], "", 5.5)
        contagem = [
            f"{n} {CATEGORIA_PT[k]}"
            for k in ("animal", "person", "vehicle")
            if (n := sum(c["categoria"] == k for c in r["caixas"]))
        ]
        ax1.set_xlabel("caixas: " + (", ".join(contagem) or "nenhuma"), fontsize=5.5, labelpad=2)

        ax2 = fig.add_subplot(grade[i, 2])
        ax3 = fig.add_subplot(grade[i, 3])
        _sem_eixos(ax2)
        if principal is None:
            ax2.text(0.5, 0.5, "sem caixa\nde animal", ha="center", va="center", fontsize=6.5,
                     color=e.TINTA_SECUNDARIA, transform=ax2.transAxes)  # fmt: skip
            _sem_eixos(ax3)
            ax3.text(0.0, 0.5, "descartada na Fase II:\nnenhuma caixa da classe animal",
                     ha="left", va="center", fontsize=6.5, transform=ax3.transAxes)  # fmt: skip
        else:
            b = principal["bbox"]
            caixa = (
                int(b["x"] * largura), int(b["y"] * altura),
                int((b["x"] + b["w"]) * largura), int((b["y"] + b["h"]) * altura),
            )  # fmt: skip
            cor = COR_STATUS.get(principal.get("status"), e.TINTA_SECUNDARIA)
            recorte, realcado = realcar(img.crop(caixa))
            ax2.imshow(np.asarray(recorte))
            for lado in ax2.spines.values():
                lado.set_visible(True)
                lado.set_color(cor)
                lado.set_linewidth(1.6)
            ax2.set_xlabel(
                f"animal {e.numero(principal['confianca'], 2)}"
                + ("\n(realçado só na figura)" if realcado else ""),
                fontsize=6, labelpad=2,
            )  # fmt: skip
            top = principal["top_k"][:3][::-1]
            ax3.barh(
                range(len(top)),
                [t["probabilidade"] for t in top],
                color=[e.GRADE] * (len(top) - 1) + [cor],
                height=0.62,
            )
            for j, t in enumerate(top):
                ax3.text(0.02, j, f"{_pt(t['especie'])} {e.numero(t['probabilidade'], 2)}",
                         va="center", ha="left", fontsize=6)  # fmt: skip
            ax3.set_xlim(0, 1)
            ax3.set_yticks([])
            ax3.set_xticks([0, 0.5, 1])
            ax3.tick_params(labelsize=5.5, length=2)
            e.eixo_virgula(ax3.xaxis, 1)
            ax3.set_xlabel(
                DESTINO.get(principal.get("status"), principal.get("status")), fontsize=6.5,
                labelpad=2, color=e.TINTA,
            )  # fmt: skip
        if i == 0:
            for ax, t in zip((ax0, ax1, ax2, ax3), titulos, strict=True):
                ax.annotate(t, (0.5, 1.0), xycoords="axes fraction", xytext=(0, 13),
                            textcoords="offset points", ha="center", va="bottom", fontsize=7.5,
                            color=e.TINTA_SECUNDARIA)  # fmt: skip
    _legenda_decisoes(fig)
    return fig


def exemplos_reid(
    vetores, ids, splits, caminhos, substituicoes: list[tuple[str, str]], k: int = 5
) -> Figure:
    """Duas consultas do closed-set e o top-k da galeria: um acerto e um erro.

    Acerto: consulta com top-1 correto e maior similaridade. Erro: primeira consulta
    (em ordem) com top-1 errado e a identidade correta ainda no top-k.
    """
    import numpy as np

    q, g = splits == "query", splits == "gallery"
    sim = vetores[q] @ vetores[g].T
    ids_q, ids_g, cam_q, cam_g = ids[q], ids[g], caminhos[q], caminhos[g]
    ordem = np.argsort(-sim, axis=1)[:, :k]
    certo = ids_g[ordem] == ids_q[:, None]
    acertos = np.where(certo[:, 0])[0]
    erros = list(np.where(~certo[:, 0] & certo.any(axis=1))[0])
    escolhidos = []
    if len(acertos):
        escolhidos.append(("acerto no Rank-1", acertos[np.argmax(sim[acertos, ordem[acertos, 0]])]))
    if erros:
        escolhidos.append(("erro no Rank-1", erros[0]))
    fig, eixos = e.nova_figura(altura_cm=3.6 * len(escolhidos), ncols=k + 1, nrows=len(escolhidos))
    for linha, (rotulo, iq) in enumerate(escolhidos):
        quadros = [(cam_q[iq], f"Consulta\n({rotulo})", e.TINTA)]
        for r, ig in enumerate(ordem[iq], 1):
            mesmo = ids_g[ig] == ids_q[iq]
            quadros.append(
                (
                    cam_g[ig],
                    f"{r}º · sim. {e.numero(sim[iq, ig], 2)}",
                    e.COR["felis"] if mesmo else e.COR["outra"],
                )
            )
        for col, (caminho, texto, cor) in enumerate(quadros):
            ax = eixos[linha * (k + 1) + col]
            ax.imshow(mpimg.imread(remapear(str(caminho), substituicoes)))
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            for lado in ax.spines.values():
                lado.set_visible(True)
                lado.set_color(cor)
                lado.set_linewidth(2.0 if col else 0.8)
            ax.set_xlabel(texto, fontsize=6.5, labelpad=2)
    fig.legend(
        handles=[
            Patch(
                facecolor="none",
                edgecolor=e.COR["felis"],
                linewidth=2,
                label="Mesmo indivíduo da consulta",
            ),
            Patch(facecolor="none", edgecolor=e.COR["outra"], linewidth=2, label="Outro indivíduo"),
        ],
        loc="outside lower center",
        ncol=2,
    )
    return fig


def amostras_datasets(
    imagens: dict[str, list[Path]], por_dataset: int = 4, semente: int = 42
) -> Figure:
    """Mosaico com ``por_dataset`` imagens sorteadas (semente fixa) da lista de cada base."""
    import random

    from PIL import Image, ImageOps

    fig, eixos = e.nova_figura(altura_cm=2.9 * len(imagens), ncols=por_dataset, nrows=len(imagens))
    for i, (nome, arquivos) in enumerate(imagens.items()):
        sorteio = random.Random(semente).sample(sorted(arquivos), min(por_dataset, len(arquivos)))
        for j in range(por_dataset):
            ax = eixos[i * por_dataset + j]
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            for lado in ax.spines.values():
                lado.set_visible(False)
            if j < len(sorteio):
                # recorte central 4:3: mesma moldura para todas, sem distorcer a imagem
                with Image.open(sorteio[j]) as img:
                    ax.imshow(ImageOps.fit(img.convert("RGB"), (480, 360)))
        eixos[i * por_dataset].set_ylabel(
            nome, fontsize=8, rotation=0, ha="right", va="center", labelpad=6
        )
    return fig
