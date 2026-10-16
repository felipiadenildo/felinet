"""Fase I — Ingestão: triagem e normalização dos quadros (Seção 3.2 da monografia).

* extração de quadros de vídeo H.264/H.265 a uma taxa configurável;
* descarte barato de quadros inutilizáveis pela média e pelo desvio da luminância (escuros,
  saturados, uniformes), conservador: na dúvida, o quadro segue para a Fase II;
* deduplicação intra-evento pela diferença absoluta média entre miniaturas de quadros vizinhos;
* normalização: CLAHE na luminância, balanço de branco (mundo cinza) e *letterbox* que preserva
  a razão de aspecto;
* metadados de proveniência por quadro (ponto P01–P10, tipologia, instante e parâmetros).

Vídeo e CLAHE usam OpenCV (extra ``[video]``), importado só quando necessário.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


@dataclass(frozen=True)
class ConfigTriagem:
    luminancia_min: float = 12.0  # média abaixo disso: quadro escuro
    luminancia_max: float = 243.0  # média acima disso: quadro saturado
    desvio_min: float = 4.0  # desvio abaixo disso: quadro uniforme (sem conteúdo)
    # diferença média (0-255) entre miniaturas abaixo da qual o quadro é duplicata
    diferenca_dedup: float = 3.0
    lado_miniatura: int = 32
    fps_amostragem: float = 1.0


def luminancia(img: Image.Image) -> tuple[float, float]:
    """Média e desvio-padrão da luminância (0-255)."""
    cinza = np.asarray(img.convert("L"), dtype=np.float32)
    return float(cinza.mean()), float(cinza.std())


def motivo_descarte(img: Image.Image, cfg: ConfigTriagem = ConfigTriagem()) -> str | None:
    """``"escuro"``, ``"saturado"``, ``"uniforme"`` ou ``None`` se o quadro deve seguir."""
    media, desvio = luminancia(img)
    if media < cfg.luminancia_min:
        return "escuro"
    if media > cfg.luminancia_max:
        return "saturado"
    if desvio < cfg.desvio_min:
        return "uniforme"
    return None


def miniatura(img: Image.Image, lado: int = 32) -> np.ndarray:
    return np.asarray(img.convert("L").resize((lado, lado), Image.BILINEAR), dtype=np.float32)


def eh_duplicata(
    anterior: np.ndarray | None, atual: np.ndarray, cfg: ConfigTriagem = ConfigTriagem()
) -> bool:
    return anterior is not None and float(np.abs(atual - anterior).mean()) < cfg.diferenca_dedup


@dataclass(frozen=True)
class QuadroTriado:
    indice: int
    instante_s: float | None
    imagem: Image.Image
    motivo: str | None  # None = aceito; senão escuro | saturado | uniforme | duplicata


def triar(
    quadros: Iterable[tuple[int, float | None, Image.Image]], cfg: ConfigTriagem = ConfigTriagem()
) -> Iterator[QuadroTriado]:
    """Aplica os dois filtros baratos, na ordem: inutilizável e depois duplicata do último aceito."""
    ultima = None
    for indice, instante, img in quadros:
        motivo = motivo_descarte(img, cfg)
        if motivo is None:
            mini = miniatura(img, cfg.lado_miniatura)
            if eh_duplicata(ultima, mini, cfg):
                motivo = "duplicata"
            else:
                ultima = mini
        yield QuadroTriado(indice, instante, img, motivo)


def extrair_quadros(video: Path, fps: float = 1.0) -> Iterator[tuple[int, float, Image.Image]]:
    """Quadros do vídeo amostrados a ``fps`` quadros por segundo (OpenCV)."""
    import cv2

    captura = cv2.VideoCapture(str(video))
    if not captura.isOpened():
        raise OSError(f"não foi possível abrir o vídeo {video}")
    fps_video = captura.get(cv2.CAP_PROP_FPS) or 30.0
    passo = max(1, round(fps_video / fps))
    indice = 0
    try:
        while True:
            ok, quadro = captura.read()
            if not ok:
                break
            if indice % passo == 0:
                yield (
                    indice,
                    indice / fps_video,
                    Image.fromarray(cv2.cvtColor(quadro, cv2.COLOR_BGR2RGB)),
                )
            indice += 1
    finally:
        captura.release()


def balanco_de_branco(img: Image.Image) -> Image.Image:
    """Mundo cinza: escala cada canal para que as médias de R, G e B fiquem iguais."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    medias = rgb.reshape(-1, 3).mean(axis=0)
    ganho = medias.mean() / np.maximum(medias, 1e-6)
    return Image.fromarray(np.clip(rgb * ganho, 0, 255).astype(np.uint8))


def clahe(img: Image.Image, limite: float = 2.0, grade: int = 8) -> Image.Image:
    """CLAHE só no canal de luminância (LAB), sem alterar a cor."""
    import cv2

    lab = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=limite, tileGridSize=(grade, grade)).apply(
        lab[:, :, 0]
    )
    return Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))


def normalizar(
    img: Image.Image,
    usar_clahe: bool = True,
    usar_balanco: bool = True,
    tamanho: tuple[int, int] | None = (1280, 1280),
) -> Image.Image:
    """Normalização primária: CLAHE, balanço de branco e letterbox (preserva a razão de aspecto)."""
    saida = img.convert("RGB")
    if usar_clahe:
        saida = clahe(saida)
    if usar_balanco:
        saida = balanco_de_branco(saida)
    if tamanho:
        saida = ImageOps.pad(saida, tamanho, color=(0, 0, 0))
    return saida


def metadados_quadro(
    ponto: str,
    tipologia: str,
    instante: str | None,
    origem: str,
    cfg: ConfigTriagem,
    **normalizacao: object,
) -> dict:
    """Proveniência mínima de cada quadro canônico (Seção 3.2)."""
    return {
        "ponto": ponto,
        "tipologia": tipologia,
        "instante": instante,
        "origem": origem,
        "triagem": asdict(cfg),
        "normalizacao": normalizacao,
    }


EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
EXTENSOES_VIDEO = {".mp4", ".mkv", ".avi", ".mov"}


def preparar_quadros_canonicos(
    pasta: Path,
    destino: Path,
    cfg: ConfigTriagem = ConfigTriagem(),
    normalizar_quadros: bool = True,
) -> tuple[list[Path], list[dict]]:
    """Fase I completa sobre uma pasta de mídias brutas (imagens e vídeos).

    Vídeos viram quadros (``cfg.fps_amostragem``); cada mídia passa pela triagem (deduplicação só
    dentro do mesmo vídeo) e os quadros aceitos são normalizados e gravados em ``destino`` como JPEG.
    Devolve ``(quadros canônicos gravados, registro de todas as decisões)``.
    """
    destino.mkdir(parents=True, exist_ok=True)
    gravados: list[Path] = []
    registro: list[dict] = []
    for midia in sorted(
        p for p in Path(pasta).rglob("*") if p.suffix.lower() in EXTENSOES_IMAGEM | EXTENSOES_VIDEO
    ):
        if midia.suffix.lower() in EXTENSOES_VIDEO:
            quadros = extrair_quadros(midia, cfg.fps_amostragem)
        else:
            with Image.open(midia) as img:
                quadros = [(0, None, img.convert("RGB"))]
        for q in triar(quadros, cfg):
            nome = (
                f"{midia.stem}__q{q.indice:06d}.jpg"
                if midia.suffix.lower() in EXTENSOES_VIDEO
                else f"{midia.stem}.jpg"
            )
            registro.append({"midia": str(midia.relative_to(pasta)), "quadro": q.indice, "instante_s": q.instante_s,
                             "motivo": q.motivo or "aceito", "arquivo": nome if q.motivo is None else ""})  # fmt: skip
            if q.motivo is None:
                saida = normalizar(q.imagem) if normalizar_quadros else q.imagem.convert("RGB")
                caminho = destino / nome
                saida.save(caminho, quality=95)
                gravados.append(caminho)
    return gravados, registro
