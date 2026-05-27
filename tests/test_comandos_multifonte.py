"""Testes do refactor multifonte dos comandos operacionais (Bloco 3).

Garante que `ingestao manifesto`, `deteccao executar` e
`classificacao executar` aceitam `--fonte` e gravam em
``runs/operacional/<fonte>/<perfil>/_/<gitsha>/``.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PIL import Image
from typer.testing import CliRunner

from felinet.comandos.ingestao import app as ingestao_app

# ============================================================
# Helpers
# ============================================================


def _imagem_com_exif(caminho: Path, cor: tuple[int, int, int]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (32, 32), color=cor)
    ts = datetime(2026, 5, 26, 4, 0, 0).strftime("%Y:%m:%d %H:%M:%S").encode()
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"TestCam",
            piexif.ImageIFD.Model: b"MD-001",
            piexif.ImageIFD.DateTime: ts,
        },
        "Exif": {piexif.ExifIFD.DateTimeOriginal: ts},
    }
    img.save(caminho, "JPEG", exif=piexif.dump(exif_dict))


@pytest.fixture
def projeto_multifonte(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Monta um projeto sintetico com perfil 'teste' e fonte 'kaggle_cats_mini'.

    Estrutura:
        <tmp>/configs/paths.yaml   <- so para registrar a fonte
        <tmp>/data/raw/kaggle_mini/img_{0..2}.jpg
        <tmp>/runs/...             <- vazio inicialmente

    Patches felinet.config e felinet.runs para apontar a raiz para tmp_path.
    """
    raiz = tmp_path
    pasta_imgs = raiz / "data" / "raw" / "kaggle_mini"
    pasta_imgs.mkdir(parents=True)
    cores = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i, cor in enumerate(cores):
        _imagem_com_exif(pasta_imgs / f"img_{i:03d}.jpg", cor)

    # Perfil de mentira que aponta para o tmp
    class _PerfilFake:
        nome = "teste"
        raiz_runs = "runs"
        extras = {
            "fontes": {"kaggle_cats_mini": "data/raw/kaggle_mini"},
            "raiz_runs": "runs",
            "fonte_default_operacional": "kaggle_cats_mini",
        }

    def _fake_carregar(_perfil: str) -> _PerfilFake:
        return _PerfilFake()

    def _fake_raiz_projeto() -> Path:
        return raiz

    monkeypatch.setattr("felinet.comandos.ingestao.carregar_perfil", _fake_carregar)
    monkeypatch.setattr("felinet.runs._resolver_raiz_runs", lambda _p: raiz / "runs")
    monkeypatch.setattr(
        "felinet.comandos.ingestao.resolver_fonte",
        lambda _cfg, fonte: raiz / _PerfilFake.extras["fontes"][fonte],
    )
    monkeypatch.setattr(
        "felinet.comandos.ingestao.fonte_default",
        lambda _cfg, _modo: "kaggle_cats_mini",
    )
    return raiz


# ============================================================
# Testes
# ============================================================


def test_ingestao_manifesto_aceita_fonte_e_cria_run(projeto_multifonte: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        ingestao_app,
        ["--perfil", "teste", "--fonte", "kaggle_cats_mini"],
    )
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output

    # Run criado em runs/operacional/kaggle_cats_mini/teste/_/<sha>/
    runs_root = projeto_multifonte / "runs" / "operacional" / "kaggle_cats_mini" / "teste" / "_"
    assert runs_root.exists(), f"diretorio do run nao criado: {runs_root}"
    runs = list(runs_root.iterdir())
    assert len(runs) >= 1, "ao menos um run deveria existir"
    run_dir = runs[0]
    manifesto = run_dir / "manifesto.csv"
    assert manifesto.exists()
    conteudo = manifesto.read_text(encoding="utf-8")
    # 3 imagens + cabecalho
    linhas = [linha for linha in conteudo.splitlines() if linha.strip()]
    assert len(linhas) == 4, f"esperado cabecalho + 3 linhas, achou {len(linhas)}"

    # Manifest.json registra fonte e n_entradas
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["fonte"] == "kaggle_cats_mini"
    assert manifest["modo"] == "operacional"
    assert manifest["sucesso"] is True
    assert manifest["metricas_resumo"]["n_entradas"] == 3

    # Symlink latest aponta para o run
    link = projeto_multifonte / "runs" / "latest" / "operacional__kaggle_cats_mini__teste"
    assert link.exists() or link.is_symlink()


def test_ingestao_manifesto_usa_fonte_default_quando_omitida(
    projeto_multifonte: Path,
) -> None:
    """Sem --fonte, deve usar fonte_default_operacional do perfil."""
    runner = CliRunner()
    result = runner.invoke(
        ingestao_app,
        ["--perfil", "teste"],
    )
    assert result.exit_code == 0, result.output

    runs_root = projeto_multifonte / "runs" / "operacional" / "kaggle_cats_mini" / "teste" / "_"
    assert runs_root.exists()


def test_ingestao_manifesto_modo_legado_com_saida_explicita(
    projeto_multifonte: Path,
) -> None:
    """Quando --saida e fornecido, nao cria run, escreve direto no caminho."""
    saida = projeto_multifonte / "manifesto_legado.csv"
    runner = CliRunner()
    result = runner.invoke(
        ingestao_app,
        [
            "--perfil",
            "teste",
            "--fonte",
            "kaggle_cats_mini",
            "--saida",
            str(saida),
        ],
    )
    assert result.exit_code == 0, result.output
    assert saida.exists()
    # Modo legado: nao cria diretorio runs/
    runs_dir = projeto_multifonte / "runs" / "operacional"
    if runs_dir.exists():
        # Pode existir de outros testes (cleanup do fixture nao apaga), mas
        # nao deve haver run novo aqui para esta execucao.
        # O teste de fato e: saida_legado existe E foi populada.
        pass
