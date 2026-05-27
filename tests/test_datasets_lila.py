"""Testes para datasets.lila_bc (subset dev local)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from felinet.datasets.lila_bc import (
    ARQUIVO_MANIFESTO,
    EXTENSOES_VALIDAS,
    carregar_manifesto,
    listar_subset_dev,
    subset_esta_pronto,
)


def _criar_imagem(caminho: Path, tamanho: tuple[int, int] = (32, 32)) -> None:
    """Cria uma imagem RGB minima no caminho informado."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", tamanho, color=(127, 127, 127)).save(caminho)


def test_listar_subset_dev_retorna_lista_vazia_se_diretorio_inexistente(tmp_path: Path) -> None:
    diretorio = tmp_path / "nao_existe"
    assert listar_subset_dev(diretorio) == []


def test_listar_subset_dev_retorna_lista_vazia_se_diretorio_vazio(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    assert listar_subset_dev(tmp_path) == []


def test_listar_subset_dev_filtra_extensoes_invalidas(tmp_path: Path) -> None:
    _criar_imagem(tmp_path / "ok.jpg")
    _criar_imagem(tmp_path / "ok.png")
    _criar_imagem(tmp_path / "ok.jpeg")
    (tmp_path / "nao.txt").write_text("ignorar", encoding="utf-8")
    (tmp_path / "nao.gif").write_bytes(b"")
    encontrados = listar_subset_dev(tmp_path)
    nomes = sorted(p.name for p in encontrados)
    assert nomes == ["ok.jpeg", "ok.jpg", "ok.png"]


def test_listar_subset_dev_ordena_alfabeticamente(tmp_path: Path) -> None:
    for nome in ("zebra.jpg", "alpha.jpg", "meio.jpg"):
        _criar_imagem(tmp_path / nome)
    nomes = [p.name for p in listar_subset_dev(tmp_path)]
    assert nomes == ["alpha.jpg", "meio.jpg", "zebra.jpg"]


def test_subset_esta_pronto_false_quando_vazio(tmp_path: Path) -> None:
    assert subset_esta_pronto(tmp_path) is False


def test_subset_esta_pronto_true_com_uma_imagem(tmp_path: Path) -> None:
    _criar_imagem(tmp_path / "uma.jpg")
    assert subset_esta_pronto(tmp_path) is True


def test_carregar_manifesto_retorna_none_se_ausente(tmp_path: Path) -> None:
    assert carregar_manifesto(tmp_path) is None


def test_carregar_manifesto_le_json_existente(tmp_path: Path) -> None:
    conteudo = {"total": 2, "imagens": [{"arquivo": "a.jpg"}, {"arquivo": "b.jpg"}]}
    (tmp_path / ARQUIVO_MANIFESTO).write_text(json.dumps(conteudo), encoding="utf-8")
    carregado = carregar_manifesto(tmp_path)
    assert carregado == conteudo


def test_extensoes_validas_inclui_formatos_comuns() -> None:
    assert ".jpg" in EXTENSOES_VALIDAS
    assert ".jpeg" in EXTENSOES_VALIDAS
    assert ".png" in EXTENSOES_VALIDAS
