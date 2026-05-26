"""Testes para `felinet tabelas comparativo-fontes` (Bloco 6).

Monta um projeto sintetico com 2 fontes (kaggle_cats, felidae) e tres
runs operacionais por fonte (ingestao, deteccao, classificacao) +
1 fonte (petface) sem run completo, e valida a tabela cruzada.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from felinet.comandos.tabelas import app as tabelas_app


def _escrever_manifest_run(
    raiz: Path,
    *,
    fonte: str,
    perfil: str,
    git_sha: str,
    comando: str,
    metricas: dict | None,
    data_inicio: str,
    sucesso: bool = True,
) -> None:
    raiz.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": "abc123",
        "modo": "operacional",
        "fonte": fonte,
        "perfil": perfil,
        "protocolo": None,
        "tag": None,
        "git_sha": git_sha,
        "git_branch": "main",
        "git_dirty": False,
        "data_inicio": data_inicio,
        "data_fim": data_inicio,
        "duracao_s": 1.0,
        "sucesso": sucesso,
        "mensagem": "",
        "extras": {"comando": comando},
        "metricas_resumo": metricas,
    }
    (raiz / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.fixture
def projeto_runs_bloco6(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Monta runs sinteticos: 2 fontes completas + 1 fonte sem nada."""
    raiz = tmp_path
    base_runs = raiz / "runs" / "operacional"

    # ---- kaggle_cats: 3 fases bem-sucedidas ----
    _escrever_manifest_run(
        base_runs / "kaggle_cats" / "prod" / "_" / "aaa1__ing",
        fonte="kaggle_cats",
        perfil="prod",
        git_sha="aaa1",
        comando="ingestao manifesto",
        metricas={"n_entradas": 500},
        data_inicio="2026-05-20T10:00:00-03:00",
    )
    _escrever_manifest_run(
        base_runs / "kaggle_cats" / "prod" / "_" / "aaa1__det",
        fonte="kaggle_cats",
        perfil="prod",
        git_sha="aaa1",
        comando="deteccao executar",
        metricas={"n_imagens": 500, "n_animais_detectados": 420, "confianca": 0.5},
        data_inicio="2026-05-20T11:00:00-03:00",
    )
    _escrever_manifest_run(
        base_runs / "kaggle_cats" / "prod" / "_" / "aaa1__cls",
        fonte="kaggle_cats",
        perfil="prod",
        git_sha="aaa1",
        comando="classificacao executar",
        metricas={"n_classificacoes": 420, "n_felis_catus": 400},
        data_inicio="2026-05-20T12:00:00-03:00",
    )

    # ---- felidae: 3 fases ----
    _escrever_manifest_run(
        base_runs / "felidae" / "prod" / "_" / "bbb2__ing",
        fonte="felidae",
        perfil="prod",
        git_sha="bbb2",
        comando="ingestao manifesto",
        metricas={"n_entradas": 8000},
        data_inicio="2026-05-21T10:00:00-03:00",
    )
    _escrever_manifest_run(
        base_runs / "felidae" / "prod" / "_" / "bbb2__det",
        fonte="felidae",
        perfil="prod",
        git_sha="bbb2",
        comando="deteccao executar",
        metricas={"n_imagens": 8000, "n_animais_detectados": 7600, "confianca": 0.5},
        data_inicio="2026-05-21T11:00:00-03:00",
    )
    _escrever_manifest_run(
        base_runs / "felidae" / "prod" / "_" / "bbb2__cls",
        fonte="felidae",
        perfil="prod",
        git_sha="bbb2",
        comando="classificacao executar",
        metricas={"n_classificacoes": 7600, "n_felis_catus": 3},
        data_inicio="2026-05-21T12:00:00-03:00",
    )

    # ---- petface: SEM runs operacionais (so reid) — deve ser pulado ----
    _escrever_manifest_run(
        raiz / "runs" / "metodologico" / "petface" / "prod" / "n0050" / "ccc3",
        fonte="petface",
        perfil="prod",
        git_sha="ccc3",
        comando="reid avaliar-closed",
        metricas={"map_at_1": 0.7},
        data_inicio="2026-05-22T10:00:00-03:00",
    )

    class _PerfilFake:
        nome = "prod"
        raiz_runs = "runs"
        extras = {
            "fontes": {
                "kaggle_cats": "data/raw/camera_trap/kaggle_cats",
                "felidae": "data/raw/camera_trap/felidae",
                "petface": "data/raw/reid/petface",
            },
            "raiz_runs": "runs",
            "artifacts_tabelas_raiz": "artifacts/tabelas",
        }

    monkeypatch.setattr("felinet.comandos.tabelas.carregar_perfil", lambda _p: _PerfilFake())
    monkeypatch.setattr("felinet.comandos.tabelas.raiz_projeto", lambda: raiz)
    return raiz


def test_comparativo_fontes_cruza_3_fases_para_2_fontes(
    projeto_runs_bloco6: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(tabelas_app, ["comparativo-fontes", "--perfil", "prod"])
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output

    csv_path = (
        projeto_runs_bloco6
        / "artifacts"
        / "tabelas"
        / "operacional"
        / "_global"
        / "comparativo_fontes.csv"
    )
    tex_path = csv_path.with_suffix(".tex")
    assert csv_path.exists()
    assert tex_path.exists()

    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 3, f"esperado 3 linhas, achou {len(linhas)}: {linhas}"

    cab = linhas[0].split(",")
    assert cab[0] == "Fonte"
    assert "N midias" in cab
    assert "N animais" in cab
    assert "Taxa felis pct" in cab

    linha_kaggle = next(linha for linha in linhas if linha.startswith("kaggle_cats"))
    campos_k = linha_kaggle.split(",")
    assert campos_k[1] == "500"
    assert campos_k[2] == "500"
    assert campos_k[3] == "420"
    assert campos_k[4] == "84.0"
    assert campos_k[5] == "420"
    assert campos_k[6] == "400"
    assert campos_k[7] == "95.2"

    linha_fel = next(linha for linha in linhas if linha.startswith("felidae"))
    campos_f = linha_fel.split(",")
    assert campos_f[1] == "8000"
    assert campos_f[3] == "7600"
    assert campos_f[4] == "95.0"
    assert campos_f[6] == "3"
    assert campos_f[7] == "0.0"

    tex = tex_path.read_text(encoding="utf-8")
    assert "\\toprule" in tex
    assert "\\bottomrule" in tex
    assert "tab:comparativo-fontes" in tex


def test_comparativo_fontes_filtra_por_fontes_explicitas(
    projeto_runs_bloco6: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        tabelas_app,
        ["comparativo-fontes", "--perfil", "prod", "--fontes", "felidae"],
    )
    assert result.exit_code == 0, result.output

    csv_path = (
        projeto_runs_bloco6
        / "artifacts"
        / "tabelas"
        / "operacional"
        / "_global"
        / "comparativo_fontes.csv"
    )
    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 2
    assert linhas[1].startswith("felidae")
    assert "kaggle_cats" not in csv_path.read_text(encoding="utf-8")


def test_comparativo_fontes_pula_fonte_sem_nenhum_run_operacional(
    projeto_runs_bloco6: Path,
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        tabelas_app,
        ["comparativo-fontes", "--perfil", "prod", "--fontes", "petface"],
    )
    assert result.exit_code == 0, result.output

    csv_path = (
        projeto_runs_bloco6
        / "artifacts"
        / "tabelas"
        / "operacional"
        / "_global"
        / "comparativo_fontes.csv"
    )
    linhas = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 1
    assert linhas[0].startswith("Fonte,")
