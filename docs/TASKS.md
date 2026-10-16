# TASKS: felinet v0.4 (revisão pós-defesa)

Origem: `~/code/estudos/10-felinet/PROPOSTA.md` (aprovada em 2026-10-15). A monografia é a referência: o felinet se
ajusta a ela. Testes leves no servidor (sem GPU); geração completa no ambiente original
(`requirements/ambiente-original.txt`). Tarefas da monografia com prefixo `M-`.

## Feito (2026-10-15)
- [x] **F9** (2026-10-15, 3ª rodada) Um caminho só para a monografia: pacote `felinet.monografia` (registro
  `elementos.py`, `graficos.py`, `exemplos.py`, `tabelas.py`, `producao.py`) e `felinet monografia {listar,gerar,verificar}`.
  Figuras **e tabelas** vão para `monografia/elementos/gerados/` com `MANIFESTO.json` (entradas com sha256, commit) e
  `LEIAME.md`; a monografia usa `\gerado{}`/`\input{}`. Removidos `felinet figuras`, `felinet tabelas`,
  `felinet relatorio`, `scripts/orquestrar_monografia.py`, `monografia.json`, `organizar_*.py`, `artifacts/`.
  Verificação: as 11 figuras regeradas são idênticas pixel a pixel às anteriores (a de amostras muda só o rótulo
  `kaggle_cats`); `verificar` OK contra os runs; testes em `tests/test_monografia.py`. (Os comandos `relatorio ...`
  citados abaixo são da fase anterior e foram substituídos por este.)
- [x] **F0.1** `comandos/figuras.py` restaurado (apagado por engano em `e253207`); CLI volta a importar. Verificação: `felinet --help`, 184 testes.
- [x] **F0.2** Código morto removido: `*_patch.py`, `instalar_figuras_cap5.sh`.
- [x] **F0.3** Dependências: núcleo leve (~250 MB) × `[modelos]` × `[dev]`; sem índice CUDA forçado; versões da execução
  original em `requirements/ambiente-original.txt`. `configs/modelos.yaml`: `MDV6-yolov10-c` (o que os runs registram).
- [x] **F0.4** CI: `.github/workflows/ci.yml` (ruff + pytest em CPU).
- [x] **F2.1** `felinet relatorio figuras`: Figs. 10–15 e 17 do Cap. 5 em estilo único (`src/felinet/relatorio/`), com
  `MANIFESTO.json`; saída reprodutível byte a byte. `felinet relatorio verificar`: Tabs. 8, 11 e 12 contra os runs (OK).
- [x] **M-1** Monografia: build, diagramação, tom, E1/E2 no texto, figuras novas (ver `docs/CHANGELOG_REVISAO.md` na monografia).

- [x] **F2.2** Fig. 10 e 11 condensadas (Fases II e III sobrepostas, decisão em 3 categorias, recorte do puma) e figura
  nova de distribuições (confiança do detector × P(gato)). Leitor de caixas e recortes em `relatorio/dados.py`.
- [x] **F2.3** `felinet exemplos cascata` (Fases II e III em qualquer pasta de imagens, mesmos limiares) e
  `felinet relatorio exemplos-cascata`: exemplos do Cap. 3 com 36 fotos de fauna do Campus 2 (iNaturalist, CC),
  executado aqui em CPU (<2 min). Reprodução em `docs/exemplos/fauna_campus2/`.
- [x] **F2.4** Comandos para o notebook (imagens originais): `relatorio casos-cascata`, `relatorio exemplos-reid`,
  `relatorio amostras-datasets`, com `--substituir` para caminhos. Roteiro: `docs/runbooks/gerar_monografia_ambiente_original.md`.
- [x] **D1** decidido (v6 no texto). **D2** resolvido por evidência (`samuelayman/cat-dataset`). **D4**: runs ficam no Drive.

## Próximas (em ordem)
- [x] **F1.1** (2026-10-15) Nomes da monografia no código: sair E0/E1/E2/E3 e "Bloco 7/9" de módulos, docstrings, testes
  (`test_e0_*`, `test_e1_*`, `test_bloco9_*`, `test_comandos_*_bloco*`) e docs. Verificação:
  `grep -rnE '\bE[0-9]\b|[Bb]loco ?[0-9]' src tests docs` vazio, e testes passando.
- [x] **F1.2** (2026-10-15; validado: reproduz a Tab. 9 em `cats_vs_dogs` e `inat_br_cats`) Portar os experimentos complementares do protótipo `felinet_mono` (Drive:
  `71_TCC_Gatosdoc2/Backups_e_Snapshots_Locais_NAO_GIT/felinet-others/felinet_mono`, cópia em
  `~/code/sandbox/felinet-drive/`) para `felinet experimentos cascatas-multifonte|sensibilidade-limiar`, gravando
  `runs/complementar/` (layout em `docs/arquitetura/layout_runs.md`). Teste leve com detector e classificador falsos.
- [x] **F1.3** (código e teste; execução no notebook, runbook §5) Projeção de Visualização Exploratória com o **CatIndividualImages real** (`wildlife-datasets`,
  MegaDescriptor-T-224, `umap-learn`), sem o substituto por raças do protótipo; gera `reid_umap.pdf` (até 8 identidades
  em cor e as demais em cinza). Rodar no ambiente original (ou em CPU se o dataset for acessível).
- [x] **F3** (2026-10-15) Cap. 3 no código, com testes sintéticos:
  - Fase I: `fase1_ingestao/triagem.py` (vídeo → quadros, escuro/saturado/uniforme, deduplicação, CLAHE, balanço de
    branco, letterbox, metadados P01–P10);
  - Fase II: `fase2_deteccao/anonimizacao.py` (desfoque de pessoas aplicado antes de gravar qualquer recorte,
    limiar dia/noite, caixas mín./máx.);
  - Fase III: filtro geográfico do SpeciesNet (`pais="BRA"`) e regra opcional "rótulo genérico de felídeo → validação";
  - Fase IV: `fase4_reid/catalogo.py` (catálogo, fusão face+flanco, Top-1 com limiar e margem, novo candidato, auditoria SQLite).
- [x] **F3.y** (2026-10-15) Triagem da Fase I ligada ao `pipeline executar --triagem` (opt-in; padrão desligado para
  reproduzir a execução da monografia): grava `01_quadros/` (quadros canônicos) e `01_triagem.csv` (decisão por quadro)
  e a cascata segue sobre os quadros aceitos.
- [x] **F7** (2026-10-15, rodada de revisão das figuras) Imagens reais dos runs no servidor: `datasets reconstruir-run`
  (kaggle_cats por kagglehub, Felidae pelo LILA; 600/600 conferidas por SHA-256); `relatorio trajetorias` (Figs. 14 e
  15), `amostras-datasets` das fontes operacionais (Fig. 10), `resumo-caixas` e `deteccao-anotada` (números novos do
  Cap. 5); Fig. 8 com rótulos em português e caixas coincidentes unidas; Fig. 12 com o caso do puma de costas aceito como gato; mapa de
  reprodução em `docs/REPRODUCAO_MONOGRAFIA.md`.
- [x] **F8** (2026-10-15, 2ª rodada) Grades de exemplos com moldura 4:3 comum (`figuras_exemplos.enquadrar`) e
  recortes escuros realçados só na figura (`realcar`); Fig. 8 com exemplos sem erro de classe; caso da única aceitação
  do Felidae corrigido (puma de costas, não quadro vazio); `verificar` cita as tabelas por nome; testes em
  `tests/test_figuras_exemplos.py`.
- [x] **F5** (2026-10-15) Manuais (pesquisador, voluntário, mantenedor), `CITATION.cff`, model card `docs/MODELOS.md`
  (licenças: MegaDescriptor CC BY-NC 4.0), `docs/governanca/` → `docs/historico/`.
- [~] **F5.1** Painel para os voluntários: **fora do escopo** (decisão do autor, 2026-10-15).
- [ ] **F6** Ambiente original: regenerar os runs, `make figuras verificar` na monografia, substituir a Fig. 16.

## Decisões pendentes do dono
- [x] **D6** (2026-10-15) Linha do `felidae_wild` mantida como publicada, com a ressalva no texto (agora Tab. 14,
  Apêndice E).
- [~] **D7** SpeciesNet + CLIP: aplicada a recomendação (2026-10-15): a monografia passa a dizer que a Fase III decide
  pelo SpeciesNet e que o CLIP foi avaliado à parte, em par com o YOLOv8n; o autor pode reverter na revisão do PDF.
- [x] **D3** Diagrama do Apêndice D: editável recuperado do PNG do Drive, corrigido e exportado em PDF vetorial.
- [x] **D5** Felidae = Felidae Conservation Fund 2020–2025 (LILA BC, CDLA-Permissive 1.0), confirmado pelo autor; monografia corrigida.
- [ ] **F6.1** No notebook: rodar o runbook e trazer `exemplos_reid.pdf` (PetFace, Seção 5.3) e o UMAP real
  (`reid_umap.pdf`, Fig. 24 do Apêndice E, hoje provisória); opcional, amostras das bases da Fase IV. Depois,
  escrever na monografia o texto dessas figuras (runbook §6).
