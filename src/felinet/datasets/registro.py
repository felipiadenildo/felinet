"""Registro de datasets locais com tipo e layout.

Carrega ``configs/datasets_locais.yaml`` e expõe API tipada. O arquivo é
versionado apenas como ``datasets_locais.example.yaml``; cada usuário copia
para ``datasets_locais.yaml`` (gitignored) e ajusta os caminhos do próprio
disco. A camada por-usuário cria os symlinks em ``data/raw/`` que o
``paths.yaml`` referencia.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

TipoDataset = Literal[
    "camera_trap_brutas",
    "reid_crops_rotulados",
    "camera_trap_rotulado_identidade",
]
LayoutDataset = Literal[
    "flat",
    "por_classe",
    "por_identidade",
    "cocotraps",
    "aninhado_livre",
]

FASES_POR_TIPO: dict[str, list[int]] = {
    "camera_trap_brutas": [1, 2, 3],
    "reid_crops_rotulados": [4],
    "camera_trap_rotulado_identidade": [1, 2, 3, 4],
}

CATEGORIA_POR_TIPO: dict[str, str] = {
    "camera_trap_brutas": "camera_trap",
    "reid_crops_rotulados": "reid",
    "camera_trap_rotulado_identidade": "camera_trap",
}


@dataclass(frozen=True)
class DatasetLocal:
    """Descrição declarativa de um dataset local."""

    nome: str
    tipo: TipoDataset
    layout: LayoutDataset
    caminho: Path
    descricao: str = ""
    fases_aplicaveis: list[int] = field(default_factory=list)

    @property
    def categoria(self) -> str:
        return CATEGORIA_POR_TIPO[self.tipo]

    @property
    def link_destino(self) -> Path:
        """Caminho relativo (a partir da raiz do projeto) do symlink esperado."""
        return Path("data") / "raw" / self.categoria / self.nome


def carregar_datasets_locais(
    arquivo: Path | None = None,
) -> dict[str, DatasetLocal]:
    """Lê ``configs/datasets_locais.yaml``. Retorna ``{}`` se ausente."""
    if arquivo is None:
        from felinet.config import raiz_projeto

        arquivo = raiz_projeto() / "configs" / "datasets_locais.yaml"
    if not arquivo.exists():
        return {}
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
    bruto = dados.get("datasets", {}) or {}
    out: dict[str, DatasetLocal] = {}
    for nome, cfg in bruto.items():
        tipo = cfg.get("tipo", "camera_trap_brutas")
        out[nome] = DatasetLocal(
            nome=nome,
            tipo=tipo,
            layout=cfg.get("layout", "aninhado_livre"),
            caminho=Path(cfg["caminho"]).expanduser(),
            descricao=cfg.get("descricao", ""),
            fases_aplicaveis=cfg.get(
                "fases_aplicaveis", FASES_POR_TIPO.get(tipo, [])
            ),
        )
    return out


def validar_fase_aplicavel(ds: DatasetLocal, fase: int) -> None:
    """Levanta ``ValueError`` se ``fase`` não pertence a ``fases_aplicaveis``."""
    if fase not in ds.fases_aplicaveis:
        raise ValueError(
            f"fonte '{ds.nome}' (tipo {ds.tipo}) não suporta fase {fase}. "
            f"Fases aplicáveis: {ds.fases_aplicaveis}"
        )
