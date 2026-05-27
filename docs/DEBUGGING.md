# Debugging e inspeção

## Logs

O nível de log é controlado pelo argumento global ``--log-level`` (``DEBUG``,
``INFO``, ``WARNING``, ``ERROR``). O default é ``INFO``. A saída vai
diretamente para o terminal; quando se deseja capturar para arquivo basta
redirecionar com ``2>&1 | tee execucao.log``. Os módulos chave usam
``felinet.logging_setup.obter_logger(nome)`` e a hierarquia segue o caminho
do módulo (``orquestrador``, ``comandos.pipeline``, ``runs``).

## Inspeção de manifests

Cada run grava ``manifest.json`` na raiz do diretório. A inspeção manual
mais útil usa ``jq`` para extrair seções específicas. Para listar todos os
manifests de uma fonte:

```bash
fd manifest.json runs/operacional/kaggle_cats -x jq -r '.data_inicio, .extras.comando, .metricas_resumo'
```

Para descobrir a contagem de Felis catus do último run de classificação:

```bash
jq '.metricas_resumo' runs/operacional/kaggle_cats/dev/_/latest/manifest.json
```

## Rastreio de uma imagem

A trajetória de uma imagem específica pode ser reconstruída sem reexecutar
o pipeline. A partir do nome do arquivo, o manifesto da Fase I em
``runs/.../02_manifesto/manifesto.csv`` carrega ``caminho_relativo`` e
``sha256``. Esse SHA-256 reaparece como chave em ``03_deteccoes/deteccoes.json``
(campo ``media_path``) e em ``04_classificacoes/classificacoes.json``. A
visualização rápida da bbox é feita a partir do crop persistido em
``05_crops_felis_catus/<sha256>__bbox<idx>.jpg``. Os embeddings do
indivíduo correspondente estão em ``07_embeddings.npz`` indexados por
``<media_path>#bbox<idx>``.

## Erros comuns

A ausência do arquivo ``configs/datasets_locais.yaml`` resulta em
``felinet datasets listar`` exibindo a mensagem de convite à
configuração — não é erro, é apenas o estado inicial. Para resolver,
copia-se o template (``cp configs/datasets_locais.example.yaml
configs/datasets_locais.yaml``) e ajustam-se os caminhos.

A falha ``TypeError: _resolver_path espera str ou dict`` indica que
alguma entrada de ``paths.yaml`` está em formato não suportado. A função
aceita string ou dict com chave ``raiz`` (preferida) ou ``path``
(compatibilidade); qualquer outra forma exige correção do YAML.

Quando ``felinet pipeline executar`` retorna ``RelatorioCascata(sucesso=False,
mensagem="Pasta de brutas nao existe: ...")``, a fonte selecionada não
está linkada. A solução é executar ``felinet datasets linkar --nome
<fonte>`` (após configurar o caminho real em ``datasets_locais.yaml``).

A falha ``ImportError`` ao importar ``PytorchWildlife`` ou ``timm``
implica que o ambiente está sem os pacotes pesados. A suíte de testes
pula essas dependências por padrão (marker ``smoke``), mas a execução
real do pipeline requer instalação completa via ``make instalar``.

## Como rodar os testes

```bash
make qualidade        # ruff + pytest (ignora marker smoke)
pytest -q             # mesmo conjunto
pytest -m smoke       # testes que dependem de GPU/modelos pesados
pytest -k bloco7      # subconjunto por nome
```

A configuração default em ``pyproject.toml`` (``addopts = "-q -m 'not smoke'"``)
já exclui os testes com dependência pesada, permitindo executar a suíte
em máquinas sem GPU.
