"""Carregamento de configuracoes (paths.yaml, modelos.yaml, pipeline.yaml).

Centraliza acesso aos caminhos de dados. Substitui todos os ``Path("04_dados/...")``
hard-coded do projeto antigo. Resolve perfil ``dev`` ou ``prod`` baseado em:

1. Argumento explicito da funcao (``perfil="..."``)
2. Variavel de ambiente ``FELINET_PERFIL``
3. Default ``"dev"``

Tambem suporta sobrescritas pontuais via variaveis de ambiente prefixadas
com ``FELINET_`` (ex.: ``FELINET_DATA_RAW`` sobrescreve ``raw_camera_trap``).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

VAR_PERFIL = "FELINET_PERFIL"
VAR_CONFIG = "FELINET_CONFIG"
PERFIL_DEFAULT = "dev"


def raiz_projeto() -> Path:
    """Retorna a raiz do projeto.

    Detecta procurando ``pyproject.toml`` ao subir a arvore a partir
    deste arquivo. Funciona tanto em editable install quanto em wheel.
    """
    aqui = Path(__file__).resolve()
    for ancestral in aqui.parents:
        if (ancestral / "pyproject.toml").exists():
            return ancestral
    # fallback: cwd
    return Path.cwd()


@dataclass(frozen=True)
class Perfil:
    """Caminhos resolvidos para um perfil."""

    nome: str
    raw_camera_trap: Path
    raw_petface: Path
    interim: Path
    processed: Path
    artifacts_figuras: Path
    artifacts_tabelas: Path
    saida_manifesto: Path
    saida_deteccoes: Path
    saida_classificacoes: Path
    saida_crops: Path
    anotacao_identidade: Path
    saida_embeddings: Path
    saida_avaliacao_pipeline: Path
    raw_campus2: Path | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def _resolver_path(raiz: Path, valor: str) -> Path:
    p = Path(valor).expanduser()
    if not p.is_absolute():
        p = raiz / p
    return p


def _aplicar_overrides_env(dados: dict[str, Any]) -> dict[str, Any]:
    """Sobrescritas pontuais por variavel de ambiente.

    Convencao: ``FELINET_<CHAVE_MAIUSCULA>`` sobrescreve a chave correspondente.
    Exemplo: ``FELINET_RAW_PETFACE=/tmp/petface`` -> raw_petface.
    """
    overrides = {}
    for chave in dados:
        var = f"FELINET_{chave.upper()}"
        if var in os.environ:
            overrides[chave] = os.environ[var]
    dados = dict(dados)
    dados.update(overrides)
    return dados


@lru_cache(maxsize=4)
def carregar_perfil(perfil: str | None = None) -> Perfil:
    """Carrega um perfil de ``configs/paths.yaml``.

    Args:
        perfil: Nome do perfil. Se ``None``, le ``FELINET_PERFIL`` ou usa
            ``"dev"`` como default.

    Raises:
        FileNotFoundError: Se ``configs/paths.yaml`` nao existir.
        KeyError: Se o perfil solicitado nao existir no YAML.
    """
    nome = perfil or os.environ.get(VAR_PERFIL, PERFIL_DEFAULT)

    caminho_yaml = os.environ.get(VAR_CONFIG)
    if caminho_yaml:
        yaml_path = Path(caminho_yaml).expanduser().resolve()
    else:
        yaml_path = raiz_projeto() / "configs" / "paths.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(
            f"configs/paths.yaml nao encontrado em {yaml_path}. "
            f"Defina FELINET_CONFIG ou execute a partir da raiz do projeto."
        )

    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    perfis = raw.get("perfis", {})
    if nome not in perfis:
        disponiveis = ", ".join(sorted(perfis))
        raise KeyError(
            f"Perfil '{nome}' nao definido em {yaml_path}. "
            f"Disponiveis: {disponiveis}"
        )

    dados = _aplicar_overrides_env(perfis[nome])
    raiz = raiz_projeto()

    campos_obrigatorios = {f.name for f in fields(Perfil) if f.name not in {"nome", "raw_campus2", "extras"}}
    resolvidos: dict[str, Any] = {"nome": nome}
    for chave, valor in dados.items():
        if chave in campos_obrigatorios or chave == "raw_campus2":
            resolvidos[chave] = _resolver_path(raiz, valor)
        else:
            resolvidos.setdefault("extras", {})[chave] = valor

    faltando = campos_obrigatorios - set(resolvidos)
    if faltando:
        raise KeyError(f"Perfil '{nome}' nao define: {sorted(faltando)}")

    return Perfil(**resolvidos)


def carregar_modelos() -> dict[str, Any]:
    """Carrega ``configs/modelos.yaml``."""
    caminho = raiz_projeto() / "configs" / "modelos.yaml"
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def carregar_pipeline() -> dict[str, Any]:
    """Carrega ``configs/pipeline.yaml``."""
    caminho = raiz_projeto() / "configs" / "pipeline.yaml"
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))
