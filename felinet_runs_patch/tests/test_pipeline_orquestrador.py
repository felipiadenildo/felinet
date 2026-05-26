"""Testes do orquestrador da cascata (smoke, sem GPU).

Os modelos pesados (MegaDetector, SpeciesNet, MegaDescriptor) ficam
fora do escopo destes testes -- o objetivo e verificar que o
encadeamento falha graciosamente quando a pasta de brutas nao existe
(checagem antes dos imports pesados).
"""
from __future__ import annotations

from pathlib import Path

from felinet.pipeline.orquestrador import RelatorioCascata, executar_cascata
from felinet.runs import RunDir


def test_relatorio_cascata_estrutura():
    """Smoke do schema RelatorioCascata."""
    rel = RelatorioCascata(
        n_brutas=5, n_manifesto=5, n_deteccoes_animal=4,
        n_classificacoes_felis_catus=3, n_crops_gerados=3, n_embeddings=3,
        sucesso=True,
    )
    d = rel.como_dicionario()
    assert d["n_brutas"] == 5
    assert d["sucesso"] is True
    assert "n_embeddings" in d


def test_cascata_pasta_brutas_inexistente(tmp_path: Path):
    """Cascata deve falhar graciosamente se pasta_brutas nao existir.

    A checagem acontece ANTES dos imports pesados (torch/MegaDetector),
    permitindo que este teste rode em ambiente minimo.
    """
    run = RunDir(
        raiz=tmp_path / "run_tmp",
        modo="operacional", fonte="fake", perfil="dev",
        protocolo="_", gitsha="nogit", chave_latest="operacional__fake__dev",
    )
    run.raiz.mkdir(parents=True)

    relatorio = executar_cascata(
        pasta_brutas=tmp_path / "inexistente",
        run=run,
    )
    assert relatorio.sucesso is False
    assert "nao existe" in relatorio.mensagem
