# Relatorio de Smoke Test (Felinet) -- v5

Executado em 2026-05-27T04:17:14.475696+00:00.  Duracao total: 129.9s.

**Passos:** 25/25 OK  |  **Falhas obrigatorias:** 0  |  **Artefatos:** 21/24 (obrigatorios: 20/20)

Config: perfil=`dev`, N_pipeline=30, N_reid=50, fonte_reid=petface_mini, fontes_op=['kaggle_cats', 'felidae'].

## Passos executados

| # | Passo | Status | Obrig | Duracao | Comando |
|---|-------|--------|-------|---------|---------|
| 1 | ruff check | OK | sim | 0.2s | `/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/.venv/bin/python -m ruff check src/ tests/` |
| 2 | pytest | OK | sim | 13.6s | `/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/.venv/bin/python -m pytest -q --tb=no` |
| 3 | dev validar-ambiente | OK | opt | 3.6s | `felinet dev validar-ambiente` |
| 4 | dev preparar-petface-mini [sintetico 20x4] | OK | sim | 0.7s | `felinet dev preparar-petface-mini --individuos 20 --imagens-por-id 4` |
| 5 | pipeline executar [kaggle_cats] | OK | sim | 32.0s | `felinet pipeline executar --perfil dev --fonte kaggle_cats --max-amostras 30 --seed-amostragem 42 --dev` |
| 6 | pipeline executar [felidae] | OK | sim | 37.2s | `felinet pipeline executar --perfil dev --fonte felidae --max-amostras 30 --seed-amostragem 42 --dev` |
| 7 | reid extrair-embeddings [petface_mini n=50] | OK | sim | 12.9s | `felinet reid extrair-embeddings --perfil dev --fonte petface_mini --n 50` |
| 8 | reid avaliar-closed | OK | sim | 3.7s | `felinet reid avaliar-closed --perfil dev --fonte petface_mini --n 50` |
| 9 | reid avaliar-openset | OK | sim | 3.9s | `felinet reid avaliar-openset --perfil dev --fonte petface_mini --n 50` |
| 10 | tabelas reid-resumo | OK | opt | 0.4s | `felinet tabelas reid-resumo --perfil dev` |
| 11 | tabelas openset-resumo | OK | opt | 0.4s | `felinet tabelas openset-resumo --perfil dev` |
| 12 | tabelas fontes-resumo | OK | sim | 0.5s | `felinet tabelas fontes-resumo --perfil dev` |
| 13 | tabelas comparativo-fontes | OK | sim | 0.6s | `felinet tabelas comparativo-fontes --perfil dev` |
| 14 | tabelas datasets-avaliados | OK | sim | 0.4s | `felinet tabelas datasets-avaliados --perfil dev` |
| 15 | tabelas run-inventory | OK | sim | 0.5s | `felinet tabelas run-inventory --perfil dev` |
| 16 | figuras comparativo-fontes | OK | sim | 3.4s | `felinet figuras comparativo-fontes --perfil dev --fontes kaggle_cats,felidae` |
| 17 | figuras matriz-confusao-fontes | OK | opt | 1.3s | `felinet figuras matriz-confusao-fontes --perfil dev` |
| 18 | figuras reid-cmc | OK | sim | 2.4s | `felinet figuras reid-cmc --perfil dev --fonte petface_mini --n 50` |
| 19 | figuras matriz-similaridade | OK | sim | 2.8s | `felinet figuras matriz-similaridade --perfil dev --fonte petface_mini --n 50` |
| 20 | figuras dist-intra-inter | OK | sim | 2.5s | `felinet figuras dist-intra-inter --perfil dev --fonte petface_mini --n 50` |
| 21 | figuras roc-openset | OK | sim | 2.4s | `felinet figuras roc-openset --perfil dev --fonte petface_mini --n 50` |
| 22 | figuras galeria-erros | OK | opt | 1.3s | `felinet figuras galeria-erros --perfil dev --fonte petface_mini --n 50` |
| 23 | figuras cmc-comparativo | OK | sim | 2.3s | `felinet figuras cmc-comparativo --perfil dev --fonte petface_mini --ns 50` |
| 24 | dev gerar-resumo-html [kaggle_cats] | OK | sim | 0.4s | `felinet dev gerar-resumo-html --fonte kaggle_cats --perfil dev` |
| 25 | dev gerar-resumo-html [felidae] | OK | sim | 0.4s | `felinet dev gerar-resumo-html --fonte felidae --perfil dev` |

## Artefatos da monografia

| Descricao | Caminho | Obrig | Presente | Tamanho |
|-----------|---------|-------|----------|---------|
| Bloco 6 -- fontes resumo | `artifacts/tabelas/operacional/_global/fontes_resumo.csv` | sim | sim | 134 B |
| Bloco 6 -- fontes resumo (TeX) | `artifacts/tabelas/operacional/_global/fontes_resumo.tex` | sim | sim | 420 B |
| Bloco 6 -- comparativo entre fontes | `artifacts/tabelas/operacional/_global/comparativo_fontes.csv` | sim | sim | 168 B |
| Bloco 6 -- comparativo (TeX) | `artifacts/tabelas/operacional/_global/comparativo_fontes.tex` | sim | sim | 589 B |
| Tabela datasets avaliados | `artifacts/tabelas/datasets_avaliados.csv` | sim | sim | 800 B |
| Inventario de runs | `artifacts/tabelas/_inventario/run_inventory.csv` | sim | sim | 564 B |
| Tabela Re-ID closed-set | `artifacts/tabelas/metodologico/petface_mini/reid_resumo.csv` | sim | sim | 88 B |
| Tabela Re-ID open-set | `artifacts/tabelas/metodologico/petface_mini/openset_resumo.csv` | sim | sim | 116 B |
| Bloco 7 -- figura comparativo-fontes | `artifacts/figuras/operacional/_global/comparativo_fontes.*` | sim | sim | 202660 B |
| Bloco 9 -- matriz confusao (PNG) | `artifacts/figuras/operacional/_global/matriz_confusao_fontes.png` | opt | NAO | - |
| Bloco 9 -- matriz confusao (CSV) | `artifacts/figuras/operacional/_global/matriz_confusao_fontes.csv` | opt | NAO | - |
| Re-ID -- curva CMC | `artifacts/figuras/metodologico/petface_mini/n0050/reid_cmc.png` | sim | sim | 63453 B |
| Re-ID -- heatmap de similaridade | `artifacts/figuras/metodologico/petface_mini/n0050/reid_matriz_sim.png` | sim | sim | 92669 B |
| Re-ID -- distribuicoes intra vs inter | `artifacts/figuras/metodologico/petface_mini/n0050/reid_dist_intra_inter.png` | sim | sim | 103886 B |
| Re-ID -- ROC open-set | `artifacts/figuras/metodologico/petface_mini/openset_n0050/reid_roc_openset.png` | sim | sim | 144003 B |
| Re-ID -- CMC comparativo (varios N) | `artifacts/figuras/metodologico/petface_mini/reid_cmc_comparativo.png` | sim | sim | 74254 B |
| Re-ID -- galeria de 5 piores | `artifacts/figuras/metodologico/petface_mini/n0050/reid_galeria_erros.png` | opt | NAO | - |
| metricas.json Re-ID closed-set | `runs/metodologico/petface_mini/dev/n0050/*/metricas.json` | sim | sim | 786 B |
| metricas.json Re-ID open-set | `runs/metodologico/petface_mini/dev/openset_n0050/*/metricas.json` | sim | sim | 3792 B |
| Galeria visual dev -- kaggle_cats | `runs/operacional/kaggle_cats/dev/_/**/dev_visualizacao/` (2 arq) | sim | sim | 4096 B |
| resumo.html -- kaggle_cats | `runs/operacional/kaggle_cats/dev/_/**/dev_visualizacao/resumo.html` (2 arq) | sim | sim | 3188 B |
| Galeria visual dev -- felidae | `runs/operacional/felidae/dev/_/**/dev_visualizacao/` (2 arq) | sim | sim | 4096 B |
| resumo.html -- felidae | `runs/operacional/felidae/dev/_/**/dev_visualizacao/resumo.html` (2 arq) | sim | sim | 3184 B |
| Especs do ambiente (monografia) | `runs/_ambiente/latest.md` | opt | sim | 983 B |

## Metricas-chave (metricas.json latest)

### reid_closed_set

Origem: `runs/metodologico/petface_mini/dev/n0050/f8a821f/metricas.json`
- `relatorio.top_k.1`: 1.0
- `relatorio.top_k.5`: 1.0
- `relatorio.top_k.10`: 1.0
- `relatorio.mAP`: 0.8491834554334554
- `n_query`: 20
- `n_galeria`: 60

### reid_open_set

Origem: `runs/metodologico/petface_mini/dev/openset_n0050/f8a821f/metricas.json`
- `auc_media`: 0.9
- `auc_desvio`: 0.11135528725660043
- `n_seeds`: None


## Conclusao

Projeto saudavel: todos os passos e artefatos obrigatorios OK.
Pronto para o experimento definitivo (N maior).
