"""Testes para pipeline.fase4_reid.schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from felinet.pipeline.fase4_reid.schema import (
    Embedding,
    carregar_embeddings_json,
    salvar_embeddings_json,
)


def _embedding_exemplo(
    media_path: str = "img.jpg",
    bbox_indice: int = 0,
    dim: int = 4,
) -> Embedding:
    return Embedding(
        media_path=media_path,
        bbox_indice=bbox_indice,
        vetor=[float(i) / 10 for i in range(dim)],
        modelo="MegaDescriptor-T-224",
        tempo_ms=12.3,
    )


def test_embedding_dimensao_corresponde_ao_vetor() -> None:
    emb = _embedding_exemplo(dim=768)
    assert emb.dimensao == 768


def test_embedding_rejeita_vetor_vazio() -> None:
    with pytest.raises(ValueError, match="vetor vazio"):
        Embedding(
            media_path="x.jpg",
            bbox_indice=0,
            vetor=[],
            modelo="m",
            tempo_ms=0.0,
        )


def test_salvar_embeddings_grava_json_com_metadados(tmp_path: Path) -> None:
    embs = [_embedding_exemplo("a.jpg"), _embedding_exemplo("b.jpg", bbox_indice=1)]
    caminho = tmp_path / "saida.json"
    salvar_embeddings_json(embs, caminho)
    assert caminho.exists()

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["total"] == 2
    assert dados["dimensao"] == 4
    assert len(dados["embeddings"]) == 2
    assert dados["embeddings"][0]["media_path"] == "a.jpg"


def test_carregar_embeddings_reconstroi_lista(tmp_path: Path) -> None:
    embs_origem = [_embedding_exemplo("a.jpg"), _embedding_exemplo("b.jpg")]
    caminho = tmp_path / "saida.json"
    salvar_embeddings_json(embs_origem, caminho)

    embs_carregados = carregar_embeddings_json(caminho)
    assert len(embs_carregados) == 2
    assert embs_carregados[0].media_path == "a.jpg"
    assert embs_carregados[0].vetor == embs_origem[0].vetor


def test_salvar_embeddings_grava_lista_vazia(tmp_path: Path) -> None:
    caminho = tmp_path / "vazio.json"
    salvar_embeddings_json([], caminho)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["total"] == 0
    assert dados["dimensao"] == 0
    assert dados["embeddings"] == []
