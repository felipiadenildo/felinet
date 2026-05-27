"""Testes para felinet.datasets.iteradores (varredura por layout)."""

from __future__ import annotations

from pathlib import Path

import pytest

from felinet.datasets.iteradores import (
    iterador_para_layout,
    iterar_aninhado_livre,
    iterar_flat,
    iterar_por_classe,
    iterar_por_identidade,
)


def _criar(raiz: Path, caminhos: list[str]) -> None:
    for c in caminhos:
        p = raiz / c
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x00")


def test_iterar_flat_filtra_extensoes(tmp_path: Path) -> None:
    _criar(tmp_path, ["a.jpg", "b.png", "c.txt", "d.JPG"])
    out = list(iterar_flat(tmp_path))
    nomes = {p.name for p in out}
    assert nomes == {"a.jpg", "b.png", "d.JPG"}


def test_iterar_por_classe(tmp_path: Path) -> None:
    _criar(tmp_path, ["cat/a.jpg", "cat/b.png", "dog/c.jpg", "ignorar.txt"])
    out = list(iterar_por_classe(tmp_path))
    assert len(out) == 3
    assert all(p.suffix.lower() in {".jpg", ".png"} for p in out)


def test_iterar_por_identidade_emite_id(tmp_path: Path) -> None:
    _criar(tmp_path, ["id001/foto1.jpg", "id001/foto2.jpg", "id002/foto3.jpg"])
    out = list(iterar_por_identidade(tmp_path))
    assert len(out) == 3
    ids = {ident for _, ident in out}
    assert ids == {"id001", "id002"}


def test_iterar_aninhado_livre(tmp_path: Path) -> None:
    _criar(tmp_path, ["a/b/c/foto.jpg", "topo.png", "ignorar.txt"])
    out = list(iterar_aninhado_livre(tmp_path))
    nomes = {p.name for p in out}
    assert nomes == {"foto.jpg", "topo.png"}


def test_iterador_para_layout_despacha(tmp_path: Path) -> None:
    _criar(tmp_path, ["a.jpg"])
    out = list(iterador_para_layout("flat", tmp_path))
    assert len(out) == 1


def test_iterador_para_layout_desconhecido(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="layout desconhecido"):
        list(iterador_para_layout("xpto", tmp_path))
