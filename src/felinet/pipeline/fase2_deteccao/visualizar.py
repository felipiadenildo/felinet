"""E1 — Detecção: desenho de bboxes sobre imagens.

Renderiza as detecções salvas no esquema neutro como overlay visual
para inspeção humana e figuras da monografia.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .schema import ResultadoDeteccao

# Paleta por categoria — cores acessíveis (contrastam em fundo claro/escuro)
_CORES = {
    "animal": (220, 50, 50),  # vermelho
    "person": (50, 130, 220),  # azul
    "vehicle": (240, 180, 40),  # amarelo
}
_COR_DEFAULT = (200, 200, 200)


def _fonte(tamanho: int = 18) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Tenta carregar uma fonte TrueType comum; cai para a padrão se falhar."""
    candidatas = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for caminho in candidatas:
        if Path(caminho).is_file():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def desenhar_deteccoes(
    resultado: ResultadoDeteccao,
    arquivo_saida: Path | str,
    espessura: int = 4,
) -> Path:
    """Abre a imagem original e desenha as bboxes com rótulo + confiança.

    Parameters
    ----------
    resultado : ResultadoDeteccao
        Detecções produzidas pelo detector.
    arquivo_saida : Path
        Caminho de saída para a imagem anotada (PNG ou JPG).
    espessura : int
        Espessura das linhas da bbox em pixels.

    Returns
    -------
    Path
        Caminho do arquivo gerado.
    """
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(resultado.media_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    fonte = _fonte(tamanho=max(14, img.height // 60))

    largura_img, altura_img = img.width, img.height
    for d in resultado.deteccoes:
        cor = _CORES.get(d.categoria, _COR_DEFAULT)
        x1 = d.bbox.x * largura_img
        y1 = d.bbox.y * altura_img
        x2 = (d.bbox.x + d.bbox.w) * largura_img
        y2 = (d.bbox.y + d.bbox.h) * altura_img

        # Caixa
        draw.rectangle((x1, y1, x2, y2), outline=cor, width=espessura)

        # Rótulo com fundo opaco para legibilidade
        rotulo = f"{d.categoria} {d.confianca:.2f}"
        bbox_texto = draw.textbbox((0, 0), rotulo, font=fonte)
        tw = bbox_texto[2] - bbox_texto[0]
        th = bbox_texto[3] - bbox_texto[1]
        pad = 4
        ty = max(0, y1 - th - 2 * pad)  # acima da caixa, ou no topo
        draw.rectangle(
            (x1, ty, x1 + tw + 2 * pad, ty + th + 2 * pad),
            fill=cor,
        )
        draw.text((x1 + pad, ty + pad), rotulo, fill=(255, 255, 255), font=fonte)

    img.save(arquivo_saida, quality=92)
    return arquivo_saida
