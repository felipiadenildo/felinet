"""Testes do helper felinet.runs (gerenciamento de execucoes rastreaveis)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from felinet.runs import (
    SLUG_PROTOCOLO_VAZIO,
    atualizar_latest,
    carregar_manifest,
    criar_run,
    finalizar_run,
    listar_runs,
    resolver_latest,
)


@pytest.fixture
def perfil_fake(tmp_path: Path, monkeypatch):
    """Constroi um Perfil sintetico apontando para tmp_path como raiz."""
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    (raiz / "pyproject.toml").write_text("[project]\nname='felinet'\n")
    configs = raiz / "configs"
    configs.mkdir()

    paths_yaml = """
fontes:
  kaggle_cats:  data/raw/camera_trap/kaggle_cats
  petface:      data/raw/reid/petface
raiz_runs: runs

perfis:
  dev:
    raw_camera_trap:    data/raw/camera_trap/kaggle_cats
    raw_petface:        data/raw/reid/petface
    interim:            data/dev/interim
    processed:          data/dev/processed
    artifacts_figuras:  artifacts/figuras
    artifacts_tabelas:  artifacts/tabelas
    saida_manifesto:           data/dev/legado/02
    saida_deteccoes:           data/dev/legado/03
    saida_classificacoes:      data/dev/legado/04
    saida_crops:               data/dev/legado/05
    anotacao_identidade:       data/dev/legado/06.json
    saida_embeddings:          data/dev/legado/07.npz
    saida_avaliacao_pipeline:  data/dev/legado/08.json
    fonte_default_operacional: kaggle_cats
    fonte_default_metodologico: petface
"""
    (configs / "paths.yaml").write_text(paths_yaml)
    monkeypatch.setenv("FELINET_CONFIG", str(configs / "paths.yaml"))

    from felinet.config import carregar_perfil
    carregar_perfil.cache_clear()
    return carregar_perfil("dev")


def test_criar_run_operacional(perfil_fake, tmp_path: Path):
    raiz_runs = tmp_path / "runs_out"
    run = criar_run(
        perfil=perfil_fake, modo="operacional", fonte="kaggle_cats",
        raiz_runs=raiz_runs,
    )

    # Estrutura do caminho
    assert run.raiz.exists()
    partes = run.raiz.relative_to(raiz_runs).parts
    assert partes[0] == "operacional"
    assert partes[1] == "kaggle_cats"
    assert partes[2] == "dev"
    assert partes[3] == SLUG_PROTOCOLO_VAZIO

    # Manifest existe e tem campos basicos
    assert run.manifest_path.exists()
    manifest = json.loads(run.manifest_path.read_text())
    assert manifest["modo"] == "operacional"
    assert manifest["fonte"] == "kaggle_cats"
    assert manifest["perfil"] == "dev"
    assert manifest["protocolo"] is None
    assert "data_inicio" in manifest
    assert manifest["data_fim"] is None  # finalizar_run preenche depois


def test_criar_run_metodologico_exige_protocolo(perfil_fake, tmp_path: Path):
    with pytest.raises(ValueError, match="protocolo"):
        criar_run(
            perfil=perfil_fake, modo="metodologico", fonte="petface",
            raiz_runs=tmp_path / "runs_out",
        )


def test_criar_run_metodologico(perfil_fake, tmp_path: Path):
    raiz_runs = tmp_path / "runs_out"
    run = criar_run(
        perfil=perfil_fake, modo="metodologico", fonte="petface",
        protocolo="n0050", raiz_runs=raiz_runs,
    )
    assert run.protocolo == "n0050"
    assert "n0050" in str(run.raiz)
    manifest = json.loads(run.manifest_path.read_text())
    assert manifest["protocolo"] == "n0050"


def test_modo_invalido_falha(perfil_fake, tmp_path: Path):
    with pytest.raises(ValueError, match="modo invalido"):
        criar_run(
            perfil=perfil_fake, modo="experimental", fonte="kaggle_cats",
            raiz_runs=tmp_path / "runs_out",
        )


def test_tag_aparece_no_caminho(perfil_fake, tmp_path: Path):
    run = criar_run(
        perfil=perfil_fake, modo="operacional", fonte="kaggle_cats",
        tag="thr025", raiz_runs=tmp_path / "runs_out",
    )
    assert "__thr025" in run.raiz.name


def test_latest_symlink(perfil_fake, tmp_path: Path):
    raiz_runs = tmp_path / "runs_out"
    run = criar_run(
        perfil=perfil_fake, modo="metodologico", fonte="petface",
        protocolo="n0200", raiz_runs=raiz_runs,
    )
    link = raiz_runs / "latest" / "metodologico__petface__dev__n0200"
    assert link.is_symlink()
    assert link.resolve() == run.raiz.resolve()


def test_resolver_latest(perfil_fake, tmp_path: Path):
    raiz_runs = tmp_path / "runs_out"
    run = criar_run(
        perfil=perfil_fake, modo="metodologico", fonte="petface",
        protocolo="n0200", raiz_runs=raiz_runs,
    )
    alvo = resolver_latest(
        modo="metodologico", fonte="petface", perfil="dev",
        protocolo="n0200", raiz_runs=raiz_runs,
    )
    assert alvo is not None
    assert alvo.resolve() == run.raiz.resolve()


def test_resolver_latest_nao_existe(tmp_path: Path):
    alvo = resolver_latest(
        modo="operacional", fonte="x", perfil="dev", raiz_runs=tmp_path,
    )
    assert alvo is None


def test_finalizar_run(perfil_fake, tmp_path: Path):
    run = criar_run(
        perfil=perfil_fake, modo="operacional", fonte="kaggle_cats",
        raiz_runs=tmp_path / "runs_out",
    )
    finalizar_run(
        run, sucesso=True, mensagem="ok",
        metricas_resumo={"n_embeddings": 42},
    )
    manifest = carregar_manifest(run)
    assert manifest["sucesso"] is True
    assert manifest["mensagem"] == "ok"
    assert manifest["metricas_resumo"]["n_embeddings"] == 42
    assert manifest["data_fim"] is not None
    assert manifest["duracao_s"] is not None


def test_listar_runs(perfil_fake, tmp_path: Path):
    raiz_runs = tmp_path / "runs_out"
    criar_run(
        perfil=perfil_fake, modo="operacional", fonte="kaggle_cats",
        raiz_runs=raiz_runs,
    )
    criar_run(
        perfil=perfil_fake, modo="metodologico", fonte="petface",
        protocolo="n0050", raiz_runs=raiz_runs,
    )
    criar_run(
        perfil=perfil_fake, modo="metodologico", fonte="petface",
        protocolo="n0200", raiz_runs=raiz_runs,
    )

    todos = listar_runs(raiz_runs)
    assert len(todos) == 3

    so_metodologico = listar_runs(raiz_runs, modo="metodologico")
    assert len(so_metodologico) == 2

    n50 = listar_runs(raiz_runs, modo="metodologico", protocolo="n0050")
    assert len(n50) == 1
    assert n50[0].manifest["protocolo"] == "n0050"


def test_atualizar_latest_idempotente(perfil_fake, tmp_path: Path):
    """Atualizar latest duas vezes nao quebra."""
    raiz_runs = tmp_path / "runs_out"
    run = criar_run(
        perfil=perfil_fake, modo="operacional", fonte="kaggle_cats",
        raiz_runs=raiz_runs,
    )
    atualizar_latest(run, raiz_runs)  # idempotente
    atualizar_latest(run, raiz_runs)
    link = raiz_runs / "latest" / "operacional__kaggle_cats__dev"
    assert link.is_symlink()
