# Migração: estrutura antiga `revisao_tcc/` → estrutura nova `tcc_gatos_campus2/`

> Data: 14/maio/2026 (Fase 2 da revisão v2).
> Objetivo: rastrear o destino de cada arquivo da estrutura antiga (revisão) na nova estrutura do projeto completo.

---

## 1. Tabela de mapeamento

| Origem (revisao_tcc/) | Destino (tcc_gatos_campus2/) | Observação |
|---|---|---|
| `_changelog_revisao_v2.md` | `00_governanca/CHANGELOG_revisao_v2.md` | Renomeado com prefixo `CHANGELOG_` |
| `_transversais/diretrizes_projeto.md` | `00_governanca/diretrizes_projeto.md` | |
| `_transversais/alinhamento_projeto_base.md` | `00_governanca/alinhamento_projeto_base.md` | |
| `_transversais/glossario_notas_rodape.md` | `00_governanca/glossario_notas_rodape.md` | |
| `_transversais/fontes_e_lacunas.md` | `00_governanca/fontes_e_lacunas.md` | |
| `_transversais/notas_pontos_futuros.md` | `00_governanca/notas_pontos_futuros.md` | |
| `etapa1/A1.1_fundamentos_CED_TNR.md` | `01_pesquisa/etapa1_fundamentacao/A1.1_fundamentos_CED_TNR.md` | |
| `etapa1/A1.2_evidencias_e_criticas.md` | `01_pesquisa/etapa1_fundamentacao/A1.2_evidencias_e_criticas.md` | |
| `etapa1/A1.3_camera_trapping.md` | `01_pesquisa/etapa1_fundamentacao/A1.3_camera_trapping.md` | |
| `etapa1/A1.4_visao_computacional_fauna_felinos.md` | `01_pesquisa/etapa1_fundamentacao/A1.4_visao_computacional_fauna_felinos.md` | Revisado v2 (Fase 1.5) |
| `etapa1/A1.5_conservacao_zoonoses_bem_estar.md` | `01_pesquisa/etapa1_fundamentacao/A1.5_conservacao_zoonoses_bem_estar.md` | |
| `etapa1/A1.6_catalogo_datasets_projetos.md` | `01_pesquisa/etapa1_fundamentacao/A1.6_catalogo_datasets_projetos.md` | |
| `etapa1/_revisao_fase1_etapa1.md` | `01_pesquisa/etapa1_fundamentacao/_revisao_fase1_etapa1.md` | |
| `etapa2/A2.0_requisitos_sistema.md` | `01_pesquisa/etapa2_engenharia/A2.0_requisitos_sistema.md` | Revisado v2 (Fases 1.4 e 1.5) |
| `etapa2/B1_contexto_operacional.md` | `01_pesquisa/etapa2_engenharia/B1_contexto_operacional.md` | Revisado v2 (Fase 1.2) |
| `etapa2/B2_pipeline_visao_computacional_parte1.md` | `01_pesquisa/etapa2_engenharia/B2_pipeline_visao_computacional_parte1.md` | Revisado v2 (Fases 1.3 e 1.5) |
| `etapa2/B2_pipeline_visao_computacional_parte2.md` | `01_pesquisa/etapa2_engenharia/B2_pipeline_visao_computacional_parte2.md` | Revisado v2 (Fases 1.3 e 1.5) |
| `etapa2/B2_pipeline_visao_computacional_parte3.md` | `01_pesquisa/etapa2_engenharia/B2_pipeline_visao_computacional_parte3.md` | Revisado v2 (Fases 1.3 e 1.5) |
| `etapa2/B3_tradeoffs_espaco_design_parte1.md` | `01_pesquisa/etapa2_engenharia/B3_tradeoffs_espaco_design_parte1.md` | A revisar |
| `etapa2/B3_tradeoffs_espaco_design_parte2.md` | `01_pesquisa/etapa2_engenharia/B3_tradeoffs_espaco_design_parte2.md` | A revisar |
| `etapa2/B4_arquitetura_referencia_parte1.md` | `01_pesquisa/etapa2_engenharia/B4_arquitetura_referencia_parte1.md` | A revisar |
| `etapa2/B4_arquitetura_referencia_parte2.md` | `01_pesquisa/etapa2_engenharia/B4_arquitetura_referencia_parte2.md` | A revisar |
| `etapa2/B5_validacao_implementacao_parte1.md` | `01_pesquisa/etapa2_engenharia/B5_validacao_implementacao_parte1.md` | A revisar |
| `etapa2/B5_validacao_implementacao_parte2.md` | `01_pesquisa/etapa2_engenharia/B5_validacao_implementacao_parte2.md` | A revisar |
| `etapa2/B5_validacao_implementacao_parte3.md` | `01_pesquisa/etapa2_engenharia/B5_validacao_implementacao_parte3.md` | A revisar |
| `etapa2/B6_consolidacao_parte1_sintese_tecnica.md` | `01_pesquisa/etapa2_engenharia/B6_consolidacao_parte1_sintese_tecnica.md` | A revisar |
| `etapa2/B6_consolidacao_parte2_anexos_operacionais.md` | `01_pesquisa/etapa2_engenharia/B6_consolidacao_parte2_anexos_operacionais.md` | A revisar |
| `etapa2/BlocoH_Hardware.md` | `01_pesquisa/etapa2_engenharia/BlocoH_Hardware.md` | Anexo de hardware |
| `etapa2/_analise_estrutural.md` | `01_pesquisa/etapa2_engenharia/_analise_estrutural.md` | Documento de análise |
| `etapa2/_plano_etapa2.md` | `01_pesquisa/etapa2_engenharia/_plano_etapa2.md` | Plano da etapa |
| `_buscas/*.json` (26 arquivos) | `01_pesquisa/_buscas_brutas/*.json` | Rastreabilidade das buscas |

---

## 2. Diretórios criados (vazios, com `.gitkeep`)

Estes diretórios são preparações para conteúdo futuro do projeto:

- `02_latex/*` — espaço para template USPSC 3.2 e capítulos da monografia (Fase 5)
- `03_codigo/pipeline/E*` — implementação dos estágios E0 a E4
- `03_codigo/{notebooks, scripts, tests, configs}` — código de apoio
- `04_dados/{raw, interim, processed, external, schemas}` — dados gerenciados via DVC
- `05_figuras/*` — figuras geradas (diagramas, ER, DFD, mapas, gráficos)
- `06_manuais/{voluntario_aex, pesquisador, mantenedor_ti}` — anexos operacionais
- `07_anexos/{autorizacoes, datasheets, protocolos_referencia}` — documentos auxiliares
- `08_modelos/{pesos, exports}` — pesos e exports de modelos
- `09_artefatos_entrega/` — saídas finais (PDF, slides, etc.)

---

## 3. Arquivos novos criados (não vieram da revisão)

| Arquivo | Função |
|---|---|
| `README.md` (raiz) | Visão geral do projeto, estrutura, ferramentas, fluxo de trabalho |
| `pyproject.toml` | Dependências Python (uv) |
| `.gitignore` | Padrões de exclusão Git (cobre Python, Jupyter, LaTeX, MLflow, DVC, SO, IDE) |
| `.gitattributes` | Normalização de line-endings e identificação de binários |
| `00_governanca/README.md` | Guia da pasta de governança |
| `01_pesquisa/README.md` | Guia da pasta de pesquisa |
| `02_latex/README.md` | Guia do LaTeX + instruções de compilação |
| `03_codigo/README.md` | Guia do código + setup uv |
| `04_dados/README.md` | Política de dados + setup DVC |
| `05_figuras/README.md` | Convenções de figuras |
| `06_manuais/README.md` | Guia dos manuais operacionais |
| `07_anexos/README.md` | Guia dos anexos |
| `08_modelos/README.md` | Inventário esperado de pesos + licenças |
| `09_artefatos_entrega/README.md` | Política de entrega final |

---

## 4. Verificação de integridade

Após a migração:

- **Total de MDs migrados**: 31 (6 transversais → governança; 7 etapa1; 17 etapa2; 1 changelog renomeado).
- **Total de JSONs migrados**: 26 (todos de `_buscas/`).
- **Total de READMEs novos**: 10 (raiz + 9 seções).
- **Arquivos de configuração novos**: 3 (`.gitignore`, `.gitattributes`, `pyproject.toml`).

---

## 5. Próximos passos no PC do Pesquisador

1. Descompactar o `.zip` em local definitivo (sugerido: `~/projetos/tcc-gatos-campus2/`).
2. Inicializar Git: `git init && git add . && git commit -m "Estrutura inicial da v2"`.
3. Instalar uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
4. Sincronizar ambiente Python: `uv sync` (na raiz).
5. Baixar o pacote USPSC 3.2 e colocar em `02_latex/uspsc-3.2/` (você já tem baixado).
6. Configurar repositório remoto no GitHub (privado até a defesa).
7. Inicializar DVC: `dvc init` e configurar storage remoto.
