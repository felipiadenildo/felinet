"""Avalia Re-ID com MegaDescriptor no PetFace (categoria cat).

Saidas (com N nos nomes para preservar runs):
    04_dados/processed/avaliacao_reid_petface_n{N:04d}_{timestamp}.json
    04_dados/processed/avaliacao_reid_petface_latest.json (symlink)
    04_dados/interim/embeddings_petface_n{N:04d}.npz (cache por N)

Uso:
    python 03_codigo/scripts/avaliar_reid_petface.py [--max-individuos N]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets.petface import (  # noqa: E402
    RegistroPetFace,
    carregar_reidentification,
    subset_esta_pronto,
)
from pipeline.fase4_reid.avaliacao import (  # noqa: E402
    avaliar_top_k,
    matriz_similaridade_cosseno,
)
from pipeline.fase4_reid.megadescriptor import (  # noqa: E402
    ExtratorMegaDescriptor,
)

DIRETORIO_SAIDA = Path("04_dados/processed")
DIRETORIO_EMBEDDINGS = Path("04_dados/interim")
ARQUIVO_LATEST = DIRETORIO_SAIDA / "avaliacao_reid_petface_latest.json"


def extrair_embeddings(
    caminhos: list[Path],
    extrator: ExtratorMegaDescriptor,
    rotulo: str = "",
) -> np.ndarray:
    """Extrai embeddings L2-normalizados via extrair_de_pil."""
    vetores: list[np.ndarray] = []
    total = len(caminhos)
    for indice, caminho in enumerate(caminhos):
        img = Image.open(caminho).convert("RGB")
        emb = extrator.extrair_de_pil(
            media_path=str(caminho),
            bbox_indice=0,
            crop_img=img,
        )
        vetores.append(np.asarray(emb.vetor, dtype=np.float32))
        if (indice + 1) % 50 == 0 or indice == total - 1:
            print(f"  {rotulo} {indice + 1}/{total} embeddings extraidos")
    return np.stack(vetores, axis=0)


def montar_listas(
    registros: list[RegistroPetFace],
) -> tuple[list[Path], list[int], list[Path], list[int]]:
    """Separa registros em (queries, ids_query, galerias, ids_galeria)."""
    queries: list[Path] = []
    ids_query: list[int] = []
    galerias: list[Path] = []
    ids_galeria: list[int] = []
    for r in registros:
        queries.append(r.query)
        ids_query.append(r.id_individuo)
        for g in r.galeria:
            galerias.append(g)
            ids_galeria.append(r.id_individuo)
    return queries, ids_query, galerias, ids_galeria


def atualizar_symlink_latest(arquivo_alvo: Path) -> None:
    """Aponta avaliacao_reid_petface_latest.json para a saida mais recente."""
    if ARQUIVO_LATEST.exists() or ARQUIVO_LATEST.is_symlink():
        ARQUIVO_LATEST.unlink()
    ARQUIVO_LATEST.symlink_to(arquivo_alvo.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-individuos",
        type=int,
        default=50,
        help="Numero maximo de individuos a avaliar (default 50).",
    )
    args = parser.parse_args()
    n = args.max_individuos

    if not subset_esta_pronto():
        print(
            "PetFace nao pronto. "
            "Baixe e descompacte conforme instrucoes em datasets/petface.py.",
            file=sys.stderr,
        )
        return 1

    print(f"[1/5] Carregando registros PetFace (max={n})")
    registros = carregar_reidentification(max_individuos=n)
    queries, ids_q, galerias, ids_g = montar_listas(registros)
    print(
        f"  {len(registros)} individuos | "
        f"{len(queries)} queries | {len(galerias)} galeria"
    )

    print("[2/5] Carregando MegaDescriptor")
    extrator = ExtratorMegaDescriptor()
    print(f"  dispositivo: {extrator.dispositivo}")

    arquivo_embeddings = (
        DIRETORIO_EMBEDDINGS / f"embeddings_petface_n{n:04d}.npz"
    )

    precisa_reextrair = True
    if arquivo_embeddings.exists():
        npz = np.load(arquivo_embeddings)
        if (
            npz["queries"].shape[0] == len(queries)
            and npz["galerias"].shape[0] == len(galerias)
        ):
            print(f"[3/5] Reusando embeddings cacheados de {arquivo_embeddings}")
            emb_q = npz["queries"]
            emb_g = npz["galerias"]
            precisa_reextrair = False
        else:
            print("[3/5] Cache existente desatualizado, reextraindo")

    if precisa_reextrair:
        print("[3/5] Extraindo embeddings")
        emb_q = extrair_embeddings(queries, extrator, rotulo="[queries]")
        emb_g = extrair_embeddings(galerias, extrator, rotulo="[galeria]")
        arquivo_embeddings.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            arquivo_embeddings,
            queries=emb_q,
            galerias=emb_g,
            ids_query=np.asarray(ids_q),
            ids_galeria=np.asarray(ids_g),
        )
        print(f"      cache salvo em {arquivo_embeddings}")

    print(f"      shapes: queries={emb_q.shape}, galerias={emb_g.shape}")

    print("[4/5] Calculando matriz de similaridade e Top-K")
    sim = matriz_similaridade_cosseno(emb_q, emb_g)
    resultado = avaliar_top_k(sim, ids_q, ids_g, k_max=10)
    resultado_dict = asdict(resultado)
    resultado_dict["dim_embedding"] = int(emb_q.shape[1])
    resultado_dict["modelo"] = "MegaDescriptor-T-224"
    resultado_dict["dataset"] = "PetFace/cat"
    resultado_dict["max_individuos"] = n

    print("[5/5] Resultados:")
    for k, acc in resultado.top_k.items():
        print(f"  Top-{k}: {acc * 100:.2f}%")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    arquivo_saida = (
        DIRETORIO_SAIDA
        / f"avaliacao_reid_petface_n{n:04d}_{timestamp}.json"
    )
    DIRETORIO_SAIDA.mkdir(parents=True, exist_ok=True)
    with arquivo_saida.open("w", encoding="utf-8") as f:
        json.dump(resultado_dict, f, indent=2, ensure_ascii=False)
    print(f"  salvo: {arquivo_saida}")

    atualizar_symlink_latest(arquivo_saida)
    print(f"  latest -> {arquivo_saida.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
