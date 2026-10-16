"""Subcomandos: felinet monografia ...

Tudo o que a monografia recebe do felinet sai daqui (registro em
``felinet.monografia.elementos``):

* ``listar``: o mapa rótulo do LaTeX -> arquivo -> função -> requisitos, com o estado
  de cada arquivo na monografia;
* ``gerar``: escreve as figuras e tabelas em ``<monografia>/elementos/gerados/``, com
  ``MANIFESTO.json`` e ``LEIAME.md``; o que depende de dados ausentes fica pendente;
* ``verificar``: confere ``.tex`` x registro x manifesto e, com os runs, se as tabelas
  ainda batem com os dados;
* ``resumo-caixas`` e ``deteccao-anotada``: números citados no texto do Cap. 5.

Caminhos padrão em ``configs/monografia.yaml``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.monografia import dados as d
from felinet.monografia import elementos as el
from felinet.monografia import producao as pr

app = typer.Typer(no_args_is_help=True)

_AJUDA_SUBSTITUIR = "Prefixo gravado nos runs e pasta local, ANTIGO=NOVO (repetível)."


def _pares(valores: list[str] | None) -> list[tuple[str, str]]:
    pares = []
    for v in valores or []:
        if "=" not in v:
            raise typer.BadParameter(f"--substituir espera ANTIGO=NOVO, recebeu {v!r}")
        antigo, novo = v.split("=", 1)
        pares.append((antigo, novo))
    return pares


def _config(config, monografia, runs, fotos, substituir) -> pr.Config:
    return pr.carregar_config(config, monografia, runs, fotos, _pares(substituir))


_OPC_CONFIG = typer.Option(
    None, "--config", help="Outro arquivo no formato de configs/monografia.yaml."
)
_OPC_MONO = typer.Option(None, "--monografia", help="Repositório da monografia.")
_OPC_RUNS = typer.Option(None, "--runs", help="Raiz dos runs da execução final.")
_OPC_FOTOS = typer.Option(None, "--fotos", help="Pasta das 36 fotos do iNaturalist.")
_OPC_SUBST = typer.Option(None, "--substituir", help=_AJUDA_SUBSTITUIR)


@app.command("listar")
def listar(
    config: Path = _OPC_CONFIG,
    monografia: Path = _OPC_MONO,
    runs: Path = _OPC_RUNS,
    fotos: Path = _OPC_FOTOS,
    substituir: list[str] = _OPC_SUBST,
) -> None:
    """Mapa dos elementos e o que falta, nesta máquina, para gerar cada um."""
    cfg = _config(config, monografia, runs, fotos, substituir)
    pasta = cfg.monografia / pr.PASTA_GERADOS
    for x in el.ELEMENTOS:
        falta = el.faltando(x, cfg.entradas)
        estado = "pode gerar" if not falta else "pendente: " + "; ".join(falta)
        existe = "existe" if (pasta / x.arquivo).is_file() else "ausente"
        typer.echo(f"{x.rotulo:32} {x.arquivo:44} [{existe}] {estado}\n{'':33}{x.codigo}")


@app.command("gerar")
def gerar(
    config: Path = _OPC_CONFIG,
    monografia: Path = _OPC_MONO,
    runs: Path = _OPC_RUNS,
    fotos: Path = _OPC_FOTOS,
    substituir: list[str] = _OPC_SUBST,
    so: list[str] = typer.Option(None, "--so", help="Só este arquivo ou rótulo (repetível)."),
) -> None:
    """Gera na monografia tudo o que os dados desta máquina permitem."""
    cfg = _config(config, monografia, runs, fotos, substituir)
    try:
        res = pr.gerar(cfg, so)
    except KeyError as exc:
        raise typer.BadParameter(
            f"elemento desconhecido: {exc} (veja `felinet monografia listar`)"
        ) from None
    for arq in res.gerados:
        typer.echo(f"OK        {arq}")
    for arq, falta in res.pendentes.items():
        typer.echo(f"PENDENTE  {arq}: requer {'; '.join(falta)}")
    for arq, erro in res.erros.items():
        typer.echo(f"ERRO      {arq}: {erro}", err=True)
    typer.echo(f"Saída: {cfg.monografia / pr.PASTA_GERADOS} (MANIFESTO.json, LEIAME.md)")
    if res.erros:
        raise typer.Exit(code=1)


@app.command("verificar")
def verificar(
    config: Path = _OPC_CONFIG,
    monografia: Path = _OPC_MONO,
    runs: Path = _OPC_RUNS,
) -> None:
    """Falha se o .tex, o registro, os arquivos gerados e o manifesto não estiverem coerentes."""
    cfg = _config(config, monografia, runs, None, None)
    problemas = pr.verificar(cfg)
    if problemas:
        typer.echo("Problemas:\n  " + "\n  ".join(problemas), err=True)
        raise typer.Exit(code=1)
    extra = " e as tabelas conferem com os runs" if el.REQUISITOS["runs"][1](cfg.entradas) else ""
    typer.echo(
        f"OK: a monografia usa exatamente os elementos do registro, sem edição à mão{extra}."
    )


@app.command("resumo-caixas")
def resumo_caixas(
    runs: Path = typer.Option(..., "--runs", help="Raiz dos runs."),
    fonte: str = typer.Option(..., "--fonte"),
) -> None:
    """Caixas por classe do detector e, nas de animal, por decisão e por top-1 "vazio" do SpeciesNet."""
    from collections import Counter

    from felinet.monografia import exemplos as fx

    imagens = fx.imagens_do_run(d.pasta_run_cascata(runs, fonte))
    caixas = [c for r in imagens.values() for c in r["caixas"]]
    animais = [c for c in caixas if c["categoria"] == "animal"]
    vazias = [c for c in animais if c["top_k"] and c["top_k"][0]["especie"] == "blank"]
    resumo = {
        "por_classe": dict(Counter(c["categoria"] for c in caixas)),
        "animal_por_decisao": dict(Counter(c["status"] for c in animais)),
        "animal_top1_vazio": len(vazias),
        "animal_top1_vazio_por_decisao": dict(Counter(c["status"] for c in vazias)),
    }
    typer.echo(json.dumps(resumo, ensure_ascii=False, indent=2))


@app.command("deteccao-anotada")
def deteccao_anotada(
    runs: Path = typer.Option(..., "--runs", help="Raiz dos runs."),
    anotacoes: Path = typer.Option(..., "--anotacoes", help="Pasta dos .txt YOLO do dataset."),
    fonte: str = typer.Option("kaggle_cats", "--fonte"),
    limiar: float = typer.Option(0.5, "--limiar-iou"),
) -> None:
    """Desfecho da Fase II para cada animal anotado: achado, achado com classe errada ou perdido."""
    from felinet.metricas.deteccao_anotada import cruzar
    from felinet.monografia import exemplos as fx

    imagens = fx.imagens_do_run(d.pasta_run_cascata(runs, fonte))
    typer.echo(json.dumps(cruzar(imagens, anotacoes, limiar), ensure_ascii=False, indent=2))


@app.command("vizinhos-umap")
def vizinhos_umap(runs: Path = typer.Option(..., "--runs", help="Raiz dos runs.")) -> None:
    """Recortes cujo vizinho mais próximo (cosseno, embeddings originais) é do mesmo indivíduo."""
    from collections import defaultdict

    import numpy as np

    pasta = Path(runs) / "complementar" / "visualizacao_exploratoria"
    z = np.load(sorted(pasta.glob("*/embeddings.npz"))[0], allow_pickle=False)
    v = z["vetores"] / np.linalg.norm(z["vetores"], axis=1, keepdims=True)
    sim = v @ v.T
    np.fill_diagonal(sim, -np.inf)
    certo = z["ids"][sim.argmax(1)] == z["ids"]
    por_id = defaultdict(list)
    for ident, ok in zip(z["ids"], certo, strict=True):
        por_id[str(ident)].append(bool(ok))
    resumo = {
        "recortes": int(len(certo)),
        "vizinho_do_mesmo_individuo": int(certo.sum()),
        "identidades": len(por_id),
        "identidades_sem_erro": sum(all(x) for x in por_id.values()),
        "com_erro": {k: f"{sum(x)}/{len(x)}" for k, x in sorted(por_id.items()) if not all(x)},
    }
    typer.echo(json.dumps(resumo, ensure_ascii=False, indent=2))
