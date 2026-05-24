#!/usr/bin/env python3
"""
validar_latex.py
----------------
Validação sintática leve dos arquivos .tex do projeto sem rodar LaTeX:
- ambientes balanceados (\\begin{X}/\\end{X})
- contagem de \\chapter, \\section, ...
- referências (\\ref/\\cite) sem alvo
- chaves desbalanceadas (heurística)
"""

from __future__ import annotations
import re
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path("/home/user/workspace/tcc_gatos_campus2/02_latex")

TEX_FILES = sorted(BASE.rglob("*.tex"))

errors: list[str] = []
warnings: list[str] = []
stats: Counter = Counter()


def check_environments(path: Path, text: str) -> None:
    """Verifica que cada \\begin{X} tem um \\end{X} correspondente, na ordem."""
    stack = []
    pattern = re.compile(r"\\(begin|end)\{([^}]+)\}")
    for m in pattern.finditer(text):
        kind, env = m.group(1), m.group(2)
        line = text.count("\n", 0, m.start()) + 1
        if kind == "begin":
            stack.append((env, line))
        else:  # end
            if not stack:
                errors.append(f"{path}:{line}: \\end{{{env}}} sem \\begin correspondente")
            else:
                top_env, top_line = stack.pop()
                if top_env != env:
                    errors.append(
                        f"{path}:{line}: \\end{{{env}}} mas o topo é \\begin{{{top_env}}} (linha {top_line})"
                    )
    for env, line in stack:
        errors.append(f"{path}:{line}: \\begin{{{env}}} sem \\end correspondente")


def check_braces(path: Path, text: str) -> None:
    """Heurística: conta { e } por arquivo, ignorando dentro de % comentários e \\{ \\}."""
    # Remove comentários (% até fim de linha) e escapes \{ \}
    cleaned = []
    for line in text.split("\n"):
        # tirar comentários (mas não em \%)
        idx = -1
        i = 0
        while i < len(line):
            if line[i] == "\\" and i + 1 < len(line):
                i += 2
                continue
            if line[i] == "%":
                idx = i
                break
            i += 1
        if idx >= 0:
            line = line[:idx]
        cleaned.append(line)
    text2 = "\n".join(cleaned)
    # remover \{ e \}
    text2 = re.sub(r"\\[{}]", "", text2)
    o = text2.count("{")
    c = text2.count("}")
    if o != c:
        warnings.append(f"{path}: chaves desbalanceadas (heurística): {{={o}, }}={c}")


def count_structure(path: Path, text: str) -> None:
    for cmd in (
        "chapter",
        "section",
        "subsection",
        "subsubsection",
        "todoex",
        "todoblock",
        "cite",
        "citeonline",
        "input",
        "include",
        "lstinputlisting",
        "label",
    ):
        stats[cmd] += len(re.findall(rf"\\{cmd}\b", text))


for fp in TEX_FILES:
    text = fp.read_text(encoding="utf-8")
    check_environments(fp.relative_to(BASE), text)
    check_braces(fp.relative_to(BASE), text)
    count_structure(fp, text)

print("=" * 70)
print(f"VALIDAÇÃO SINTÁTICA DO PROJETO TCC LaTeX")
print("=" * 70)
print(f"\nArquivos .tex varridos: {len(TEX_FILES)}")
print(f"\n--- Erros ({len(errors)}) ---")
for e in errors:
    print(f"  {e}")
print(f"\n--- Avisos ({len(warnings)}) ---")
for w in warnings:
    print(f"  {w}")
print(f"\n--- Estatísticas estruturais ---")
for cmd in (
    "chapter",
    "section",
    "subsection",
    "subsubsection",
    "input",
    "include",
    "lstinputlisting",
    "label",
    "cite",
    "citeonline",
    "todoex",
    "todoblock",
):
    print(f"  \\{cmd:18}: {stats[cmd]}")

# Verificar BibTeX entries usados vs definidos
bib_paths = [BASE / "bib" / "references.bib", BASE / "bib" / "references_complemento.bib"]
bib_keys: set[str] = set()
for bib_path in bib_paths:
    if bib_path.exists():
        bib_text = bib_path.read_text(encoding="utf-8")
        bib_keys.update(re.findall(r"@\w+\s*\{\s*([^,]+),", bib_text))
if bib_keys:
    cite_keys: set[str] = set()
    for fp in TEX_FILES:
        text = fp.read_text(encoding="utf-8")
        for m in re.finditer(
            r"\\(?:cite|citeonline|citeauthor|citeyear|citet|citep)(?:\[[^]]*\])?\{([^}]+)\}", text
        ):
            for k in m.group(1).split(","):
                cite_keys.add(k.strip())
    missing = sorted(cite_keys - bib_keys)
    unused = sorted(bib_keys - cite_keys)
    print(f"\n--- Bibliografia ---")
    print(f"  Entradas em references.bib: {len(bib_keys)}")
    print(f"  Chaves citadas no texto:    {len(cite_keys)}")
    print(f"  Citadas mas SEM entrada bib: {len(missing)}")
    for k in missing[:25]:
        print(f"    - {k}")
    if len(missing) > 25:
        print(f"    ... e mais {len(missing) - 25}")
    print(f"  Entradas bib NUNCA citadas:  {len(unused)}")

print()
print("=" * 70)
if errors:
    print(f"FALHAS: {len(errors)} erro(s). Revisar acima.")
else:
    print("OK: nenhum erro estrutural detectado.")
print("=" * 70)
