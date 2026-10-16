"""Leitura dos resultados que alimentam as figuras do Cap. 5.

Lê o layout de ``runs/`` (``docs/arquitetura/layout_runs.md``):

* operacional: ``operacional/<fonte>/<perfil>/_/<sha>__<tag>/manifest.json``
* re-ID closed-set: ``metodologico/<fonte>/<perfil>/n<NNNN>/<sha>/{metricas.json,embeddings.npz}``
* re-ID open-set: ``metodologico/<fonte>/<perfil>/openset_n<NNNN>/<sha>/metricas.json``
* experimentos complementares: ``complementar/<experimento>/<origem>/resultados.csv``

Quando há mais de um run para o mesmo experimento (reexecuções com outro
``git_sha``), exige-se que as métricas sejam idênticas; havendo divergência,
o erro lista os runs para que se escolha um explicitamente.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


class DadosAusentesError(FileNotFoundError):
    """Nenhum run encontrado para o experimento pedido."""


class RunsDivergentesError(ValueError):
    """Runs do mesmo experimento com métricas diferentes."""


@dataclass(frozen=True)
class CascataOperacional:
    """Totais da cascata Fases I-III para uma fonte (Tab. 8)."""

    fonte: str
    midias: int
    caixas: int
    imagens_com_animal: int
    caixas_felis: int

    @property
    def taxa_animal(self) -> float:
        return self.imagens_com_animal / self.midias

    @property
    def taxa_felis(self) -> float:
        return self.caixas_felis / self.caixas


@dataclass(frozen=True)
class EmbeddingsReid:
    vetores: np.ndarray
    ids: np.ndarray
    splits: np.ndarray

    def consulta_galeria(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        q = self.splits == "query"
        g = self.splits == "gallery"
        return self.vetores[q], self.ids[q], self.vetores[g], self.ids[g]


def _unico(candidatos: list[Path], chave, descricao: str):
    """Devolve o valor comum a todos os candidatos ou levanta erro explicativo."""
    if not candidatos:
        raise DadosAusentesError(f"nenhum run encontrado para {descricao}")
    valores = {c: chave(c) for c in candidatos}
    distintos = {json.dumps(v, sort_keys=True, default=str) for v in valores.values()}
    if len(distintos) > 1:
        lista = "\n".join(f"  {c}" for c in candidatos)
        raise RunsDivergentesError(f"runs divergentes para {descricao}:\n{lista}")
    return next(iter(valores.values()))


def carregar_cascata_operacional(
    raiz_runs: Path, fonte: str, tag: str = "monografia_n300", perfil: str = "dev"
) -> CascataOperacional:
    pasta = Path(raiz_runs) / "operacional" / fonte / perfil / "_"
    candidatos = sorted(pasta.glob(f"*__{tag}/manifest.json"))

    def resumo(p: Path) -> dict:
        m = json.loads(p.read_text(encoding="utf-8"))["metricas_resumo"]
        return {
            "midias": int(m["n_manifesto"]),
            "caixas": int(m["n_deteccoes_animal"]),
            "imagens_com_animal": int(m["n_imagens_com_animal"]),
            "caixas_felis": int(m["n_classificacoes_felis_catus"]),
        }

    r = _unico(candidatos, resumo, f"cascata operacional {fonte} (tag {tag})")
    return CascataOperacional(fonte=fonte, **r)


@dataclass(frozen=True)
class CaixaClassificada:
    """Uma caixa da Fase II com a decisão da Fase III (``04_classificacoes``)."""

    imagem: str  # nome do arquivo de origem
    classe_origem: str  # pasta da fonte (rótulo de pasta, ex.: "puma")
    indice: int
    status: str  # felis_catus | validacao_humana | outra_especie
    top_k: tuple[tuple[str, float], ...]
    confianca_deteccao: float
    recorte: Path | None  # PNG em 05_crops_felis_catus (só para caixas aceitas)

    @property
    def p_gato(self) -> float:
        """Probabilidade de "domestic cat" no top-5 do SpeciesNet (0 se fora do top-5)."""
        return next((p for esp, p in self.top_k if esp == "domestic cat"), 0.0)


def _caixas_do_run(pasta: Path) -> list[CaixaClassificada]:
    det = json.loads((pasta / "03_deteccoes" / "deteccoes.json").read_text(encoding="utf-8"))
    cls = json.loads(
        (pasta / "04_classificacoes" / "classificacoes.json").read_text(encoding="utf-8")
    )
    por_imagem = {r["media_path"]: r["deteccoes"] for r in det["resultados"]}
    caixas = []
    for c in cls["resultados"]:
        origem = Path(c["media_path"])
        recorte = pasta / "05_crops_felis_catus" / f"{origem.stem}__bbox{c['bbox_indice']:02d}.png"
        caixas.append(
            CaixaClassificada(
                imagem=origem.name,
                classe_origem=origem.parent.name,
                indice=int(c["bbox_indice"]),
                status=c["status"],
                top_k=tuple((t["especie"], float(t["probabilidade"])) for t in c["top_k"]),
                confianca_deteccao=float(
                    por_imagem[c["media_path"]][c["bbox_indice"]]["confianca"]
                ),
                recorte=recorte if recorte.exists() else None,
            )
        )
    return caixas


def pasta_run_cascata(
    raiz_runs: Path, fonte: str, tag: str = "monografia_n300", perfil: str = "dev"
) -> Path:
    """Pasta do run da cascata operacional (runs repetidos precisam ter as mesmas decisões)."""
    pasta = Path(raiz_runs) / "operacional" / fonte / perfil / "_"
    candidatos = sorted(p.parent for p in pasta.glob(f"*__{tag}/manifest.json"))

    def assinatura(run: Path) -> list:
        return [(c.imagem, c.indice, c.status) for c in _caixas_do_run(run)]

    _unico(candidatos, assinatura, f"caixas da cascata {fonte} (tag {tag})")
    # Entre runs idênticos, prefere o que gravou os recortes.
    com_recortes = [r for r in candidatos if (r / "05_crops_felis_catus").is_dir()]
    return (com_recortes or candidatos)[0]


def carregar_caixas(
    raiz_runs: Path, fonte: str, tag: str = "monografia_n300", perfil: str = "dev"
) -> list[CaixaClassificada]:
    """Caixas classificadas da cascata operacional (com recortes, quando gravados)."""
    return _caixas_do_run(pasta_run_cascata(raiz_runs, fonte, tag, perfil))


def _pasta_metodologica(raiz_runs: Path, protocolo: str, fonte: str, perfil: str) -> Path:
    return Path(raiz_runs) / "metodologico" / fonte / perfil / protocolo


def carregar_closed(raiz_runs: Path, n: int, fonte: str = "petface", perfil: str = "prod") -> dict:
    """Métricas closed-set (``relatorio`` do ``metricas.json``) mais n_query e n_galeria."""
    pasta = _pasta_metodologica(raiz_runs, f"n{n:04d}", fonte, perfil)

    def metricas(p: Path) -> dict:
        d = json.loads(p.read_text(encoding="utf-8"))
        r = dict(d["relatorio"])
        r["n_query"], r["n_galeria"] = d["n_query"], d["n_galeria"]
        return r

    return _unico(sorted(pasta.glob("*/metricas.json")), metricas, f"closed-set N={n}")


def carregar_openset(raiz_runs: Path, n: int, fonte: str = "petface", perfil: str = "prod") -> dict:
    """Métricas open-set agregadas e por semente (com as curvas FPR/TPR)."""
    pasta = _pasta_metodologica(raiz_runs, f"openset_n{n:04d}", fonte, perfil)
    return _unico(
        sorted(pasta.glob("*/metricas.json")),
        lambda p: json.loads(p.read_text(encoding="utf-8")),
        f"open-set N={n}",
    )


def carregar_embeddings(
    raiz_runs: Path, n: int, fonte: str = "petface", perfil: str = "prod"
) -> EmbeddingsReid:
    pasta = _pasta_metodologica(raiz_runs, f"n{n:04d}", fonte, perfil)
    candidatos = sorted(pasta.glob("*/embeddings.npz"))

    def conteudo(p: Path) -> str:
        import hashlib

        return hashlib.sha256(p.read_bytes()).hexdigest()

    _unico(candidatos, conteudo, f"embeddings N={n}")
    z = np.load(candidatos[0], allow_pickle=False)
    return EmbeddingsReid(vetores=z["vetores"], ids=z["ids"], splits=z["splits"])


def carregar_complementar(raiz_runs: Path, experimento: str) -> list[dict]:
    """Linhas do CSV de um experimento complementar (Cascatas Multifonte, Sensibilidade)."""
    pasta = Path(raiz_runs) / "complementar" / experimento
    candidatos = sorted(pasta.glob("*/resultados.csv"))

    def linhas(p: Path) -> list[dict]:
        with p.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    return _unico(candidatos, linhas, f"experimento complementar {experimento}")
