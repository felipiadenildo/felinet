"""Tabelas da monografia em LaTeX (só o ``tabular``; legenda, rótulo e fonte ficam no capítulo).

Cada função recebe os dados já carregados e devolve o texto ``.tex``. Qual tabela da
monografia cada função produz está em ``elementos.py``.
"""

from __future__ import annotations

import statistics
from collections import Counter

from felinet.monografia import dados as d
from felinet.monografia.estilo import numero

CABECALHO = "% Gerado por felinet ({funcao}); não edite: rode `felinet monografia gerar`.\n"


def _n3(v: float) -> str:
    return numero(v, 3)


def _pct(v: float) -> str:
    return numero(100 * v, 1) + r"\%"


def tex_escapar(texto: str) -> str:
    """Escapa os caracteres especiais do LaTeX que aparecem em nomes e créditos."""
    for a, b in (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("_", r"\_"),
        ("#", r"\#"),
        ("$", r"\$"),
    ):
        texto = texto.replace(a, b)
    return texto


def _tabular(
    funcao: str, colunas: str, cabecalho: list[str], linhas: list[str], largura: str = ""
) -> str:
    """``tabular`` com booktabs; com ``largura``, ``tabularx`` (colunas ``X`` ocupam o resto)."""
    corpo = "\n".join(f"    {lin} \\\\" for lin in linhas)
    cab = "\n".join(f"    {c}" for c in cabecalho)
    amb, arg = ("tabularx", f"{{{largura}}}") if largura else ("tabular", "")
    return (
        CABECALHO.format(funcao=funcao)
        + f"\\begin{{{amb}}}{arg}{{{colunas}}}\n    \\toprule\n{cab}\n    \\midrule\n{corpo}\n"
        f"    \\bottomrule\n\\end{{{amb}}}\n"
    )


def comparativo_fontes(cascatas: list[d.CascataOperacional]) -> str:
    """Totais e taxas das Fases II e III por fonte operacional."""
    nome = {"kaggle_cats": r"\texttt{kaggle\_cats}", "felidae": "Felidae"}
    linhas = [
        f"{nome.get(c.fonte, c.fonte)} & {c.midias} & {c.caixas} & {c.imagens_com_animal} & "
        f"{_pct(c.taxa_animal)} & {c.caixas_felis} & {_pct(c.taxa_felis)}"
        for c in cascatas
    ]
    return _tabular(
        "tabelas.comparativo_fontes",
        "@{}l r r r r r r@{}",
        [
            r"\textbf{Fonte} & \textbf{Mídias} & \textbf{Caixas de} & \textbf{Imagens c/}"
            r" & \textbf{Taxa} & \textbf{Caixas} & \textbf{Taxa} \\",
            r" & & \textbf{animal} & \textbf{animal} & \textbf{animal}"
            r" & \textit{F.\,catus} & \textit{F.\,catus} \\",
        ],
        linhas,
    )


def closed_set(closed: dict[int, dict]) -> str:
    """Top-k, mAP@10 e mAP do closed-set por tamanho de catálogo."""
    linhas = []
    for n, m in sorted(closed.items()):
        tk = m["top_k"]
        linhas.append(
            f"{n} & {_n3(tk['1'])} & {_n3(tk['5'])} & {_n3(tk['10'])} & "
            f"{_n3(m['mAP_at_k']['10'])} & {_n3(m['mAP'])} & {m['n_query']} & {m['n_galeria']}"
        )
    return _tabular(
        "tabelas.closed_set",
        "@{}rrrrrrrr@{}",
        [
            r"\textbf{N} & \textbf{Top-1} & \textbf{Top-5} & \textbf{Top-10} & \textbf{mAP@10}"
            r" & \textbf{mAP} & \textbf{Consultas} & \textbf{Galeria} \\"
        ],
        linhas,
    )


def open_set(openset: dict[int, dict]) -> str:
    """AUC-ROC, TPR a FPR fixo, EER e Rank-1 do open-set, médias das sementes."""
    linhas = []
    for n, o in sorted(openset.items()):
        seeds = [s["relatorio"] for s in o["por_seed"]]
        eer = statistics.mean(float(s["eer"]) for s in seeds)
        r1 = statistics.mean(float(s["rank1_open_set"]) for s in seeds)
        linhas.append(
            f"{n} & {_n3(o['auc_media'])} $\\pm$ {_n3(o['auc_desvio'])} & "
            f"{_n3(o['tpr_at_fpr_01_media'])} & {_n3(o['tpr_at_fpr_05_media'])} & "
            f"{_n3(eer)} & {_n3(r1)} & {len(seeds)}"
        )
    return _tabular(
        "tabelas.open_set",
        "@{}r c c c c c c@{}",
        [
            r"\textbf{N} & \textbf{AUC-ROC} & \textbf{TPR@} & \textbf{TPR@} & \textbf{EER}"
            r" & \textbf{\textit{Rank}-1} & \textbf{Sem.} \\",
            r" & \textbf{($\mu\pm\sigma$)} & \textbf{FPR=1\%} & \textbf{FPR=5\%} & &"
            r" \textbf{open} & \\",
        ],
        linhas,
    )


NOME_COMPLEMENTAR = {
    "oxford_pet_cats": r"\texttt{oxford\_pet\_cats}",
    "felidae_wild": r"\texttt{felidae\_wild}",
    "cats_vs_dogs": r"\texttt{cats\_vs\_dogs}",
    "inat_br_cats": r"\texttt{inat\_br\_cats}",
}


def cascatas_multifonte(linhas_csv: list[dict]) -> str:
    """Experimento complementar YOLOv8n + CLIP em quatro fontes."""
    linhas = [
        f"{NOME_COMPLEMENTAR.get(r['source'], tex_escapar(r['source']))} & {r['n_images']} & "
        f"{r['n_detection_boxes']} & {_pct(float(r['rate_animal']))} & "
        f"{_pct(float(r['rate_cat']))} & {numero(float(r['elapsed_s']), 1)}"
        for r in linhas_csv
    ]
    return _tabular(
        "tabelas.cascatas_multifonte",
        "@{}lrrrrr@{}",
        [
            r"\textbf{Fonte} & \textbf{Mídias} & \textbf{Caixas} & \textbf{Taxa animal}"
            r" & \textbf{Taxa gato} & \textbf{Tempo (s)} \\"
        ],
        linhas,
    )


def sensibilidade_limiar(linhas_csv: list[dict]) -> str:
    """Experimento complementar de varredura do limiar do detector."""
    linhas = [
        f"{numero(float(r['threshold']), 1)} & {r['n_boxes']} & {r['n_images_with_animal']} & "
        f"{numero(float(r['rate_animal']), 2)} & {_n3(float(r['mean_score']))}"
        for r in linhas_csv
    ]
    return _tabular(
        "tabelas.sensibilidade_limiar",
        "@{}rrrrr@{}",
        [
            r"\textbf{Limiar} & \textbf{Caixas} & \textbf{Imagens c/ animal}"
            r" & \textbf{Taxa animal} & \textbf{Confiança média} \\"
        ],
        linhas,
    )


DESFECHOS = ("felis_catus", "validacao_humana", "outra_especie", "sem_animal")


def desfecho_principal(resultado: dict) -> str:
    """Decisão sobre a caixa de maior confiança da classe animal (ou ``sem_animal``)."""
    animais = [c for c in resultado["caixas"] if c["categoria"] == "animal"]
    if not animais:
        return "sem_animal"
    return max(animais, key=lambda c: c["confianca"])["status"]


def exemplos_cascata(resultados: dict[str, dict], especies: list[dict]) -> str:
    """Desfecho das 36 fotos do iNaturalist, por espécie (prefixo do nome do arquivo)."""
    linhas = []
    for esp in especies:
        cont = Counter(
            desfecho_principal(r)
            for arq, r in resultados.items()
            if arq.rsplit("_", 1)[0] == esp["prefixo"]
        )
        linhas.append(
            f"{esp['comum']} (\\textit{{{esp['cientifico']}}}) & "
            + " & ".join(str(cont[s]) for s in DESFECHOS)
        )
    return _tabular(
        "tabelas.exemplos_cascata",
        r"@{}>{\raggedright\arraybackslash}X c c c c@{}",
        [
            r"\textbf{Espécie} & \textbf{Aceita como} & \textbf{Validação} & \textbf{Outra}"
            r" & \textbf{Sem animal} \\",
            r" & \textbf{\textit{F.\,catus}} & \textbf{humana} & \textbf{espécie}"
            r" & \textbf{detectado} \\",
        ],
        linhas,
        largura=r"\textwidth",
    )


def creditos_fotos(registro: list[dict], arquivos: list[str]) -> str:
    """Autor e licença de cada foto, na ordem dada, para o ``\\fonte`` da figura."""
    reg = {r["arquivo"]: r for r in registro}
    itens = []
    for arq in arquivos:
        r = reg[arq]
        autor = r["atribuicao"].removeprefix("(c) ").split(", some rights reserved")[0]
        licenca = r["licenca"].upper().replace("-", " ", 1)
        itens.append(f"{tex_escapar(autor)} ({licenca})")
    return CABECALHO.format(funcao="tabelas.creditos_fotos") + "; ".join(itens) + "%\n"
