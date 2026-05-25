"""Valida estrutura do PetFace antes da avaliacao Re-ID."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets.petface import (
    carregar_reidentification,
    subset_esta_pronto,
)


def main() -> int:
    raiz = Path("04_dados/raw/petface")
    csv = raiz / "split" / "cat" / "reidentification.csv"
    img_dir = raiz / "images" / "cat"

    print(f"[1/4] Verificando raiz: {raiz}")
    if not raiz.exists():
        print(f"  ERRO: {raiz} nao existe.")
        return 1
    print("  OK")

    print(f"[2/4] Verificando CSV: {csv}")
    if not csv.exists():
        print(f"  ERRO: {csv} nao encontrado.")
        return 1
    print("  OK")

    print(f"[3/4] Verificando diretorio de imagens: {img_dir}")
    if not img_dir.exists():
        print(f"  ERRO: {img_dir} nao encontrado.")
        return 1
    pastas = [p for p in img_dir.iterdir() if p.is_dir()]
    print(f"  OK -- {len(pastas)} pastas de individuos em disco")

    print("[4/4] Validando integridade e prontidao do subset")
    pronto = subset_esta_pronto(raiz)
    print(f"  subset_esta_pronto = {pronto}")
    if not pronto:
        return 2

    # Amostra com 50 individuos
    registros = carregar_reidentification(raiz, max_individuos=50)
    total_galeria = sum(len(r.galeria) for r in registros)
    media_galeria = total_galeria / len(registros) if registros else 0
    print("  Amostra (max_individuos=50):")
    print(f"    Individuos validos: {len(registros)}")
    print(f"    Total imagens query: {len(registros)}")
    print(f"    Total imagens galeria: {total_galeria}")
    print(f"    Media imagens/galeria: {media_galeria:.2f}")
    if registros:
        primeiro = registros[0]
        print(
            f"    Exemplo ID {primeiro.id_individuo}: "
            f"query={primeiro.query.name}, "
            f"galeria={[p.name for p in primeiro.galeria]}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
