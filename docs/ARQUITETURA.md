# Arquitetura do felinet

## Visão geral do pipeline

O felinet implementa um pipeline de visão computacional em cascata sobre
imagens de armadilhas fotográficas. A cascata é composta por quatro fases
independentes, cada uma com responsabilidade bem delimitada e artefatos
intermediários auditáveis. A Fase I recebe as mídias brutas e produz um
manifesto auditável com hash SHA-256, EXIF e dimensões; a Fase II aplica o
MegaDetector v6 (via PytorchWildlife) para identificar bbox de animais; a
Fase III usa o SpeciesNet como classificador binário Felis-catus contra o
resto; e a Fase IV extrai embeddings com o MegaDescriptor para
re-identificação de indivíduos (closed-set e open-set).

A arquitetura preserva o princípio da separação entre o modo *operacional*
(cascata I→II→III→IV sobre uma fonte de camera-trap) e o modo
*metodológico* (avaliação isolada de Re-ID sobre PetFace para a geração
de métricas da monografia). Os comandos da CLI refletem essa separação:
``felinet pipeline executar`` cobre o operacional; ``felinet reid
avaliar-closed`` e ``felinet reid avaliar-openset`` cobrem o metodológico.

## Conceitos centrais

O *perfil* (selecionado por ``--perfil dev`` ou ``--perfil prod``) define
defaults de fonte, recursos e diretórios. O perfil ``dev`` aponta para
amostras leves que rodam em menos de um minuto sem GPU; ``prod`` aponta
para os datasets reais via symlinks. O *modo* (``operacional`` ou
``metodologico``) determina a estrutura de saída em ``runs/``. A *fonte*
(``--fonte`` ou registrada como default no perfil) é o identificador
estável de um dataset, configurado em ``configs/paths.yaml`` na seção
``fontes:``. O *protocolo*, usado apenas em modo metodológico, identifica
o experimento de Re-ID (``n0200`` para closed-set com N=200,
``openset_n0200`` para open-set). O *run* é o diretório que recebe os
artefatos de uma execução; *latest* é o symlink que aponta para o run mais
recente bem-sucedido para uma dada tupla.

## Layout de runs em disco

O esquema de diretórios é determinado pelos parâmetros do comando (estilo
Snakemake) e acompanhado de um ``manifest.json`` (estilo MLflow). A
estrutura é

```
runs/<modo>/<fonte>/<perfil>/<protocolo|_>/<gitsha>[__<tag>]/
runs/<modo>/<fonte>/<perfil>/<protocolo|_>/latest -> <gitsha>[__<tag>]
```

O slug do protocolo é ``_`` quando o modo não usa protocolo (operacional).
A *tag* é um sufixo opcional para distinguir execuções com o mesmo
``git_sha``.

## Schema dos manifests

Cada run grava ``manifest.json`` com a tupla rastreável (modo, fonte,
perfil, protocolo, git_sha, tag), o ambiente (Python, hostname, plataforma)
e a seção ``metricas_resumo`` produzida pela fase. A seção ``extras``
recebe o nome do comando que originou o run (``ingestao``, ``deteccao``,
``classificacao``, ``pipeline executar``) e parâmetros relevantes
(``max_amostras``, ``seed_amostragem``, ``dev_visual``,
``confianca_deteccao``). Os comandos de tabela e figura filtram os runs
por ``extras.comando`` para cruzar dados de fases distintas da mesma fonte.

## Fluxo entre fases

A cascata é orquestrada por ``felinet.pipeline.orquestrador.executar_cascata``.
A função varre as mídias brutas, aplica amostragem determinística quando
``max_amostras > 0`` (helper ``_amostrar_deterministico``), gera o
manifesto da Fase I, executa a Fase II (com fallback de modelo dummy
quando o MegaDetector não está instalado), aplica o classificador da
Fase III e, finalmente, persiste crops e embeddings para a Fase IV. O
modo ``--dev`` reaproveita o mesmo fluxo, adicionando registros CSV em
``runs/.../dev_visualizacao/`` para inspeção humana.

## Esquema de tipos e layouts de datasets

A configuração por-usuário ``configs/datasets_locais.yaml`` declara,
por dataset, o *tipo* (``camera_trap_brutas``, ``reid_crops_rotulados``,
``camera_trap_rotulado_identidade``) e o *layout* físico em disco
(``flat``, ``por_classe``, ``por_identidade``, ``cocotraps``,
``aninhado_livre``). O tipo restringe as fases aplicáveis: um dataset
``camera_trap_brutas`` roda 1, 2 e 3; um ``reid_crops_rotulados`` roda
somente a 4. O layout determina o iterador usado pelo pipeline para
varrer os arquivos. O módulo ``felinet.datasets.iteradores`` exibe um
dispatcher por nome de layout.
