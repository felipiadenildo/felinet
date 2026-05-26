"""Gerenciamento de runs (execucoes rastreaveis do pipeline).

Cada execucao do felinet (operacional ou metodologica) cria um diretorio
identificado pela tupla (modo, fonte, perfil, [protocolo], git_sha[, tag])
em ``runs/``. Esse diretorio recebe todos os artefatos produzidos pela
execucao, junto a um ``manifest.json`` que registra a tupla rastreavel
e o ambiente de execucao.

Layout determinado pelos parametros (estilo Snakemake) + manifesto MLflow-like:

    runs/<modo>/<fonte>/<perfil>/<protocolo|_>/<gitsha>[__<tag>]/

Decisao documentada em ``docs/arquitetura/layout_runs.md``.

Funcao principal:
    criar_run() - cria diretorio, escreve manifest, atualiza latest/.

Funcoes auxiliares:
    atualizar_latest() - move symlink runs/latest/<chave>.
    carregar_manifest() - le manifest.json de um run.
    listar_runs() - itera runs por filtro.
"""

from __future__ import annotations

import json
import os
import platform
import secrets
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from felinet.config import Perfil

MODOS_VALIDOS = ("operacional", "metodologico")
SLUG_PROTOCOLO_VAZIO = "_"  # quando o modo nao usa protocolo (operacional)


@dataclass
class RunDir:
    """Diretorio de um run com helpers de subdiretorio."""

    raiz: Path
    modo: str
    fonte: str
    perfil: str
    protocolo: str  # SLUG_PROTOCOLO_VAZIO quando nao se aplica
    gitsha: str
    tag: str | None = None
    chave_latest: str = ""  # preenchida em criar_run()

    # ---------- subdiretorios padronizados ----------

    @property
    def manifest_path(self) -> Path:
        return self.raiz / "manifest.json"

    @property
    def logs_dir(self) -> Path:
        return self.raiz / "logs"

    # Operacional (cascata)
    @property
    def manifesto_dir(self) -> Path:
        return self.raiz / "02_manifesto"

    @property
    def deteccoes_dir(self) -> Path:
        return self.raiz / "03_deteccoes"

    @property
    def classificacoes_dir(self) -> Path:
        return self.raiz / "04_classificacoes"

    @property
    def crops_dir(self) -> Path:
        return self.raiz / "05_crops_felis_catus"

    @property
    def anotacao_path(self) -> Path:
        return self.raiz / "06_anotacao_identidade.json"

    @property
    def embeddings_path(self) -> Path:
        return self.raiz / "07_embeddings.npz"

    @property
    def avaliacao_path(self) -> Path:
        return self.raiz / "08_avaliacao_pipeline.json"

    # Metodologico (Re-ID isolado)
    @property
    def splits_path(self) -> Path:
        return self.raiz / "splits.json"

    @property
    def matriz_similaridade_path(self) -> Path:
        return self.raiz / "matriz_similaridade.npz"

    @property
    def metricas_path(self) -> Path:
        return self.raiz / "metricas.json"

    @property
    def curvas_path(self) -> Path:
        return self.raiz / "curvas.json"


# ============================================================
# CRIACAO DE RUN
# ============================================================


def criar_run(
    *,
    perfil: Perfil,
    modo: str,
    fonte: str,
    protocolo: str | None = None,
    tag: str | None = None,
    raiz_runs: Path | None = None,
    extras: dict[str, Any] | None = None,
) -> RunDir:
    """Cria diretorio de um novo run, escreve manifest.json e atualiza latest/.

    Args:
        perfil: Perfil carregado (``felinet.config.carregar_perfil``).
        modo: ``"operacional"`` ou ``"metodologico"``.
        fonte: Identificador da fonte de dados (ex.: ``"kaggle_cats"``,
            ``"petface"``, ``"campus2_2025"``). Deve estar registrado em
            ``configs/paths.yaml`` na secao ``fontes``.
        protocolo: Slug do protocolo metodologico (ex.: ``"n50"``,
            ``"openset_n200"``). Obrigatorio quando ``modo=="metodologico"``,
            ignorado em ``"operacional"``.
        tag: Sufixo opcional para distinguir runs com mesmo gitsha
            (ex.: ``"thr020"``, ``"sem_blur"``).
        raiz_runs: Sobrescreve ``perfil.raiz_runs``. Util em testes.
        extras: Campos adicionais para o ``manifest.json`` (parametros do
            comando, hiperparametros, etc.).

    Returns:
        RunDir apontando para o diretorio criado.

    Raises:
        ValueError: Se ``modo`` invalido ou ``protocolo`` ausente em modo
            metodologico.
    """
    if modo not in MODOS_VALIDOS:
        raise ValueError(f"modo invalido: {modo!r}. Esperado um de {MODOS_VALIDOS}.")
    if modo == "metodologico" and not protocolo:
        raise ValueError("modo='metodologico' exige 'protocolo' (ex.: 'n50').")
    proto_slug = protocolo if (modo == "metodologico" and protocolo) else SLUG_PROTOCOLO_VAZIO

    raiz_runs_efetiva = Path(raiz_runs) if raiz_runs else _resolver_raiz_runs(perfil)
    raiz_runs_efetiva.mkdir(parents=True, exist_ok=True)

    gitsha = _git_sha_curto()
    nome_run = f"{gitsha}__{tag}" if tag else gitsha

    raiz_run = raiz_runs_efetiva / modo / fonte / perfil.nome / proto_slug / nome_run
    # Se ja existe (re-execucao com mesmo sha sem tag), sobrescreve em-place.
    raiz_run.mkdir(parents=True, exist_ok=True)
    (raiz_run / "logs").mkdir(exist_ok=True)

    # Monta chave estavel para latest/
    partes_chave = [modo, fonte, perfil.nome]
    if proto_slug != SLUG_PROTOCOLO_VAZIO:
        partes_chave.append(proto_slug)
    chave = "__".join(partes_chave)

    run = RunDir(
        raiz=raiz_run,
        modo=modo,
        fonte=fonte,
        perfil=perfil.nome,
        protocolo=proto_slug,
        gitsha=gitsha,
        tag=tag,
        chave_latest=chave,
    )

    _gravar_manifest_inicial(run, perfil, extras or {})
    atualizar_latest(run, raiz_runs_efetiva)
    return run


def finalizar_run(
    run: RunDir,
    *,
    metricas_resumo: dict[str, Any] | None = None,
    sucesso: bool = True,
    mensagem: str = "",
) -> None:
    """Atualiza ``manifest.json`` com data_fim, duracao e metricas resumo.

    Deve ser chamada ao final da execucao para fechar o registro.
    """
    manifest = carregar_manifest(run)
    fim = datetime.now().astimezone()
    inicio_iso = manifest.get("data_inicio")
    if inicio_iso:
        inicio = datetime.fromisoformat(inicio_iso)
        manifest["duracao_s"] = round((fim - inicio).total_seconds(), 2)
    manifest["data_fim"] = fim.isoformat(timespec="seconds")
    manifest["sucesso"] = sucesso
    manifest["mensagem"] = mensagem
    if metricas_resumo is not None:
        manifest["metricas_resumo"] = metricas_resumo
    run.manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ============================================================
# LATEST
# ============================================================


def atualizar_latest(run: RunDir, raiz_runs: Path) -> Path:
    """Cria/atualiza symlink ``runs/latest/<chave>`` apontando para o run."""
    pasta_latest = raiz_runs / "latest"
    pasta_latest.mkdir(parents=True, exist_ok=True)
    link = pasta_latest / run.chave_latest
    if link.is_symlink() or link.exists():
        link.unlink()
    # Symlink relativo: latest/<chave> -> ../<modo>/<fonte>/<perfil>/<proto>/<nome>
    alvo_relativo = Path(os.path.relpath(run.raiz, pasta_latest))
    link.symlink_to(alvo_relativo, target_is_directory=True)
    return link


def resolver_latest(
    *,
    modo: str,
    fonte: str,
    perfil: str,
    protocolo: str | None = None,
    raiz_runs: Path,
) -> Path | None:
    """Retorna o caminho real (resolvido) do run latest para a chave."""
    partes = [modo, fonte, perfil]
    if protocolo:
        partes.append(protocolo)
    chave = "__".join(partes)
    link = raiz_runs / "latest" / chave
    if not link.exists():
        return None
    return link.resolve()


# ============================================================
# MANIFEST
# ============================================================


def carregar_manifest(run: RunDir | Path) -> dict[str, Any]:
    """Le ``manifest.json`` de um run."""
    caminho = run.manifest_path if isinstance(run, RunDir) else Path(run) / "manifest.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def _gravar_manifest_inicial(
    run: RunDir,
    perfil: Perfil,
    extras: dict[str, Any],
) -> None:
    """Escreve o manifest inicial; finalizar_run() completa data_fim/metricas."""
    agora = datetime.now().astimezone()
    payload: dict[str, Any] = {
        "run_id": secrets.token_hex(3),
        "modo": run.modo,
        "fonte": run.fonte,
        "perfil": run.perfil,
        "protocolo": None if run.protocolo == SLUG_PROTOCOLO_VAZIO else run.protocolo,
        "tag": run.tag,
        "git_sha": run.gitsha,
        "git_branch": _git_branch(),
        "git_dirty": _git_dirty(),
        "data_inicio": agora.isoformat(timespec="seconds"),
        "data_fim": None,
        "duracao_s": None,
        "sucesso": None,
        "mensagem": "",
        "fonte_path_real": _resolver_fonte_path(perfil, run.fonte, run.modo),
        "configs": {
            "paths": "configs/paths.yaml",
            "modelos": "configs/modelos.yaml",
            "pipeline": "configs/pipeline.yaml",
        },
        "ambiente": _coletar_ambiente(),
        "extras": extras,
        "metricas_resumo": None,
    }
    run.manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ============================================================
# LISTAGEM
# ============================================================


@dataclass
class RegistroRun:
    """Registro leve de um run, para listagem."""

    raiz: Path
    manifest: dict[str, Any] = field(default_factory=dict)


def listar_runs(
    raiz_runs: Path,
    *,
    modo: str | None = None,
    fonte: str | None = None,
    perfil: str | None = None,
    protocolo: str | None = None,
) -> list[RegistroRun]:
    """Lista runs em ``raiz_runs/`` aplicando filtros opcionais."""
    if not raiz_runs.exists():
        return []
    registros: list[RegistroRun] = []
    for manifest in raiz_runs.rglob("manifest.json"):
        if "latest" in manifest.parts:
            continue
        try:
            dados = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if modo and dados.get("modo") != modo:
            continue
        if fonte and dados.get("fonte") != fonte:
            continue
        if perfil and dados.get("perfil") != perfil:
            continue
        if protocolo and dados.get("protocolo") != protocolo:
            continue
        registros.append(RegistroRun(raiz=manifest.parent, manifest=dados))
    registros.sort(key=lambda r: r.manifest.get("data_inicio", ""), reverse=True)
    return registros


# ============================================================
# HELPERS PRIVADOS
# ============================================================


def _resolver_raiz_runs(perfil: Perfil) -> Path:
    """Resolve raiz de runs (campo do perfil ou default ``runs/``)."""
    raiz = perfil.extras.get("raiz_runs") if perfil.extras else None
    if raiz:
        from felinet.config import raiz_projeto, _resolver_path

        return _resolver_path(raiz_projeto(), raiz)
    from felinet.config import raiz_projeto

    return raiz_projeto() / "runs"


def _resolver_fonte_path(perfil: Perfil, fonte: str, modo: str) -> str | None:
    """Resolve o caminho real (com symlink resolvido) da fonte."""
    fontes = (perfil.extras or {}).get("fontes", {})
    entrada = fontes.get(fonte)
    if entrada is None:
        return None
    from felinet.config import raiz_projeto, _resolver_path

    caminho = _resolver_path(raiz_projeto(), entrada)
    try:
        return str(caminho.resolve())
    except OSError:
        return str(caminho)


def _git_sha_curto() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"


def _git_branch() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _git_dirty() -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return bool(out.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _coletar_ambiente() -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
    }
    try:
        import torch  # type: ignore[import-not-found]

        info["torch"] = torch.__version__
        info["cuda"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
    except ImportError:
        info["torch"] = None
        info["cuda"] = False
    return info
