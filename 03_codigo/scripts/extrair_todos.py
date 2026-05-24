#!/usr/bin/env python3
"""
extrair_todos.py
----------------
Varre todos os arquivos .tex em 02_latex/capitulos/ e pos-textuais/
e extrai os comandos \\todoex{descricao}{explicacao} e
\\todoblock{titulo}{texto} para gerar o conteúdo do Apêndice F.

Uso:
    python extrair_todos.py
Saída:
    /home/user/workspace/tcc_gatos_campus2/02_latex/pos-textuais/apendice_f_lista_todos.tex
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

BASE = Path("/home/user/workspace/tcc_gatos_campus2/02_latex")
OUTPUT = BASE / "pos-textuais" / "apendice_f_lista_todos.tex"

# Pastas a varrer (ordem importa — define a ordem na lista final)
SCAN_DIRS = [
    ("Capítulo 1 -- Introdução", [BASE / "capitulos" / "cap1_introducao.tex"]),
    ("Capítulo 2 -- Fundamentação", [BASE / "capitulos" / "cap2_fundamentacao.tex"]),
    (
        "Capítulo 3 -- Correlatos e Requisitos",
        [BASE / "capitulos" / "cap3_correlatos_requisitos.tex"],
    ),
    ("Capítulo 4 -- Projeto", [BASE / "capitulos" / "cap4_projeto.tex"]),
    ("Capítulo 5 -- Arquitetura", sorted((BASE / "capitulos" / "cap5_arquitetura").glob("*.tex"))),
    ("Capítulo 6 -- Pipeline", sorted((BASE / "capitulos" / "cap6_pipeline").glob("*.tex"))),
    ("Capítulo 7 -- Validação", sorted((BASE / "capitulos" / "cap7_validacao").glob("*.tex"))),
    ("Capítulo 8 -- Considerações Finais", [BASE / "capitulos" / "cap8_consideracoes_finais.tex"]),
    (
        "Pós-textuais (Apêndices e Anexos)",
        sorted(
            [
                p
                for p in (BASE / "pos-textuais").glob("*.tex")
                if p.name != "apendice_f_lista_todos.tex"
            ]
        ),
    ),
]


# Regex para \todoex e \todoblock — capturam os dois argumentos {..}{..}
# Aceitam quebras de linha dentro dos argumentos e suportam chaves balanceadas
# simples (não aninhadas profundamente).
def find_braced_arg(text: str, start: int) -> tuple[str, int]:
    """Retorna conteúdo de {..} começando em text[start]=='{' e o índice após o }."""
    assert text[start] == "{", f"esperado '{{' em {start}, achei {text[start]!r}"
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError(f"chave não fechada começando em {start}")


def extract_todos(filepath: Path) -> list[tuple[str, str, str, int]]:
    """Retorna lista de (tipo, descricao, explicacao, linha) encontrados em filepath."""
    text = filepath.read_text(encoding="utf-8")
    results = []
    for m in re.finditer(r"\\(todoex|todoblock)\b\s*", text):
        cmd = m.group(1)
        pos = m.end()
        # pular espaços
        while pos < len(text) and text[pos] in " \t\n":
            pos += 1
        if pos >= len(text) or text[pos] != "{":
            continue
        try:
            arg1, after1 = find_braced_arg(text, pos)
            while after1 < len(text) and text[after1] in " \t\n":
                after1 += 1
            if after1 >= len(text) or text[after1] != "{":
                continue
            arg2, _ = find_braced_arg(text, after1)
        except ValueError:
            continue
        # linha (1-based)
        linha = text.count("\n", 0, m.start()) + 1
        # limpar quebras de linha internas
        arg1_clean = " ".join(arg1.split())
        arg2_clean = " ".join(arg2.split())
        results.append((cmd, arg1_clean, arg2_clean, linha))
    return results


def escape_latex(s: str) -> str:
    """Escapa apenas o mínimo para inserir texto puro dentro de LaTeX.
    Como os argumentos JÁ vieram de LaTeX, NÃO escapamos comandos — só ajustamos
    caracteres potencialmente problemáticos quando o texto é exibido em lista."""
    # As strings vêm de \todoex que já são LaTeX; preservamos.
    return s


def main():
    grouped: dict[str, list[tuple[str, str, str, str, int]]] = defaultdict(list)
    total = 0
    arquivos_visitados = 0

    for grupo, files in SCAN_DIRS:
        for fp in files:
            if not fp.exists():
                continue
            arquivos_visitados += 1
            for cmd, desc, expl, linha in extract_todos(fp):
                grouped[grupo].append((fp.name, cmd, desc, expl, linha))
                total += 1

    # Construir o LaTeX
    out = []
    out.append("% =============================================================================")
    out.append("% APÊNDICE F — LISTA CONSOLIDADA DE TODOS (PENDÊNCIAS DO DRAFT)")
    out.append("%")
    out.append("% ATENÇÃO: este arquivo é GERADO AUTOMATICAMENTE pelo script")
    out.append("%          03_codigo/scripts/extrair_todos.py")
    out.append("%          Edições manuais serão sobrescritas. Para mudar conteúdo,")
    out.append("%          edite o \\todoex correspondente no arquivo de origem.")
    out.append("% =============================================================================")
    out.append("")
    out.append("\\chapter{Lista consolidada de pendências do draft}")
    out.append("\\label{apendice:todos}")
    out.append("")
    out.append(
        "Este apêndice reúne, de forma consolidada e organizada por capítulo, todas as pendências marcadas no corpo do trabalho com os comandos \\verb|\\todoex| e \\verb|\\todoblock|. A lista é gerada automaticamente pelo script \\texttt{03\\_codigo/scripts/extrair\\_todos.py} a partir da varredura dos arquivos-fonte \\texttt{.tex} do projeto."
    )
    out.append("")
    out.append(
        f"Total de pendências identificadas no momento desta compilação: \\textbf{{{total}}}, distribuídas em {arquivos_visitados} arquivos-fonte."
    )
    out.append("")
    out.append(
        "\\noindent\\textbf{Como ler esta lista:} cada entrada apresenta o arquivo de origem, a descrição curta da pendência e a explicação detalhada do que precisa ser feito. A localização exata no texto pode ser encontrada buscando-se o comando \\verb|\\todoex| ou \\verb|\\todoblock| no arquivo de origem."
    )
    out.append("")

    for grupo, _files in SCAN_DIRS:
        items = grouped.get(grupo, [])
        if not items:
            continue
        out.append(f"\\section*{{{grupo}}}")
        out.append(f"\\addcontentsline{{toc}}{{section}}{{{grupo}}}")
        out.append("")
        out.append(f"\\noindent\\textbf{{Pendências neste capítulo:}} {len(items)}.")
        out.append("")
        out.append("\\begin{enumerate}[label=\\textbf{F.\\arabic*},leftmargin=*,itemsep=0.4em]")
        for fname, cmd, desc, expl, linha in items:
            badge = "TODO" if cmd == "todoex" else "TODO-BLOCO"
            out.append(f"    \\item \\textbf{{[{badge}]}} \\textit{{{escape_latex(desc)}}}\\\\")
            out.append(f"          \\textbf{{O quê fazer:}} {escape_latex(expl)}\\\\")
            out.append(f"          \\textbf{{Origem:}} \\texttt{{{fname}}} (linha~{linha}).")
        out.append("\\end{enumerate}")
        out.append("")

    out.append("\\section*{Observações de governança}")
    out.append("\\addcontentsline{toc}{section}{Observações de governança}")
    out.append("")
    out.append("\\begin{itemize}")
    out.append(
        "    \\item As pendências aqui listadas referem-se exclusivamente a lacunas do \\textit{draft}: dados a coletar em campo, validações com orientador, fotos a inserir, autorizações pendentes etc."
    )
    out.append(
        "    \\item Pendências de prazo macro (cronograma Mai/Out 2026) estão consolidadas em \\texttt{00\\_governanca/todo\\_mestre\\_executavel.md}."
    )
    out.append(
        "    \\item Antes de cada commit relevante no repositório, recomenda-se rodar \\texttt{python 03\\_codigo/scripts/extrair\\_todos.py} para manter este apêndice atualizado."
    )
    out.append(
        "    \\item Na versão final do trabalho, o pacote \\texttt{todonotes} deve ser desabilitado e os comandos \\verb|\\todoex|/\\verb|\\todoblock| devem ser redefinidos para não imprimir nada (ou todos os \\textit{TODOs} devem ter sido resolvidos)."
    )
    out.append("\\end{itemize}")
    out.append("")

    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"[ok] Apêndice F atualizado: {OUTPUT}")
    print(f"     Total de TODOs: {total}")
    print(f"     Arquivos varridos: {arquivos_visitados}")
    for g in grouped:
        print(f"     - {g}: {len(grouped[g])}")


if __name__ == "__main__":
    main()
