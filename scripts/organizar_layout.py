#!/usr/bin/env python3
"""Organiza o layout de pastas para o esquema runs/.

Cria:
    data/raw/{camera_trap,reid}/       (pontos de montagem - symlinks externos)
    data/dev/reid_mini/                (subset Re-ID versionado)
    runs/{operacional,metodologico,latest}/
    artifacts/{figuras,tabelas}/{operacional,metodologico}/
    reports/                           (relatorios MD/HTML)

E atualiza:
    .gitignore                         (cobre runs/, data/raw/, etc.)

Idempotente: pode ser rodado multiplas vezes sem efeitos colaterais.

Uso:
    python scripts/organizar_layout.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DIRETORIOS = [
    "data/raw/camera_trap",
    "data/raw/reid",
    "data/dev/reid_mini",
    "data/dev/interim",
    "data/dev/processed",
    "runs/operacional",
    "runs/metodologico",
    "runs/latest",
    "artifacts/figuras/operacional",
    "artifacts/figuras/metodologico",
    "artifacts/tabelas/operacional",
    "artifacts/tabelas/metodologico",
    "reports",
    "scripts",
]

READMES = {
    "data/raw/camera_trap": (
        "# data/raw/camera_trap/\n\n"
        "Pontos de montagem para datasets de camera-trap (operacional).\n"
        "Cada subpasta e um SYMLINK para a localizacao real do dataset.\n\n"
        "Exemplos:\n\n"
        "    ln -s /mnt/ssd/datasets/campus2_2025 campus2_2025\n"
        "    ln -s /mnt/ssd/datasets/lila_ena24   lila_ena24\n"
        "    ln -s ~/.cache/kagglehub/datasets/samuelayman/cat-dataset/versions/1 kaggle_cats\n\n"
        "Registrar a fonte tambem em ``configs/paths.yaml`` -> ``fontes:``.\n"
        "Ver ``docs/runbooks/conectar_ssd_symlinks.md``.\n"
    ),
    "data/raw/reid": (
        "# data/raw/reid/\n\n"
        "Pontos de montagem para datasets de Re-ID (metodologico).\n"
        "Cada subpasta e um SYMLINK para a localizacao real do dataset.\n\n"
        "Exemplos:\n\n"
        "    ln -s /mnt/ssd/datasets/petface petface\n\n"
        "Registrar a fonte tambem em ``configs/paths.yaml`` -> ``fontes:``.\n"
    ),
    "runs": (
        "# runs/\n\n"
        "Diretorio de execucoes (gitignored).\n\n"
        "Cada execucao do felinet (operacional ou metodologica) cria um\n"
        "diretorio identificado pela tupla (modo, fonte, perfil, [protocolo],\n"
        "git_sha[, tag]):\n\n"
        "    runs/<modo>/<fonte>/<perfil>/<protocolo|_>/<gitsha>[__<tag>]/\n\n"
        "O symlink ``latest/<chave>`` aponta para o ultimo run de cada combinacao.\n"
        "Ver ``docs/arquitetura/layout_runs.md``.\n"
    ),
    "reports": (
        "# reports/\n\n"
        "Relatorios consolidados (Markdown/HTML) gerados a partir dos runs.\n"
        "Versionados quando representam um snapshot citado na monografia.\n"
    ),
}

GITKEEPS = [
    "data/raw/camera_trap/.gitkeep",
    "data/raw/reid/.gitkeep",
    "runs/.gitkeep",
    "reports/.gitkeep",
]

# Linhas a adicionar ao .gitignore (idempotente)
GITIGNORE_BLOCO = """
# Layout runs/ ---------------------------------------------------
runs/
!runs/.gitkeep
!runs/README.md

# Datasets externos (pontos de montagem) -------------------------
data/raw/
!data/raw/camera_trap/.gitkeep
!data/raw/camera_trap/README.md
!data/raw/reid/.gitkeep
!data/raw/reid/README.md
data/dev/interim/
data/dev/processed/
data/dev/reid_mini/*
!data/dev/reid_mini/README.md

# Reports gerados (exceto os curados) ----------------------------
reports/_tmp_*.md
reports/_tmp_*.html
"""

MARCADOR_GITIGNORE = "# Layout runs/"


def criar_diretorios(dry_run: bool) -> None:
    for d in DIRETORIOS:
        caminho = RAIZ / d
        if caminho.exists():
            print(f"[skip] {d} (ja existe)")
            continue
        if dry_run:
            print(f"[DRY ] mkdir -p {d}")
        else:
            caminho.mkdir(parents=True, exist_ok=True)
            print(f"[ ok ] mkdir -p {d}")


def criar_readmes(dry_run: bool) -> None:
    for relativo, conteudo in READMES.items():
        caminho = RAIZ / relativo / "README.md"
        if caminho.exists():
            print(f"[skip] {relativo}/README.md (ja existe)")
            continue
        if dry_run:
            print(f"[DRY ] write {relativo}/README.md")
        else:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(conteudo, encoding="utf-8")
            print(f"[ ok ] write {relativo}/README.md")


def criar_gitkeeps(dry_run: bool) -> None:
    for relativo in GITKEEPS:
        caminho = RAIZ / relativo
        if caminho.exists():
            print(f"[skip] {relativo} (ja existe)")
            continue
        if dry_run:
            print(f"[DRY ] touch {relativo}")
        else:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.touch()
            print(f"[ ok ] touch {relativo}")


def atualizar_gitignore(dry_run: bool) -> None:
    gitignore = RAIZ / ".gitignore"
    if not gitignore.exists():
        if dry_run:
            print("[DRY ] cria .gitignore")
        else:
            gitignore.write_text(GITIGNORE_BLOCO.lstrip(), encoding="utf-8")
            print("[ ok ] cria .gitignore")
        return
    texto = gitignore.read_text(encoding="utf-8")
    if MARCADOR_GITIGNORE in texto:
        print("[skip] .gitignore ja contem bloco runs/")
        return
    novo = texto.rstrip() + "\n" + GITIGNORE_BLOCO
    if dry_run:
        print("[DRY ] append bloco runs/ ao .gitignore")
    else:
        gitignore.write_text(novo, encoding="utf-8")
        print("[ ok ] append bloco runs/ ao .gitignore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="So mostra o que faria, sem modificar nada.",
    )
    args = parser.parse_args()
    print(f"Raiz do projeto: {RAIZ}")
    print(f"Modo: {'dry-run' if args.dry_run else 'EXECUTAR'}")
    print()

    print("[1/4] Criando diretorios...")
    criar_diretorios(args.dry_run)
    print()
    print("[2/4] Criando READMEs...")
    criar_readmes(args.dry_run)
    print()
    print("[3/4] Criando .gitkeep...")
    criar_gitkeeps(args.dry_run)
    print()
    print("[4/4] Atualizando .gitignore...")
    atualizar_gitignore(args.dry_run)
    print()
    print("OK. Proximos passos:")
    print("  1. Criar symlinks em data/raw/camera_trap/ e data/raw/reid/")
    print("     (ver docs/runbooks/conectar_ssd_symlinks.md)")
    print("  2. Registrar fontes em configs/paths.yaml -> fontes:")
    print("  3. Rodar: felinet pipeline executar --fonte <slug> --perfil dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
