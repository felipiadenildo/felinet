"""Desenha bboxes de deteccoes sobre as imagens originais.

Le um JSON de saida da Fase II (lista de ``ResultadoDeteccao``) e gera,
para cada imagem, uma versao anotada com as bounding boxes coloridas
por categoria (animal/person/vehicle).

Uso:
    python 03_codigo/scripts/visualizar_deteccoes.py \\
        [--entrada-json PATH] [--saida PATH]

Por padrao consome ``04_dados/interim/deteccoes_amostras.json`` e grava
em ``05_figuras/deteccoes_dev/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ENTRADA_PADRAO = Path("04_dados/interim/deteccoes_amostras.json")
SAIDA_PADRAO = Path("05_figuras/deteccoes_dev")

CORES_CATEGORIA = {
    "animal": (255, 64, 64),    # vermelho
    "person": (64, 160, 255),   # azul
    "vehicle": (64, 255, 96),   # verde
}


def _carregar_resultados(caminho: Path) -> list[dict]:
    """Carrega o JSON da Fase II como lista de dicts."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    # Aceita tanto {"resultados": [...]} quanto lista crua
    if isinstance(dados, dict):
        return dados.get("resultados", dados.get("imagens", []))
    return dados


def _desenhar_bboxes(media_path: Path, resultado: dict, saida: Path) -> int:
    """Desenha as bboxes do resultado sobre a imagem e salva. Retorna n bboxes."""
    img = Image.open(media_path).convert("RGB")
    largura, altura = img.size
    desenho = ImageDraw.Draw(img)
    try:
        fonte = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
    except OSError:
        fonte = ImageFont.load_default()

    deteccoes = resultado.get("deteccoes", [])
    for det in deteccoes:
        bbox = det["bbox"]
        x1 = int(bbox["x"] * largura)
        y1 = int(bbox["y"] * altura)
        x2 = int((bbox["x"] + bbox["w"]) * largura)
        y2 = int((bbox["y"] + bbox["h"]) * altura)
        cor = CORES_CATEGORIA.get(det["categoria"], (255, 255, 255))
        desenho.rectangle([x1, y1, x2, y2], outline=cor, width=4)
        rotulo = f"{det['categoria']} {det['confianca']:.2f}"
        desenho.text((x1 + 4, max(0, y1 - 32)), rotulo, fill=cor, font=fonte)

    saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, quality=92)
    return len(deteccoes)


def visualizar(entrada_json: Path, saida_dir: Path) -> int:
    """Le o JSON e gera as imagens anotadas. Retorna codigo de saida."""
    if not entrada_json.exists():
        print(f"JSON de deteccoes nao encontrado: {entrada_json}")
        return 1

    resultados = _carregar_resultados(entrada_json)
    if not resultados:
        print(f"Nenhum resultado em {entrada_json}")
        return 1

    saida_dir.mkdir(parents=True, exist_ok=True)
    print(f"Anotando {len(resultados)} imagem(ns)...")

    for resultado in resultados:
        media_path = Path(resultado["media_path"])
        if not media_path.exists():
            print(f"  ! arquivo ausente: {media_path}")
            continue
        nome_anotado = f"{media_path.stem}_anotada{media_path.suffix}"
        saida = saida_dir / nome_anotado
        n_bboxes = _desenhar_bboxes(media_path, resultado, saida)
        marca = "✓" if n_bboxes else "—"
        print(f"  {marca} {nome_anotado}: {n_bboxes} bboxes")

    print(f"\nImagens anotadas em: {saida_dir.resolve()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entrada-json",
        type=Path,
        default=ENTRADA_PADRAO,
        help=f"JSON de deteccoes (padrao: {ENTRADA_PADRAO})",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=SAIDA_PADRAO,
        help=f"Diretorio de saida (padrao: {SAIDA_PADRAO})",
    )
    args = parser.parse_args()
    return visualizar(args.entrada_json, args.saida)


if __name__ == "__main__":
    sys.exit(main())
