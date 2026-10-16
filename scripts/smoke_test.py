#!/usr/bin/env python3
"""Smoke test do felinet: a cascata e a re-ID de ponta a ponta, com volumes pequenos.

Executa em sequência:
  1. ruff + pytest
  2. dev validar-ambiente
  3. dev preparar-petface-mini (sintético)
  4. pipeline executar (kaggle_cats + felidae) com --dev e N=30 (tag smoke_n30)
  5. reid extrair-embeddings + avaliar-closed + avaliar-openset (petface_mini, N=50)
  6. dev gerar-resumo-html por fonte
  7. monografia verificar (opcional: só se a monografia estiver em ../monografia-felinet)

As figuras e tabelas da monografia não saem do smoke: vêm dos runs da execução final, por
`felinet monografia gerar` (testado em tests/test_monografia.py com runs sintéticos).
Gera RELATORIO_SMOKE.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Parametros (deliberadamente pequenos)
# ---------------------------------------------------------------------------
N_PIPELINE = 30
TAG_SMOKE = "smoke_n30"  # isola runs do smoke do resolver_latest
N_REID = 50
PERFIL = "dev"
FONTES_OPERACIONAIS = ["kaggle_cats", "felidae"]
FONTE_REID = "petface_mini"
N_INDIVIDUOS_MINI = 20
N_IMGS_POR_INDIVIDUO = 4


# Helpers de path derivados ---------------------------------------------------
def _proto_closed(n: int) -> str:
    return f"n{n:04d}"


def _proto_openset(n: int) -> str:
    return f"openset_n{n:04d}"


def _pasta_run_metodologico(protocolo: str) -> str:
    return f"runs/metodologico/{FONTE_REID}/{PERFIL}/{protocolo}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def passo(nome: str, args: list[str], timeout: int = 1800, obrigatorio: bool = True) -> dict:
    inicio = time.monotonic()
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"TIMEOUT apos {timeout}s"
    return {
        "nome": nome,
        "comando": " ".join(args),
        "exit_code": rc,
        "ok": rc == 0,
        "obrigatorio": obrigatorio,
        "duracao_s": round(time.monotonic() - inicio, 1),
        "stdout_tail": out[-600:],
        "stderr_tail": err[-600:],
    }


def conferir(rel: str | Path, descricao: str = "", obrigatorio: bool = True) -> dict:
    p = Path(rel)
    return {
        "caminho": str(p),
        "descricao": descricao,
        "existe": p.exists(),
        "obrigatorio": obrigatorio,
        "tamanho_bytes": p.stat().st_size if p.exists() else 0,
    }


def conferir_glob(padrao: str, descricao: str = "", obrigatorio: bool = True) -> dict:
    achados = sorted(Path(".").glob(padrao))
    return {
        "caminho": padrao,
        "descricao": descricao,
        "existe": bool(achados),
        "obrigatorio": obrigatorio,
        "tamanho_bytes": achados[0].stat().st_size if achados else 0,
        "n_arquivos": len(achados),
        "primeiro": str(achados[0]) if achados else "",
    }


def metricas_de_run(protocolo: str, campos: list[str]) -> dict:
    """Le metricas.json dentro de runs/metodologico/<fonte>/<perfil>/<proto>/<sha>/."""
    padrao = f"{_pasta_run_metodologico(protocolo)}/*/metricas.json"
    achados = sorted(Path(".").glob(padrao))
    if not achados:
        return {"_origem": "(ausente)", "_padrao": padrao}
    arq = achados[-1]
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_origem": str(arq), "_erro": str(exc)[:200]}
    saida = {"_origem": str(arq)}
    for campo in campos:
        valor: object = dados
        try:
            for parte in campo.split("."):
                valor = valor[parte] if isinstance(valor, dict) else None
        except Exception:  # noqa: BLE001
            valor = None
        saida[campo] = valor
    return saida


# ---------------------------------------------------------------------------
# Plano de execucao
# ---------------------------------------------------------------------------


def montar_plano() -> list[dict]:
    py = sys.executable
    p: list[dict] = []

    # 1-2. Qualidade
    p.append(passo("ruff check", [py, "-m", "ruff", "check", "src/", "tests/"]))
    p.append(passo("pytest", [py, "-m", "pytest", "-q", "--tb=no"]))

    # 3. Ambiente
    p.append(
        passo("dev validar-ambiente", ["felinet", "dev", "validar-ambiente"], obrigatorio=False)
    )

    # 4. Bootstrap petface_mini sintetico (idempotente)
    p.append(
        passo(
            f"dev preparar-petface-mini [sintetico {N_INDIVIDUOS_MINI}x{N_IMGS_POR_INDIVIDUO}]",
            [
                "felinet",
                "dev",
                "preparar-petface-mini",
                "--individuos",
                str(N_INDIVIDUOS_MINI),
                "--imagens-por-id",
                str(N_IMGS_POR_INDIVIDUO),
            ],
            timeout=180,
            obrigatorio=True,
        )
    )

    # 5. Pipeline operacional (2 fontes, modo dev)
    for fonte in FONTES_OPERACIONAIS:
        p.append(
            passo(
                f"pipeline executar [{fonte}]",
                [
                    "felinet",
                    "pipeline",
                    "executar",
                    "--perfil",
                    PERFIL,
                    "--fonte",
                    fonte,
                    "--max-amostras",
                    str(N_PIPELINE),
                    "--tag",
                    TAG_SMOKE,
                    "--seed-amostragem",
                    "42",
                    "--dev",
                ],
                timeout=1800,
            )
        )

    # 6. Re-ID -- extrair embeddings
    p.append(
        passo(
            f"reid extrair-embeddings [{FONTE_REID} n={N_REID}]",
            [
                "felinet",
                "reid",
                "extrair-embeddings",
                "--perfil",
                PERFIL,
                "--fonte",
                FONTE_REID,
                "--n",
                str(N_REID),
            ],
            timeout=900,
            obrigatorio=True,
        )
    )

    # 7. Avaliacoes Re-ID
    p.append(
        passo(
            "reid avaliar-closed",
            [
                "felinet",
                "reid",
                "avaliar-closed",
                "--perfil",
                PERFIL,
                "--fonte",
                FONTE_REID,
                "--n",
                str(N_REID),
            ],
            obrigatorio=True,
        )
    )
    p.append(
        passo(
            "reid avaliar-openset",
            [
                "felinet",
                "reid",
                "avaliar-openset",
                "--perfil",
                PERFIL,
                "--fonte",
                FONTE_REID,
                "--n",
                str(N_REID),
            ],
            obrigatorio=True,
        )
    )

    # 6. HTML consolidado por fonte
    for fonte in FONTES_OPERACIONAIS:
        p.append(
            passo(
                f"dev gerar-resumo-html [{fonte}]",
                ["felinet", "dev", "gerar-resumo-html", "--fonte", fonte, "--perfil", PERFIL],
                obrigatorio=True,
            )
        )

    # 7. Coerência da monografia com o registro (sem os runs: só .tex x registro x manifesto)
    if Path("../monografia-felinet/main.tex").is_file():
        p.append(
            passo("monografia verificar", ["felinet", "monografia", "verificar"], obrigatorio=False)
        )

    return p


# ---------------------------------------------------------------------------
# Artefatos (paths derivados das observa\u00e7\u00f5es da v4)
# ---------------------------------------------------------------------------


def montar_artefatos() -> list[dict]:
    a: list[dict] = []
    proto_closed = _proto_closed(N_REID)
    proto_openset = _proto_openset(N_REID)

    # Metricas Re-ID em runs/metodologico (n\u00e3o em data/processed)
    a.append(
        conferir_glob(
            f"{_pasta_run_metodologico(proto_closed)}/*/metricas.json",
            "metricas.json Re-ID closed-set",
        )
    )
    a.append(
        conferir_glob(
            f"{_pasta_run_metodologico(proto_openset)}/*/metricas.json",
            "metricas.json Re-ID open-set",
        )
    )

    # Runs operacionais (galeria dev + resumo.html)
    for fonte in FONTES_OPERACIONAIS:
        a.append(
            conferir_glob(
                f"runs/operacional/{fonte}/dev/_/**/dev_visualizacao/",
                f"Galeria visual dev -- {fonte}",
            )
        )
        a.append(
            conferir_glob(
                f"runs/operacional/{fonte}/dev/_/**/dev_visualizacao/resumo.html",
                f"resumo.html -- {fonte}",
            )
        )

    # Ambiente
    a.append(
        conferir("runs/_ambiente/latest.md", "Especs do ambiente (monografia)", obrigatorio=False)
    )
    return a


# ---------------------------------------------------------------------------
# Metricas
# ---------------------------------------------------------------------------


def extrair_metricas() -> dict:
    return {
        "reid_closed_set": metricas_de_run(
            _proto_closed(N_REID),
            [
                "relatorio.top_k.1",
                "relatorio.top_k.5",
                "relatorio.top_k.10",
                "relatorio.mAP",
                "n_query",
                "n_galeria",
            ],
        ),
        "reid_open_set": metricas_de_run(
            _proto_openset(N_REID),
            ["auc_media", "auc_desvio", "n_seeds"],
        ),
    }


# ---------------------------------------------------------------------------
# Renderizacao
# ---------------------------------------------------------------------------


def renderizar(
    passos: list[dict], artefatos: list[dict], metricas: dict, duracao_total: float
) -> str:
    ts = datetime.now(UTC).isoformat()
    total = len(passos)
    okk = sum(1 for x in passos if x["ok"])
    falhas_obrig = [x for x in passos if not x["ok"] and x["obrigatorio"]]
    arq_obrig = [a for a in artefatos if a["obrigatorio"]]
    arq_ok_obrig = sum(1 for a in arq_obrig if a["existe"])
    arq_ok_total = sum(1 for a in artefatos if a["existe"])

    linhas = [
        "# Relatorio de Smoke Test (Felinet)",
        "",
        f"Executado em {ts}.  Duracao total: {duracao_total:.1f}s.",
        "",
        f"**Passos:** {okk}/{total} OK  |  "
        f"**Falhas obrigatorias:** {len(falhas_obrig)}  |  "
        f"**Artefatos:** {arq_ok_total}/{len(artefatos)} "
        f"(obrigatorios: {arq_ok_obrig}/{len(arq_obrig)})",
        "",
        f"Config: perfil=`{PERFIL}`, N_pipeline={N_PIPELINE}, "
        f"N_reid={N_REID}, fonte_reid={FONTE_REID}, "
        f"fontes_op={FONTES_OPERACIONAIS}.",
        "",
        "## Passos executados",
        "",
        "| # | Passo | Status | Obrig | Duracao | Comando |",
        "|---|-------|--------|-------|---------|---------|",
    ]
    for i, x in enumerate(passos, 1):
        status = "OK" if x["ok"] else f"FALHA ({x['exit_code']})"
        obrig = "sim" if x["obrigatorio"] else "opt"
        linhas.append(
            f"| {i} | {x['nome']} | {status} | {obrig} | {x['duracao_s']}s | `{x['comando']}` |"
        )

    linhas += [
        "",
        "## Saidas esperadas nos runs",
        "",
        "| Descricao | Caminho | Obrig | Presente | Tamanho |",
        "|-----------|---------|-------|----------|---------|",
    ]
    for a in artefatos:
        marca = "sim" if a["existe"] else "NAO"
        obrig = "sim" if a["obrigatorio"] else "opt"
        tam = f"{a['tamanho_bytes']} B" if a["existe"] else "-"
        extra = f" ({a['n_arquivos']} arq)" if "n_arquivos" in a and a["n_arquivos"] > 1 else ""
        linhas.append(f"| {a['descricao']} | `{a['caminho']}`{extra} | {obrig} | {marca} | {tam} |")

    linhas += ["", "## Metricas-chave (metricas.json latest)", ""]
    for nome, blob in metricas.items():
        linhas.append(f"### {nome}")
        linhas.append("")
        if "_erro" in blob:
            linhas.append(f"Erro: `{blob['_erro']}`")
        elif blob.get("_origem", "(ausente)") == "(ausente)":
            padrao = blob.get("_padrao", "")
            linhas.append(f"(sem dados -- padrao buscado: `{padrao}`)")
        else:
            linhas.append(f"Origem: `{blob['_origem']}`")
            for k, v in blob.items():
                if k.startswith("_"):
                    continue
                linhas.append(f"- `{k}`: {v}")
        linhas.append("")

    falhas = [x for x in passos if not x["ok"]]
    if falhas:
        linhas += ["## Detalhes das falhas", ""]
        for x in falhas:
            tag = "OBRIGATORIO" if x["obrigatorio"] else "opcional"
            linhas += [
                f"### {x['nome']} -- {tag}",
                "",
                "```",
                (x["stderr_tail"] or x["stdout_tail"] or "(sem saida)"),
                "```",
                "",
            ]

    linhas += ["", "## Conclusao", ""]
    arq_obrig_faltando = [a for a in arq_obrig if not a["existe"]]
    if not falhas_obrig and not arq_obrig_faltando:
        linhas.append("Projeto saudavel: todos os passos e artefatos obrigatorios OK.")
        linhas.append("Pronto para o experimento definitivo (N maior).")
    elif not falhas_obrig:
        linhas.append(
            f"Passos obrigatorios OK, mas {len(arq_obrig_faltando)} artefato(s) "
            "obrigatorio(s) ausente(s). Revisar."
        )
    else:
        linhas.append(
            f"ATENCAO: {len(falhas_obrig)} passo(s) obrigatorio(s) falharam. "
            "Corrigir antes do experimento definitivo."
        )
    linhas.append("")
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    raiz = Path.cwd()
    inicio = time.monotonic()

    plano = montar_plano()
    duracao = time.monotonic() - inicio
    artefatos = montar_artefatos()
    metricas = extrair_metricas()

    md = renderizar(plano, artefatos, metricas, duracao)
    saida = raiz / "RELATORIO_SMOKE.md"
    saida.write_text(md, encoding="utf-8")

    print(f"\n[smoke] relatorio: {saida}")
    falhas_obrig = sum(1 for x in plano if not x["ok"] and x["obrigatorio"])
    arq_obrig_faltando = sum(1 for a in artefatos if not a["existe"] and a["obrigatorio"])
    if falhas_obrig:
        print(f"[smoke] {falhas_obrig} passo(s) obrigatorio(s) FALHOU")
        return 1
    if arq_obrig_faltando:
        print(
            f"[smoke] {arq_obrig_faltando} artefato(s) obrigatorio(s) ausente(s) -- ver relatorio"
        )
        return 2
    print("[smoke] tudo OK -- pronto para o experimento definitivo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
