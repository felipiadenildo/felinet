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


def _status_dataset(ds, raiz_projeto_path: Path) -> str:
    """Retorna o glifo de status de um DatasetLocal."""
    if not ds.caminho.exists():
        return "⚠ caminho ausente"
    link = raiz_projeto_path / ds.link_destino
    if link.is_symlink():
        try:
            destino = link.resolve(strict=False)
        except OSError:
            return "✗ caminho quebrado"
        if destino == ds.caminho.resolve():
            return "✓ linkado"
        if not destino.exists():
            return "✗ caminho quebrado"
        return "✓ linkado (outro destino)"
    if link.exists():
        return "⚠ existe não-symlink"
    return "— não linkado"


@app.command("listar")
def listar() -> None:
    """Mostra status dos datasets configurados em configs/datasets_locais.yaml."""
    from felinet.config import raiz_projeto
    from felinet.datasets.registro import carregar_datasets_locais

    raiz = raiz_projeto()
    arquivo = raiz / "configs" / "datasets_locais.yaml"
    datasets = carregar_datasets_locais(arquivo)
    if not datasets:
        typer.echo(
            "Configure seus datasets em configs/datasets_locais.yaml. "
            "Veja configs/datasets_locais.example.yaml para o formato."
        )
        return

    cabecalho = f"{'nome':16s} {'tipo':36s} {'layout':14s} {'status':22s} fases"
    typer.echo(cabecalho)
    typer.echo("-" * len(cabecalho))
    for nome, ds in datasets.items():
        status = _status_dataset(ds, raiz)
        fases = ",".join(str(f) for f in ds.fases_aplicaveis)
        typer.echo(f"{nome:16s} {ds.tipo:36s} {ds.layout:14s} {status:22s} {fases}")


@app.command("linkar")
def linkar(
    nome: str = typer.Option(
        None, "--nome", help="Linkar apenas o dataset com este nome."
    ),
    apenas_planejar: bool = typer.Option(
        False, "--apenas-planejar", help="Imprime o que faria, sem executar."
    ),
    forcar: bool = typer.Option(
        False, "--forcar", help="Sobrescreve symlink/diretório existente."
    ),
) -> None:
    """Cria symlinks data/raw/<categoria>/<nome>/ → caminho_local."""
    from felinet.config import raiz_projeto
    from felinet.datasets.registro import carregar_datasets_locais

    raiz = raiz_projeto()
    arquivo = raiz / "configs" / "datasets_locais.yaml"
    datasets = carregar_datasets_locais(arquivo)
    if not datasets:
        typer.echo(
            "Configure seus datasets em configs/datasets_locais.yaml. "
            "Veja configs/datasets_locais.example.yaml para o formato."
        )
        raise typer.Exit(code=1)

    if nome is not None and nome not in datasets:
        disponiveis = ", ".join(sorted(datasets))
        typer.echo(f"[erro] dataset '{nome}' não configurado. Disponíveis: {disponiveis}")
        raise typer.Exit(code=2)

    alvos = {nome: datasets[nome]} if nome else datasets

    for nome_ds, ds in alvos.items():
        link = raiz / ds.link_destino
        if not ds.caminho.exists():
            typer.echo(
                f"[skip] {nome_ds}: caminho local não existe: {ds.caminho}"
            )
            continue
        if not ds.caminho.is_dir():
            typer.echo(
                f"[skip] {nome_ds}: caminho local não é diretório: {ds.caminho}"
            )
            continue
        if link.is_symlink() or link.exists():
            try:
                destino_atual = link.resolve(strict=False)
            except OSError:
                destino_atual = None
            if destino_atual == ds.caminho.resolve():
                typer.echo(f"[ok ] {nome_ds}: já linkado → {ds.caminho}")
                continue
            if not forcar:
                typer.echo(
                    f"[skip] {nome_ds}: {link} já existe. Use --forcar para sobrescrever."
                )
                continue
            if apenas_planejar:
                typer.echo(f"[plano] {nome_ds}: substituiria {link} → {ds.caminho}")
                continue
            if link.is_symlink() or link.is_file():
                link.unlink()
            else:
                typer.echo(
                    f"[skip] {nome_ds}: {link} é diretório regular; remova manualmente."
                )
                continue

        if apenas_planejar:
            typer.echo(f"[plano] {nome_ds}: criaria {link} → {ds.caminho}")
            continue

        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(ds.caminho)
        typer.echo(f"[link] {nome_ds}: {link} → {ds.caminho}")


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
