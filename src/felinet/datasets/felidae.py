"""Loader + sampler estratificado + downloader do dataset Felidae Conservation Fund.

Dataset: 357k imagens, 66 categorias (espécies + agrupamentos), formato
COCO Camera Traps. Coletado em armadilhas fotográficas da Bay Area por
Felidae Conservation Fund (Bay Area Puma + Bobcat Projects).

Refs:
    https://lila.science/datasets/felidae-conservation-fund
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger("felinet.datasets.felidae")

URL_BASE_AZURE = (
    "https://lilawildlife.blob.core.windows.net/lila-wildlife/felidae-conservation-fund/"
)
URL_METADATA_ZIP = URL_BASE_AZURE + "felidae_conservation_fund_2020_2025.zip"
NOME_JSON_INTERNO = "felidae_conservation_fund_2020_2025.json"

# Cota padrão (estratificação) por classe — alvos do TCC.
#   * Felinos: foco principal (Re-ID + classificação).
#   * Confundíveis: animais que MegaDetector pode confundir com felinos.
#   * Demais: amostra mínima para o classificador SpeciesNet.
COTAS_PADRAO: dict[str, int] = {
    # Felinos
    "bobcat": 1500,
    "puma": 1500,
    "domestic cat": 3,
    # Confundíveis (mamíferos médios/grandes)
    "gray fox": 1200,
    "coyote": 1200,
    "raccoon": 800,
    "mule deer": 600,
}
# Cota default para classes não listadas em COTAS_PADRAO
COTA_DEMAIS_PADRAO: int = 30

# Preset SMOKE: ~200 imgs / ~460 MB — validação ponta-a-ponta do pipeline
# operacional (ingestão -> detecção -> classificação) sem comprometer a
# estratificação por espécies-chave. Após validar, re-execute com o
# preset 'completo' (COTAS_PADRAO).
COTAS_SMOKE: dict[str, int] = {
    # Felinos
    "bobcat": 40,
    "puma": 40,
    "domestic cat": 3,
    # Confundíveis
    "gray fox": 30,
    "coyote": 30,
    "raccoon": 20,
    "mule deer": 15,
}
COTA_DEMAIS_SMOKE: int = 1

# Tabela de presets nomeados.
PRESETS: dict[str, tuple[dict[str, int], int]] = {
    "completo": (COTAS_PADRAO, COTA_DEMAIS_PADRAO),
    "smoke": (COTAS_SMOKE, COTA_DEMAIS_SMOKE),
}


@dataclass(frozen=True)
class ImagemFelidae:
    """Entrada amostrada do dataset."""

    id: str  # caminho relativo no blob, ex.: '1/2025-03/<sha>.jpg'
    categoria_id: int
    categoria_nome: str
    location: str
    datetime: str


def baixar_metadados(destino_zip: Path, *, force: bool = False) -> Path:
    """Baixa (se necessário) o ZIP de metadados COCO Camera Traps.

    Returns:
        Caminho para o JSON descompactado.
    """
    import zipfile

    destino_zip.parent.mkdir(parents=True, exist_ok=True)
    if force or not destino_zip.exists():
        LOG.info(f"Baixando metadados Felidae ({URL_METADATA_ZIP}) -> {destino_zip}")
        urllib.request.urlretrieve(URL_METADATA_ZIP, destino_zip)

    pasta = destino_zip.parent
    json_path = pasta / NOME_JSON_INTERNO
    if force or not json_path.exists():
        with zipfile.ZipFile(destino_zip, "r") as zf:
            zf.extract(NOME_JSON_INTERNO, pasta)
    return json_path


def carregar_anotacoes(
    json_path: Path,
) -> tuple[list[dict], list[dict], dict[int, str]]:
    """Lê o JSON COCO e retorna (images, annotations, categoria_id->nome)."""
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    cat_map = {c["id"]: c["name"] for c in payload["categories"]}
    return payload["images"], payload["annotations"], cat_map


def amostrar_estratificado(
    images: list[dict],
    annotations: list[dict],
    cat_map: dict[int, str],
    *,
    cotas: dict[str, int] | None = None,
    cota_demais: int = COTA_DEMAIS_PADRAO,
    seed: int = 0,
) -> list[ImagemFelidae]:
    """Amostragem estratificada por categoria, respeitando cotas por classe."""
    rng = random.Random(seed)
    cotas = cotas if cotas is not None else dict(COTAS_PADRAO)

    # Indexa image_id -> primeira annotation
    img_para_cat: dict[str, int] = {}
    for ann in annotations:
        if ann["image_id"] not in img_para_cat:
            img_para_cat[ann["image_id"]] = ann["category_id"]

    info_por_id: dict[str, dict] = {img["id"]: img for img in images}

    por_categoria: dict[int, list[str]] = defaultdict(list)
    for img_id, cat_id in img_para_cat.items():
        por_categoria[cat_id].append(img_id)

    selecionados: list[ImagemFelidae] = []
    for cat_id, ids in por_categoria.items():
        nome = cat_map[cat_id]
        alvo = cotas.get(nome, cota_demais)
        if alvo <= 0:
            continue
        rng.shuffle(ids)
        amostra = ids[:alvo]
        for img_id in amostra:
            info = info_por_id.get(img_id, {})
            selecionados.append(
                ImagemFelidae(
                    id=img_id,
                    categoria_id=cat_id,
                    categoria_nome=nome,
                    location=str(info.get("location", "")),
                    datetime=str(info.get("datetime", "")),
                )
            )
    return selecionados


def _baixar_uma(
    item: ImagemFelidae,
    destino_raiz: Path,
    *,
    timeout: float = 30.0,
    tentativas: int = 3,
) -> tuple[ImagemFelidae, bool, str]:
    """Baixa uma imagem (idempotente). Retorna (item, sucesso, mensagem)."""
    pasta = destino_raiz / item.categoria_nome.replace(" ", "_")
    pasta.mkdir(parents=True, exist_ok=True)
    nome = Path(item.id).name
    destino = pasta / nome
    if destino.exists() and destino.stat().st_size > 0:
        return item, True, "ja-existe"

    url = URL_BASE_AZURE + item.id
    erro: str = ""
    for tentativa in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "felinet/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = resp.read()
            destino.write_bytes(dados)
            return item, True, "ok"
        except (urllib.error.URLError, TimeoutError) as exc:
            erro = f"tentativa {tentativa}: {exc}"
            continue
    return item, False, erro


def baixar_em_paralelo(
    itens: list[ImagemFelidae],
    destino_raiz: Path,
    *,
    n_threads: int = 8,
    timeout: float = 30.0,
    tentativas: int = 3,
    callback_progresso=None,
) -> dict[str, int]:
    """Baixa lista de imagens em paralelo. Retorna contadores."""
    destino_raiz.mkdir(parents=True, exist_ok=True)
    contadores = {"ok": 0, "ja-existe": 0, "falha": 0}
    erros_path = destino_raiz / "_erros.log"
    erros_lines: list[str] = []

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futuros = {
            pool.submit(
                _baixar_uma, item, destino_raiz, timeout=timeout, tentativas=tentativas
            ): item
            for item in itens
        }
        for i, fut in enumerate(as_completed(futuros), start=1):
            item, sucesso, msg = fut.result()
            if sucesso:
                contadores[msg] = contadores.get(msg, 0) + 1
            else:
                contadores["falha"] += 1
                erros_lines.append(f"{item.id}\t{msg}")
            if callback_progresso is not None and i % 50 == 0:
                callback_progresso(i, len(itens), contadores)

    if erros_lines:
        erros_path.write_text("\n".join(erros_lines), encoding="utf-8")
    return contadores


def gravar_manifesto_selecao(
    itens: list[ImagemFelidae],
    destino: Path,
) -> None:
    """Persiste a seleção amostral como CSV (para rastreabilidade)."""
    import csv

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "categoria_id", "categoria_nome", "location", "datetime", "sha_id"])
        for it in itens:
            sha_id = hashlib.sha256(it.id.encode()).hexdigest()[:16]
            writer.writerow(
                [
                    it.id,
                    it.categoria_id,
                    it.categoria_nome,
                    it.location,
                    it.datetime,
                    sha_id,
                ]
            )
