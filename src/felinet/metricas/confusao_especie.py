"""Cálculo de matriz de confusão Felis-vs-resto por fonte (Bloco 9).

Cruza a predição do classificador de espécie (SpeciesNet, registrada em
``classificacoes.csv`` ou ``manifest.json`` da fase 3) com o rótulo
verdadeiro derivado de :mod:`felinet.datasets.labels_proxy`.

Saída: ``MatrizConfusao`` com TP/FP/TN/FN e métricas derivadas (precisão,
revocação, F1).
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from felinet.datasets.labels_proxy import (
    RotuloBinario,
    resolver_rotulo_verdadeiro,
)


@dataclass(frozen=True)
class MatrizConfusao:
    """Matriz 2x2 Felis catus vs. outros, com métricas derivadas."""

    fonte: str
    tp: int  # predito felis_catus & verdade felis_catus
    fp: int  # predito felis_catus & verdade outros
    tn: int  # predito outros & verdade outros
    fn: int  # predito outros & verdade felis_catus
    sem_ground_truth: int = 0  # imagens sem rótulo verdadeiro disponível

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def precisao(self) -> float:
        """TP / (TP + FP). 'Dos que disse Felis, quantos eram?'"""
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def revocacao(self) -> float:
        """TP / (TP + FN). 'Dos Felis que existiam, quantos achei?'"""
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precisao, self.revocacao
        return (2 * p * r / (p + r)) if (p + r) else 0.0

    @property
    def acuracia(self) -> float:
        return (self.tp + self.tn) / self.total if self.total else 0.0

    def como_dict(self) -> dict:
        return {
            "fonte": self.fonte,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "sem_ground_truth": self.sem_ground_truth,
            "total": self.total,
            "precisao": round(self.precisao, 4),
            "revocacao": round(self.revocacao, 4),
            "f1": round(self.f1, 4),
            "acuracia": round(self.acuracia, 4),
        }


def calcular_matriz(
    fonte: str,
    predicoes: list[tuple[str, RotuloBinario]],
    classe_origem_por_imagem: dict[str, str] | None = None,
) -> MatrizConfusao:
    """Calcula a matriz a partir de uma lista de predições.

    Args:
        fonte: nome da fonte (usado em ``resolver_rotulo_verdadeiro``).
        predicoes: lista de tuplas ``(id_imagem, classe_predita)`` onde
            ``classe_predita`` é ``'felis_catus'`` ou ``'outros'``.
        classe_origem_por_imagem: opcional, dict ``{id_imagem: classe_origem}``
            usado para datasets ``layout=por_classe``. Se ausente ou imagem
            não listada, recorre ao proxy de fonte.

    Returns:
        :class:`MatrizConfusao` populada.
    """
    classe_origem_por_imagem = classe_origem_por_imagem or {}
    tp = fp = tn = fn = sem_gt = 0
    for id_img, predito in predicoes:
        verdade = resolver_rotulo_verdadeiro(fonte, classe_origem_por_imagem.get(id_img))
        if verdade is None:
            sem_gt += 1
            continue
        if predito == "felis_catus" and verdade == "felis_catus":
            tp += 1
        elif predito == "felis_catus" and verdade == "outros":
            fp += 1
        elif predito == "outros" and verdade == "outros":
            tn += 1
        elif predito == "outros" and verdade == "felis_catus":
            fn += 1
    return MatrizConfusao(fonte=fonte, tp=tp, fp=fp, tn=tn, fn=fn, sem_ground_truth=sem_gt)


# ============================================================
# Leitores de runs reais
# ============================================================


def ler_predicoes_de_run(run_dir: Path) -> list[tuple[str, RotuloBinario]]:
    """Lê predições da fase 3 a partir de uma pasta de run.

    Procura, em ordem:
    1. ``classificacoes.csv`` (formato preferencial — uma linha por crop).
    2. ``manifest.json`` com chave ``classificacoes`` ou ``crops``.

    Retorna lista de ``(id_imagem, 'felis_catus' | 'outros')``. ``id_imagem``
    é o caminho relativo ou hash usado como chave estável entre fases.
    """
    csv_path = _achar_classificacoes_csv(run_dir)
    if csv_path is not None:
        return _ler_csv_classificacoes(csv_path)

    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        return _ler_manifest_classificacoes(manifest_path)

    return []


def _achar_classificacoes_csv(run_dir: Path) -> Path | None:
    candidatos = [
        run_dir / "classificacoes.csv",
        run_dir / "fase3_classificacao" / "classificacoes.csv",
        run_dir / "dev_visualizacao" / "03_classificacao" / "classificacoes.csv",
    ]
    for c in candidatos:
        if c.exists():
            return c
    return None


def _ler_csv_classificacoes(arq: Path) -> list[tuple[str, RotuloBinario]]:
    out: list[tuple[str, RotuloBinario]] = []
    with arq.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_img = row.get("nome_arq") or row.get("caminho_relativo") or row.get("sha256") or ""
            classe = (row.get("classe") or "").strip().lower()
            if not id_img:
                continue
            predito: RotuloBinario = (
                "felis_catus" if classe in {"felis_catus", "cat", "domestic_cat"} else "outros"
            )
            out.append((id_img, predito))
    return out


def _ler_manifest_classificacoes(arq: Path) -> list[tuple[str, RotuloBinario]]:
    out: list[tuple[str, RotuloBinario]] = []
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return out
    lista = dados.get("classificacoes") or dados.get("crops") or dados.get("predicoes") or []
    for entry in lista:
        if not isinstance(entry, dict):
            continue
        id_img = entry.get("caminho_relativo") or entry.get("nome_arq") or entry.get("sha256") or ""
        classe = (entry.get("classe") or entry.get("especie") or "").strip().lower()
        if not id_img:
            continue
        predito: RotuloBinario = (
            "felis_catus" if classe in {"felis_catus", "cat", "domestic_cat"} else "outros"
        )
        out.append((id_img, predito))
    return out


def ler_classe_origem_de_run(run_dir: Path) -> dict[str, str]:
    """Lê o mapa ``{id_imagem: classe_origem}`` a partir do manifest de ingestão.

    Procura ``manifest.json`` da fase 1 ou um ``manifesto.csv`` com coluna
    ``classe_origem``. Retorna ``{}`` se ausente.
    """
    candidatos_csv = [
        run_dir / "manifesto.csv",
        run_dir / "fase1_ingestao" / "manifesto.csv",
    ]
    for c in candidatos_csv:
        if c.exists():
            return _ler_csv_classe_origem(c)

    manifest = run_dir / "manifest.json"
    if manifest.exists():
        return _ler_manifest_classe_origem(manifest)
    return {}


def _ler_csv_classe_origem(arq: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with arq.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_img = row.get("caminho_relativo") or row.get("sha256") or ""
            classe = row.get("classe_origem") or ""
            if id_img and classe:
                out[id_img] = classe
    return out


def _ler_manifest_classe_origem(arq: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return out
    entradas = dados.get("entradas") or dados.get("manifesto") or []
    for e in entradas:
        if not isinstance(e, dict):
            continue
        id_img = e.get("caminho_relativo") or e.get("sha256") or ""
        classe = e.get("classe_origem") or (e.get("extras") or {}).get("classe_origem") or ""
        if id_img and classe:
            out[id_img] = classe
    return out
