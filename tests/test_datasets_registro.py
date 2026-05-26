"""Testes para felinet.datasets.registro (carga de datasets_locais.yaml)."""

from __future__ import annotations

from pathlib import Path

import pytest

from felinet.datasets.registro import (
    DatasetLocal,
    carregar_datasets_locais,
    validar_fase_aplicavel,
)


def test_yaml_ausente_retorna_dict_vazio(tmp_path: Path) -> None:
    assert carregar_datasets_locais(tmp_path / "ausente.yaml") == {}


def test_carregar_yaml_minimo(tmp_path: Path) -> None:
    arq = tmp_path / "ds.yaml"
    arq.write_text(
        "datasets:\n"
        "  kaggle_cats:\n"
        "    tipo: camera_trap_brutas\n"
        "    layout: flat\n"
        "    caminho: /tmp/kaggle\n"
        "    descricao: Kaggle cats\n"
        "    fases_aplicaveis: [1, 2, 3]\n"
    )
    out = carregar_datasets_locais(arq)
    assert "kaggle_cats" in out
    ds = out["kaggle_cats"]
    assert ds.tipo == "camera_trap_brutas"
    assert ds.layout == "flat"
    assert ds.caminho == Path("/tmp/kaggle")
    assert ds.fases_aplicaveis == [1, 2, 3]


def test_defaults_aplicados_quando_ausentes(tmp_path: Path) -> None:
    arq = tmp_path / "ds.yaml"
    arq.write_text(
        "datasets:\n"
        "  meu:\n"
        "    caminho: /tmp/meu\n"
    )
    out = carregar_datasets_locais(arq)
    assert out["meu"].tipo == "camera_trap_brutas"
    assert out["meu"].layout == "aninhado_livre"
    assert out["meu"].fases_aplicaveis == [1, 2, 3]


def test_categoria_por_tipo(tmp_path: Path) -> None:
    ds = DatasetLocal(
        nome="pf",
        tipo="reid_crops_rotulados",
        layout="por_identidade",
        caminho=Path("/tmp/pf"),
        fases_aplicaveis=[4],
    )
    assert ds.categoria == "reid"
    assert ds.link_destino == Path("data") / "raw" / "reid" / "pf"


def test_link_destino_camera_trap(tmp_path: Path) -> None:
    ds = DatasetLocal(
        nome="kc",
        tipo="camera_trap_brutas",
        layout="flat",
        caminho=Path("/tmp/kc"),
        fases_aplicaveis=[1, 2, 3],
    )
    assert ds.link_destino == Path("data") / "raw" / "camera_trap" / "kc"


def test_validar_fase_aplicavel_levanta(tmp_path: Path) -> None:
    ds = DatasetLocal(
        nome="pf",
        tipo="reid_crops_rotulados",
        layout="por_identidade",
        caminho=Path("/tmp/pf"),
        fases_aplicaveis=[4],
    )
    with pytest.raises(ValueError, match="não suporta fase 1"):
        validar_fase_aplicavel(ds, 1)
    validar_fase_aplicavel(ds, 4)  # nao deve levantar
