"""Subcomandos: felinet experimentos ...

Experimentos complementares do Cap. 5 (Tabs. 9 e 10), gravados em
``runs/complementar/<experimento>/<commit>/`` (``resultados.csv`` + ``manifest.json``),
o layout que ``felinet monografia gerar`` lê. Requer o extra ``[complementares]``.
"""

from __future__ import annotations

import csv
import json
import platform
import random
from pathlib import Path

import typer

from felinet import __version__
from felinet.experimentos import complementares as c
from felinet.logging_setup import obter_logger
from felinet.runs import _git_sha_curto

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.experimentos")
_RAIZ_PACOTE = Path(__file__).resolve().parent


def _fontes(valores: list[str]) -> dict[str, Path]:
    pares = {}
    for v in valores:
        if "=" not in v:
            raise typer.BadParameter(f"--fonte espera nome=pasta, recebeu {v!r}")
        nome, pasta = v.split("=", 1)
        pares[nome] = Path(pasta)
    return pares


def _gravar(runs: Path, experimento: str, linhas: list[dict], manifesto: dict) -> Path:
    pasta = runs / "complementar" / experimento / _git_sha_curto(cwd=_RAIZ_PACOTE)
    pasta.mkdir(parents=True, exist_ok=True)
    with (pasta / "resultados.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    manifesto |= {"felinet": __version__, "python": platform.python_version()}
    (pasta / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return pasta


def _versoes() -> dict[str, str]:
    import importlib.metadata as md

    pacotes = ("torch", "timm", "ultralytics", "open_clip_torch", "umap-learn")
    return {p: md.version(p) for p in pacotes if _instalado(p)}


def _instalado(pacote: str) -> bool:
    import importlib.metadata as md

    try:
        md.version(pacote)
    except md.PackageNotFoundError:
        return False
    return True


@app.command("cascatas-multifonte")
def cascatas_multifonte(
    fonte: list[str] = typer.Option(
        ..., "--fonte", help="nome=pasta de imagens (repetível, em ordem)."
    ),
    runs: Path = typer.Option(Path("runs"), "--runs", help="Raiz dos runs."),
    pesos_yolo: Path = typer.Option(Path("yolov8n.pt"), "--pesos-yolo"),
    conf: float = typer.Option(0.2, "--conf"),
    dispositivo: str = typer.Option("auto", "--dispositivo"),
) -> None:
    """Experimento de Cascatas Multifonte (Tab. 9): YOLOv8n (classe cat) + CLIP ViT-B/32."""
    pastas = _fontes(fonte)
    imagens, duplicatas = {}, {}
    for nome, pasta in pastas.items():
        imagens[nome], duplicatas[nome] = c.imagens_da_fonte(pasta)
        LOG.info(
            "%s: %d imagens únicas (%d duplicatas descartadas)",
            nome,
            len(imagens[nome]),
            duplicatas[nome],
        )
    linhas = c.cascatas_multifonte(
        imagens,
        c.DetectorGatoYolo(pesos_yolo, dispositivo),
        c.ClassificadorGatoClip(dispositivo),
        conf,
    )
    pasta = _gravar(
        runs,
        "cascatas_multifonte",
        linhas,
        {
            "experimento": "cascatas_multifonte",
            "detector": f"YOLOv8n COCO classe cat ({pesos_yolo.name}), conf {conf}",
            "classificador": "CLIP ViT-B/32 (openai) zero-shot, imagem inteira, 4 prompts",
            "prompts": list(c.PROMPTS),
            "fontes": {
                n: {
                    "pasta": str(p),
                    "imagens": len(imagens[n]),
                    "duplicatas_descartadas": duplicatas[n],
                }
                for n, p in pastas.items()
            },  # fmt: skip
            "versoes": _versoes(),
        },
    )
    typer.echo(f"OK  {pasta / 'resultados.csv'}")


@app.command("sensibilidade-limiar")
def sensibilidade_limiar(
    fonte: str = typer.Option(..., "--fonte", help="nome=pasta de imagens."),
    runs: Path = typer.Option(Path("runs"), "--runs", help="Raiz dos runs."),
    max_imagens: int = typer.Option(
        0, "--max-imagens", help="Amostra com semente fixa (0 = todas)."
    ),
    semente: int = typer.Option(42, "--semente"),
    pesos_yolo: Path = typer.Option(Path("yolov8n.pt"), "--pesos-yolo"),
    dispositivo: str = typer.Option("auto", "--dispositivo"),
) -> None:
    """Experimento de Sensibilidade ao Limiar do Detector (Tab. 10)."""
    nome, pasta = next(iter(_fontes([fonte]).items()))
    imagens, duplicatas = c.imagens_da_fonte(pasta)
    if max_imagens and max_imagens < len(imagens):
        imagens = sorted(random.Random(semente).sample(imagens, max_imagens))
    linhas = c.sensibilidade_limiar(nome, imagens, c.DetectorGatoYolo(pesos_yolo, dispositivo))
    destino = _gravar(
        runs,
        "sensibilidade_limiar",
        linhas,
        {
            "experimento": "sensibilidade_limiar",
            "detector": f"YOLOv8n COCO classe cat ({pesos_yolo.name}), extração a 0,05",
            "fonte": {
                "nome": nome,
                "pasta": str(pasta),
                "imagens": len(imagens),
                "duplicatas_descartadas": duplicatas,
                "semente": semente,
            },  # fmt: skip
            "versoes": _versoes(),
        },
    )
    typer.echo(f"OK  {destino / 'resultados.csv'}")


@app.command("visualizacao-exploratoria")
def visualizacao_exploratoria(
    catalogo: Path = typer.Option(
        ..., "--catalogo", help="Pasta com uma subpasta por indivíduo (CatIndividualImages)."
    ),
    runs: Path = typer.Option(Path("runs"), "--runs", help="Raiz dos runs."),
    n_identidades: int = typer.Option(20, "--n-identidades"),
    min_por_id: int = typer.Option(3, "--min-por-id"),
    max_por_id: int = typer.Option(8, "--max-por-id"),
    semente: int = typer.Option(42, "--semente"),
    dispositivo: str = typer.Option("auto", "--dispositivo"),
) -> None:
    """Projeção de Visualização Exploratória (Fig. 16): MegaDescriptor-T-224 + UMAP 2D."""
    import numpy as np
    from PIL import Image

    from felinet.experimentos import visualizacao as v
    from felinet.pipeline.fase4_reid.megadescriptor import ExtratorMegaDescriptor

    itens = v.selecionar_catalogo(catalogo, n_identidades, min_por_id, max_por_id, semente)
    extrator = ExtratorMegaDescriptor(dispositivo=dispositivo)

    def extrair(caminho: Path) -> np.ndarray:
        with Image.open(caminho) as img:
            return np.asarray(extrator.extrair_de_pil(str(caminho), 0, img.convert("RGB")).vetor)

    vetores, coords, linhas = v.visualizacao_exploratoria(
        itens, extrair, lambda x: v.projetar_umap(x, semente=semente)
    )
    pasta = _gravar(
        runs,
        "visualizacao_exploratoria",
        linhas,
        {
            "experimento": "visualizacao_exploratoria",
            "catalogo": str(catalogo),
            "identidades": len({i for i, _ in itens}),
            "imagens": len(itens),
            "parametros": {
                "min_por_id": min_por_id,
                "max_por_id": max_por_id,
                "semente": semente,
                "umap": {"n_neighbors": 15, "min_dist": 0.1, "metric": "cosine"},
            },  # fmt: skip
            "versoes": _versoes(),
            # onde os embeddings foram extraídos (a execução final da monografia usou GPU MX250;
            # esta projeção pode ter sido gerada em outra máquina, inclusive em CPU)
            "ambiente": {
                "dispositivo": extrator.dispositivo,
                "maquina": platform.node(),
                "sistema": platform.platform(),
                "processador": platform.machine(),
            },
        },
    )
    np.savez(pasta / "embeddings.npz", vetores=vetores, coords=coords,
             ids=np.array([i for i, _ in itens]), arquivos=np.array([p.name for _, p in itens]))  # fmt: skip
    typer.echo(f"OK  {pasta / 'resultados.csv'}")
