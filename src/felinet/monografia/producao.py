"""Gera os elementos do registro na monografia, grava o manifesto e confere o ``.tex``.

Saída em ``<monografia>/elementos/gerados/``:

* os arquivos de ``elementos.ELEMENTOS`` (PDF vetorial ou ``.tex``), por capítulo;
* ``MANIFESTO.json``: para cada arquivo, sha256, função, comando, requisitos e os arquivos
  de entrada lidos (com sha256), além do commit do felinet que gerou;
* ``LEIAME.md``: o mapa legível (rótulo -> arquivo -> função -> requisitos);
* ``apendice/mapa_reproducao.tex``: o mesmo mapa como tabela, para o apêndice da monografia.
"""

from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from felinet import __version__
from felinet.monografia import dados as d
from felinet.monografia import elementos as el
from felinet.monografia import estilo as e
from felinet.monografia.tabelas import CABECALHO, tex_escapar
from felinet.runs import _git_dirty, _git_sha_curto

PASTA_GERADOS = Path("elementos") / "gerados"
CONFIG_PADRAO = el.RAIZ_FELINET / "configs" / "monografia.yaml"
MAPA = "apendice/mapa_reproducao.tex"
COMANDO = "felinet monografia gerar"


# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------


@dataclass
class Config:
    monografia: Path
    entradas: el.Entradas


def carregar_config(
    arquivo: Path | None = None,
    monografia: Path | None = None,
    runs: Path | None = None,
    fotos: Path | None = None,
    substituir: list[tuple[str, str]] | None = None,
) -> Config:
    """Lê ``configs/monografia.yaml`` (caminhos relativos à raiz do felinet); opções explícitas vencem."""
    arquivo = Path(arquivo) if arquivo else CONFIG_PADRAO
    cfg = yaml.safe_load(arquivo.read_text(encoding="utf-8")) if arquivo.is_file() else {}
    cfg = cfg or {}

    def caminho(valor, chave):
        if valor is not None:
            return Path(valor)
        if cfg.get(chave):
            p = Path(cfg[chave]).expanduser()
            return p if p.is_absolute() else (el.RAIZ_FELINET / p)
        return None

    pares = list((cfg.get("substituir") or {}).items()) + list(substituir or [])
    return Config(
        monografia=caminho(monografia, "monografia")
        or el.RAIZ_FELINET.parent / "monografia-felinet",
        entradas=el.Entradas(
            runs=caminho(runs, "runs"), fotos=caminho(fotos, "fotos"), substituir=tuple(pares)
        ),
    )


# ----------------------------------------------------------------------------
# Registro dos arquivos lidos (proveniência no manifesto)
# ----------------------------------------------------------------------------


@contextlib.contextmanager
def _registrar_leituras() -> Iterator[set[Path]]:
    """Anota todo arquivo aberto para leitura (``open``/``Path.read_*``/``np.load``/PIL)."""
    lidos: set[Path] = set()
    original_b, original_io = builtins.open, io.open

    def espiao(arquivo, modo="r", *args, **kwargs):
        if isinstance(arquivo, (str, Path)) and "r" in modo and "+" not in modo:
            lidos.add(Path(arquivo).resolve())
        return original_b(arquivo, modo, *args, **kwargs)

    builtins.open = io.open = espiao
    try:
        yield lidos
    finally:
        builtins.open, io.open = original_b, original_io


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _descrever_entradas(lidos: set[Path], en: el.Entradas) -> dict:
    """Arquivos dos runs e do felinet com sha256; imagens só contadas."""
    raizes = [("runs", en.runs), ("felinet", el.RAIZ_FELINET)]
    arquivos, imagens = [], 0
    for p in sorted(lidos):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and "05_crops" not in str(p):
            imagens += 1
            continue
        for nome, raiz in raizes:
            if raiz is None:
                continue
            with contextlib.suppress(ValueError):
                rel = p.relative_to(Path(raiz).resolve())
                if nome == "felinet" and rel.parts[:1] not in (("docs",), ("configs",)):
                    break  # código e fontes do próprio pacote não são entrada de dados
                arquivos.append({"arquivo": f"{nome}/{rel.as_posix()}", "sha256": _sha256(p)})
                break
    return {"arquivos": arquivos, "imagens_lidas": imagens}


# ----------------------------------------------------------------------------
# Geração
# ----------------------------------------------------------------------------


@dataclass
class Resultado:
    gerados: list[str] = field(default_factory=list)
    pendentes: dict[str, list[str]] = field(default_factory=dict)  # arquivo -> requisitos
    erros: dict[str, str] = field(default_factory=dict)


def _selecionar(so: list[str] | None) -> list[el.Elemento]:
    if not so:
        return list(el.ELEMENTOS)
    escolhidos = [x for x in el.ELEMENTOS if x.arquivo in so or x.rotulo in so]
    desconhecidos = set(so) - {x.arquivo for x in escolhidos} - {x.rotulo for x in escolhidos}
    if desconhecidos:
        raise KeyError(", ".join(sorted(desconhecidos)))
    return escolhidos


def _gravar(conteudo, destino: Path) -> None:
    if isinstance(conteudo, str):
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo, encoding="utf-8")
    else:
        e.salvar(conteudo, destino)


def _ler_manifesto(pasta: Path) -> dict:
    arq = pasta / "MANIFESTO.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.is_file() else {}


def gerar(cfg: Config, so: list[str] | None = None) -> Resultado:
    """Gera os elementos cujos requisitos estão disponíveis; os demais ficam pendentes."""
    pasta = cfg.monografia / PASTA_GERADOS
    if not (cfg.monografia / "main.tex").is_file():
        raise FileNotFoundError(f"não parece a monografia (sem main.tex): {cfg.monografia}")
    anterior = {i["arquivo"]: i for i in _ler_manifesto(pasta).get("elementos", [])}
    res = Resultado()
    for item in _selecionar(so):
        falta = el.faltando(item, cfg.entradas)
        if falta:
            res.pendentes[item.arquivo] = falta
            continue
        try:
            with _registrar_leituras() as lidos:
                conteudo = item.produzir(cfg.entradas)
            _gravar(conteudo, pasta / item.arquivo)
        except (d.DadosAusentesError, d.RunsDivergentesError, FileNotFoundError, KeyError) as exc:
            res.erros[item.arquivo] = f"{type(exc).__name__}: {exc}"
            continue
        anterior[item.arquivo] = {
            **_descricao(item),
            "sha256": _sha256(pasta / item.arquivo),
            "entradas": _descrever_entradas(lidos, cfg.entradas),
        }
        res.gerados.append(item.arquivo)
    _gravar(mapa_reproducao(), pasta / MAPA)
    commit = _git_sha_curto(cwd=el.RAIZ_FELINET)
    manifesto = {
        "felinet": __version__,
        "commit": commit,
        # Sem git (ex.: pacote instalado de wheel), o estado é desconhecido.
        "alteracoes_nao_commitadas": None if commit == "nogit" else _git_dirty(cwd=el.RAIZ_FELINET),
        "elementos": [anterior[x.arquivo] for x in el.ELEMENTOS if x.arquivo in anterior],
    }
    (pasta / "MANIFESTO.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (pasta / "LEIAME.md").write_text(leiame(), encoding="utf-8")
    return res


def _descricao(item: el.Elemento) -> dict:
    return {
        "arquivo": item.arquivo,
        "rotulo": item.rotulo,
        "descricao": item.descricao,
        "codigo": item.codigo,
        "requer": list(item.requer),
        "comando": f"{COMANDO} --so {item.arquivo}",
    }


# ----------------------------------------------------------------------------
# Mapas (LEIAME.md e tabela do apêndice)
# ----------------------------------------------------------------------------

_ONDE = {
    (): "felinet (dados no repositório)",
    ("fotos",): "fotos do iNaturalist",
    ("runs",): "runs",
    ("runs", "imagens"): "runs + imagens",
    ("runs", "petface"): "runs + PetFace (ambiente original)",
    ("runs", "umap"): "CatIndividualImages (ambiente original)",
}


def leiame() -> str:
    linhas = [
        "# Elementos gerados pelo felinet",
        "",
        "Não edite estes arquivos: eles são escritos por `felinet monografia gerar` (repositório",
        "[felinet](https://github.com/felipiadenildo/felinet)) a partir dos runs da execução final.",
        "O registro está em `src/felinet/monografia/elementos.py`; `MANIFESTO.json` guarda o sha256",
        "de cada arquivo, os arquivos de entrada e o commit do felinet que gerou.",
        "",
        "```bash",
        "felinet monografia gerar                 # tudo o que os dados desta máquina permitem",
        "felinet monografia gerar --so <arquivo>  # um elemento",
        "felinet monografia verificar             # .tex x registro x manifesto",
        "```",
        "",
        "| Rótulo no LaTeX | Arquivo | Função no felinet | Requer |",
        "|---|---|---|---|",
    ]
    for x in el.ELEMENTOS:
        linhas.append(
            f"| `{x.rotulo}` | `{x.arquivo}` | `{x.codigo}` | {_ONDE.get(x.requer, ', '.join(x.requer))} |"
        )
    linhas += [
        "",
        "Desenhos que não vêm de dados ficam em `elementos/diagramas/` (TikZ em `tikz/`, o diagrama",
        "completo em `diagrama_completo_sistema.drawio`, exportado por `make diagramas`).",
        "",
    ]
    return "\n".join(linhas)


def mapa_reproducao() -> str:
    """Tabela (longtable) do apêndice de reprodução: elemento, arquivo, função e requisito."""
    vistos, linhas = set(), []
    for x in el.ELEMENTOS:
        if x.rotulo in vistos:
            continue
        vistos.add(x.rotulo)
        tipo = "Figura" if x.rotulo.startswith("fig:") else "Tabela"
        modulo, funcao = x.codigo.removeprefix("src/felinet/monografia/").split(".py::")
        linhas.append(
            f"{tipo}~\\ref{{{x.rotulo}}} & \\texttt{{{tex_escapar(x.arquivo)}}}\\newline"
            f" \\texttt{{{modulo}.{tex_escapar(funcao)}}} & {_ONDE.get(x.requer, '')} \\\\"
        )
    corpo = "\n".join(f"  {lin}" for lin in linhas)
    return (
        CABECALHO.format(funcao="producao.mapa_reproducao")
        + "\\begin{longtable}{@{}l >{\\raggedright\\arraybackslash}p{0.52\\textwidth}"
        " >{\\raggedright\\arraybackslash}p{0.28\\textwidth}@{}}\n"
        "  \\caption[Origem de cada figura e tabela gerada pelo FELINET.]{Origem de cada figura e"
        " tabela gerada pelo FELINET: arquivo em \\texttt{elementos/gerados/}, função em"
        " \\texttt{src/felinet/monografia/} e dados necessários.}\\label{tab:mapa-reproducao}\\\\\n"
        "  \\toprule\n"
        "  \\textbf{Elemento} & \\textbf{Arquivo e função} & \\textbf{Requer} \\\\\n"
        "  \\midrule\n  \\endfirsthead\n"
        "  \\toprule\n"
        "  \\textbf{Elemento} & \\textbf{Arquivo e função} & \\textbf{Requer} \\\\\n"
        "  \\midrule\n  \\endhead\n"
        f"{corpo}\n  \\bottomrule\n\\end{{longtable}}\n"
    )


# ----------------------------------------------------------------------------
# Verificação
# ----------------------------------------------------------------------------

_USO = re.compile(r"\\(?:gerado|input)(?:\[[^\]]*\])?\{(?:elementos/gerados/)?([^}]+)\}")


def usos_no_tex(monografia: Path) -> dict[str, list[str]]:
    """Arquivos de ``elementos/gerados`` citados no ``.tex`` -> arquivos .tex que os citam."""
    usos: dict[str, list[str]] = {}
    for tex in sorted(monografia.rglob("*.tex")):
        rel = tex.relative_to(monografia)
        if rel.parts[0] in {"build", "USPSC-classe"} or rel.parts[:2] == PASTA_GERADOS.parts:
            continue
        texto = re.sub(r"(?<!\\)%.*", "", tex.read_text(encoding="utf-8"))
        for m in _USO.finditer(texto):
            alvo = m.group(1)
            bruto = m.group(0)
            if bruto.startswith("\\input") and "elementos/gerados/" not in bruto:
                continue
            if not Path(alvo).suffix:
                alvo += ".tex"
            usos.setdefault(alvo, []).append(str(rel))
    return usos


def verificar(cfg: Config) -> list[str]:
    """Problemas encontrados (lista vazia = monografia, registro e manifesto coerentes)."""
    pasta = cfg.monografia / PASTA_GERADOS
    problemas = []
    usos = usos_no_tex(cfg.monografia)
    registrados = {x.arquivo for x in el.ELEMENTOS} | {MAPA}
    for alvo in sorted(set(usos) - registrados):
        problemas.append(f"{alvo}: citado em {', '.join(usos[alvo])}, mas não está no registro")
    for alvo in sorted(registrados - set(usos)):
        problemas.append(f"{alvo}: está no registro, mas a monografia não o usa")
    manifesto = {i["arquivo"]: i for i in _ler_manifesto(pasta).get("elementos", [])}
    pendentes_ok = set()
    for x in el.ELEMENTOS:
        arq = pasta / x.arquivo
        if not arq.is_file():
            if set(x.requer) & {"petface", "umap"}:
                pendentes_ok.add(x.arquivo)  # a monografia mostra o quadro de pendência
                continue
            problemas.append(f"{x.arquivo}: arquivo ausente (rode `{COMANDO} --so {x.arquivo}`)")
            continue
        info = manifesto.get(x.arquivo)
        if info is None:
            problemas.append(f"{x.arquivo}: sem entrada no MANIFESTO.json")
        elif info["sha256"] != _sha256(arq):
            problemas.append(f"{x.arquivo}: difere do manifesto (editado à mão ou desatualizado)")
        elif cfg.entradas.runs is not None:
            for ent in info["entradas"]["arquivos"]:
                raiz, rel = ent["arquivo"].split("/", 1)
                base = cfg.entradas.runs if raiz == "runs" else el.RAIZ_FELINET
                lido = Path(base) / rel
                if lido.is_file() and _sha256(lido) != ent["sha256"]:
                    problemas.append(
                        f"{x.arquivo}: a entrada {ent['arquivo']} mudou desde a geração"
                    )
        # Tabelas que só dependem dos runs: o texto gerado agora tem de ser idêntico.
        if x.tipo != "tabela" or el.faltando(x, cfg.entradas):
            continue
        try:
            atual = x.produzir(cfg.entradas)
        except (d.DadosAusentesError, d.RunsDivergentesError) as exc:
            problemas.append(f"{x.arquivo}: não deu para conferir com os runs ({exc})")
            continue
        if atual != arq.read_text(encoding="utf-8"):
            problemas.append(f"{x.arquivo}: os números não conferem com os dados atuais")
    return problemas
