# TCC — Sistema de Monitoramento por Visão Computacional da Colônia de Gatos do Campus 2 da USP São Carlos

> **Estudo e concepção** de um sistema de visão computacional aplicado ao monitoramento da colônia de gatos comunitários do Campus 2 da USP São Carlos, em parceria com o projeto **AEX Gatosdoc2**.
> Trabalho de Conclusão de Curso — **Engenharia de Computação, ICMC/USP São Carlos**.
> Defesa prevista: **setembro/2026**.

---

## 1. Visão geral

Este repositório contém **todos os artefatos** do TCC, organizados em camadas que refletem o ciclo de vida do trabalho: pesquisa de fundamentação → engenharia de sistema → implementação computacional → dados → resultados → entrega.

A organização segue boas práticas de:

- **Projetos científicos reprodutíveis** (estrutura inspirada em [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/) e [The Turing Way](https://book.the-turing-way.org/)).
- **Trabalhos acadêmicos USP** (template **USPSC 3.2** para a monografia em LaTeX).
- **Norma ABNT** para apresentação e estrutura textual.
- **Convenções FAIR** (Findable, Accessible, Interoperable, Reusable) para dados e código.

---

## 2. Estrutura de pastas

```
tcc_gatos_campus2/
│
├── README.md                   ← este arquivo
├── pyproject.toml              ← dependências Python (uv)
├── .gitignore                  ← padrões git
├── .gitattributes              ← line-endings e LFS
│
├── 00_governanca/              ← documentos de gestão do projeto
│   ├── CHANGELOG_revisao_v2.md     histórico de revisões
│   ├── diretrizes_projeto.md       diretrizes vinculantes
│   ├── alinhamento_projeto_base.md alinhamento com PDF original
│   ├── glossario_notas_rodape.md   glossário (vira notas de rodapé na monografia)
│   ├── fontes_e_lacunas.md         pendências de fontes
│   └── notas_pontos_futuros.md     ideias e pontos abertos
│
├── 01_pesquisa/                ← MDs de pesquisa (fonte do conteúdo do .tex)
│   ├── etapa1_fundamentacao/       A1.1 a A1.6 + revisão narrativa
│   ├── etapa2_engenharia/          A2.0, B1 a B6 + análises estruturais
│   └── _buscas_brutas/             saídas JSON de buscas (rastreabilidade)
│
├── 02_latex/                   ← monografia LaTeX (USPSC 3.2)
│   ├── uspsc-3.2/                  pacote oficial baixado
│   ├── main.tex                    arquivo raiz da monografia (a criar na Fase 5)
│   ├── pre-textuais/               capa, folha de rosto, dedicatória, resumo
│   ├── capitulos/                  capítulos do desenvolvimento
│   ├── pos-textuais/               referências, apêndices, anexos
│   ├── figuras/                    imagens incluídas pelo .tex (cópia de 05_figuras)
│   ├── tabelas/                    tabelas em .tex (se separadas)
│   └── bib/                        referências BibTeX
│
├── 03_codigo/                  ← código computacional do TCC
│   ├── pipeline/                   estágios do pipeline E0 → E4
│   │   ├── E0_ingestao/                cartão SD, RTSP, sincronização
│   │   ├── E1_deteccao/                MegaDetector v6, YOLO11n
│   │   ├── E2_classificacao/           SpeciesNet, classificador local
│   │   ├── E2_6_preprocessamento/      crops, normalização, filtros
│   │   ├── E3_reid/                    MiewID, MegaDescriptor, PPGNet-Cat
│   │   └── E4_persistencia/            SQLite, Camtrap-DP, hnswlib
│   ├── notebooks/                  Jupyter para exploração e gráficos
│   ├── scripts/                    CLIs utilitários (ingestão, export, etc.)
│   ├── tests/                      testes unitários (pytest)
│   └── configs/                    YAMLs de configuração por experimento
│
├── 04_dados/                   ← dados (gerenciados via DVC)
│   ├── raw/                        dados originais imutáveis
│   ├── interim/                    transformações intermediárias
│   ├── processed/                  pronto para modelagem e relatório
│   ├── external/                   datasets de terceiros (PetFace, etc.)
│   └── schemas/                    Camtrap-DP, JSON Schemas, DDL SQLite
│
├── 05_figuras/                 ← figuras geradas (PNG/SVG/PDF)
│   ├── diagramas_pipeline/         ASCII → SVG do pipeline
│   ├── diagramas_arquitetura/      camadas, deploys, sequência
│   ├── er_chen/                    ER Chen do banco
│   ├── dfd/                        Data Flow Diagrams
│   ├── mapas/                      mapas do Campus 2 com pontos
│   ├── graficos_resultados/        plots de métricas, ablação
│   └── fotos_campo/                fotos do kit, dos pontos (placeholders)
│
├── 06_manuais/                 ← manuais operacionais (anexos da monografia)
│   ├── voluntario_aex/             procedimento 15 passos, kit, formulários
│   ├── pesquisador/                ingestão, treino, validação, deploy
│   └── mantenedor_ti/              backup, restauração, controle de acesso
│
├── 07_anexos/                  ← documentos auxiliares
│   ├── autorizacoes/               CEUA, Prefeitura do Campus, AEX, LGPD
│   ├── datasheets/                 PDFs de câmeras, sensores, baterias
│   └── protocolos_referencia/      Lifeplan, Saving Nature, NTCA, GBIF
│
├── 08_modelos/                 ← pesos e exports de modelos
│   ├── pesos/                      checkpoints baixados (não-versionado)
│   └── exports/                    ONNX, TorchScript para deploy
│
└── 09_artefatos_entrega/       ← saídas finais consolidadas
                                    (PDF do TCC, slides, vídeos, posters)
```

---

## 3. Convenções

### 3.1 Nomenclatura

- **Pastas**: `snake_case`, sem espaços ou acentos.
- **Arquivos Markdown de pesquisa**: prefixo de bloco (`A1.1_`, `B2_parte1_`).
- **Arquivos de código**: `snake_case.py`, módulos curtos e específicos.
- **Datasets externos**: subpasta dedicada em `04_dados/external/`.
- **Pesos de modelo**: nome canônico do modelo (ex.: `megadetector_v6c.pt`).

### 3.2 Atores e perfis (fixados na revisão v2)

- **Atores**: `Voluntário-AEX`, `Pesquisador`, `Mantenedor-TI`, `equipe veterinária parceira`, `Gestores do campus`, `Comunidade do campus`.
- **Perfis operacionais de ponto**: `OFF-SD`, `NET`, `AC`, `AC+NET`.
- **Princípio arquitetural**: pipeline E1–E4 é **agnóstico ao perfil**.

Ver `00_governanca/glossario_notas_rodape.md` para definições completas.

### 3.3 Placeholders

Marcadores `[PLACEHOLDER-*]` no texto indicam informação dependente de coleta/decisão. Ver inventário em `00_governanca/CHANGELOG_revisao_v2.md` §4.

### 3.4 Citações

- **Markdown** (pesquisa): citações inline em formato `[Nome (ano)](url)`.
- **LaTeX** (monografia): BibTeX em `02_latex/bib/referencias.bib`, citações com `\cite{}`.

---

## 4. Ferramentas e ambiente

### 4.1 Python (código do pipeline)

- Gerenciador de ambiente: **[uv](https://docs.astral.sh/uv/)** (lockfile reprodutível).
- Versão: **Python 3.11+**.
- Principais dependências: PyTorch 2.4+, OpenCV 4.10+, Ultralytics 8.3+, hnswlib, SQLAlchemy, Streamlit, Plotly, Folium, DVC, MLflow.
- Instalação: `uv sync` na raiz do repositório.

### 4.2 LaTeX (monografia)

- Template: **USPSC 3.2** ([download oficial](http://biblioteca.puspsc.usp.br/index.php/pacote-uspsc-modelo-para-teses-e-dissertacoes-em-latex/) | [Overleaf](https://www.overleaf.com/latex/templates/pacote-uspsc-modelos-de-trabalhos-de-academicos-em-latex-versao-3-dot-2-campus-usp-de-sao-carlos/ydqymxwkgcnn)).
- Compilação local: VS Code + LaTeX Workshop (no Linux Mint do Pesquisador).
- Bibliografia: BibTeX (não biber, conforme USPSC padrão).

### 4.3 Versionamento

- **Git** para código e texto (.md, .tex).
- **DVC** para dados em `04_dados/` e pesos em `08_modelos/pesos/`.
- **GitHub** público ao final do TCC (licença MIT ou Apache 2.0).

### 4.4 Reprodutibilidade

- Experimentos rastreados em **MLflow** (`03_codigo/notebooks/.mlruns/`).
- Configurações de cada run em `03_codigo/configs/*.yaml`.
- Pipeline reproduzível via `dvc repro` (a definir na Fase 5).

---

## 5. Fluxo de trabalho recomendado

```
[ pesquisa ]        →   01_pesquisa/*.md (fonte)
       │
       ▼
[ engenharia ]      →   01_pesquisa/etapa2_engenharia/B*.md (decisões)
       │
       ▼
[ implementação ]   →   03_codigo/pipeline/E*/  (rodando no notebook)
       │                03_codigo/configs/*.yaml
       │
       ▼
[ experimentos ]    →   03_codigo/notebooks/*.ipynb (MLflow)
       │                04_dados/processed/
       │
       ▼
[ figuras / tabelas]→   05_figuras/ (gerados por notebook)
       │                02_latex/tabelas/
       │
       ▼
[ monografia ]      →   02_latex/main.tex
       │                02_latex/capitulos/*.tex (migração dos MDs)
       │
       ▼
[ entrega ]         →   09_artefatos_entrega/tcc_final.pdf
                        09_artefatos_entrega/slides_defesa.pdf
```

---

## 6. Documentos-chave para começar

1. **`00_governanca/diretrizes_projeto.md`** — diretrizes vinculantes do TCC.
2. **`00_governanca/CHANGELOG_revisao_v2.md`** — histórico completo da revisão v2.
3. **`01_pesquisa/etapa2_engenharia/A2.0_requisitos_sistema.md`** — requisitos funcionais, não-funcionais e restrições.
4. **`01_pesquisa/etapa2_engenharia/B1_contexto_operacional.md`** — contexto Campus 2.
5. **`01_pesquisa/etapa2_engenharia/B2_pipeline_visao_computacional_parte1.md`** — pipeline E0/E1.

---

## 7. Próximas fases (TODO)

- [ ] **Fase 2** (em conclusão) — reorganização de pastas.
- [ ] **Fase 3** — sumário detalhado da monografia (mapeamento Bloco→Capítulo).
- [ ] **Fase 4** — TODO mestre executável (fichamento, código, autorizações).
- [ ] **Fase 5** — draft LaTeX completo (capítulos esqueleto migrando os MDs).

---

## 8. Como esta estrutura foi gerada

Esta estrutura é a saída da **Fase 2 da revisão v2** (14/maio/2026), conduzida em diálogo com o Pesquisador para refletir:

- Padrões de projetos científicos reprodutíveis em ciência de dados.
- Convenções ABNT/USPSC para trabalhos acadêmicos.
- Separação clara entre **pesquisa** (fonte textual), **engenharia** (decisões de sistema), **implementação** (código), **dados**, **artefatos visuais**, **manuais operacionais**, **anexos** e **entrega**.

A estrutura é **viva** e pode ser ajustada conforme o TCC avança — qualquer mudança deve ser registrada em `00_governanca/CHANGELOG_revisao_v2.md`.

---

> **Autor**: Felipi Adenildo Soares Sousa
> **Orientador**: Prof. Dr. Matheus Machado dos Santos
> **Instituição**: ICMC/USP São Carlos
