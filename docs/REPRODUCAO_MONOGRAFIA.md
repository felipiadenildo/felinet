# Reprodução da monografia

Tudo o que a monografia mostra a partir de dados (figuras e tabelas) é escrito pelo felinet em
`monografia-felinet/elementos/gerados/`. Nada ali é editado à mão.

```
runs da execução final ──► felinet monografia gerar ──► monografia/elementos/gerados/{cap3,cap4,cap5,apendice_e}/
(+ imagens, fotos)          (registro: src/felinet/        + MANIFESTO.json (sha256, entradas, commit)
                             monografia/elementos.py)       + LEIAME.md (mapa rótulo → arquivo → função)
```

## Navegar entre a monografia e o código

| Quero saber… | Onde olhar |
|---|---|
| de onde sai a Figura/Tabela X | `elementos/gerados/LEIAME.md` na monografia, ou o Apêndice F (Tabela "Origem de cada figura…") no PDF |
| qual função desenha | coluna "Função" do mapa → `src/felinet/monografia/{graficos,exemplos,tabelas}.py` |
| quais dados entraram | `elementos/gerados/MANIFESTO.json` → `entradas` (arquivos dos runs com sha256) |
| com qual versão do felinet | `MANIFESTO.json` → `commit` e `alteracoes_nao_commitadas` |
| o que falta gerar nesta máquina | `felinet monografia listar` |
| se o texto e os dados ainda batem | `felinet monografia verificar --runs <runs>` |

No `.tex`, as figuras geradas entram por `\gerado{cap5/arquivo.pdf}` e as tabelas por
`\input{elementos/gerados/cap5/tab_...}`; legenda, rótulo e texto ficam no capítulo. Enquanto um arquivo não existe
(figuras que dependem do ambiente original), `\gerado` mostra um quadro "Pendente" no lugar.

Desenhos que não vêm de dados ficam na monografia: TikZ em `elementos/diagramas/tikz/` (Figs. de posicionamento da
câmera, funil, Fase IV e closed/open-set) e o diagrama completo em `elementos/diagramas/diagrama_completo_sistema.drawio`
(exportado por `make diagramas` na monografia).

## Gerar

Caminhos padrão em `configs/monografia.yaml` (monografia em `../monografia-felinet`, runs em `runs/`, fotos em
`data/exemplos/fauna_campus2`).

```bash
make monografia                          # = felinet monografia gerar && felinet monografia verificar
felinet monografia gerar --so cap5/reid_cmc.pdf      # um elemento (arquivo ou rótulo do LaTeX)
```

Cada elemento declara o que precisa; sem isso ele fica **pendente** (não é erro):

| Requisito | O que é | Onde obter |
|---|---|---|
| `runs` | runs da execução final (`operacional/`, `metodologico/`, `complementar/`) | pacote da execução final (ver runbook) |
| `imagens` | as imagens referenciadas pelos runs operacionais | no ambiente original, nos caminhos gravados; fora dele, `felinet datasets reconstruir-run` + `substituir` |
| `fotos` | 36 fotos do iNaturalist (Cap. 3) | `python scripts/baixar_exemplos_inat.py data/exemplos/fauna_campus2 docs/exemplos/fauna_campus2/registro.json` |
| `petface` | imagens do PetFace citadas nos embeddings | ambiente original, ou `felinet datasets extrair-petface` (lê o `cat.tar.gz` oficial em fluxo e grava só as 576 imagens) |
| `umap` | run de `felinet experimentos visualizacao-exploratoria` | já incluído no pacote de runs (gerado em CPU no servidor); para refazer, CatIndividualImages do Kaggle |

Os runs guardam caminhos absolutos da máquina original. Em outra máquina, mapeie o prefixo em
`configs/monografia.yaml → substituir` (ou `--substituir ANTIGO=NOVO`):

| Prefixo gravado nos runs | Conteúdo |
|---|---|
| `/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/data/raw/camera_trap` | imagens do `kaggle_cats` e do Felidae |
| `/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/data/raw/reid/petface/images` | galeria do PetFace |
| `/media/felipi/ssd/dados_tcc/PetFace/images` | consultas do PetFace |

### Reconstruir as imagens dos runs (sem GPU, sem credenciais)
As duas fontes operacionais são públicas e cada imagem é conferida pelo SHA-256 do manifesto do run:
```bash
python -c "import kagglehub; print(kagglehub.dataset_download('samuelayman/cat-dataset'))"   # sem login
felinet datasets reconstruir-run --run <run kaggle_cats> --fonte kaggle_cats --origem <pasta acima> --destino $IMG/kaggle_cats
felinet datasets reconstruir-run --run <run felidae> --fonte felidae --destino $IMG/felidae     # LILA BC
```

## Números citados no texto (fora das tabelas)

| No texto | Comando |
|---|---|
| caixas de pessoa e veículo; caixas de animal com top-1 "vazio" | `felinet monografia resumo-caixas --runs $RUNS --fonte kaggle_cats` (e `felidae`) |
| animais anotados sem caixa de animal | `felinet monografia deteccao-anotada --runs $RUNS --anotacoes <cat-dataset>/cat/labels [--limiar-iou 0.3]` |
| vizinho mais próximo do mesmo gato na projeção UMAP (Apêndice E) | `felinet monografia vizinhos-umap --runs $RUNS` |
| Tab. 11 (síntese por fase) | texto, a partir das Tabs. 8 a 10 |

## Refazer os runs da execução final (GPU)

Só é preciso para mudar um resultado; para gerar as figuras basta o pacote de runs. Os comandos são os gravados em
`manifest.json → extras` de cada run:

```bash
make execucao-final
# = felinet pipeline executar --perfil dev --fonte {kaggle_cats,felidae} --tag monografia_n300 \
#       --max-amostras 300 --seed-amostragem 42 --dev
#   + para N em 50,100,200: felinet reid extrair-embeddings / avaliar-closed / avaliar-openset --seeds 42,7,123
```

Os experimentos complementares (`runs/complementar/`) foram executados no protótipo `felinet_mono` e importados; o
porte está em `felinet experimentos cascatas-multifonte` e `sensibilidade-limiar` (reproduz a tabela para
`cats_vs_dogs` e `inat_br_cats`; ver `docs/runbooks/gerar_monografia_ambiente_original.md`).

## Validação
```bash
make qualidade                 # ruff + pytest (inclui tests/test_monografia.py, com runs sintéticos)
felinet monografia verificar   # .tex x registro x manifesto (+ tabelas x runs, se houver runs)
```
