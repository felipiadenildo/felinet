"""Testes para `felinet tabelas fontes-resumo` e `tabelas run-inventory` (Bloco 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.tabelas import app as tabelas_app


def _escrever_manifesto_csv(caminho: Path, linhas: list[dict[str, str]]) -> None:
    import csv

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "caminho_relativo",
                "sha256",
                "largura",
                "altura",
                "timestamp",
                "fabricante",
                "modelo",
            ],
        )
        writer.writeheader()
        for linha in linhas:
            writer.writerow(linha)


def _escrever_manifest_run(
    raiz: Path,
    *,
    modo: str,
    fonte: str,
    perfil: str,
    git_sha: str,
    comando: str,
    sucesso: bool = True,
    metricas: dict | None = None,
    duracao_s: float = 1.5,
) -> None:
    payload = {
        "run_id": "abc123",
        "modo": modo,
        "fonte": fonte,
        "perfil": perfil,
        "protocolo": None,
        "tag": None,
        "git_sha": git_sha,
        "git_branch": "main",
        "git_dirty": False,
        "data_inicio": "2026-05-26T04:00:00-03:00",
        "data_fim": "2026-05-26T04:00:01-03:00",
        "duracao_s": duracao_s,
        "sucesso": sucesso,
        "mensagem": "",
        "extras": {"comando": comando},
        "metricas_resumo": metricas,
    }
    (raiz / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.fixture
def projeto_runs_bloco4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Monta um projeto sintetico com 2 fontes operacionais e runs gravados."""
    raiz = tmp_path

    # Run de ingestao kaggle_cats
    run_kaggle = raiz / "runs" / "operacional" / "kaggle_cats" / "prod" / "_" / "abc1234"
    run_kaggle.mkdir(parents=True)
    _escrever_manifesto_csv(
        run_kaggle / "manifesto.csv",
        [
            {
                "caminho_relativo": f"img_{i:03d}.jpg",
                "sha256": f"sha{i:03d}",
                "largura": "640",
                "altura": "480",
                "timestamp": f"2025-08-{1 + i:02d}T12:00:00",
                "fabricante": "TestCam",
                "modelo": "MD-001",
            }
            for i in range(5)
        ],
    )
    _escrever_manifest_run(
        run_kaggle,
        modo="operacional",
        fonte="kaggle_cats",
        perfil="prod",
        git_sha="abc1234",
        comando="ingestao manifesto",
        metricas={"n_entradas": 5},
    )

    # Run de ingestao petface (1 imagem duplicada para testar n_unicas)
    run_petface = raiz / "runs" / "operacional" / "petface" / "prod" / "_" / "def5678"
    run_petface.mkdir(parents=True)
    _escrever_manifesto_csv(
        run_petface / "manifesto.csv",
        [
            {
                "caminho_relativo": "a.png",
                "sha256": "x",
                "largura": "256",
                "altura": "256",
                "timestamp": "2024-01-01T00:00:00",
                "fabricante": "",
                "modelo": "",
            },
            {
                "caminho_relativo": "b.png",
                "sha256": "x",  # duplicado
                "largura": "256",
                "altura": "256",
                "timestamp": "2024-01-02T00:00:00",
                "fabricante": "",
                "modelo": "",
            },
            {
                "caminho_relativo": "c.png",
                "sha256": "y",
                "largura": "256",
                "altura": "256",
                "timestamp": "2024-01-03T00:00:00",
                "fabricante": "",
                "modelo": "",
            },
        ],
    )
    _escrever_manifest_run(
        run_petface,
        modo="operacional",
        fonte="petface",
        perfil="prod",
        git_sha="def5678",
        comando="ingestao manifesto",
        metricas={"n_entradas": 3},
    )

    # Run de deteccao kaggle (gera entrada no run-inventory diferente)
    run_det = raiz / "runs" / "operacional" / "kaggle_cats" / "prod" / "_" / "abc1234__det"
    run_det.mkdir(parents=True)
    _escrever_manifest_run(
        run_det,
        modo="operacional",
        fonte="kaggle_cats",
        perfil="prod",
        git_sha="abc1234",
        comando="deteccao executar",
        metricas={"n_imagens": 5, "n_animais_detectados": 3},
    )

    # latest symlinks: resolver_latest le runs/latest/<chave> e segue o symlink.
    pasta_latest = raiz / "runs" / "latest"
    pasta_latest.mkdir(parents=True, exist_ok=True)
    (pasta_latest / "operacional__kaggle_cats__prod").symlink_to(
        run_kaggle, target_is_directory=True
    )
    (pasta_latest / "operacional__petface__prod").symlink_to(run_petface, target_is_directory=True)

    class _PerfilFake:
        nome = "prod"
        raiz_runs = "runs"
        extras = {
            "fontes": {
                "kaggle_cats": "data/raw/camera_trap/kaggle_cats",
                "petface": "data/raw/reid/petface",
            },
            "raiz_runs": "runs",
            "artifacts_tabelas_raiz": "artifacts/tabelas",
            "fonte_default_operacional": "kaggle_cats",
        }

    monkeypatch.setattr("felinet.comandos.tabelas.carregar_perfil", lambda _p: _PerfilFake())
    monkeypatch.setattr("felinet.comandos.tabelas.raiz_projeto", lambda: raiz)
    return raiz


# ============================================================
# Testes
# ============================================================


def test_fontes_resumo_gera_csv_e_tex_com_n_midias_e_unicas(
    projeto_runs_bloco4: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(tabelas_app, ["fontes-resumo", "--perfil", "prod"])
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output

    csv_path = (
        projeto_runs_bloco4
        / "artifacts"
        / "tabelas"
        / "operacional"
        / "_global"
        / "fontes_resumo.csv"
    )
    tex_path = csv_path.with_suffix(".tex")
    assert csv_path.exists()
    assert tex_path.exists()

    conteudo = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(conteudo) == 3  # cabecalho + 2 fontes

    # petface tem 3 midias mas 2 unicas (SHA duplicado)
    linha_petface = [linha for linha in conteudo if linha.startswith("petface")][0]
    campos = linha_petface.split(",")
    assert campos[1] == "3"
    assert campos[2] == "2"

    # kaggle tem 5 midias, 5 unicas
    linha_kaggle = [linha for linha in conteudo if linha.startswith("kaggle_cats")][0]
    campos_k = linha_kaggle.split(",")
    assert campos_k[1] == "5"
    assert campos_k[2] == "5"

    # .tex tem booktabs
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\toprule" in tex
    assert "\\bottomrule" in tex
    assert "tab:fontes-resumo" in tex


def test_run_inventory_inclui_todos_os_runs_com_fase_correta(
    projeto_runs_bloco4: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(tabelas_app, ["run-inventory", "--perfil", "prod"])
    assert result.exit_code == 0, result.output

    csv_path = projeto_runs_bloco4 / "artifacts" / "tabelas" / "_inventario" / "run_inventory.csv"
    assert csv_path.exists()
    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    # cabecalho + 3 runs (kaggle ingestao + petface ingestao + kaggle deteccao)
    assert len(linhas) == 4, f"esperado 4 linhas, achou {len(linhas)}"
    corpo = linhas[1:]
    for linha in corpo:
        assert ",sim," in linha, linha
    fases = {linha.split(",")[4] for linha in corpo}
    assert "ingestao" in fases
    assert "deteccao" in fases


def test_run_inventory_filtra_por_fonte(projeto_runs_bloco4: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(tabelas_app, ["run-inventory", "--perfil", "prod", "--fonte", "petface"])
    assert result.exit_code == 0, result.output
    csv_path = projeto_runs_bloco4 / "artifacts" / "tabelas" / "_inventario" / "run_inventory.csv"
    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    # cabecalho + 1 run de petface
    assert len(linhas) == 2
    assert "petface" in linhas[1]
    assert "kaggle_cats" not in linhas[1]
