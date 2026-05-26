"""Testes para hotfix smoke validation (max-amostras, resolver dict, paths felidae)."""

from __future__ import annotations

from pathlib import Path

import pytest

from felinet.config import _resolver_path
from felinet.pipeline.orquestrador import _amostrar_deterministico

# ============================================================
# _resolver_path: aceitar str | dict
# ============================================================


def test_resolver_path_aceita_str_relativo(tmp_path: Path) -> None:
    raiz = tmp_path
    p = _resolver_path(raiz, "data/raw/foo")
    assert p == raiz / "data" / "raw" / "foo"


def test_resolver_path_aceita_str_absoluto(tmp_path: Path) -> None:
    abs_path = tmp_path / "abs"
    p = _resolver_path(tmp_path, str(abs_path))
    assert p == abs_path


def test_resolver_path_aceita_dict_com_raiz(tmp_path: Path) -> None:
    p = _resolver_path(tmp_path, {"raiz": "data/raw/x", "tipo": "operacional"})
    assert p == tmp_path / "data" / "raw" / "x"


def test_resolver_path_aceita_dict_com_path(tmp_path: Path) -> None:
    """Compatibilidade com formato antigo {path: ...}."""
    p = _resolver_path(tmp_path, {"path": "data/raw/y"})
    assert p == tmp_path / "data" / "raw" / "y"


def test_resolver_path_dict_sem_chave_valida_levanta(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="raiz' ou 'path'"):
        _resolver_path(tmp_path, {"foo": "bar"})


def test_resolver_path_tipo_invalido_levanta(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="espera str ou dict"):
        _resolver_path(tmp_path, 123)  # type: ignore[arg-type]


# ============================================================
# Amostragem determinística (helper isolado)
# ============================================================


def test_amostragem_max_amostras_zero_retorna_todas(tmp_path: Path) -> None:
    """Quando max_amostras=0, devolve todas as mídias varridas."""
    brutas = [tmp_path / f"f{i:03d}.jpg" for i in range(50)]
    out = _amostrar_deterministico(brutas, 0, seed=42)
    assert len(out) == 50
    assert out == brutas


def test_amostragem_determinista_mesma_seed(tmp_path: Path) -> None:
    """Mesma seed produz mesma seleção entre execuções."""
    brutas = [tmp_path / f"f{i:03d}.jpg" for i in range(100)]
    a = _amostrar_deterministico(brutas, 10, seed=42)
    b = _amostrar_deterministico(brutas, 10, seed=42)
    assert a == b
    assert len(a) == 10
    # ordem determinística após sort
    assert a == sorted(a)


def test_amostragem_diferente_quando_seed_diferente(tmp_path: Path) -> None:
    """Seeds diferentes produzem subconjuntos diferentes (probabilisticamente)."""
    brutas = [tmp_path / f"f{i:03d}.jpg" for i in range(100)]
    a = _amostrar_deterministico(brutas, 10, seed=42)
    b = _amostrar_deterministico(brutas, 10, seed=43)
    assert a != b


def test_amostragem_n_maior_que_total_retorna_todas(tmp_path: Path) -> None:
    """Quando n >= total, devolve todas."""
    brutas = [tmp_path / f"f{i:03d}.jpg" for i in range(5)]
    out = _amostrar_deterministico(brutas, 100, seed=42)
    assert len(out) == 5
