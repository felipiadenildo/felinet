# Migração v0.2.x → v0.3.0 (release candidate v23)

Documento de governança que registra as mudanças entre a versão anterior
(0.2.x, branch ``refactor/layout-runs``) e a release v0.3.0 (branch
``refactor/v23-release-candidate``). O leitor que vier de uma versão
anterior precisa apenas seguir as seções abaixo para reproduzir o estado
esperado.

## Sumário executivo

A release consolida o layout-runs introduzido na 0.2.x, fecha os
hotfixes pendentes da validação de smoke, adiciona o sistema de
*datasets locais* declarativo, expõe o modo ``--dev`` com galeria visual
e cria o wizard interativo ``felinet easyrun``. A documentação técnica
foi reescrita em quatro arquivos novos (ARQUITETURA, DEBUGGING,
REPRODUCAO_MONOGRAFIA, DATASETS) e o pacote sobe para 0.3.0.

## Mudanças no código

A função ``felinet.config._resolver_path`` passou a aceitar
``str | dict``. Quando recebe um dict, lê a chave ``raiz`` (preferida) ou
``path`` (compatibilidade); demais chaves são tratadas como metadados.
Esse ajuste desbloqueia a entrada ``felidae`` em ``configs/paths.yaml``,
que já estava no formato ``{raiz, tipo}``.

O comando ``felinet pipeline executar`` ganhou três opções novas:
``--max-amostras`` (limite de imagens, com amostragem determinística),
``--seed-amostragem`` (seed correspondente, default 42) e ``--dev`` (modo
visual). O orquestrador propaga essas opções para o helper
``_amostrar_deterministico`` e para o módulo ``felinet.pipeline.dev_visual``,
que cria ``runs/.../dev_visualizacao/`` com CSVs por fase
(``01_ingestao/motivos.csv``, ``02_deteccao/deteccoes.csv``,
``03_classificacao/classificacoes.csv``).

A função ``gerar_manifesto`` em ``felinet.pipeline.fase1_ingestao.manifesto``
passou a aceitar um argumento opcional ``midias=list[Path]``. Quando
fornecido, usa a lista pré-amostrada em vez de varrer o disco; mantém
compatibilidade total quando omitido.

## Comandos novos

A CLI expõe seis novos subcomandos. ``felinet datasets linkar`` cria os
symlinks em ``data/raw/`` a partir de ``configs/datasets_locais.yaml``;
``felinet datasets listar`` mostra status (✓ linkado, ✗ caminho quebrado,
⚠ caminho ausente, — não linkado) por dataset. ``felinet figuras
comparativo-fontes`` materializa o Bloco 7 da monografia; ``felinet
figuras matriz-confusao-fontes`` registra o esqueleto do Bloco 9 (sem
ground truth por imagem, retorna aviso). ``felinet dev demo`` é um atalho
para ``pipeline executar --max-amostras N --dev``. ``felinet easyrun`` é
o wizard interativo (TUI) recomendado para usuários novos.

## Módulos novos

``src/felinet/datasets/registro.py`` centraliza o modelo declarativo de
datasets (dataclass ``DatasetLocal``, mapeamentos ``FASES_POR_TIPO`` e
``CATEGORIA_POR_TIPO``, validador ``validar_fase_aplicavel``).
``src/felinet/datasets/iteradores.py`` expõe os iteradores por layout e o
dispatcher ``iterador_para_layout``. ``src/felinet/pipeline/dev_visual.py``
implementa a galeria visual do modo ``--dev``. ``src/felinet/comandos/easyrun.py``
implementa o wizard interativo. ``src/felinet/comandos/datasets.py``
ganhou os subcomandos ``linkar`` e ``listar``.

## Dependência nova

``questionary >= 2.0`` foi adicionada ao bloco principal de dependências
de ``pyproject.toml``. A biblioteca é leve (~50 KB) e é usada apenas pelo
wizard.

## Reorganização de pastas

A pasta ``felinet_runs_patch/`` foi removida via ``git rm -r``. Tratava-se
de um patch já aplicado na refatoração layout-runs (vide
``_INSTRUCOES_APLICAR.md`` que constava da raiz da pasta). Não há mais
referências no código.

As pastas ``entrega/`` e ``reports/`` foram movidas via ``git mv`` para
``_quarentena/entrega/`` e ``_quarentena/reports/``. Continham apenas
``README.md`` declarativo + ``.gitkeep``, sem código ativo. A pasta
``_quarentena/`` está listada em ``.gitignore`` para novos itens; itens
já movidos com ``git mv`` permanecem rastreados para fins de
rastreabilidade. A pasta ``_quarentena/README.md`` foi criada (com
``git add -f``) para documentar a política.

A pasta ``anexos/`` foi mantida no estado atual; o ``README.md``
descreve a intenção declarada (autorizações CEUA, datasheets,
protocolos de referência) e justifica a presença mesmo vazia.

## Pre-commit

A release introduz ``.pre-commit-config.yaml`` na raiz com hooks de
``ruff`` (lint + format, com ``--fix``) e ``pytest`` no estágio
``pre-push``. O alvo ``make pre-commit-install`` instala os hooks via
``pre-commit install --hook-type pre-commit --hook-type pre-push``.

## Versão

O ``version`` de ``pyproject.toml`` sobe de ``0.2.0`` para ``0.3.0``.

## Sem breaking changes externas

A CLI permanece compatível com chamadas v0.2.x. As opções novas têm
defaults conservadores (``--max-amostras 0`` = todas; ``--dev`` desligado
por default; ``--seed-amostragem 42``). Os manifests gravados em ``runs/``
mantêm o schema; novos campos em ``extras`` são adicionais. Quem usava o
caminho legado ``felinet datasets baixar-felidae`` continua usando
exatamente da mesma forma — o subcomando ganhou apenas vizinhos
(``linkar``, ``listar``).
