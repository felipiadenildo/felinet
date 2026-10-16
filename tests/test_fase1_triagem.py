"""Fase I: triagem (escuro, saturado, uniforme, duplicata), normalização e vídeo."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from felinet.pipeline.fase1_ingestao import triagem as t


def _ruido(
    semente: int, media: float = 120.0, desvio: float = 40.0, tamanho=(64, 48)
) -> Image.Image:
    rng = np.random.default_rng(semente)
    arr = np.clip(rng.normal(media, desvio, (*tamanho[::-1], 3)), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def test_motivos_de_descarte() -> None:
    assert t.motivo_descarte(Image.new("RGB", (32, 32), (2, 2, 2))) == "escuro"
    assert t.motivo_descarte(Image.new("RGB", (32, 32), (252, 252, 252))) == "saturado"
    assert t.motivo_descarte(Image.new("RGB", (32, 32), (120, 120, 120))) == "uniforme"
    assert t.motivo_descarte(_ruido(0)) is None


def test_triar_descarta_duplicata_do_ultimo_aceito() -> None:
    a, b = _ruido(1), _ruido(2)
    quadros = [(0, 0.0, a), (1, 1.0, a.copy()), (2, 2.0, Image.new("RGB", (64, 48))), (3, 3.0, b)]
    motivos = [q.motivo for q in t.triar(quadros)]
    assert motivos == [None, "duplicata", "escuro", None]


def test_normalizacao_preserva_aspecto_e_balanceia() -> None:
    pytest.importorskip("cv2")
    img = Image.new("RGB", (200, 100), (180, 90, 60))
    saida = t.normalizar(img, tamanho=(128, 128))
    assert saida.size == (128, 128)
    faixa = (
        np.asarray(saida)[32:96, :, :].reshape(-1, 3).mean(axis=0)
    )  # conteúdo no meio, bordas pretas
    assert np.ptp(faixa) < 10  # mundo cinza: canais com médias próximas
    assert np.asarray(saida)[:20].max() == 0  # letterbox em cima


def test_extrair_quadros_de_video(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    caminho = tmp_path / "v.avi"
    escritor = cv2.VideoWriter(str(caminho), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (32, 24))
    for i in range(30):
        escritor.write(np.full((24, 32, 3), i * 8, dtype=np.uint8))
    escritor.release()
    quadros = list(t.extrair_quadros(caminho, fps=2.0))
    assert [q[0] for q in quadros] == [0, 5, 10, 15, 20, 25]
    assert quadros[1][1] == pytest.approx(0.5)


def test_metadados_quadro() -> None:
    m = t.metadados_quadro(
        "P03", "ipcam", "2026-10-15T03:00:00", "cartao/01.mp4", t.ConfigTriagem(), clahe=True
    )
    assert (
        m["ponto"] == "P03" and m["triagem"]["fps_amostragem"] == 1.0 and m["normalizacao"]["clahe"]
    )


def test_preparar_quadros_canonicos_imagens_e_video(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    brutas = tmp_path / "brutas"
    brutas.mkdir()
    _ruido(10).save(brutas / "foto.png")
    Image.new("RGB", (64, 48)).save(brutas / "preta.png")
    escritor = cv2.VideoWriter(
        str(brutas / "v.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 4.0, (64, 48)
    )
    quadro = np.asarray(_ruido(11))[:, :, ::-1]
    for _ in range(8):  # 2 s de vídeo parado: só o primeiro quadro amostrado deve sobrar
        escritor.write(quadro)
    escritor.release()
    gravados, registro = t.preparar_quadros_canonicos(brutas, tmp_path / "quadros")
    motivos = {(r["midia"], r["quadro"]): r["motivo"] for r in registro}
    assert motivos[("foto.png", 0)] == "aceito" and motivos[("preta.png", 0)] == "escuro"
    assert [m for (arq, _), m in motivos.items() if arq == "v.avi"] == ["aceito", "duplicata"]
    assert sorted(p.name for p in gravados) == ["foto.jpg", "v__q000000.jpg"]
