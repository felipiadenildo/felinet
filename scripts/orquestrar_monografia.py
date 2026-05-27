#!/usr/bin/env python3
# ruff: noqa: E501
"""orquestrar_monografia.py — gerador end-to-end dos artefatos da monografia.

Lê toda a configuração de ``scripts/monografia.json`` e executa as etapas
declaradas, com modo incremental por default (pula artefatos existentes).

Uso:
    python scripts/orquestrar_monografia.py                # incremental
    python scripts/orquestrar_monografia.py --force        # regera tudo
    python scripts/orquestrar_monografia.py --so-faltam    # só o que falta (idem default, explícito)
    python scripts/orquestrar_monografia.py --dry-run      # plano sem executar
    python scripts/orquestrar_monografia.py --so-tabelas
    python scripts/orquestrar_monografia.py --so-figuras
    python scripts/orquestrar_monografia.py --config OUTRO.json
    python scripts/orquestrar_monografia.py --etapa reid_closed --etapa tabelas

Saídas (em logs/monografia/<timestamp>/):
    erros.log        — apenas linhas ERROR/WARN
    execucao.log     — log completo (DEBUG)
    inventario.md    — tabela expected vs found
    manifesto.json   — JSON com metadados do run (versão, sha, falhas, etc.)

Zip versionado em entrega/dados_monografia/dados_monografia_<timestamp>.zip
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------
ROOT_DEFAULT = Path(__file__).resolve().parent.parent
CONFIG_DEFAULT = ROOT_DEFAULT / "scripts" / "monografia.json"


# ----------------------------------------------------------------------
# DATACLASSES
# ----------------------------------------------------------------------
@dataclass
class Resultado:
    nome: str
    comando: list[str]
    sucesso: bool
    duracao_s: float
    saida: str = ""
    erro: str = ""
    pulado: bool = False
    motivo_pulo: str = ""
    falha_tolerada: bool = False


@dataclass
class Contexto:
    repo: Path
    config: dict[str, Any]
    args: argparse.Namespace
    timestamp: str
    runner: list[str]
    git_sha: str
    log_dir: Path
    logger: logging.Logger
    resultados: list[Resultado] = field(default_factory=list)


# ----------------------------------------------------------------------
# HELPERS DE CONFIG
# ----------------------------------------------------------------------
def carregar_config(caminho: Path) -> dict[str, Any]:
    if not caminho.is_file():
        raise FileNotFoundError(f"config não encontrada: {caminho}")
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def detectar_runner(repo: Path, runner_cfg: str) -> list[str]:
    """Detecta o comando para invocar a CLI felinet."""
    if runner_cfg and runner_cfg != "auto":
        return runner_cfg.split()
    if shutil.which("uv") and (repo / "pyproject.toml").is_file():
        return ["uv", "run", "felinet"]
    if shutil.which("felinet"):
        return ["felinet"]
    raise RuntimeError("felinet não encontrado (nem uv run nem instalação global)")


def detectar_git_sha(repo: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def configurar_logging(log_dir: Path, timestamp: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("monografia")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt_full = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    fmt_short = logging.Formatter("[%(levelname)s] %(message)s")

    # arquivo execucao (tudo)
    fh = logging.FileHandler(log_dir / f"execucao_{timestamp}.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_full)
    logger.addHandler(fh)

    # arquivo erros (só WARN/ERROR)
    eh = logging.FileHandler(log_dir / f"erros_{timestamp}.log", encoding="utf-8")
    eh.setLevel(logging.WARNING)
    eh.setFormatter(fmt_full)
    logger.addHandler(eh)

    # console (INFO+)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt_short)
    logger.addHandler(ch)

    return logger


# ----------------------------------------------------------------------
# SUBSTITUIÇÃO DE PLACEHOLDERS
# ----------------------------------------------------------------------
_PLACEHOLDER_RE = re.compile(r"\{(\w+)(?::(\w+))?\}")


def substituir(template: str, contexto: dict[str, Any]) -> str:
    """Substitui {chave} ou {chave:formato} (ex: {n:04d}) usando o contexto."""

    def _sub(m: re.Match) -> str:
        chave, fmt = m.group(1), m.group(2)
        if chave not in contexto:
            raise KeyError(f"placeholder não resolvido: {{{chave}}}")
        val = contexto[chave]
        if fmt:
            return format(val, fmt)
        return str(val)

    return _PLACEHOLDER_RE.sub(_sub, template)


def substituir_lista(lst: list[str], contexto: dict[str, Any]) -> list[str]:
    return [substituir(x, contexto) if isinstance(x, str) else str(x) for x in lst]


# ----------------------------------------------------------------------
# EXECUÇÃO DE COMANDOS
# ----------------------------------------------------------------------
def executar_comando(
    ctx: Contexto,
    nome: str,
    argumentos: list[str],
    artefatos_esperados: list[str] | None = None,
    falha_tolerada: bool = False,
    regerar_sempre: bool = False,
) -> Resultado:
    """Executa um subcomando da CLI felinet."""
    comando = list(ctx.runner) + argumentos
    artefatos_esperados = artefatos_esperados or []

    # check incremental
    if not ctx.args.force and not regerar_sempre and artefatos_esperados:
        todos_presentes = all((ctx.repo / a).is_file() for a in artefatos_esperados)
        if todos_presentes:
            ctx.logger.info(f"  ⏭  pulando '{nome}' (artefatos já existem)")
            return Resultado(
                nome=nome,
                comando=comando,
                sucesso=True,
                duracao_s=0.0,
                pulado=True,
                motivo_pulo="incremental: artefatos presentes",
            )

    # dry-run
    if ctx.args.dry_run:
        ctx.logger.info(f"  (dry-run) {' '.join(comando)}")
        return Resultado(
            nome=nome, comando=comando, sucesso=True, duracao_s=0.0, pulado=True, motivo_pulo="dry-run"
        )

    ctx.logger.info(f"  ▶ {nome}")
    ctx.logger.debug(f"    cmd: {' '.join(comando)}")
    t0 = time.time()
    try:
        proc = subprocess.run(
            comando,
            cwd=ctx.repo,
            capture_output=True,
            text=True,
            timeout=ctx.args.timeout,
        )
        dt = time.time() - t0
        if proc.returncode == 0:
            ctx.logger.info(f"  ✓ {nome} ({dt:.1f}s)")
            return Resultado(
                nome=nome,
                comando=comando,
                sucesso=True,
                duracao_s=dt,
                saida=proc.stdout[-500:],
            )
        msg = f"return={proc.returncode}\nSTDERR:\n{proc.stderr[-2000:]}"
        if falha_tolerada:
            ctx.logger.warning(f"  ⚠ {nome} falhou (tolerada): {msg.splitlines()[0]}")
        else:
            ctx.logger.error(f"  ✗ {nome} falhou: {msg}")
        return Resultado(
            nome=nome,
            comando=comando,
            sucesso=False,
            duracao_s=dt,
            erro=msg,
            falha_tolerada=falha_tolerada,
        )
    except subprocess.TimeoutExpired:
        ctx.logger.error(f"  ✗ {nome} TIMEOUT após {ctx.args.timeout}s")
        return Resultado(
            nome=nome,
            comando=comando,
            sucesso=False,
            duracao_s=ctx.args.timeout,
            erro="timeout",
            falha_tolerada=falha_tolerada,
        )
    except Exception as e:  # noqa: BLE001
        ctx.logger.error(f"  ✗ {nome} exceção: {e}")
        return Resultado(
            nome=nome,
            comando=comando,
            sucesso=False,
            duracao_s=time.time() - t0,
            erro=str(e),
            falha_tolerada=falha_tolerada,
        )


def existe_padrao(repo: Path, padrao: str) -> bool:
    """Confere se ao menos um arquivo casa com glob (com **)."""
    matches = glob.glob(str(repo / padrao), recursive=True)
    return any(Path(m).is_file() for m in matches)


# ----------------------------------------------------------------------
# ETAPAS
# ----------------------------------------------------------------------
def etapa_smoke(ctx: Contexto) -> None:
    if not ctx.config["ambiente"].get("rodar_smoke", True):
        ctx.logger.info("smoke pulado (config)")
        return
    smoke = ctx.repo / "scripts" / "smoke_test.py"
    if not smoke.is_file():
        ctx.logger.warning("smoke_test.py não encontrado")
        return
    ctx.logger.info("▶ smoke test")
    if ctx.args.dry_run:
        ctx.logger.info(f"  (dry-run) python {smoke}")
        return
    r = subprocess.run([sys.executable, str(smoke)], cwd=ctx.repo)
    if r.returncode != 0:
        ctx.logger.warning("smoke falhou (continuando — revisar erros.log)")
    else:
        ctx.logger.info("✓ smoke OK")


def etapa_registrar_ambiente(ctx: Contexto) -> None:
    if not ctx.config["ambiente"].get("registrar_ambiente", True):
        return
    script = ctx.repo / "scripts" / "registrar_ambiente.py"
    if not script.is_file() or ctx.args.dry_run:
        return
    subprocess.run([sys.executable, str(script)], cwd=ctx.repo, capture_output=True)


def _eh_para_rodar(nome_etapa: str, ctx: Contexto) -> bool:
    """Respeita --etapa (whitelist), --so-tabelas/--so-figuras (whitelist específica)."""
    if ctx.args.etapa:
        return nome_etapa in ctx.args.etapa
    if ctx.args.so_tabelas:
        return nome_etapa == "tabelas"
    if ctx.args.so_figuras:
        return nome_etapa in {"figuras_globais", "figuras_por_n"}
    return True


def etapa_reid_extrair_embeddings(ctx: Contexto, cfg_etapa: dict) -> None:
    """Passo 1 da Fase IV: extrai embeddings MegaDescriptor.

    Saída: ``runs/metodologico/<fonte>/<perfil>/n<NNNN>/<gitsha>/embeddings.npz``
    É pré-requisito de reid_closed, reid_openset e das figuras matriz-sim/dist-intra/galeria-erros.
    """
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("reid_extrair_embeddings", ctx):
        ctx.logger.info("⏭  reid_extrair_embeddings pulado")
        return
    ctx.logger.info("══ reid_extrair_embeddings ══")
    base = {**ctx.config["padroes"], **cfg_etapa, "git_sha": ctx.git_sha}
    for n in cfg_etapa["ns"]:
        sub_ctx = {**base, "n": n}
        cmd = substituir_lista(cfg_etapa["comando_template"], sub_ctx)
        artefato = substituir(cfg_etapa["artefato_template"], sub_ctx)
        ctx.resultados.append(
            executar_comando(ctx, f"reid_extrair_embeddings n={n}", cmd, [artefato])
        )


def etapa_reid_closed(ctx: Contexto, cfg_etapa: dict) -> None:
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("reid_closed", ctx):
        ctx.logger.info("⏭  reid_closed pulado")
        return
    ctx.logger.info("══ reid_closed ══")
    base = {**ctx.config["padroes"], **cfg_etapa, "git_sha": ctx.git_sha}
    extras_tpl = cfg_etapa.get("artefatos_extras_template", [])
    for n in cfg_etapa["ns"]:
        sub_ctx = {**base, "n": n}
        cmd = substituir_lista(cfg_etapa["comando_template"], sub_ctx)
        artefato = substituir(cfg_etapa["artefato_template"], sub_ctx)
        extras = [substituir(a, sub_ctx) for a in extras_tpl]
        ctx.resultados.append(
            executar_comando(ctx, f"reid_closed n={n}", cmd, [artefato, *extras])
        )


def etapa_reid_openset(ctx: Contexto, cfg_etapa: dict) -> None:
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("reid_openset", ctx):
        ctx.logger.info("⏭  reid_openset pulado")
        return
    ctx.logger.info("══ reid_openset ══")
    base = {**ctx.config["padroes"], **cfg_etapa, "git_sha": ctx.git_sha}
    for n in cfg_etapa["ns"]:
        sub_ctx = {**base, "n": n}
        cmd = substituir_lista(cfg_etapa["comando_template"], sub_ctx)
        artefato = substituir(cfg_etapa["artefato_template"], sub_ctx)
        ctx.resultados.append(
            executar_comando(ctx, f"reid_openset n={n}", cmd, [artefato])
        )


def etapa_pipeline_operacional(ctx: Contexto, cfg_etapa: dict) -> None:
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("pipeline_operacional", ctx):
        ctx.logger.info("⏭  pipeline_operacional pulado")
        return
    ctx.logger.info("══ pipeline_operacional ══")
    base = {**ctx.config["padroes"], **cfg_etapa, "git_sha": ctx.git_sha}
    for fonte in cfg_etapa["fontes"]:
        sub_ctx = {**base, "fonte": fonte}
        cmd = substituir_lista(cfg_etapa["comando_template"], sub_ctx)
        glob_padrao = substituir(cfg_etapa["artefato_glob"], sub_ctx)
        # incremental via glob (não path exato)
        if not ctx.args.force and existe_padrao(ctx.repo, glob_padrao):
            ctx.logger.info(f"  ⏭  pulando pipeline {fonte} (glob bate)")
            ctx.resultados.append(
                Resultado(
                    nome=f"pipeline {fonte}",
                    comando=list(ctx.runner) + cmd,
                    sucesso=True,
                    duracao_s=0.0,
                    pulado=True,
                    motivo_pulo="glob existente",
                )
            )
            continue
        ctx.resultados.append(
            executar_comando(ctx, f"pipeline {fonte}", cmd, artefatos_esperados=[])
        )


def etapa_regenerar_resumo_html(ctx: Contexto, cfg_etapa: dict) -> None:
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("regenerar_resumo_html", ctx):
        return
    ctx.logger.info("══ regenerar resumo.html ══")
    base = {**ctx.config["padroes"], **cfg_etapa}
    regerar = cfg_etapa.get("regerar_sempre", True)
    for fonte in cfg_etapa["fontes"]:
        sub_ctx = {**base, "fonte": fonte}
        cmd = substituir_lista(cfg_etapa["comando_template"], sub_ctx)
        ctx.resultados.append(
            executar_comando(
                ctx,
                f"resumo {fonte}",
                cmd,
                artefatos_esperados=[],
                regerar_sempre=regerar,
                falha_tolerada=True,
            )
        )


def etapa_items_genericos(ctx: Contexto, cfg_etapa: dict, nome_etapa: str) -> None:
    """Tabelas e figuras_globais seguem o mesmo padrão: lista de items."""
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar(nome_etapa, ctx):
        ctx.logger.info(f"⏭  {nome_etapa} pulado")
        return
    ctx.logger.info(f"══ {nome_etapa} ══")
    base = ctx.config["padroes"]
    for item in cfg_etapa["items"]:
        sub_ctx = {**base, **item}
        cmd = substituir_lista(item["comando"], sub_ctx)
        artefatos = [substituir(a, sub_ctx) for a in item["artefatos"]]
        ctx.resultados.append(
            executar_comando(
                ctx,
                item["nome"],
                cmd,
                artefatos,
                falha_tolerada=item.get("falha_tolerada", False),
            )
        )


def etapa_figuras_por_n(ctx: Contexto, cfg_etapa: dict) -> None:
    if not cfg_etapa.get("habilitada", True) or not _eh_para_rodar("figuras_por_n", ctx):
        ctx.logger.info("⏭  figuras_por_n pulado")
        return
    ctx.logger.info("══ figuras_por_n ══")
    base = {**ctx.config["padroes"], "fonte": cfg_etapa["fonte"]}
    for n in cfg_etapa["ns"]:
        for grupo, key in [("closed", "figuras_closed"), ("openset", "figuras_openset")]:
            for item in cfg_etapa.get(key, []):
                sub_ctx = {**base, **item, "n": n}
                cmd = substituir_lista(item["comando"], sub_ctx)
                artefato = substituir(item["artefato_template"], sub_ctx)
                ctx.resultados.append(
                    executar_comando(
                        ctx,
                        f"{item['nome']}[{grupo}] n={n}",
                        cmd,
                        [artefato],
                        falha_tolerada=item.get("falha_tolerada", False),
                    )
                )


# ----------------------------------------------------------------------
# INVENTÁRIO + EMPACOTAMENTO
# ----------------------------------------------------------------------
def coletar_artefatos_esperados(ctx: Contexto) -> list[str]:
    """Reconstrói a lista flat de todos os artefatos esperados a partir do JSON."""
    esperados: list[str] = []
    etapas = ctx.config["etapas"]
    base = ctx.config["padroes"]

    if etapas["tabelas"].get("habilitada", True):
        for item in etapas["tabelas"]["items"]:
            sub_ctx = {**base, **item}
            esperados.extend(substituir(a, sub_ctx) for a in item["artefatos"])

    if etapas["figuras_globais"].get("habilitada", True):
        for item in etapas["figuras_globais"]["items"]:
            if item.get("falha_tolerada"):
                continue
            sub_ctx = {**base, **item}
            esperados.extend(substituir(a, sub_ctx) for a in item["artefatos"])

    if etapas["figuras_por_n"].get("habilitada", True):
        f = etapas["figuras_por_n"]
        ctx_n = {**base, "fonte": f["fonte"]}
        for n in f["ns"]:
            for key in ("figuras_closed", "figuras_openset"):
                for item in f.get(key, []):
                    if item.get("falha_tolerada"):
                        continue
                    sub = {**ctx_n, **item, "n": n}
                    esperados.append(substituir(item["artefato_template"], sub))
    return esperados


def gerar_inventario_md(ctx: Contexto, esperados: list[str]) -> Path:
    out = ctx.log_dir / f"inventario_{ctx.timestamp}.md"
    presentes = sum(1 for a in esperados if (ctx.repo / a).is_file())

    falhas = [r for r in ctx.resultados if not r.sucesso and not r.falha_tolerada]
    falhas_toleradas = [r for r in ctx.resultados if not r.sucesso and r.falha_tolerada]
    pulados = [r for r in ctx.resultados if r.pulado]

    linhas = [
        f"# Inventário monografia — {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- Repo: `{ctx.repo}`",
        f"- Git SHA: `{ctx.git_sha}`",
        f"- Score: **{presentes}/{len(esperados)} artefatos obrigatórios**",
        f"- Falhas: {len(falhas)} (toleradas: {len(falhas_toleradas)}) | Pulados: {len(pulados)} | Total: {len(ctx.resultados)}",
        "",
        "## Artefatos esperados",
        "",
        "| Status | Caminho | Tamanho |",
        "|--------|---------|---------|",
    ]
    for art in esperados:
        p = ctx.repo / art
        if p.is_file():
            tam = p.stat().st_size
            linhas.append(f"| ✓ | `{art}` | {tam} B |")
        else:
            linhas.append(f"| ✗ | `{art}` | — |")

    if falhas:
        linhas += ["", "## Falhas (NÃO toleradas)", ""]
        for r in falhas:
            linhas.append(f"### {r.nome}")
            linhas.append("")
            linhas.append("```")
            linhas.append(" ".join(r.comando))
            linhas.append("")
            linhas.append(r.erro[:1500])
            linhas.append("```")
            linhas.append("")

    if falhas_toleradas:
        linhas += ["", "## Falhas TOLERADAS", ""]
        for r in falhas_toleradas:
            linhas.append(f"- `{r.nome}` — {r.erro.splitlines()[0] if r.erro else 'sem msg'}")

    linhas += ["", "## Resultados (resumo)", ""]
    linhas.append("| Etapa | Status | Tempo (s) |")
    linhas.append("|-------|--------|-----------|")
    for r in ctx.resultados:
        st = "⏭ pulado" if r.pulado else ("✓ OK" if r.sucesso else "✗ FALHA")
        linhas.append(f"| {r.nome} | {st} | {r.duracao_s:.1f} |")

    out.write_text("\n".join(linhas), encoding="utf-8")
    return out


def gerar_manifesto_run(ctx: Contexto, esperados: list[str], inventario: Path, zip_path: Path | None) -> Path:
    """JSON com tudo que aconteceu — útil para automação posterior."""
    out = ctx.log_dir / f"manifesto_{ctx.timestamp}.json"
    presentes = [a for a in esperados if (ctx.repo / a).is_file()]
    ausentes = [a for a in esperados if not (ctx.repo / a).is_file()]
    data = {
        "timestamp": ctx.timestamp,
        "repo": str(ctx.repo),
        "git_sha": ctx.git_sha,
        "runner": ctx.runner,
        "args": vars(ctx.args),
        "esperados_total": len(esperados),
        "esperados_presentes": len(presentes),
        "esperados_ausentes": ausentes,
        "resultados": [
            {
                "nome": r.nome,
                "sucesso": r.sucesso,
                "pulado": r.pulado,
                "motivo_pulo": r.motivo_pulo,
                "falha_tolerada": r.falha_tolerada,
                "duracao_s": r.duracao_s,
                "erro_resumo": (r.erro.splitlines()[0] if r.erro else ""),
            }
            for r in ctx.resultados
        ],
        "inventario_md": str(inventario.relative_to(ctx.repo)) if inventario.is_relative_to(ctx.repo) else str(inventario),
        "zip": str(zip_path) if zip_path else None,
    }
    out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return out


def empacotar_zip(ctx: Contexto, inventario: Path) -> Path | None:
    cfg = ctx.config["empacotamento"]
    if not cfg.get("habilitada", True) or ctx.args.dry_run:
        ctx.logger.info("⏭  empacotamento pulado")
        return None
    ctx.logger.info("══ empacotamento ══")

    out_dir = ctx.repo / cfg["diretorio_saida"]
    out_dir.mkdir(parents=True, exist_ok=True)
    nome = f"{cfg['prefixo']}_{ctx.timestamp}.zip"
    zip_path = out_dir / nome

    arquivos_para_zip: list[tuple[Path, str]] = []  # (abs, arcname)

    def adicionar(abs_path: Path, arcname: str) -> None:
        if abs_path.is_file():
            arquivos_para_zip.append((abs_path, arcname))

    # diretorios "incluir"
    for entrada in cfg.get("incluir", []):
        base = ctx.repo / entrada
        if base.is_dir():
            for p in base.rglob("*"):
                if p.is_file():
                    arcname = str(p.relative_to(ctx.repo))
                    adicionar(p, arcname)
        elif base.is_file():
            adicionar(base, str(base.relative_to(ctx.repo)))

    # globs de runs
    incluir_globs = cfg.get("incluir_de_runs", {})
    for grupo, padroes in incluir_globs.items():
        for padrao in padroes:
            matches = glob.glob(str(ctx.repo / padrao), recursive=True)
            for m in matches:
                p = Path(m)
                if not p.is_file():
                    continue
                rel = str(p.relative_to(ctx.repo))
                # manifesto.csv → reduz a 50 linhas em arquivo .amostra
                if grupo == "manifesto_amostra_50_linhas":
                    amostra = ctx.log_dir / f".tmp_amostra_{ctx.timestamp}_{p.parent.parent.name}.csv"
                    with p.open("r", encoding="utf-8", errors="replace") as fin:
                        head = [next(fin, "") for _ in range(50)]
                    total = sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
                    amostra.parent.mkdir(parents=True, exist_ok=True)
                    amostra.write_text(
                        f"# arquivo original: {rel}\n# total de linhas: {total}\n# === PRIMEIRAS 50 LINHAS ===\n" + "".join(head),
                        encoding="utf-8",
                    )
                    arquivos_para_zip.append((amostra, rel + ".amostra"))
                else:
                    adicionar(p, rel)

    # arquivos raiz opcionais
    for nome_arq in cfg.get("arquivos_raiz_opcionais", []):
        p = ctx.repo / nome_arq
        adicionar(p, nome_arq)

    # inventário e manifesto sempre vão
    adicionar(inventario, f"_logs/{inventario.name}")
    # erros + execucao
    for fn in (f"erros_{ctx.timestamp}.log", f"execucao_{ctx.timestamp}.log"):
        p = ctx.log_dir / fn
        adicionar(p, f"_logs/{fn}")

    # escreve zip
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for abs_path, arcname in arquivos_para_zip:
            zf.write(abs_path, arcname=arcname)

    # limpa amostras temporárias
    for p in ctx.log_dir.glob(f".tmp_amostra_{ctx.timestamp}_*.csv"):
        p.unlink(missing_ok=True)

    tam_mb = zip_path.stat().st_size / (1024 * 1024)
    ctx.logger.info(f"  ✓ zip: {zip_path} ({tam_mb:.1f} MB, {len(arquivos_para_zip)} arquivos)")
    return zip_path


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def parsear_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--config", type=Path, default=CONFIG_DEFAULT, help="Arquivo JSON de configuração.")
    p.add_argument("--repo", type=Path, default=ROOT_DEFAULT, help="Raiz do repo (default: parent do script).")
    p.add_argument("--force", action="store_true", help="Regerar tudo mesmo se artefato existir.")
    p.add_argument("--so-faltam", action="store_true", help="Só roda o que falta (default — só explícito).")
    p.add_argument("--dry-run", action="store_true", help="Mostra plano sem executar.")
    p.add_argument("--so-tabelas", action="store_true", help="Roda só etapa 'tabelas'.")
    p.add_argument("--so-figuras", action="store_true", help="Roda só etapas 'figuras_*'.")
    p.add_argument(
        "--etapa",
        action="append",
        default=[],
        help="Whitelist de etapas (repetível). Etapas válidas: reid_extrair_embeddings, reid_closed, reid_openset, pipeline_operacional, regenerar_resumo_html, tabelas, figuras_globais, figuras_por_n.",
    )
    p.add_argument("--skip-smoke", action="store_true", help="Pula o smoke test inicial.")
    p.add_argument("--timeout", type=int, default=3600, help="Timeout por comando em segundos.")
    return p.parse_args()


def main() -> int:
    args = parsear_args()
    config = carregar_config(args.config)

    repo = args.repo.resolve()
    if not (repo / "pyproject.toml").is_file():
        print(f"ERRO: {repo} não parece ser a raiz do repo (sem pyproject.toml)", file=sys.stderr)
        return 2

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    log_dir = repo / config["saida"]["log_diretorio"]
    logger = configurar_logging(log_dir, timestamp)

    runner = detectar_runner(repo, config["ambiente"].get("runner", "auto"))
    git_sha = detectar_git_sha(repo)

    ctx = Contexto(
        repo=repo,
        config=config,
        args=args,
        timestamp=timestamp,
        runner=runner,
        git_sha=git_sha,
        log_dir=log_dir,
        logger=logger,
    )

    logger.info(f"Repo: {repo}")
    logger.info(f"Runner: {' '.join(runner)}")
    logger.info(f"Git SHA: {git_sha}")
    logger.info(f"Timestamp: {timestamp}")
    if args.dry_run:
        logger.info("MODO DRY-RUN — nenhum comando será executado")
    if args.force:
        logger.info("MODO FORCE — regerando mesmo se existir")

    # pre-flight: smoke + ambiente
    if not args.skip_smoke:
        etapa_smoke(ctx)
    etapa_registrar_ambiente(ctx)

    # etapas principais
    etapas = config["etapas"]
    if "reid_extrair_embeddings" in etapas:
        etapa_reid_extrair_embeddings(ctx, etapas["reid_extrair_embeddings"])
    etapa_reid_closed(ctx, etapas["reid_closed"])
    etapa_reid_openset(ctx, etapas["reid_openset"])
    etapa_pipeline_operacional(ctx, etapas["pipeline_operacional"])
    etapa_regenerar_resumo_html(ctx, etapas["regenerar_resumo_html"])
    etapa_items_genericos(ctx, etapas["tabelas"], "tabelas")
    etapa_items_genericos(ctx, etapas["figuras_globais"], "figuras_globais")
    etapa_figuras_por_n(ctx, etapas["figuras_por_n"])

    # inventário + manifesto + zip
    esperados = coletar_artefatos_esperados(ctx)
    inventario = gerar_inventario_md(ctx, esperados)
    zip_path = empacotar_zip(ctx, inventario)
    gerar_manifesto_run(ctx, esperados, inventario, zip_path)

    # relatório final
    presentes = sum(1 for a in esperados if (ctx.repo / a).is_file())
    falhas = [r for r in ctx.resultados if not r.sucesso and not r.falha_tolerada]

    logger.info("")
    logger.info("═══════════════════════════════════════════")
    logger.info(f"Artefatos: {presentes}/{len(esperados)}")
    logger.info(f"Falhas (não toleradas): {len(falhas)}")
    logger.info(f"Inventário: {inventario}")
    if zip_path:
        logger.info(f"Zip: {zip_path}")
    logger.info(f"Logs: {log_dir}")
    logger.info("═══════════════════════════════════════════")

    # exit codes
    if falhas:
        return 3
    if presentes < len(esperados):
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
