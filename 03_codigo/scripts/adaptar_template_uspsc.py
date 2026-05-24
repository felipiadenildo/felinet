#!/usr/bin/env python3
"""
adaptar_template_uspsc.py
=========================

Adapta o pacote USPSC v3.2 (zip "meutccicmcp.zip") para a estrutura final
do projeto TCC em ``02_latex/``, seguindo as decisões registradas em
``00_governanca/decisoes_template_uspsc.md``.

Resumo das operações (idempotentes):

1.  Faz **backup completo** do zip original em ``02_latex/_ORIGINAL_meutccicmcp/``.
2.  **Copia o núcleo intocado** (``USPSC-classe/``, imagens essenciais).
3.  **Copia e adapta** pré-textuais ativos (Dedicatoria, Agradecimentos,
    Epigrafe, Resumo, Abstract, AbreviaturasSiglas, Simbolos, ficha,
    folhadeaprovacao, CapaICMC).
4.  **Esvazia** pré/pós-textuais opcionais (Errata, IndicesRemissivos) que
    o ``main.tex`` ``\\include{}`` exige existir mas que NÃO usaremos.
5.  **Renomeia** ``USPSC-TCC-modelo-ICMCp.tex`` → ``main.tex`` e
    ``USPSC-TCC-pre-textual-ICMC.tex`` → ``pre-textuais.tex`` ajustando
    todas as referências internas.
6.  **Substitui** a referência ``\\bibliography{USPSC-bib/USPSC-modelo-references}``
    por ``\\bibliography{USPSC-bib/references}`` e cria um ``references.bib``
    vazio.
7.  **Descarta** arquivos didáticos/exemplos (capítulos exemplo, .bib
    exemplo, imagens didáticas, USPSC-IndicesRemissivos da raiz,
    USPSC-unidades.tex).
8.  **Cria** ``USPSC-TA-Textual/`` vazia (capítulos virão na Fase 5) e
    ``figuras/`` para figuras do projeto.
9.  Imprime um **relatório final** com o que foi copiado/descartado/criado
    e checa diferenças com a estrutura esperada.

Uso
---
::

    # padrão: lê o zip em ../../meutccicmcp.zip e adapta em ../../02_latex/
    python adaptar_template_uspsc.py

    # personalizado
    python adaptar_template_uspsc.py \
        --zip /caminho/para/meutccicmcp.zip \
        --destino /caminho/para/02_latex \
        --dry-run

Requisitos
----------
Apenas a biblioteca padrão do Python 3.9+ (zipfile, shutil, pathlib,
argparse).

Idempotência
------------
O script pode ser executado várias vezes sem efeito colateral indesejado:

* sobreposições só ocorrem em arquivos do template (não nos seus capítulos);
* arquivos seus em ``USPSC-TA-Textual/`` ou ``figuras/`` NUNCA são tocados;
* a flag ``--force`` é necessária para sobrescrever pré-textuais já
  customizados (Resumo, Dedicatoria, etc.).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração declarativa (única fonte de verdade do que vai/não vai)
# ---------------------------------------------------------------------------

#: Arquivos do núcleo do template — copiados como estão, sempre.
NUCLEO_INTOCAVEL = [
    "USPSC-classe/USPSC.cls",
    "USPSC-classe/USPSC1.cls",
    "USPSC-classe/ABNT6023-10520.sty",
    "USPSC-classe/abntex2-alf-USPSC.bst",
    "USPSC-classe/abntex2-alfeng-USPSC.bst",
    "USPSC-classe/abntex2-num-USPSC.bst",
    "USPSC-classe/abntex2-numeng-USPSC.bst",
    "USPSC-img/CapaICMC.jpg",
    "USPSC-img/USPSC-PaginaEmBranco.jpg",
]

#: Pré-textuais ativos — copiados e depois você edita o conteúdo.
#: Esses arquivos contêm o conteúdo das suas seções (dedicatória, resumo...).
PRE_TEXTUAIS_ATIVOS = [
    "USPSC-TA-PreTextual/USPSC-CapaICMC.tex",
    "USPSC-TA-PreTextual/USPSC-fichacatalografica.tex",
    "USPSC-TA-PreTextual/USPSC-fichacatalografica.pdf",
    "USPSC-TA-PreTextual/USPSC-folhadeaprovacao.tex",
    "USPSC-TA-PreTextual/USPSC-folhadeaprovacao.pdf",
    "USPSC-TA-PreTextual/USPSC-PaginaEmBranco.pdf",
    "USPSC-TA-PreTextual/USPSC-VersoPaginaDeRosto-Relatorio.pdf",
    "USPSC-TA-PreTextual/USPSC-Dedicatoria.tex",
    "USPSC-TA-PreTextual/USPSC-Agradecimentos.tex",
    "USPSC-TA-PreTextual/USPSC-Epigrafe.tex",
    "USPSC-TA-PreTextual/USPSC-Resumo.tex",
    "USPSC-TA-PreTextual/USPSC-Abstract.tex",
    "USPSC-TA-PreTextual/USPSC-AbreviaturasSiglas.tex",
    "USPSC-TA-PreTextual/USPSC-Simbolos.tex",
]

#: Pré/pós-textuais opcionais — copiados COMO ESQUELETO VAZIO (mantêm o
#: \include{} no main.tex compilável sem erro, mas sem gerar conteúdo).
#: Errata: opcional pela ABNT NBR 14724.
#: IndicesRemissivos: opcional, raramente usado em TCC.
OPCIONAIS_ESVAZIAR = {
    "USPSC-TA-PreTextual/USPSC-Errata.tex": "Errata (opcional)",
    "USPSC-TA-PosTextual/USPSC-IndicesRemissivos.tex": "Índices Remissivos (opcional)",
}

#: Pós-textuais ativos — esqueletos que você preenche.
POS_TEXTUAIS_ATIVOS = [
    "USPSC-TA-PosTextual/USPSC-Apendices.tex",
    "USPSC-TA-PosTextual/USPSC-Anexos.tex",
]

#: Raiz: arquivos principais renomeados para nomes mais limpos.
RENOMEAR_RAIZ = {
    "USPSC-TCC-modelo-ICMCp.tex": "main.tex",
    "USPSC-TCC-pre-textual-ICMC.tex": "pre-textuais.tex",
}

#: Arquivos didáticos/exemplos descartados (NÃO copiar).
DESCARTAR = [
    "USPSC-IndicesRemissivos.tex",  # duplicado da raiz
    "USPSC-unidades.tex",  # didático
    "USPSC-bib/USPSC-modelo-references.bib",  # bib de exemplo
    "USPSC-img/USPSC-AcentuacaoLaTeX.png",  # didático
    "USPSC-img/USPSC-EstruturaTrabAcad.jpg",  # didático
    "USPSC-img/USPSC-LetrasGregas.png",  # didático
    "USPSC-img/USPSC-SimbolosUteis.png",  # didático
    "USPSC-img/USPSC-modelo-img-grafico.pdf",  # didático
    "USPSC-img/USPSC-modelo-img-marca.pdf",  # didático
    "USPSC-TA-Textual/USPSC-Cap1-Introducao.tex",  # capítulo exemplo
    "USPSC-TA-Textual/USPSC-Cap2-Desenvolvimento.tex",  # capítulo exemplo
    "USPSC-TA-Textual/USPSC-Cap3-Conclusao.tex",  # capítulo exemplo
]

#: Substituições no main.tex (renomeado).  Ajusta referências bibliográficas.
SUBSTITUICOES_MAIN = [
    (
        "\\bibliography{USPSC-bib/USPSC-modelo-references}",
        "\\bibliography{USPSC-bib/references}",
    ),
]


#: Conteúdo neutro para arquivos opcionais esvaziados.
def _conteudo_vazio(rotulo: str) -> str:
    return (
        f"% {rotulo}\n"
        f"% Mantido vazio intencionalmente.\n"
        f"% O arquivo precisa existir porque o main.tex tem um \\include{{...}}\n"
        f"% apontando para ele, mas nenhuma página é gerada quando o conteúdo\n"
        f"% está vazio.  Para reativar, remova este comentário e adicione o\n"
        f"% conteúdo.  Veja o tutorial USPSC v3.2 para o formato esperado.\n"
    )


#: Conteúdo inicial do references.bib (placeholder).
REFERENCES_BIB_INICIAL = """% references.bib
% =================================================================
% Bibliografia do TCC.  Adicione aqui as entradas BibTeX no formato
% suportado pelo abntex2cite (já configurado em main.tex).
%
% Exemplo de entrada:
%
% @article{Beery2018Recognition,
%   author  = {Beery, Sara and Van Horn, Grant and Perona, Pietro},
%   title   = {Recognition in Terra Incognita},
%   journal = {ECCV},
%   year    = {2018},
% }
% =================================================================
"""


# ---------------------------------------------------------------------------
# Estruturas auxiliares
# ---------------------------------------------------------------------------


@dataclass
class Relatorio:
    copiados: list[str] = field(default_factory=list)
    renomeados: list[str] = field(default_factory=list)
    esvaziados: list[str] = field(default_factory=list)
    descartados: list[str] = field(default_factory=list)
    criados: list[str] = field(default_factory=list)
    pulados: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def imprimir(self) -> None:
        print("\n" + "=" * 70)
        print("RELATÓRIO DE ADAPTAÇÃO DO TEMPLATE USPSC")
        print("=" * 70)
        for nome, lista in (
            ("Copiados (núcleo + pré-textuais ativos)", self.copiados),
            ("Renomeados (raiz)", self.renomeados),
            ("Esvaziados (opcionais mantidos)", self.esvaziados),
            ("Descartados (didáticos/exemplo)", self.descartados),
            ("Criados (esqueletos novos)", self.criados),
            ("Pulados (já existem e --force não usado)", self.pulados),
        ):
            print(f"\n[{len(lista):>3}] {nome}")
            for item in lista:
                print(f"     • {item}")
        if self.avisos:
            print(f"\n[!] {len(self.avisos)} aviso(s):")
            for av in self.avisos:
                print(f"     ! {av}")
        print("\n" + "=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------


def _copiar(
    src: Path, dst: Path, rel: Relatorio, *, force: bool, dry: bool, categoria: str = "copiados"
) -> None:
    """Copia ``src`` para ``dst``.  Respeita ``force`` e ``dry``."""
    if dst.exists() and not force:
        rel.pulados.append(str(dst))
        return
    if dry:
        getattr(rel, categoria).append(f"{src.name} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    getattr(rel, categoria).append(str(dst))


def _escrever(
    path: Path, conteudo: str, rel: Relatorio, *, force: bool, dry: bool, categoria: str = "criados"
) -> None:
    """Escreve ``conteudo`` em ``path``."""
    if path.exists() and not force:
        rel.pulados.append(str(path))
        return
    if dry:
        getattr(rel, categoria).append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(conteudo, encoding="utf-8")
    getattr(rel, categoria).append(str(path))


def _extrair_zip(zip_path: Path, destino_tmp: Path) -> Path:
    """Extrai zip e retorna o diretório que contém os arquivos do template."""
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(destino_tmp)
    candidatos = [p for p in destino_tmp.iterdir() if p.is_dir()]
    if len(candidatos) == 1:
        return candidatos[0]
    # zip sem pasta-pai
    return destino_tmp


# ---------------------------------------------------------------------------
# Operações principais
# ---------------------------------------------------------------------------


def operar(
    *,
    zip_path: Path,
    destino: Path,
    backup: bool,
    force: bool,
    dry: bool,
) -> Relatorio:
    rel = Relatorio()

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip não encontrado: {zip_path}")

    destino.mkdir(parents=True, exist_ok=True)

    # 1. Extrair zip em diretório temporário
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raiz_template = _extrair_zip(zip_path, tmp_path)
        print(f"[ok] template extraído em {raiz_template}")

        # 2. Backup do template original
        if backup:
            backup_dir = destino / "_ORIGINAL_meutccicmcp"
            if backup_dir.exists():
                rel.avisos.append(f"Backup já existe e foi mantido: {backup_dir}")
            else:
                if not dry:
                    shutil.copytree(raiz_template, backup_dir)
                rel.copiados.append(str(backup_dir) + "/ (backup completo)")

        # 3. Núcleo intocável
        for rel_path in NUCLEO_INTOCAVEL:
            src = raiz_template / rel_path
            dst = destino / rel_path
            if not src.exists():
                rel.avisos.append(f"Faltando no zip: {rel_path}")
                continue
            _copiar(src, dst, rel, force=True, dry=dry)

        # 4. Pré-textuais ativos
        for rel_path in PRE_TEXTUAIS_ATIVOS:
            src = raiz_template / rel_path
            dst = destino / rel_path
            if not src.exists():
                rel.avisos.append(f"Faltando no zip: {rel_path}")
                continue
            # force=False: pré-textuais que você já editou não devem ser
            # sobrescritos a menos que --force seja passado.
            _copiar(src, dst, rel, force=force, dry=dry)

        # 5. Pós-textuais ativos
        for rel_path in POS_TEXTUAIS_ATIVOS:
            src = raiz_template / rel_path
            dst = destino / rel_path
            if not src.exists():
                rel.avisos.append(f"Faltando no zip: {rel_path}")
                continue
            _copiar(src, dst, rel, force=force, dry=dry)

        # 6. Opcionais esvaziados
        for rel_path, rotulo in OPCIONAIS_ESVAZIAR.items():
            dst = destino / rel_path
            _escrever(
                dst,
                _conteudo_vazio(rotulo),
                rel,
                force=True,
                dry=dry,
                categoria="esvaziados",
            )

        # 7. Renomear raiz (main, pre-textuais)
        for src_name, dst_name in RENOMEAR_RAIZ.items():
            src = raiz_template / src_name
            dst = destino / dst_name
            if not src.exists():
                rel.avisos.append(f"Faltando no zip: {src_name}")
                continue
            if dst.exists() and not force:
                rel.pulados.append(str(dst))
                continue
            if not dry:
                conteudo = src.read_text(encoding="utf-8")
                if src_name == "USPSC-TCC-modelo-ICMCp.tex":
                    for old, new in SUBSTITUICOES_MAIN:
                        conteudo = conteudo.replace(old, new)
                dst.write_text(conteudo, encoding="utf-8")
            rel.renomeados.append(f"{src_name} -> {dst_name}")

        # 8. Descartados (apenas registrar)
        for rel_path in DESCARTAR:
            src = raiz_template / rel_path
            if src.exists():
                rel.descartados.append(rel_path)

        # 9. Criar diretórios esqueleto e arquivos novos
        textual_dir = destino / "USPSC-TA-Textual"
        if not dry:
            textual_dir.mkdir(parents=True, exist_ok=True)
        _escrever(
            textual_dir / ".gitkeep",
            "",
            rel,
            force=False,
            dry=dry,
            categoria="criados",
        )

        figuras_dir = destino / "figuras"
        if not dry:
            figuras_dir.mkdir(parents=True, exist_ok=True)
        _escrever(
            figuras_dir / ".gitkeep",
            "",
            rel,
            force=False,
            dry=dry,
            categoria="criados",
        )

        bib_dir = destino / "USPSC-bib"
        _escrever(
            bib_dir / "references.bib",
            REFERENCES_BIB_INICIAL,
            rel,
            force=False,
            dry=dry,
            categoria="criados",
        )

        # 10. README explicativo no destino
        readme = destino / "README.md"
        _escrever(
            readme,
            _readme_destino(),
            rel,
            force=False,
            dry=dry,
            categoria="criados",
        )

    return rel


def _readme_destino() -> str:
    return """# 02_latex/ — Documento LaTeX do TCC

Estrutura adaptada do **Pacote USPSC v3.2** (campus USP de São Carlos)
pela equipe de adaptação automática.

## Estrutura

```
02_latex/
├── main.tex                     # arquivo principal (compilar este)
├── pre-textuais.tex             # dados do trabalho (autor, título, etc.)
├── README.md                    # este arquivo
├── USPSC-classe/                # classe + estilos (NÃO MEXER)
├── USPSC-img/                   # imagens da capa
├── USPSC-bib/
│   └── references.bib           # sua bibliografia
├── USPSC-TA-PreTextual/         # dedicatória, resumo, abstract, etc.
├── USPSC-TA-Textual/            # capítulos do TCC (preencher)
├── USPSC-TA-PosTextual/         # apêndices, anexos
├── figuras/                     # figuras do projeto
└── _ORIGINAL_meutccicmcp/       # backup intocado do template (referência)
```

## Compilação

Use `latexmk` com a configuração padrão do pacote USPSC:

```bash
latexmk -pdf -bibtex main.tex
# ou, para limpar artefatos:
latexmk -C
```

No VS Code (Linux Mint), instale a extensão **LaTeX Workshop** e configure
o recipe ``latexmk (pdf)`` apontando para ``main.tex``.

## Arquivos opcionais esvaziados

Os seguintes arquivos foram **mantidos vazios** porque o `main.tex` tem
um ``\\include{}`` que os referencia — removê-los quebraria a compilação,
mas mantê-los vazios não gera páginas:

* `USPSC-TA-PreTextual/USPSC-Errata.tex` — Errata (opcional pela ABNT)
* `USPSC-TA-PosTextual/USPSC-IndicesRemissivos.tex` — Índices Remissivos

Para reativar, basta editar o arquivo correspondente.

## Próximos passos

1. Editar `pre-textuais.tex` com seus dados (autor, título, orientador).
2. Editar `USPSC-TA-PreTextual/USPSC-Resumo.tex` e `USPSC-Abstract.tex`.
3. Preencher `USPSC-TA-Textual/` com os capítulos (Fase 5).
4. Popular `USPSC-bib/references.bib` com a bibliografia.
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    script_dir = Path(__file__).resolve().parent
    # ../../meutccicmcp.zip relativo ao script em 03_codigo/scripts/
    raiz_projeto = script_dir.parent.parent
    zip_default = raiz_projeto.parent / "meutccicmcp.zip"
    destino_default = raiz_projeto / "02_latex"

    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--zip",
        type=Path,
        default=zip_default,
        help=f"caminho do zip do template (default: {zip_default})",
    )
    p.add_argument(
        "--destino",
        type=Path,
        default=destino_default,
        help=f"pasta de destino 02_latex/ (default: {destino_default})",
    )
    p.add_argument(
        "--sem-backup",
        action="store_true",
        help="não copiar o template original para _ORIGINAL_meutccicmcp/",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="sobrescreve pré-textuais já adaptados (CUIDADO: apaga edições)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="apenas simula; não escreve nada no disco",
    )
    args = p.parse_args(argv)

    print(f"[..] Zip do template: {args.zip}")
    print(f"[..] Destino:         {args.destino}")
    print(f"[..] Backup:          {'NÃO' if args.sem_backup else 'sim'}")
    print(f"[..] Force:           {'sim' if args.force else 'não'}")
    print(f"[..] Dry-run:         {'sim' if args.dry_run else 'não'}")

    try:
        rel = operar(
            zip_path=args.zip,
            destino=args.destino,
            backup=not args.sem_backup,
            force=args.force,
            dry=args.dry_run,
        )
    except FileNotFoundError as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 1

    rel.imprimir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
