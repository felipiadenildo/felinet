"""Extrato isolado: helper + comando `dev preparar-petface-mini`.

Este arquivo NAO substitui `src/felinet/comandos/dev.py`. Serve como
referencia "stand-alone" do patch aplicado ao comando
`felinet dev preparar-petface-mini` no escopo do v23-smoke-fix.

Como usar em substituicao manual:
  1. Abra `src/felinet/comandos/dev.py`.
  2. Substitua a definicao existente de `preparar_petface_mini` (linhas
     ~20-62 na versao original) pelo bloco @app.command abaixo.
  3. Acrescente, antes da primeira @app.command, o helper privado
     `_gerar_petface_mini_sintetico`.
  4. Mantenha intactos os outros comandos do arquivo (`validar-ambiente`,
     `demo`, `gerar-resumo-html`, `limpar-saidas-dev`).

Mudanca em relacao a versao original:
  - `--origem` passa a ser OPCIONAL. Quando omitido, gera um subset
    SINTETICO via PIL respeitando a estrutura oficial PetFace:
        data/dev/reid_mini/split/cat/reidentification.csv
        data/dev/reid_mini/images/cat/<id_pad>/<n>.png
  - Quando `--origem` e' passado, comportamento legado preservado, mas
    agora tambem grava `reidentification.csv` (antes nao gravava).
  - Defaults atualizados para 20 individuos x 4 imagens (smoke).
"""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

# ---------------------------------------------------------------------------
# As tres linhas abaixo (`app`, `LOG`) ja existem em `comandos/dev.py`. Estao
# aqui apenas para o arquivo isolado importar/rodar sozinho. NAO duplique-as
# quando colar dentro de `dev.py`.
# ---------------------------------------------------------------------------

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.dev")


# ---------------------------------------------------------------------------
# helper interno (cole antes do primeiro @app.command em dev.py)
# ---------------------------------------------------------------------------


def _gerar_petface_mini_sintetico(
    destino: Path,
    individuos: int,
    imagens_por_id: int,
    seed: int = 42,
) -> int:
    """Cria um PetFace-like sintetico em ``destino`` (estrutura oficial).

    Layout produzido:
        destino/
            split/cat/reidentification.csv
            images/cat/<id_pad>/<n>.png

    Cada individuo recebe ``imagens_por_id`` PNGs gerados via PIL com cor
    distinta para servir de smoke da pipeline Re-ID (nao tem semantica
    biologica - serve apenas para validar o fluxo).

    Returns:
        Numero total de imagens criadas.
    """
    import csv
    from random import Random

    from PIL import Image, ImageDraw

    rng = Random(seed)
    img_root = destino / "images" / "cat"
    split_dir = destino / "split" / "cat"
    img_root.mkdir(parents=True, exist_ok=True)
    split_dir.mkdir(parents=True, exist_ok=True)

    n_total = 0
    linhas_csv: list[tuple[str, str]] = []  # (filename, label)
    for idx in range(individuos):
        id_pad = f"{idx:06d}"
        pasta = img_root / id_pad
        pasta.mkdir(exist_ok=True)
        # cor base unica por individuo, com leve jitter por imagem
        cor_base = (
            rng.randint(40, 220),
            rng.randint(40, 220),
            rng.randint(40, 220),
        )
        for j in range(imagens_por_id):
            jitter = tuple(max(0, min(255, c + rng.randint(-20, 20))) for c in cor_base)
            img = Image.new("RGB", (128, 128), color=jitter)
            draw = ImageDraw.Draw(img)
            # marca textual para inspecao visual humana
            draw.text((10, 10), f"id={idx}", fill=(255, 255, 255))
            draw.text((10, 30), f"n={j}", fill=(255, 255, 255))
            nome = f"{j:02d}.png"
            img.save(pasta / nome)
            n_total += 1
        # a primeira imagem de cada individuo e' a query oficial
        linhas_csv.append((f"cat/{id_pad}/00.png", str(idx)))

    csv_path = split_dir / "reidentification.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["filename", "label"])
        for filename, label in linhas_csv:
            escritor.writerow([filename, label])

    return n_total


# ---------------------------------------------------------------------------
# comando @app.command (substitui o existente em dev.py)
# ---------------------------------------------------------------------------


@app.command("preparar-petface-mini")
def preparar_petface_mini(
    origem: Path = typer.Option(
        None,
        "--origem",
        help=(
            "Caminho para o PetFace completo (e.g. /mnt/ssd/petface). "
            "Quando omitido, gera um subset SINTETICO via PIL (smoke)."
        ),
    ),
    individuos: int = typer.Option(20, "--individuos", help="N de IDs a amostrar/gerar."),
    imagens_por_id: int = typer.Option(
        4,
        "--imagens-por-id",
        help="Imagens por individuo.",
    ),
) -> None:
    """Cria ``data/dev/reid_mini/`` com subset PetFace (real ou sintetico).

    Modos de operacao:

    * ``--origem <caminho>`` aponta para um PetFace real (estrutura oficial
      ``images/cat/<id_pad>/*.png``). Faz amostragem aleatoria de
      ``individuos`` IDs com ``imagens_por_id`` imagens cada.
    * Sem ``--origem``: gera um dataset SINTETICO usando PIL (PNGs coloridos
      etiquetados), respeitando a estrutura oficial. Util como smoke
      bootstrap quando o PetFace real ainda nao esta linkado em
      ``data/raw/reid/petface``.
    """
    import shutil
    from random import Random

    cfg = carregar_perfil("dev")
    destino = cfg.raw_petface
    destino.mkdir(parents=True, exist_ok=True)

    if origem is None:
        n_total = _gerar_petface_mini_sintetico(destino, individuos, imagens_por_id)
        typer.echo(
            f"OK [sintetico]: {individuos} IDs x {imagens_por_id} imgs "
            f"= {n_total} -> {destino}"
        )
        return

    if not origem.exists():
        LOG.error(f"Origem inexistente: {origem}")
        raise typer.Exit(code=1)

    # caminho real: aceita tanto a raiz do PetFace quanto a subpasta images/cat
    raiz_imgs = origem / "images" / "cat" if (origem / "images" / "cat").is_dir() else origem
    img_dest_root = destino / "images" / "cat"
    img_dest_root.mkdir(parents=True, exist_ok=True)

    rng = Random(42)
    ids = sorted(p for p in raiz_imgs.iterdir() if p.is_dir())
    ids = rng.sample(ids, min(individuos, len(ids)))

    import csv

    linhas_csv: list[tuple[str, str]] = []
    n_copiadas = 0
    for ordem, id_dir in enumerate(ids):
        imgs = sorted(
            p for p in id_dir.glob("*") if p.suffix.lower() in {".jpg", ".png", ".jpeg"}
        )
        imgs = rng.sample(imgs, min(imagens_por_id, len(imgs)))
        # padroniza nome do diretorio destino para 6 digitos (ordem na amostra)
        id_pad = f"{ordem:06d}"
        dest_id = img_dest_root / id_pad
        dest_id.mkdir(exist_ok=True)
        for j, img in enumerate(imgs):
            nome = f"{j:02d}{img.suffix.lower()}"
            shutil.copy2(img, dest_id / nome)
            n_copiadas += 1
        if imgs:
            linhas_csv.append((f"cat/{id_pad}/00{imgs[0].suffix.lower()}", str(ordem)))

    split_dir = destino / "split" / "cat"
    split_dir.mkdir(parents=True, exist_ok=True)
    csv_path = split_dir / "reidentification.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["filename", "label"])
        for filename, label in linhas_csv:
            escritor.writerow([filename, label])

    typer.echo(
        f"OK [real]: {len(ids)} IDs x ~{imagens_por_id} imgs = {n_copiadas} -> {destino}"
    )
