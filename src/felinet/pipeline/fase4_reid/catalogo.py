"""Fase IV — Re-ID operacional: catálogo, fusão, atribuição e auditoria (Seção 3.5 da monografia).

* **catálogo**: embeddings cadastrais de cada indivíduo da colônia (vários por indivíduo e por parte);
* **fusão**: média ponderada, entre as partes disponíveis (face, flanco), da similaridade de cada
  indivíduo, de modo que a falta de uma parte (oclusão, pose) não zera o score;
* **atribuição** conservadora: Top-1 acima do limiar e com margem sobre o Top-2 é atribuído; margem
  estreita vai à curadoria com a lista ranqueada; abaixo do limiar vira candidato a novo indivíduo;
* **trilha de auditoria**: cada decisão, automática ou humana, com score, margem, responsável e data.

Os limiares padrão são de partida: a monografia (Cap. 5) mostra que precisam ser calibrados por
tamanho de catálogo, com dados da própria colônia.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


@dataclass
class Catalogo:
    """Embeddings L2-normalizados por parte (``"face"``, ``"flanco"``), com o indivíduo de cada linha."""

    vetores: dict[str, np.ndarray] = field(default_factory=dict)
    ids: dict[str, np.ndarray] = field(default_factory=dict)

    def adicionar(self, parte: str, individuo: str, vetor: np.ndarray) -> None:
        v = np.asarray(vetor, dtype=np.float32)
        v = v / max(float(np.linalg.norm(v)), 1e-12)
        if parte in self.vetores:
            self.vetores[parte] = np.vstack([self.vetores[parte], v])
            self.ids[parte] = np.append(self.ids[parte], individuo)
        else:
            self.vetores[parte], self.ids[parte] = v[None, :], np.array([individuo])

    def similaridades(self, parte: str, consulta: np.ndarray) -> dict[str, float]:
        """Maior similaridade cosseno da consulta com os cadastros de cada indivíduo, na parte."""
        if parte not in self.vetores:
            return {}
        q = np.asarray(consulta, dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-12)
        sims = self.vetores[parte] @ q
        melhor: dict[str, float] = {}
        for ident, s in zip(self.ids[parte], sims, strict=True):
            melhor[str(ident)] = max(melhor.get(str(ident), -1.0), float(s))
        return melhor

    def salvar(self, caminho: Path) -> None:
        dados = {f"vetores__{p}": v for p, v in self.vetores.items()} | {
            f"ids__{p}": i for p, i in self.ids.items()
        }
        np.savez(caminho, **dados)

    @classmethod
    def carregar(cls, caminho: Path) -> Catalogo:
        z = np.load(caminho, allow_pickle=False)
        partes = {k.split("__", 1)[1] for k in z.files}
        return cls({p: z[f"vetores__{p}"] for p in partes}, {p: z[f"ids__{p}"] for p in partes})


def fundir(
    scores_por_parte: dict[str, dict[str, float]], pesos: dict[str, float]
) -> dict[str, float]:
    """Média ponderada por indivíduo, só sobre as partes em que ele foi pontuado."""
    soma: dict[str, float] = {}
    peso_total: dict[str, float] = {}
    for parte, scores in scores_por_parte.items():
        w = pesos.get(parte, 0.0)
        for ident, s in scores.items():
            soma[ident] = soma.get(ident, 0.0) + w * s
            peso_total[ident] = peso_total.get(ident, 0.0) + w
    return {i: soma[i] / peso_total[i] for i in soma if peso_total[i] > 0}


@dataclass(frozen=True)
class ConfigAtribuicao:
    limiar: float = 0.65  # similaridade mínima do Top-1 para não ser candidato a novo indivíduo
    margem: float = 0.05  # diferença mínima Top-1 - Top-2 para atribuição automática
    k: int = 5
    pesos: dict[str, float] = field(default_factory=lambda: {"face": 0.6, "flanco": 0.4})


@dataclass(frozen=True)
class Decisao:
    status: str  # atribuido | curadoria | novo_candidato
    individuo: str | None
    ranking: list[tuple[str, float]]
    margem: float | None


def atribuir(scores: dict[str, float], cfg: ConfigAtribuicao = ConfigAtribuicao()) -> Decisao:
    ranking = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[: cfg.k]
    if not ranking or ranking[0][1] < cfg.limiar:
        return Decisao("novo_candidato", None, ranking, None)
    margem = ranking[0][1] - ranking[1][1] if len(ranking) > 1 else None
    if margem is not None and margem < cfg.margem:
        return Decisao("curadoria", None, ranking, margem)
    return Decisao("atribuido", ranking[0][0], ranking, margem)


def reidentificar(
    catalogo: Catalogo, consultas: dict[str, np.ndarray], cfg: ConfigAtribuicao = ConfigAtribuicao()
) -> Decisao:
    """Consulta com as partes disponíveis (ex.: só ``face`` se o flanco estiver ocluído)."""
    por_parte = {parte: catalogo.similaridades(parte, v) for parte, v in consultas.items()}
    return atribuir(fundir(por_parte, cfg.pesos), cfg)


class TrilhaAuditoria:
    """Registro das decisões de re-ID (SQLite): automáticas e de curadoria humana."""

    def __init__(self, caminho: Path) -> None:
        self.conexao = sqlite3.connect(caminho)
        self.conexao.execute(
            "CREATE TABLE IF NOT EXISTS decisoes ("
            " id INTEGER PRIMARY KEY, observacao TEXT NOT NULL, status TEXT NOT NULL, individuo TEXT,"
            " score REAL, margem REAL, ranking TEXT, responsavel TEXT NOT NULL, quando TEXT NOT NULL)"
        )

    def registrar(self, observacao: str, decisao: Decisao, responsavel: str = "automatico") -> None:
        self.conexao.execute(
            "INSERT INTO decisoes (observacao, status, individuo, score, margem, ranking, responsavel, quando)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                observacao,
                decisao.status,
                decisao.individuo,
                decisao.ranking[0][1] if decisao.ranking else None,
                decisao.margem,
                json.dumps(decisao.ranking),
                responsavel,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        self.conexao.commit()

    def historico(self, observacao: str) -> list[tuple]:
        return self.conexao.execute(
            "SELECT status, individuo, responsavel, quando FROM decisoes WHERE observacao = ? ORDER BY id",
            (observacao,),
        ).fetchall()
