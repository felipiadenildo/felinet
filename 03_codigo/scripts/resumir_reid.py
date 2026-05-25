"""Imprime tabela comparativa de todas as rodadas de avaliacao Re-ID.

Le todos ``04_dados/processed/avaliacao_reid_petface_n*.json`` e mostra
N, n_queries, n_galeria, Top-1, Top-5, Top-10 em formato tabular.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DIRETORIO_SAIDA = Path("04_dados/processed")


def main() -> int:
    arquivos = sorted(
        DIRETORIO_SAIDA.glob("avaliacao_reid_petface_n*.json"),
        key=lambda p: p.name,
    )
    arquivos = [p for p in arquivos if not p.is_symlink()]

    if not arquivos:
        print("Nenhuma avaliacao encontrada em", DIRETORIO_SAIDA)
        return 1

    # Pega a rodada mais recente de cada N
    por_n: dict[int, Path] = {}
    for arq in arquivos:
        with arq.open(encoding="utf-8") as f:
            meta = json.load(f)
        n = meta["max_individuos"]
        # Como sorted alfabeticamente e timestamp UTC esta no nome, o ultimo vence
        por_n[n] = arq

    print()
    print(
        f"{'N':>5} | {'queries':>7} | {'galeria':>7} | "
        f"{'Top-1':>7} | {'Top-5':>7} | {'Top-10':>7} | arquivo"
    )
    print("-" * 95)
    for n in sorted(por_n.keys()):
        arq = por_n[n]
        with arq.open(encoding="utf-8") as f:
            meta = json.load(f)
        t1 = meta["top_k"].get("1", 0) * 100
        t5 = meta["top_k"].get("5", 0) * 100
        t10 = meta["top_k"].get("10", 0) * 100
        print(
            f"{n:>5} | {meta['n_queries']:>7} | {meta['n_galeria']:>7} | "
            f"{t1:>6.2f}% | {t5:>6.2f}% | {t10:>6.2f}% | {arq.name}"
        )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
