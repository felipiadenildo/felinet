"""Subcomandos: felinet datasets ...

Utilitários para baixar/preparar datasets externos. O download grava no
destino indicado (recomendado: SSD externo). Em seguida, basta criar um
symlink em ``data/raw/camera_trap/<fonte>`` apontando para o destino
real para que o pipeline operacional encontre as imagens.
"""

from __future__ import annotations

from pathlib import Path

import typer

from felinet.logging_setup import obter_logger

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.datasets")


@app.command("baixar-felidae")
def baixar_felidae(
    destino: Path = typer.Option(
        ...,
        "--destino",
        help="Raiz onde gravar as imagens (recomendado: /media/<user>/ssd/dados_tcc/Felidae).",
    ),
    cache_meta: Path = typer.Option(
        None,
        "--cache-meta",
        help="Diretório para o ZIP/JSON de metadados. Default: <destino>/_metadata/.",
    ),
        preset: str = typer.Option(
        "completo",
        "--preset",
        help="Preset de cotas: 'completo' (~8.3k imgs/~18.6 GB) ou "
        "'smoke' (~200 imgs/~460 MB) para validação rápida.",
    ),
    cotas: str = typer.Option(
        None,
        "--cotas",
        help="Overrides 'nome=N,nome=N' (ex.: 'bobcat=2000,puma=2000'). "
        "Mantém defaults do preset para classes não citadas.",
    ),
    cota_demais: int = typer.Option(
        None,
        "--cota-demais",
        help="Cota para classes não listadas (override; default vem do preset).",
    ),
    seed: int = typer.Option(0, "--seed"),
    threads: int = typer.Option(8, "--threads", min=1, max=32),
    timeout: float = typer.Option(30.0, "--timeout"),
    tentativas: int = typer.Option(3, "--tentativas", min=1),
    apenas_planejar: bool = typer.Option(
        False,
        "--apenas-planejar",
        help="Lista a amostra e tamanho estimado, sem baixar.",
    ),
    force_meta: bool = typer.Option(
        False, "--force-meta", help="Re-baixa metadados mesmo se já existem."
    ),
) -> None:
    """Baixa subset estratificado do dataset Felidae Conservation Fund (LILA BC).

    Fluxo:
      1. Baixa o ZIP de metadados COCO (~38 MB) -> extrai JSON (~169 MB).
      2. Amostra estratificada por classe (cotas configuráveis).
      3. Persiste ``selecao_amostral.csv`` com os IDs escolhidos.
      4. Baixa as imagens em paralelo para ``<destino>/<categoria>/<arquivo>.jpg``.
    """
    from felinet.datasets.felidae import (
        PRESETS,
        amostrar_estratificado,
        baixar_em_paralelo,
        baixar_metadados,
        carregar_anotacoes,
        gravar_manifesto_selecao,
    )

    if preset not in PRESETS:
        raise typer.BadParameter(
            f"Preset '{preset}' invalido. Opcoes: {sorted(PRESETS.keys())}."
        )
    cotas_base, cota_demais_base = PRESETS[preset]
    LOG.info(f"Preset de cotas: '{preset}' (cota_demais={cota_demais_base}).")

    cache = cache_meta or (destino / "_metadata")
    cache.mkdir(parents=True, exist_ok=True)

    LOG.info("=== Etapa 1/4: metadados ===")
    json_path = baixar_metadados(cache / "felidae_meta.zip", force=force_meta)
    LOG.info(f"JSON: {json_path}")

    LOG.info("=== Etapa 2/4: amostragem estratificada ===")
    images, anns, cat_map = carregar_anotacoes(json_path)
    LOG.info(f"Dataset: {len(images)} imagens, {len(cat_map)} categorias.")

    # Constrói cotas (baseline do preset + overrides do usuário)
    cotas_efetivas = dict(cotas_base)
    if cotas:
        for par in cotas.split(","):
            par = par.strip()
            if not par or "=" not in par:
                continue
            nome, valor = par.split("=", 1)
            cotas_efetivas[nome.strip()] = int(valor.strip())

    cota_demais_efetiva = cota_demais if cota_demais is not None else cota_demais_base

    selecao = amostrar_estratificado(
        images,
        anns,
        cat_map,
        cotas=cotas_efetivas,
        cota_demais=cota_demais_efetiva,
        seed=seed,
    )
    LOG.info(f"Selecionadas: {len(selecao)} imagens.")

    from collections import Counter

    cont = Counter(item.categoria_nome for item in selecao)
    LOG.info("Top classes na seleção:")
    for nome, n in cont.most_common(10):
        LOG.info(f"  {nome:30s} {n:>5d}")

    estimado_gb = len(selecao) * 2.3 / 1024
    LOG.info(f"Estimativa de tamanho total: ~{estimado_gb:.1f} GB (~2.3 MB/img).")

    destino.mkdir(parents=True, exist_ok=True)
    manifesto_path = destino / "selecao_amostral.csv"
    gravar_manifesto_selecao(selecao, manifesto_path)
    LOG.info(f"Manifesto da seleção: {manifesto_path}")

    if apenas_planejar:
        typer.echo(
            f"PLANO: {len(selecao)} imagens, ~{estimado_gb:.1f} GB. "
            f"Manifesto em {manifesto_path}. Use sem '--apenas-planejar' para baixar."
        )
        return

    LOG.info("=== Etapa 3/4: download paralelo ===")

    def _progresso(i: int, total: int, contadores: dict) -> None:
        LOG.info(f"  progresso: {i}/{total}  contadores={contadores}")

    contadores = baixar_em_paralelo(
        selecao,
        destino,
        n_threads=threads,
        timeout=timeout,
        tentativas=tentativas,
        callback_progresso=_progresso,
    )

    LOG.info("=== Etapa 4/4: relatório final ===")
    LOG.info(f"Contadores: {contadores}")
    if contadores.get("falha", 0) > 0:
        LOG.warning(
            f"{contadores['falha']} falhas registradas em {destino}/_erros.log "
            "(re-rode o comando para tentar de novo as faltantes)."
        )
    typer.echo(
        f"OK: {contadores.get('ok', 0)} baixadas, "
        f"{contadores.get('ja-existe', 0)} já existiam, "
        f"{contadores.get('falha', 0)} falhas. "
        f"Imagens em {destino}/<categoria>/. "
        f"Manifesto em {manifesto_path}."
    )
