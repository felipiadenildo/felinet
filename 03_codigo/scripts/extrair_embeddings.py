"""Extrai embeddings MegaDescriptor para crops felis_catus do subset dev.

Le o JSON consolidado da Fase III (gerado por classificar_amostras.py),
filtra apenas as classificacoes com status ``felis_catus`` e produz um
``Embedding`` por crop usando o MegaDescriptor-T-224.

Saida em ``04_dados/interim/embeddings_subset_dev.json`` no schema da
Fase IV (Embedding com media_path, bbox_indice, vetor 768-d, modelo,
tempo_ms).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.fase2_deteccao.schema import BoundingBox  # noqa: E402
from pipeline.fase3_classificacao.schema import STATUS_FELIS_CATUS  # noqa: E402
from pipeline.fase3_classificacao.speciesnet import CropEntrada  # noqa: E402
from pipeline.fase4_reid.megadescriptor import (  # noqa: E402
    ExtratorMegaDescriptor,
)
from pipeline.fase4_reid.schema import (  # noqa: E402
    Embedding,
    salvar_embeddings_json,
)

ENTRADA_CLASSIFICACOES = Path("04_dados/interim/classificacoes_amostras.json")
ENTRADA_DETECCOES = Path("04_dados/interim/deteccoes_subset_dev.json")
ARQUIVO_SAIDA = Path("04_dados/interim/embeddings_subset_dev.json")


def _carregar_json(caminho: Path) -> dict:
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {caminho}. "
            "Rode 'make subset-dev' antes de extrair embeddings."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def _construir_indice_bboxes(deteccoes_json: dict) -> dict[str, list[dict]]:
    """Mapeia media_path -> lista de deteccoes (com bbox)."""
    indice: dict[str, list[dict]] = {}
    resultados = deteccoes_json.get("resultados") or deteccoes_json.get("imagens", [])
    for resultado in resultados:
        media_path = resultado["media_path"]
        indice[media_path] = resultado["deteccoes"]
    return indice


def _crop_de_classificacao(
    classificacao: dict,
    deteccoes_da_imagem: list[dict],
) -> CropEntrada:
    """Reconstroi CropEntrada a partir do JSON de classificacao + deteccoes."""
    bbox_indice = classificacao["bbox_indice"]
    bbox_dict = deteccoes_da_imagem[bbox_indice]["bbox"]
    bbox = BoundingBox(
        x=bbox_dict["x"],
        y=bbox_dict["y"],
        w=bbox_dict["w"],
        h=bbox_dict["h"],
    )
    return CropEntrada(
        media_path=Path(classificacao["media_path"]),
        bbox=bbox,
        indice=bbox_indice,
    )


def extrair_embeddings_subset() -> int:
    """Extrai embeddings para todos os crops felis_catus do subset."""
    classificacoes_json = _carregar_json(ENTRADA_CLASSIFICACOES)
    deteccoes_json = _carregar_json(ENTRADA_DETECCOES)
    indice_deteccoes = _construir_indice_bboxes(deteccoes_json)

    # Coleta todas as classificacoes felis_catus
    candidatos: list[tuple[str, dict]] = []
    for imagem in classificacoes_json.get("imagens", []):
        for classificacao in imagem.get("classificacoes", []):
            if classificacao["status"] == STATUS_FELIS_CATUS:
                candidatos.append((imagem["arquivo"], classificacao))

    if not candidatos:
        print("Nenhum crop felis_catus encontrado no subset.")
        return 1

    print(f"Extraindo embeddings de {len(candidatos)} crop(s) felis_catus...")
    print("Inicializando MegaDescriptor-T-224 (primeira execucao baixa pesos)...")
    extrator = ExtratorMegaDescriptor()

    embeddings: list[Embedding] = []
    for indice, (arquivo, classificacao) in enumerate(candidatos, start=1):
        media_path = classificacao["media_path"]
        deteccoes = indice_deteccoes.get(media_path, [])
        crop = _crop_de_classificacao(classificacao, deteccoes)
        embedding = extrator.extrair(crop)
        embeddings.append(embedding)
        print(
            f"  [{indice:02d}/{len(candidatos):02d}] {arquivo:<32s} "
            f"crop#{crop.indice} -> dim={embedding.dimensao} "
            f"[{embedding.tempo_ms:.0f} ms]"
        )

    salvar_embeddings_json(embeddings, ARQUIVO_SAIDA)
    print(f"\nEmbeddings gravados em: {ARQUIVO_SAIDA}")
    print(f"Total: {len(embeddings)} vetor(es) de {embeddings[0].dimensao} dimensoes")
    return 0


if __name__ == "__main__":
    sys.exit(extrair_embeddings_subset())
