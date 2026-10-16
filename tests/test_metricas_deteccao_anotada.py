"""Fase II contra anotações YOLO: animal, classe errada (pessoa/veículo) ou perdido."""

from __future__ import annotations

from pathlib import Path

from felinet.metricas.deteccao_anotada import cruzar


def _caixa(categoria: str, x: float, y: float, w: float = 0.2, h: float = 0.2) -> dict:
    return {"categoria": categoria, "confianca": 0.5, "bbox": {"x": x, "y": y, "w": w, "h": h}}


def test_desfechos_por_animal_e_por_imagem(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("0 0.2 0.2 0.2 0.2\n0 0.7 0.7 0.2 0.2\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    imagens = {
        "/x/a.jpg": {"caixas": [_caixa("animal", 0.1, 0.1), _caixa("person", 0.6, 0.6)]},
        "/x/b.jpg": {"caixas": [_caixa("vehicle", 0.41, 0.4)]},
        "/x/c.jpg": {"caixas": []},
    }
    r = cruzar(imagens, tmp_path)
    assert r["por_animal"] == {"animal": 1, "classe_errada": 2}
    assert r["por_imagem"] == {
        "sem_caixa_animal": 1,
        "sem_caixa_animal_com_gato_em_classe_errada": 1,
        "sem_anotacao": 1,
    }
