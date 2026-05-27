"""Logging estruturado em JSONL para rastreabilidade.

Escreve mensagens em formato JSON-Lines (uma linha por evento), facilitando
ingestao posterior por scripts de analise e DVC/MLflow. Tambem espelha
para stderr em formato humano quando rodando em terminal.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

VAR_LOG_LEVEL = "FELINET_LOG_LEVEL"


class FormatadorJSONL(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "nivel": record.levelname,
            "modulo": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for chave, valor in record.__dict__.items():
            if chave.startswith("ctx_"):
                payload[chave[4:]] = valor
        return json.dumps(payload, ensure_ascii=False)


def configurar_logging(
    nivel: str | None = None,
    arquivo_jsonl: Path | None = None,
) -> logging.Logger:
    """Configura logger raiz. Idempotente.

    Args:
        nivel: ``DEBUG``/``INFO``/``WARNING``/``ERROR``. Default ``INFO``
            ou ``FELINET_LOG_LEVEL``.
        arquivo_jsonl: Se fornecido, espelha em JSONL adicionalmente
            ao stderr humano.
    """
    nivel_efetivo = nivel or os.environ.get(VAR_LOG_LEVEL, "INFO")
    raiz = logging.getLogger("felinet")
    raiz.setLevel(nivel_efetivo.upper())
    raiz.handlers.clear()

    h_humano = logging.StreamHandler(sys.stderr)
    h_humano.setFormatter(logging.Formatter(fmt="[%(levelname)s] %(name)s :: %(message)s"))
    raiz.addHandler(h_humano)

    if arquivo_jsonl is not None:
        arquivo_jsonl.parent.mkdir(parents=True, exist_ok=True)
        h_jsonl = logging.FileHandler(arquivo_jsonl, mode="a", encoding="utf-8")
        h_jsonl.setFormatter(FormatadorJSONL())
        raiz.addHandler(h_jsonl)

    raiz.propagate = False
    return raiz


def obter_logger(nome: str) -> logging.Logger:
    return logging.getLogger(f"felinet.{nome}")
