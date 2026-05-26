"""Testes do orquestrador da cascata (smoke, sem GPU).

Os modelos pesados (MegaDetector, SpeciesNet, MegaDescriptor) sao
mockados via monkeypatch -- o objetivo destes testes nao e avaliar
acuracia, mas verificar que o encadeamento I -> II -> III -> IV grava
os artefatos esperados nas pastas certas do perfil dev.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def perfil_dev_tmp(tmp_path: Path, monkeypatch):
    """Constroi um perfil dev sintetico apontando para tmp_path.

    Cria 2 imagens cruas em ``01_brutas/`` e injeta um paths.yaml.
    """
    raiz = tmp_path / "felinet_repo"
    raiz.mkdir()
    (raiz / "pyproject.toml").write_text("[project]\nname='felinet'\n")
    configs = raiz / "configs"
    configs.mkdir()

    brutas = raiz / "data/dev/pipeline/01_brutas"
    brutas.mkdir(parents=True)
    for i, cor in enumerate([(255, 0, 0), (0, 255, 0)]):
        Image.new("RGB", (640, 480), color=cor).save(brutas / f"IMG_{i:04d}.jpg")

    paths_yaml = f"""
perfis:
  dev:
    raw_camera_trap:    data/dev/pipeline/01_brutas
    raw_petface:        data/dev/petface_mini
    interim:            data/dev/pipeline
    processed:          data/dev/pipeline
    artifacts_figuras:  artifacts/figuras
    artifacts_tabelas:  artifacts/tabelas
    saida_manifesto:           data/dev/pipeline/02_manifesto
    saida_deteccoes:           data/dev/pipeline/03_deteccoes
    saida_classificacoes:      data/dev/pipeline/04_classificacoes
    saida_crops:               data/dev/pipeline/05_crops_felis_catus
    anotacao_identidade:       data/dev/pipeline/06_anotacao_identidade.json
    saida_embeddings:          data/dev/pipeline/07_embeddings.npz
    saida_avaliacao_pipeline:  data/dev/pipeline/08_avaliacao_pipeline.json
"""
    (configs / "paths.yaml").write_text(paths_yaml)
    monkeypatch.setenv("FELINET_CONFIG", str(configs / "paths.yaml"))

    # Limpa cache do lru_cache
    from felinet.config import carregar_perfil
    carregar_perfil.cache_clear()
    return carregar_perfil("dev")


def test_relatorio_cascata_estrutura():
    """Smoke do schema RelatorioCascata (sem dependencias externas)."""
    from felinet.pipeline.orquestrador import RelatorioCascata

    rel = RelatorioCascata(
        n_brutas=5, n_manifesto=5, n_deteccoes_animal=4,
        n_classificacoes_felis_catus=3, n_crops_gerados=3, n_embeddings=3,
        sucesso=True,
    )
    d = rel.como_dicionario()
    assert d["n_brutas"] == 5
    assert d["sucesso"] is True
    assert "n_embeddings" in d


def test_cascata_pasta_brutas_inexistente(tmp_path, monkeypatch):
    """Cascata deve falhar graciosamente se 01_brutas/ nao existir.

    Importante: a checagem da pasta acontece ANTES dos imports pesados
    (torch/MegaDetector), entao este teste roda em ambiente minimo.
    """
    from felinet.config import Perfil
    from felinet.pipeline.orquestrador import executar_cascata

    perfil = Perfil(
        nome="teste",
        raw_camera_trap=tmp_path / "inexistente",
        raw_petface=tmp_path / "pf",
        interim=tmp_path / "interim",
        processed=tmp_path / "processed",
        artifacts_figuras=tmp_path / "figs",
        artifacts_tabelas=tmp_path / "tabs",
        saida_manifesto=tmp_path / "manif",
        saida_deteccoes=tmp_path / "det",
        saida_classificacoes=tmp_path / "clf",
        saida_crops=tmp_path / "crops",
        anotacao_identidade=tmp_path / "anot.json",
        saida_embeddings=tmp_path / "emb.npz",
        saida_avaliacao_pipeline=tmp_path / "aval.json",
    )
    relatorio = executar_cascata(perfil)
    assert relatorio.sucesso is False
    assert "nao existe" in relatorio.mensagem
