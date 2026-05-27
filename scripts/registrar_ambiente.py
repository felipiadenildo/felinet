#!/usr/bin/env python3
"""Registra as especificacoes do ambiente para reprodutibilidade.

Coleta hardware, SO, GPU, versao do Python e principais pacotes.
Salva em `runs/_ambiente/ambiente_<timestamp>.md` (e atualiza
`runs/_ambiente/latest.md`). Pensado para ser citado na monografia.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def cmd(args: list[str]) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=10, check=False)
        return r.stdout.strip() or r.stderr.strip()
    except Exception:  # noqa: BLE001
        return "n/d"


def pacotes_principais() -> dict[str, str]:
    pkgs = [
        "torch", "torchvision", "ultralytics", "transformers",
        "numpy", "pandas", "matplotlib", "pillow", "opencv-python",
        "scikit-learn", "typer", "ruff", "pytest", "questionary",
    ]
    out: dict[str, str] = {}
    for nome in pkgs:
        try:
            mod = __import__(nome.replace("-", "_") if nome != "pillow" else "PIL")
            ver = getattr(mod, "__version__", "?")
            out[nome] = ver
        except Exception:  # noqa: BLE001
            out[nome] = "ausente"
    return out


def info_torch_gpu() -> dict[str, str]:
    info = {"cuda_disponivel": "n/d", "cuda_versao": "n/d", "dispositivos": "n/d"}
    try:
        import torch
        info["cuda_disponivel"] = str(torch.cuda.is_available())
        info["cuda_versao"] = str(torch.version.cuda)
        if torch.cuda.is_available():
            n = torch.cuda.device_count()
            nomes = [torch.cuda.get_device_name(i) for i in range(n)]
            info["dispositivos"] = ", ".join(nomes)
    except Exception:  # noqa: BLE001
        pass
    return info


def commit_atual() -> dict[str, str]:
    return {
        "branch": cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": cmd(["git", "rev-parse", "--short", "HEAD"]),
        "dirty": "sim" if cmd(["git", "status", "--porcelain"]) else "nao",
    }


def coletar() -> dict:
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "sistema_operacional": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "distro": cmd(["lsb_release", "-ds"]) if shutil.which("lsb_release") else "n/d",
        "kernel": cmd(["uname", "-r"]),
        "python": sys.version.split()[0],
        "executavel_python": sys.executable,
        "cpu": cmd(["bash", "-c", "lscpu | grep 'Model name' | head -1 | sed 's/Model name:[ ]*//'"]) or "n/d",
        "nucleos": cmd(["nproc"]),
        "ram_total": cmd(["bash", "-c", "free -h | awk '/^Mem:/{print $2}'"]),
        "gpu_nvidia": cmd(["bash", "-c", "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null"]) or "n/d",
        "torch_gpu": info_torch_gpu(),
        "pacotes": pacotes_principais(),
        "git": commit_atual(),
    }


def renderizar_md(info: dict) -> str:
    g = info["git"]
    t = info["torch_gpu"]
    linhas = [
        "# Especificacoes do Ambiente",
        "",
        f"Coletado em {info['timestamp_utc']}.",
        "",
        "## Sistema",
        "",
        f"- Sistema operacional: {info['sistema_operacional']}",
        f"- Distribuicao: {info['distro']}",
        f"- Kernel: {info['kernel']}",
        f"- CPU: {info['cpu']}",
        f"- Nucleos logicos: {info['nucleos']}",
        f"- RAM total: {info['ram_total']}",
        "",
        "## GPU",
        "",
        f"- NVIDIA: {info['gpu_nvidia']}",
        f"- CUDA disponivel (PyTorch): {t['cuda_disponivel']}",
        f"- Versao CUDA: {t['cuda_versao']}",
        f"- Dispositivos: {t['dispositivos']}",
        "",
        "## Software",
        "",
        f"- Python: {info['python']}",
        f"- Executavel: {info['executavel_python']}",
        "",
        "### Pacotes principais",
        "",
    ]
    for nome, ver in info["pacotes"].items():
        linhas.append(f"- {nome}: {ver}")
    linhas += [
        "",
        "## Estado do Repositorio",
        "",
        f"- Branch: {g['branch']}",
        f"- Commit: {g['commit']}",
        f"- Arvore suja (uncommitted changes): {g['dirty']}",
        "",
    ]
    return "\n".join(linhas)


def main() -> int:
    raiz = Path.cwd()
    destino = raiz / "runs" / "_ambiente"
    destino.mkdir(parents=True, exist_ok=True)

    info = coletar()
    ts = info["timestamp_utc"].replace(":", "").replace("-", "").split(".")[0]
    md_path = destino / f"ambiente_{ts}.md"
    json_path = destino / f"ambiente_{ts}.json"
    latest = destino / "latest.md"

    md = renderizar_md(info)
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    latest.write_text(md, encoding="utf-8")

    print(f"[ambiente] {md_path}")
    print(f"[ambiente] {latest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
