#!/usr/bin/env python3
"""Remove arquivos orfaos/duplicados nao alinhados ao projeto v23.

Lista o que pretende remover, pede confirmacao, e executa com `git rm`
quando possivel (preserva rastreabilidade Git).

Uso:
    python scripts/organizar_repo.py           # interativo
    python scripts/organizar_repo.py --aplicar # sem perguntar
    python scripts/organizar_repo.py --listar  # so lista, nao remove
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Pastas/arquivos identificados como orfaos no v23
ALVOS = [
    # Pasta de patch ja aplicada (Bloco 11 do TODO)
    "felinet_runs_patch",
    # Pasta de patch ja aplicada (resumo_html)
    "resumo_html_patch",
    # Artefatos antigos de runs no data/dev (substituidos por runs/)
    "data/dev/pipeline/02_manifesto",
    "data/dev/pipeline/03_deteccoes",
    "data/dev/pipeline/04_classificacoes",
    "data/dev/pipeline/05_crops_felis_catus",
    "data/dev/pipeline/06_anotacao_identidade.json",
    # Duplicatas em interim (substituidas pelo layout runs/)
    "data/interim/classificacoes_amostras.json",
    "data/interim/deteccoes_amostras.json",
    "data/interim/deteccoes_subset_dev.json",
    "data/interim/embeddings_subset_dev.json",
    "data/interim/embeddings_petface.npz",
    # avaliacao antigos (sem sufixo nXXXX) — ficam apenas os versionados
    "data/processed/avaliacao_reid_petface.json",
    "data/processed/resumo_reid_petface.md",
]


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        sys.stderr.write("ERRO: nao parece ser um repo git.\n")
        sys.exit(2)
    return Path(out.stdout.strip())


def existe(raiz: Path, alvo: str) -> Path | None:
    p = raiz / alvo
    return p if p.exists() else None


def remover(raiz: Path, alvo: str) -> str:
    p = raiz / alvo
    rel = str(p.relative_to(raiz))
    # tenta git rm primeiro
    r = subprocess.run(
        ["git", "rm", "-rf", "--quiet", rel],
        cwd=raiz, capture_output=True, text=True, check=False,
    )
    if r.returncode == 0:
        return f"git rm  {rel}"
    # fallback: nao estava rastreado
    if p.is_dir():
        import shutil
        shutil.rmtree(p)
    else:
        p.unlink()
    return f"rm      {rel}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true",
                        help="Remove sem perguntar")
    parser.add_argument("--listar", action="store_true",
                        help="So lista, nao remove")
    args = parser.parse_args()

    raiz = repo_root()
    presentes = [a for a in ALVOS if existe(raiz, a)]

    if not presentes:
        print("Nada a limpar — repo ja alinhado ao v23.")
        return 0

    print(f"\nEncontrados {len(presentes)} alvos para remocao:\n")
    for a in presentes:
        print(f"  - {a}")
    print()

    if args.listar:
        return 0

    if not args.aplicar:
        resp = input("Confirma remocao? [s/N]: ").strip().lower()
        if resp not in ("s", "sim", "y", "yes"):
            print("Abortado.")
            return 1

    print()
    for a in presentes:
        acao = remover(raiz, a)
        print(f"  {acao}")
    print(f"\nRemocao concluida ({len(presentes)} alvos).")
    print("Lembre de revisar com `git status` e commitar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
