"""Subcomandos: felinet tabelas ...

Gera tabelas CSV + .tex (booktabs) para inclusao na monografia. Le metricas
dos runs metodologicos latest (closed e openset) e agrega em uma unica
linha por N. Saida em ``artifacts/tabelas/<modo>/<fonte>/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from felinet.config import carregar_perfil, fonte_default, raiz_projeto
from felinet.logging_setup import obter_logger
from felinet.runs import resolver_latest
from felinet.utils.tex import csv_para_booktabs

app = typer.Typer(no_args_is_help=True)
LOG = obter_logger("comandos.tabelas")


def _pasta_artifacts(cfg, modo: str, fonte: str) -> Path:
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_tabelas_raiz") or "artifacts/tabelas")
    return raiz / modo / fonte


def _ler_metricas_closed(raiz_runs: Path, fonte: str, perfil_nome: str, n: int) -> dict | None:
    alvo = resolver_latest(
        modo="metodologico",
        fonte=fonte,
        perfil=perfil_nome,
        protocolo=f"n{n:04d}",
        raiz_runs=raiz_runs,
    )
    if alvo is None:
        return None
    arq = alvo / "metricas.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None


def _ler_metricas_openset(raiz_runs: Path, fonte: str, perfil_nome: str, n: int) -> dict | None:
    alvo = resolver_latest(
        modo="metodologico",
        fonte=fonte,
        perfil=perfil_nome,
        protocolo=f"openset_n{n:04d}",
        raiz_runs=raiz_runs,
    )
    if alvo is None:
        return None
    arq = alvo / "metricas.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None


@app.command("reid-resumo")
def reid_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    ns: str = typer.Option("50,200,500", "--ns"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo Re-ID closed-set variando N (lendo runs latest)."""
    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [
        [
            "N",
            "Top-1",
            "Top-5",
            "Top-10",
            "mAP@10",
            "mAP",
            "n_query",
            "n_galeria",
        ]
    ]
    for n in valores_n:
        payload = _ler_metricas_closed(raiz_runs, fonte_efetiva, cfg.nome, n)
        if payload is None:
            LOG.warning(f"N={n}: avaliacao ausente em runs/")
            continue
        rel = payload["relatorio"]
        top_k = rel.get("top_k", {})
        cmc = rel.get("cmc", [])
        map_at_k = rel.get("mAP_at_k", {})
        top1 = float(top_k.get("1", cmc[0] if cmc else 0.0))
        top5 = float(top_k.get("5", cmc[4] if len(cmc) >= 5 else 0.0))
        top10 = float(top_k.get("10", cmc[9] if len(cmc) >= 10 else 0.0))
        map10 = float(map_at_k.get("10", 0.0))
        map_global = float(rel.get("mAP", 0.0))
        linhas.append(
            [
                str(n),
                f"{top1:.3f}",
                f"{top5:.3f}",
                f"{top10:.3f}",
                f"{map10:.3f}",
                f"{map_global:.3f}",
                str(payload["n_query"]),
                str(payload["n_galeria"]),
            ]
        )

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva)
    saida_csv = saida or (pasta / "reid_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")

    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv,
        saida_tex,
        legenda=f"Avaliacao Re-ID closed-set sobre {fonte_efetiva} para diferentes N.",
        rotulo=f"tab:reid-resumo-{fonte_efetiva}",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("openset-resumo")
def openset_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    ns: str = typer.Option("50,200,500", "--ns"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela resumo open-set (AUC + TAR@FAR) variando N."""
    cfg = carregar_perfil(perfil)
    fonte_efetiva = fonte or fonte_default(cfg, "metodologico")
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    valores_n = [int(s) for s in ns.split(",")]

    linhas = [
        [
            "N",
            "AUC-ROC (media +/- std)",
            "TPR@FPR=1%",
            "TPR@FPR=5%",
            "EER",
            "Rank-1 open",
            "n_seeds",
        ]
    ]
    for n in valores_n:
        payload = _ler_metricas_openset(raiz_runs, fonte_efetiva, cfg.nome, n)
        if payload is None:
            LOG.warning(f"N={n}: openset ausente em runs/")
            continue
        tpr01 = float(payload.get("tpr_at_fpr_01_media", 0.0))
        tpr05 = float(payload.get("tpr_at_fpr_05_media", 0.0))
        auc_media = float(payload.get("auc_media", 0.0))
        auc_desvio = float(payload.get("auc_desvio", 0.0))
        # Agregados extras a partir de por_seed (medias entre seeds)
        por_seed = payload.get("por_seed", [])
        if por_seed:
            eers = [float(s["relatorio"].get("eer", 0.0)) for s in por_seed]
            r1s = [float(s["relatorio"].get("rank1_open_set", 0.0)) for s in por_seed]
            eer_media = sum(eers) / len(eers)
            r1_media = sum(r1s) / len(r1s)
        else:
            eer_media = float(payload.get("eer_media", 0.0))
            r1_media = float(payload.get("rank1_open_media", 0.0))
        linhas.append(
            [
                str(n),
                f"{auc_media:.3f} +/- {auc_desvio:.3f}",
                f"{tpr01:.3f}",
                f"{tpr05:.3f}",
                f"{eer_media:.3f}",
                f"{r1_media:.3f}",
                str(len(payload.get("seeds", []))),
            ]
        )

    pasta = _pasta_artifacts(cfg, "metodologico", fonte_efetiva)
    saida_csv = saida or (pasta / "openset_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv,
        saida_tex,
        legenda=f"Avaliacao Re-ID open-set sobre {fonte_efetiva} (AUC-ROC e TPR@FPR, media entre seeds).",
        rotulo=f"tab:openset-resumo-{fonte_efetiva}",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("datasets-avaliados")
def datasets_avaliados(
    perfil: str = typer.Option("dev", "--perfil", "-p"),
) -> None:
    """Regera a tabela 'datasets avaliados vs descartados' (.tex)."""
    cfg = carregar_perfil(perfil)
    raiz = raiz_projeto() / (cfg.extras.get("artifacts_tabelas_raiz") or "artifacts/tabelas")
    fonte = raiz / "datasets_avaliados.csv"
    if not fonte.exists():
        LOG.error(f"CSV-fonte ausente: {fonte}")
        raise typer.Exit(code=1)
    saida_tex = fonte.with_suffix(".tex")
    csv_para_booktabs(
        fonte,
        saida_tex,
        legenda="Datasets avaliados durante o desenvolvimento e veredito de uso.",
        rotulo="tab:datasets-avaliados",
    )
    typer.echo(f"OK: {saida_tex}")


# ============================================================
# Bloco 4: tabelas operacionais (fontes-resumo, run-inventory)
# ============================================================


def _ler_manifesto_csv(caminho: Path) -> list[dict[str, str]]:
    import csv

    with caminho.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _resumir_manifesto(linhas: list[dict[str, str]]) -> dict[str, str]:
    """Resume estatisticas de um manifesto.csv para uma fonte."""
    n_midias = len(linhas)
    shas = {linha.get("sha256", "") for linha in linhas if linha.get("sha256")}
    n_unicas = len(shas)
    timestamps = sorted(linha.get("timestamp", "") for linha in linhas if linha.get("timestamp"))
    janela = f"{timestamps[0][:10]} -> {timestamps[-1][:10]}" if timestamps else "-"
    extensoes: dict[str, int] = {}
    for linha in linhas:
        ext = Path(linha.get("caminho_relativo", "")).suffix.lower() or "-"
        extensoes[ext] = extensoes.get(ext, 0) + 1
    if n_midias > 0:
        ext_str = ", ".join(
            f"{ext}={100 * cnt / n_midias:.0f}%"
            for ext, cnt in sorted(extensoes.items(), key=lambda x: -x[1])
        )
    else:
        ext_str = "-"
    return {
        "n_midias": str(n_midias),
        "n_unicas": str(n_unicas),
        "janela_temporal": janela,
        "extensoes": ext_str,
    }


@app.command("fontes-resumo")
def fontes_resumo(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fontes: str = typer.Option(
        None,
        "--fontes",
        help="Lista separada por virgula (ex.: 'petface,kaggle_cats'). "
        "Default: todas as fontes do perfil com manifesto ingerido.",
    ),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela 'fontes operacionais': mídias, únicas (SHA), janela temporal, extensões.

    Lê ``manifesto.csv`` do run de ingestão latest de cada fonte.
    Saída CSV + .tex em ``artifacts/tabelas/operacional/_global/fontes_resumo.{csv,tex}``.
    """
    cfg = carregar_perfil(perfil)
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")

    if fontes:
        lista_fontes = [s.strip() for s in fontes.split(",") if s.strip()]
    else:
        lista_fontes = sorted((cfg.extras.get("fontes") or {}).keys())

    cabecalho = [
        "Fonte",
        "N midias",
        "N unicas (SHA)",
        "Janela temporal",
        "Extensoes",
    ]
    linhas: list[list[str]] = [cabecalho]
    for fonte in lista_fontes:
        latest = resolver_latest(
            modo="operacional",
            fonte=fonte,
            perfil=cfg.nome,
            raiz_runs=raiz_runs,
        )
        if latest is None or not (latest / "manifesto.csv").exists():
            LOG.warning(f"Fonte '{fonte}': manifesto ausente em runs/ (skip).")
            continue
        resumo = _resumir_manifesto(_ler_manifesto_csv(latest / "manifesto.csv"))
        linhas.append(
            [
                fonte,
                resumo["n_midias"],
                resumo["n_unicas"],
                resumo["janela_temporal"],
                resumo["extensoes"],
            ]
        )

    pasta = _pasta_artifacts(cfg, "operacional", "_global")
    saida_csv = saida or (pasta / "fontes_resumo.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv,
        saida_tex,
        legenda="Resumo das fontes operacionais ingeridas (mídias, únicas por SHA-256, janela temporal e extensões).",
        rotulo="tab:fontes-resumo",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")


@app.command("run-inventory")
def run_inventory(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    modo: str = typer.Option(None, "--modo", help="Filtra por modo (operacional|metodologico)."),
    fonte: str = typer.Option(None, "--fonte", "-f"),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela inventário de runs (gitsha, modo, fonte, fase, sucesso, métricas-chave).

    Varre ``runs/`` aplicando filtros opcionais e produz CSV + .tex.
    Saída default: ``artifacts/tabelas/_inventario/run_inventory.{csv,tex}``.
    """
    from felinet.runs import listar_runs

    cfg = carregar_perfil(perfil)
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")
    registros = listar_runs(raiz_runs, modo=modo, fonte=fonte, perfil=cfg.nome)

    cabecalho = [
        "gitsha",
        "modo",
        "fonte",
        "protocolo",
        "fase",
        "sucesso",
        "duracao s",
        "metricas chave",
    ]
    linhas: list[list[str]] = [cabecalho]
    for reg in registros:
        m = reg.manifest
        extras = m.get("extras") or {}
        comando = extras.get("comando", "-")
        fase = comando.split(" ")[0] if comando != "-" else "-"
        metricas = m.get("metricas_resumo") or {}
        # Seleciona uma ou duas métricas representativas
        if metricas:
            pares = list(metricas.items())[:2]
            metricas_str = "; ".join(f"{k}={v}" for k, v in pares)
        else:
            metricas_str = "-"
        sucesso = m.get("sucesso")
        sucesso_str = "sim" if sucesso is True else ("nao" if sucesso is False else "-")
        linhas.append(
            [
                str(m.get("git_sha", "-")),
                str(m.get("modo", "-")),
                str(m.get("fonte", "-")),
                str(m.get("protocolo") or "_"),
                fase,
                sucesso_str,
                f"{m.get('duracao_s', 0) or 0:.1f}",
                metricas_str,
            ]
        )

    raiz_art = raiz_projeto() / (cfg.extras.get("artifacts_tabelas_raiz") or "artifacts/tabelas")
    pasta = raiz_art / "_inventario"
    saida_csv = saida or (pasta / "run_inventory.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv,
        saida_tex,
        legenda="Inventário de runs reproduzíveis registrados em ``runs/`` (gitsha, modo, fonte, fase e métricas-chave).",
        rotulo="tab:run-inventory",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")

# ============================================================
# Bloco 6 — Tabela comparativa entre fontes
# ============================================================


def _latest_por_fase(
    raiz_runs: Path,
    *,
    fonte: str,
    perfil_nome: str,
    prefixo_comando: str,
) -> dict | None:
    """Retorna o ``manifest`` do run mais recente cuja ``extras.comando``
    comeca com ``prefixo_comando`` (ex.: 'ingestao', 'deteccao',
    'classificacao'), filtrado por modo=operacional + fonte + perfil.

    Em modo operacional os tres runs (ingestao/deteccao/classificacao)
    compartilham a mesma chave latest, portanto ``resolver_latest`` nao
    discrimina por fase. Aqui usa-se ``listar_runs`` (ordenado por
    ``data_inicio`` desc) e filtra-se pelo prefixo do comando.
    """
    from felinet.runs import listar_runs

    registros = listar_runs(
        raiz_runs,
        modo="operacional",
        fonte=fonte,
        perfil=perfil_nome,
    )
    for reg in registros:
        comando = (reg.manifest.get("extras") or {}).get("comando", "")
        if comando.startswith(prefixo_comando) and reg.manifest.get("sucesso") is True:
            return reg.manifest
    return None


def _formatar_pct(numerador: float, denominador: float) -> str:
    if denominador <= 0:
        return "-"
    return f"{100.0 * numerador / denominador:.1f}"


@app.command("comparativo-fontes")
def comparativo_fontes(
    perfil: str = typer.Option("prod", "--perfil", "-p"),
    fontes: str = typer.Option(
        None,
        "--fontes",
        help="Lista separada por virgula (ex.: 'kaggle_cats,felidae,petface'). "
        "Default: todas as fontes do perfil.",
    ),
    saida: Path = typer.Option(None, "--saida"),
) -> None:
    """Tabela comparativa entre fontes (Kaggle vs Felidae vs PetFace).

    Para cada fonte cruza os tres runs operacionais latest:
    ingestao (n_entradas), deteccao (n_imagens, n_animais_detectados) e
    classificacao (n_classificacoes, n_felis_catus). Saida CSV + .tex em
    ``artifacts/tabelas/operacional/_global/comparativo_fontes.{csv,tex}``.

    Fontes sem run bem-sucedido em alguma fase ficam com '-' nas colunas
    correspondentes; fontes sem nenhum run completo sao puladas com aviso.
    """
    cfg = carregar_perfil(perfil)
    raiz_runs = raiz_projeto() / (cfg.extras.get("raiz_runs") or "runs")

    if fontes:
        lista_fontes = [s.strip() for s in fontes.split(",") if s.strip()]
    else:
        lista_fontes = sorted((cfg.extras.get("fontes") or {}).keys())

    cabecalho = [
        "Fonte",
        "N midias",
        "N deteccoes",
        "N animais",
        "Taxa animal pct",
        "N classificacoes",
        "N felis catus",
        "Taxa felis pct",
    ]
    linhas: list[list[str]] = [cabecalho]

    for fonte in lista_fontes:
        man_ing = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="ingestao"
        )
        man_det = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="deteccao"
        )
        man_cls = _latest_por_fase(
            raiz_runs, fonte=fonte, perfil_nome=cfg.nome, prefixo_comando="classificacao"
        )

        if man_ing is None and man_det is None and man_cls is None:
            LOG.warning(f"Fonte '{fonte}': sem runs operacionais (skip).")
            continue

        n_midias = (man_ing or {}).get("metricas_resumo", {}).get("n_entradas") if man_ing else None
        m_det = (man_det or {}).get("metricas_resumo") or {}
        n_imagens_det = m_det.get("n_imagens")
        n_animais = m_det.get("n_animais_detectados")
        m_cls = (man_cls or {}).get("metricas_resumo") or {}
        n_class = m_cls.get("n_classificacoes")
        n_felis = m_cls.get("n_felis_catus")

        if n_animais is not None and n_imagens_det:
            taxa_animal = _formatar_pct(float(n_animais), float(n_imagens_det))
        else:
            taxa_animal = "-"
        if n_felis is not None and n_class:
            taxa_felis = _formatar_pct(float(n_felis), float(n_class))
        else:
            taxa_felis = "-"

        linhas.append(
            [
                fonte,
                "-" if n_midias is None else str(n_midias),
                "-" if n_imagens_det is None else str(n_imagens_det),
                "-" if n_animais is None else str(n_animais),
                taxa_animal,
                "-" if n_class is None else str(n_class),
                "-" if n_felis is None else str(n_felis),
                taxa_felis,
            ]
        )

    pasta = _pasta_artifacts(cfg, "operacional", "_global")
    saida_csv = saida or (pasta / "comparativo_fontes.csv")
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    saida_csv.write_text("\n".join(",".join(c) for c in linhas), encoding="utf-8")
    saida_tex = saida_csv.with_suffix(".tex")
    csv_para_booktabs(
        saida_csv,
        saida_tex,
        legenda=(
            "Comparativo entre fontes operacionais: total de midias ingeridas, "
            "deteccoes de animais, classificacoes de \\textit{Felis catus} e taxas "
            "derivadas. Metricas extraidas dos runs latest de cada fase."
        ),
        rotulo="tab:comparativo-fontes",
    )
    typer.echo(f"OK: {saida_csv} + {saida_tex}")
