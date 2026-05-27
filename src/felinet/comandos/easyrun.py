"""Wizard interativo (TUI) para configurar e rodar o felinet."""

from __future__ import annotations

import subprocess
import sys

import questionary
import typer

from felinet.config import raiz_projeto
from felinet.datasets.registro import carregar_datasets_locais

app = typer.Typer(
    help="Wizard interativo (TUI). Comece por aqui!",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def easyrun(ctx: typer.Context) -> None:
    """Menu principal do wizard."""
    if ctx.invoked_subcommand:
        return
    typer.echo("\n=== felinet easyrun ===\n")
    while True:
        escolha = questionary.select(
            "O que você quer fazer?",
            choices=[
                "Configurar/validar datasets locais",
                "Linkar datasets (criar symlinks)",
                "Listar status dos datasets",
                "Rodar pipeline (operacional)",
                "Rodar avaliação Re-ID",
                "Rodar demo didática (--dev, amostra pequena)",
                "Gerar tabelas da monografia",
                "Gerar figuras da monografia",
                "Validar instalação (make qualidade)",
                "Sair",
            ],
        ).ask()
        if not escolha or escolha == "Sair":
            break
        _despachar(escolha)
    typer.echo("\nAté!")


def _despachar(escolha: str) -> None:
    if escolha.startswith("Configurar"):
        _wizard_configurar_datasets()
    elif escolha.startswith("Linkar"):
        _executar(["datasets", "linkar"])
    elif escolha.startswith("Listar"):
        _executar(["datasets", "listar"])
    elif escolha.startswith("Rodar pipeline"):
        _wizard_pipeline()
    elif escolha.startswith("Rodar avaliação"):
        _wizard_reid()
    elif escolha.startswith("Rodar demo"):
        _wizard_demo()
    elif escolha.startswith("Gerar tabelas"):
        _wizard_tabelas()
    elif escolha.startswith("Gerar figuras"):
        _wizard_figuras()
    elif escolha.startswith("Validar"):
        subprocess.run(["make", "qualidade"], check=False)


def _executar(args: list[str]) -> None:
    cmd = [sys.executable, "-m", "felinet", *args]
    typer.echo(f"\n>>> {' '.join(cmd)}\n")
    subprocess.run(cmd, check=False)


def _wizard_configurar_datasets() -> None:
    raiz = raiz_projeto()
    arq = raiz / "configs" / "datasets_locais.yaml"
    exemplo = raiz / "configs" / "datasets_locais.example.yaml"
    if arq.exists():
        typer.echo(f"\nArquivo já existe: {arq}")
        if not questionary.confirm("Editar manualmente agora?", default=False).ask():
            return
        editor = questionary.text(
            "Comando do editor:", default="${EDITOR:-nano}"
        ).ask()
        subprocess.run(f"{editor} {arq}", shell=True, check=False)
        return
    if not exemplo.exists():
        typer.echo(f"[erro] não achei {exemplo}")
        return
    if questionary.confirm(
        f"Criar {arq} a partir do exemplo?", default=True
    ).ask():
        arq.write_text(exemplo.read_text())
        typer.echo(f"criado: {arq}")
        typer.echo(
            "→ edite o arquivo e ajuste os caminhos para os SEUS datasets."
        )
        editor = questionary.text(
            "Comando do editor:", default="${EDITOR:-nano}"
        ).ask()
        subprocess.run(f"{editor} {arq}", shell=True, check=False)


def _wizard_pipeline() -> None:
    datasets = carregar_datasets_locais()
    fontes_validas = [
        nome for nome, ds in datasets.items() if 1 in ds.fases_aplicaveis
    ]
    if not fontes_validas:
        typer.echo("\n[!] nenhuma fonte aplicável a pipeline operacional.")
        typer.echo("    Configure pelo menos uma fonte do tipo camera_trap_*.")
        return
    fonte = questionary.select("Fonte:", choices=fontes_validas).ask()
    perfil = questionary.select("Perfil:", choices=["prod", "dev"]).ask()
    n_str = questionary.text(
        "Máximo de amostras (0 = todas):",
        default="1000",
        validate=lambda v: v.isdigit() or "número inteiro >= 0",
    ).ask()
    dev_visual = questionary.confirm(
        "Modo --dev (galeria visual de descartes/bbox/crops)?",
        default=False,
    ).ask()
    args = [
        "pipeline",
        "executar",
        "--perfil",
        perfil,
        "--fonte",
        fonte,
        "--max-amostras",
        n_str,
    ]
    if dev_visual:
        args.append("--dev")
    if questionary.confirm(
        f"\nExecutar: felinet {' '.join(args)}?", default=True
    ).ask():
        _executar(args)


def _wizard_reid() -> None:
    datasets = carregar_datasets_locais()
    fontes_validas = [
        nome for nome, ds in datasets.items() if 4 in ds.fases_aplicaveis
    ]
    if not fontes_validas:
        typer.echo("\n[!] nenhuma fonte aplicável a Re-ID.")
        return
    fonte = questionary.select(
        "Fonte (Re-ID):", choices=fontes_validas
    ).ask()
    protocolo = questionary.select(
        "Protocolo:", choices=["closed-set", "open-set"]
    ).ask()
    n_str = questionary.text("Tamanho do conjunto (n):", default="200").ask()
    perfil = questionary.select("Perfil:", choices=["prod", "dev"]).ask()
    cmd_proto = (
        "avaliar-closed" if protocolo == "closed-set" else "avaliar-openset"
    )
    args = [
        "reid",
        cmd_proto,
        "--perfil",
        perfil,
        "--fonte",
        fonte,
        "--n",
        n_str,
    ]
    if questionary.confirm(
        f"Executar: felinet {' '.join(args)}?", default=True
    ).ask():
        _executar(args)


def _wizard_demo() -> None:
    datasets = carregar_datasets_locais()
    fontes = [n for n, ds in datasets.items() if 1 in ds.fases_aplicaveis]
    if not fontes:
        typer.echo("[!] sem fonte camera_trap configurada.")
        return
    fonte = questionary.select(
        "Fonte da demo (recomendado kaggle_cats — é menor):",
        choices=fontes,
    ).ask()
    n = questionary.text("Quantas imagens?", default="50").ask()
    args = ["dev", "demo", "--fonte", fonte, "--n", n]
    if questionary.confirm(
        f"Executar: felinet {' '.join(args)}?", default=True
    ).ask():
        _executar(args)


def _wizard_tabelas() -> None:
    tabelas_disponiveis = [
        "comparativo-fontes",
        "fontes-resumo",
        "datasets-avaliados",
        "reid-resumo",
        "openset-resumo",
        "run-inventory",
    ]
    nome = questionary.select("Tabela:", choices=tabelas_disponiveis).ask()
    perfil = questionary.select("Perfil:", choices=["prod", "dev"]).ask()
    args = ["tabelas", nome, "--perfil", perfil]
    if questionary.confirm(
        f"Executar: felinet {' '.join(args)}?", default=True
    ).ask():
        _executar(args)


def _wizard_figuras() -> None:
    figuras_disponiveis = [
        "comparativo-fontes",
        "matriz-confusao-fontes",
        "reid-cmc",
        "cmc-comparativo",
        "matriz-similaridade",
        "dist-intra-inter",
        "roc-openset",
        "galeria-erros",
    ]
    nome = questionary.select("Figura:", choices=figuras_disponiveis).ask()
    perfil = questionary.select("Perfil:", choices=["prod", "dev"]).ask()
    args = ["figuras", nome, "--perfil", perfil]
    if questionary.confirm(
        f"Executar: felinet {' '.join(args)}?", default=True
    ).ask():
        _executar(args)
