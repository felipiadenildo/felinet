"""Testes para o modo --dev e o comando felinet dev demo."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from felinet.pipeline.dev_visual import (
    desenhar_bbox,
    preparar_estrutura,
    registrar_classificacao,
    registrar_deteccao,
    registrar_ingestao,
)


def test_preparar_estrutura_cria_subpastas_e_csv(tmp_path: Path) -> None:
    base = preparar_estrutura(tmp_path)
    assert base == tmp_path / "dev_visualizacao"
    assert (base / "01_ingestao" / "motivos.csv").exists()
    assert (base / "02_deteccao" / "deteccoes.csv").exists()
    assert (base / "03_classificacao" / "classificacoes.csv").exists()
    # Cabeçalho gravado
    cabecalho = (base / "01_ingestao" / "motivos.csv").read_text().splitlines()[0]
    assert "motivo" in cabecalho


def test_registrar_ingestao_adiciona_linha(tmp_path: Path) -> None:
    base = preparar_estrutura(tmp_path)
    registrar_ingestao(base, "foo.jpg", "aceita", "")
    linhas = (base / "01_ingestao" / "motivos.csv").read_text().splitlines()
    assert len(linhas) == 2
    assert "foo.jpg" in linhas[1]


def test_registrar_deteccao_adiciona_linha(tmp_path: Path) -> None:
    base = preparar_estrutura(tmp_path)
    registrar_deteccao(base, "bar.jpg", 2, 0.95, "com_animal")
    linhas = (base / "02_deteccao" / "deteccoes.csv").read_text().splitlines()
    assert "bar.jpg" in linhas[1]
    assert "0.950" in linhas[1]


def test_registrar_classificacao_adiciona_linha(tmp_path: Path) -> None:
    base = preparar_estrutura(tmp_path)
    registrar_classificacao(base, "baz.jpg", 0, "felis_catus", 0.82)
    linhas = (base / "03_classificacao" / "classificacoes.csv").read_text().splitlines()
    assert "felis_catus" in linhas[1]


def test_desenhar_bbox_produz_arquivo(tmp_path: Path) -> None:
    src = tmp_path / "src.jpg"
    Image.new("RGB", (64, 64), (200, 200, 200)).save(src)
    dst = tmp_path / "dst.jpg"
    desenhar_bbox(
        img_path=src,
        bboxes=[(8.0, 8.0, 50.0, 50.0)],
        scores=[0.9],
        limiar=0.5,
        saida=dst,
    )
    assert dst.exists()
    assert dst.stat().st_size > 100
