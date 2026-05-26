"""E0 — Ingestão: conversão para esquema Camtrap-DP simplificado.

Camtrap-DP é o padrão GBIF para dados de armadilhas fotográficas.
Esta versão implementa o subconjunto mínimo: deployment + media,
sem observations (que virão dos estágios E1-E3).

Especificação completa: https://camtrap-dp.tdwg.org/
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .exif import extrair_metadados


@dataclass(frozen=True)
class Deployment:
    """Registro de implantação (câmera em um ponto, por um período)."""

    deployment_id: str
    location_id: str  # ex.: "P01"
    location_name: str
    deployment_start: datetime
    deployment_end: datetime
    camera_model: str


@dataclass(frozen=True)
class MediaRecord:
    """Uma mídia (imagem) registrada em um deployment."""

    media_id: str
    deployment_id: str
    timestamp: datetime
    file_path: str
    file_mediatype: str  # "image/jpeg" etc.
    capture_method: str = "activityDetection"


def _media_id_estavel(caminho: Path, deployment_id: str) -> str:
    """Gera um media_id determinístico (UUIDv5) — reproduzível."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
    chave = f"{deployment_id}::{caminho.name}"
    return str(uuid.uuid5(namespace, chave))


def _mediatype(caminho: Path) -> str:
    ext = caminho.suffix.lower()
    mapa = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }
    return mapa.get(ext, "application/octet-stream")


def imagens_para_media(
    imagens: list[Path],
    deployment: Deployment,
) -> list[MediaRecord]:
    """Converte uma lista de imagens em registros Camtrap-DP `media`."""
    registros: list[MediaRecord] = []
    for img in imagens:
        meta = extrair_metadados(img)
        ts = meta.timestamp or deployment.deployment_start
        registros.append(
            MediaRecord(
                media_id=_media_id_estavel(img, deployment.deployment_id),
                deployment_id=deployment.deployment_id,
                timestamp=ts,
                file_path=str(img),
                file_mediatype=_mediatype(img),
            )
        )
    return registros


def salvar_camtrap_json(
    deployment: Deployment,
    media: list[MediaRecord],
    arquivo_saida: Path | str,
) -> None:
    """Serializa deployment + media em JSON Camtrap-DP simplificado."""
    payload = {
        "profile": "camtrap-dp-simplified/0.1",
        "deployments": [
            {
                **dict(deployment.__dict__.items()),
                "deployment_start": deployment.deployment_start.isoformat(),
                "deployment_end": deployment.deployment_end.isoformat(),
            }
        ],
        "media": [{**m.__dict__, "timestamp": m.timestamp.isoformat()} for m in media],
    }
    arquivo_saida = Path(arquivo_saida)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_saida.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
