"""Experimentos complementares (Tabs. 9 e 10) com detector e classificador falsos."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from felinet.experimentos import complementares as c


def _imagem(caminho: Path, cor: tuple[int, int, int]) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), cor).save(caminho)
    return caminho


class DetectorFalso:
    """Detecta conforme o nome do arquivo: 'gato*' -> 2 caixas, 'cao*' -> 1, demais -> nenhuma."""

    def detectar(self, caminho: Path, conf: float) -> list[float]:
        scores = {"gato": [0.9, 0.3], "cao": [0.15]}.get(caminho.stem.split("_")[0], [])
        return [s for s in scores if s >= conf]


class ClassificadorFalso:
    def classificar(self, caminho: Path) -> str:
        return "cat" if caminho.stem.startswith("gato") else "dog"


def test_deduplica_por_conteudo(tmp_path: Path) -> None:
    _imagem(tmp_path / "a.jpg", (10, 10, 10))
    _imagem(tmp_path / "b.jpg", (10, 10, 10))  # mesmo conteúdo de a.jpg
    _imagem(tmp_path / "sub" / "c.png", (20, 20, 20))
    imagens, duplicatas = c.imagens_da_fonte(tmp_path)
    assert [p.name for p in imagens] == ["a.jpg", "c.png"]
    assert duplicatas == 1


def test_cascatas_multifonte_conta_por_imagem(tmp_path: Path) -> None:
    imagens = [
        _imagem(tmp_path / "gato_1.jpg", (1, 0, 0)),
        _imagem(tmp_path / "gato_2.jpg", (2, 0, 0)),
        _imagem(tmp_path / "cao_1.jpg", (3, 0, 0)),
        _imagem(tmp_path / "vazio_1.jpg", (4, 0, 0)),
    ]
    tempos = iter([0.0, 2.5])
    (linha,) = c.cascatas_multifonte(
        {"fonte": imagens},
        DetectorFalso(),
        ClassificadorFalso(),
        conf=0.2,
        relogio=lambda: next(tempos),
    )
    # limiar 0,2: cada gato tem 2 caixas (0,9 e 0,3); o cão (0,15) fica de fora
    assert linha["n_images"] == 4
    assert linha["n_images_with_animal"] == 2
    assert linha["n_detection_boxes"] == 4
    assert linha["n_classified_cat"] == 2
    assert linha["rate_cat"] == pytest.approx(1.0)
    assert linha["rate_animal"] == pytest.approx(0.5)
    assert linha["mean_det_score"] == pytest.approx(0.6)
    assert linha["elapsed_s"] == pytest.approx(2.5)


def test_sensibilidade_limiar_e_monotona(tmp_path: Path) -> None:
    imagens = [
        _imagem(tmp_path / f"{n}.jpg", (i, 0, 0)) for i, n in enumerate(["gato_1", "cao_1", "x"])
    ]
    linhas = c.sensibilidade_limiar("fonte", imagens, DetectorFalso(), limiares=(0.1, 0.2, 0.5))
    assert [r["n_boxes"] for r in linhas] == [3, 2, 1]
    assert [r["n_images_with_animal"] for r in linhas] == [2, 1, 1]
    assert linhas[0]["rate_animal"] == pytest.approx(2 / 3)


def test_visualizacao_exploratoria_sem_modelos(tmp_path: Path) -> None:
    import numpy as np

    from felinet.experimentos import visualizacao as v
    from felinet.monografia.graficos import projecao_umap

    for i in range(8):
        for j in range(4 if i % 2 else 2):  # identidades ímpares com 4 imagens, pares com 2
            _imagem(tmp_path / f"id{i}" / f"{j}.jpg", (i, j, 0))
    itens = v.selecionar_catalogo(tmp_path, n_identidades=3, min_por_id=3, max_por_id=3, semente=1)
    assert len({i for i, _ in itens}) == 3 and len(itens) == 9  # só identidades com 3+ imagens
    assert all(int(i[2:]) % 2 for i, _ in itens)

    _, coords, linhas = v.visualizacao_exploratoria(
        itens, lambda p: np.array([len(p.parent.name), int(p.stem), 1.0]), lambda x: x[:, :2]
    )
    assert coords.shape == (9, 2) and {"identity", "file", "x", "y"} <= set(linhas[0])
    assert projecao_umap(linhas).axes


def test_selecionar_catalogo_sem_identidades_falha(tmp_path: Path) -> None:
    from felinet.experimentos import visualizacao as v

    (tmp_path / "vazio").mkdir()
    with pytest.raises(FileNotFoundError):
        v.selecionar_catalogo(tmp_path)
