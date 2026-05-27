"""Conversao CSV -> booktabs .tex para inclusao em artifacts/tabelas/.

Saida pode ser usada com ``\\input{tabelas/reid_closed_set.tex}`` em LaTeX.
"""

from __future__ import annotations

import csv
from pathlib import Path


def _escapar_tex(texto: str) -> str:
    """Escapa caracteres especiais do LaTeX em strings de celula."""
    substituicoes = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    saida = texto
    for original, escape in substituicoes.items():
        saida = saida.replace(original, escape)
    return saida


def csv_para_booktabs(
    csv_path: Path,
    tex_path: Path,
    legenda: str = "",
    rotulo: str = "",
    colunas_align: str | None = None,
) -> None:
    """Converte CSV em tabela booktabs.

    Args:
        csv_path: CSV de entrada (com cabecalho na primeira linha).
        tex_path: ``.tex`` de saida.
        legenda: ``\\caption{...}``.
        rotulo: ``\\label{...}``.
        colunas_align: especificacao tipo ``"lrr"``. Se ``None``, primeira
            coluna ``l`` e demais ``r``.
    """
    csv_path = Path(csv_path)
    with csv_path.open("r", encoding="utf-8") as f:
        leitor = csv.reader(f)
        linhas = list(leitor)
    if not linhas:
        raise ValueError(f"CSV vazio: {csv_path}")

    cabecalho = linhas[0]
    corpo = linhas[1:]
    n_col = len(cabecalho)
    if colunas_align is None:
        colunas_align = "l" + "r" * (n_col - 1)

    tex_path = Path(tex_path)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    with tex_path.open("w", encoding="utf-8") as out:
        out.write("\\begin{table}[!htb]\n")
        out.write("\\centering\n")
        if legenda:
            out.write(f"\\caption{{{_escapar_tex(legenda)}}}\n")
        if rotulo:
            out.write(f"\\label{{{rotulo}}}\n")
        out.write(f"\\begin{{tabular}}{{{colunas_align}}}\n")
        out.write("\\toprule\n")
        out.write(" & ".join(_escapar_tex(c) for c in cabecalho) + " \\\\\n")
        out.write("\\midrule\n")
        for linha in corpo:
            out.write(" & ".join(_escapar_tex(c) for c in linha) + " \\\\\n")
        out.write("\\bottomrule\n")
        out.write("\\end{tabular}\n")
        out.write("\\end{table}\n")
