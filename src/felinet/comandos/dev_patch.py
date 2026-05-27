"""Subcomandos: felinet dev ...

Utilitarios de desenvolvimento. Nao usados na execucao oficial; servem
apenas para preparar/validar o ambiente dev.
"""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.config import carregar_perfil
from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.dev")


# ---------------------------------------------------------------------------
# helpers internos
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
            # marca textual para inspeção visual humana
            draw.text((10, 10), f"id={idx}", fill=(255, 255, 255))
            draw.text((10, 30), f"n={j}", fill=(255, 255, 255))
            nome = f"{j:02d}.png"
            img.save(pasta / nome)
            n_total += 1
        # a primeira imagem de cada individuo é a query oficial
        linhas_csv.append((f"cat/{id_pad}/00.png", str(idx)))

    csv_path = split_dir / "reidentification.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["filename", "label"])
        for filename, label in linhas_csv:
            escritor.writerow([filename, label])

    return n_total


# ---------------------------------------------------------------------------
# comandos
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


@app.command("validar-ambiente")
def validar_ambiente() -> None:
    """Sanity check: verifica imports, modelos, perfis e GPU."""
    import importlib

    typer.echo("== felinet: validacao de ambiente ==")
    pacotes = ["torch", "numpy", "PIL", "yaml", "typer", "matplotlib"]
    for pkg in pacotes:
        try:
            mod = importlib.import_module(pkg)
            versao = getattr(mod, "__version__", "?")
            typer.echo(f"  [OK] {pkg:12s} {versao}")
        except ImportError as exc:
            typer.echo(f"  [!!] {pkg:12s} {exc}")

    try:
        import torch

        cuda = torch.cuda.is_available()
        dispositivo = torch.cuda.get_device_name(0) if cuda else "CPU"
        typer.echo(f"  [OK] CUDA disponivel: {cuda} ({dispositivo})")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"  [!!] torch/CUDA: {exc}")

    cfg_dev = carregar_perfil("dev")
    typer.echo(f"  [OK] Perfil dev raiz: {cfg_dev.raw_camera_trap.parent}")


@app.command("demo")
def demo(
    fonte: str = typer.Option(
        "kaggle_cats",
        "--fonte",
        help="Fonte para a demo (precisa estar linkada via 'datasets linkar').",
    ),
    n: int = typer.Option(
        50,
        "--n",
        help="Número de imagens a processar (recomendado 30-100 para ver tudo).",
    ),
    perfil: str = typer.Option("dev", "--perfil"),
) -> None:
    """Roda o pipeline em modo dev com amostra pequena.

    Equivale a ``felinet pipeline executar --perfil <perfil> --fonte <fonte>
    --max-amostras <n> --dev``. Ao final aponta a pasta
    ``dev_visualizacao/`` onde estão os artefatos visuais.
    """
    import subprocess
    import sys

    typer.echo(f"[demo] rodando pipeline em {fonte} ({n} imagens, perfil {perfil}, modo --dev)...")
    cmd = [
        sys.executable,
        "-m",
        "felinet",
        "pipeline",
        "executar",
        "--perfil",
        perfil,
        "--fonte",
        fonte,
        "--max-amostras",
        str(n),
        "--dev",
    ]
    subprocess.run(cmd, check=False)

    # gera resumo.html ao final, se a pasta dev_visualizacao tiver sido criada
    from felinet.runs import resolver_latest

    cfg = carregar_perfil(perfil)
    raiz_runs = getattr(cfg, "raiz_runs", Path("runs"))
    base_run = resolver_latest(
        modo="operacional", fonte=fonte, perfil=perfil, raiz_runs=raiz_runs
    )

    if base_run is None:
        typer.echo("\n[demo] nao achei run operacional via latest/. Veja runs/operacional/.")
        return

    base_dev = base_run / "dev_visualizacao"

    if base_dev.is_dir():
        from felinet.pipeline.dev_visual import gerar_resumo_html

        try:
            arq_html = gerar_resumo_html(
                base_dev, titulo_run=f"fonte={fonte} | perfil={perfil} | n={n}"
            )
            typer.echo("\n[demo] pronto. Galeria did\u00e1tica gerada:")
            typer.echo(f"  {arq_html}")
            typer.echo("  abrir no navegador: xdg-open ou file://...")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"[demo] aviso: falhou gerar resumo.html: {exc}")
            typer.echo(f"  pasta bruta: {base_dev}")
    else:
        typer.echo("\n[demo] pipeline n\u00e3o gerou dev_visualizacao/. Veja:")
        typer.echo(f"  ls -la {base_run}")


@app.command("gerar-resumo-html")
def gerar_resumo_html_cmd(
    fonte: str = typer.Option(..., "--fonte", help="Fonte do run (e.g. kaggle_cats)."),
    perfil: str = typer.Option("dev", "--perfil"),
    run: str = typer.Option(
        "latest",
        "--run",
        help="Tag do run (default: 'latest'). Use o nome do diretorio em runs/.../_/.",
    ),
) -> None:
    """Gera ``resumo.html`` em ``dev_visualizacao/`` de um run ja' executado."""
    from felinet.config import raiz_projeto
    from felinet.pipeline.dev_visual import gerar_resumo_html
    from felinet.runs import listar_runs, resolver_latest

    cfg = carregar_perfil(perfil)
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")

    base_run = None
    if run == "latest":
        # 1) tenta symlink runs/latest/<chave> via resolver_latest
        base_run = resolver_latest(
            modo="operacional",
            fonte=fonte,
            perfil=cfg.nome,
            raiz_runs=raiz_runs,
        )
        # 2) fallback: ultimo run em runs/operacional/<fonte>/<perfil>/_/
        if base_run is None:
            registros = listar_runs(
                raiz_runs,
                modo="operacional",
                fonte=fonte,
                perfil=cfg.nome,
            )
            if registros:
                base_run = registros[0].raiz
    else:
        base_run = raiz_runs / "operacional" / fonte / cfg.nome / "_" / run

    if base_run is None or not base_run.is_dir():
        typer.echo(
            f"[erro] nao encontrei run operacional para fonte={fonte}, "
            f"perfil={cfg.nome}, run={run}."
        )
        typer.echo("  certifique-se de ter rodado o pipeline com --dev.")
        raise typer.Exit(code=1)

    base_dev = base_run / "dev_visualizacao"
    if not base_dev.is_dir():
        typer.echo(f"[erro] nao achei pasta dev_visualizacao em: {base_run}")
        typer.echo("  certifique-se de ter rodado o pipeline com --dev.")
        raise typer.Exit(code=1)

    arq = gerar_resumo_html(
        base_dev,
        titulo_run=f"fonte={fonte} | perfil={cfg.nome} | run={base_run.name}",
    )
    typer.echo(f"[ok] gerado: {arq}")
    typer.echo(f"  abrir: xdg-open {arq}")
