"""Smoke test do MegaDetector v6 — NÃO roda por padrão.

Rodar manualmente quando quiser validar carregamento real do modelo:
    pytest -m smoke

Requer:
- Internet (primeira vez baixa pesos)
- ~50 MB de download
- ~10s de inicialização
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.smoke
def test_carrega_modelo_e_detecta_em_amostra(
    pasta_midias_sintetica: Path,
) -> None:
    from pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6

    detector = DetectorMegaDetectorV6(dispositivo="auto")
    primeira = sorted(pasta_midias_sintetica.glob("*.jpg"))[0]
    resultado = detector.detectar(primeira, limite_confianca=0.01)
    # Imagem sintética 64×48 não tem nenhum gato — só validamos
    # que o pipeline rodou sem erro e devolveu o schema esperado.
    assert resultado.modelo.startswith("MDv6")
    assert resultado.largura == 64
    assert resultado.altura == 48
