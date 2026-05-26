# Reprodução da monografia

Este documento lista a sequência exata de comandos para gerar cada
artefato (tabela ou figura) citado na monografia, com indicação do tempo
esperado e das dependências entre comandos. Todos os comandos pressupõem
que ``configs/datasets_locais.yaml`` está configurado e que
``felinet datasets linkar`` já foi executado.

## Pré-requisitos

A configuração inicial precisa ser feita uma única vez:

```bash
make instalar
cp configs/datasets_locais.example.yaml configs/datasets_locais.yaml
# editar configs/datasets_locais.yaml com seus caminhos
felinet datasets linkar
felinet datasets listar    # confirmar status
```

O download do Kaggle Cats (smoke test, ~1.5 GB) é opcional; o subset
Felidae Conservation Fund pode ser baixado em duas variantes:

```bash
felinet datasets baixar-felidae --destino /media/USUARIO/ssd/Felidae --preset smoke
felinet datasets baixar-felidae --destino /media/USUARIO/ssd/Felidae --preset completo
```

A variante ``smoke`` baixa cerca de 200 imagens (~460 MB) e serve para
validar o pipeline; a ``completo`` baixa cerca de 8.3 mil imagens
(~18.6 GB) e é a base estatística para a monografia.

## Cascata operacional por fonte

Cada fonte camera-trap roda a cascata completa em modo prod. O comando é
o mesmo, variando apenas ``--fonte``. Tempo total esperado em GPU
MX250 2 GB: 8–25 min por fonte (proporcional ao número de imagens
amostradas).

```bash
felinet pipeline executar --perfil prod --fonte kaggle_cats
felinet pipeline executar --perfil prod --fonte felidae
felinet pipeline executar --perfil prod --fonte lila_ena24
```

Para reduzir o volume de imagens em uma execução experimental, usar
``--max-amostras N --seed-amostragem 42``. A amostragem é determinística;
a mesma seed em duas máquinas produz o mesmo subset.

## Avaliação metodológica Re-ID

A Fase IV isolada sobre PetFace gera as métricas de Re-ID que aparecem na
seção experimental.

```bash
felinet reid avaliar-closed --perfil prod --fonte petface --n 50
felinet reid avaliar-closed --perfil prod --fonte petface --n 200
felinet reid avaliar-closed --perfil prod --fonte petface --n 500
felinet reid avaliar-openset --perfil prod --fonte petface --n 200
```

Os comandos populam ``runs/metodologico/petface/prod/n0200/`` (closed) e
``runs/metodologico/petface/prod/openset_n0200/`` (open-set). Tempo
esperado em GPU: 2–8 min por N.

## Tabelas (artifacts/tabelas/)

Após os passos acima, as tabelas comparativas são geradas a partir dos
manifests dos runs latest. Cada comando produz CSV e .tex (booktabs) na
estrutura ``artifacts/tabelas/<modo>/<fonte>/``.

```bash
felinet tabelas fontes-resumo --perfil prod
felinet tabelas comparativo-fontes --perfil prod
felinet tabelas datasets-avaliados --perfil prod
felinet tabelas reid-resumo --perfil prod --fonte petface
felinet tabelas openset-resumo --perfil prod --fonte petface
felinet tabelas run-inventory --perfil prod
```

## Figuras (artifacts/figuras/)

As figuras seguem o mesmo padrão, gravando PNG 300 DPI prontos para
inclusão na monografia.

```bash
felinet figuras comparativo-fontes --perfil prod
felinet figuras reid-cmc --perfil prod --fonte petface --n 200
felinet figuras cmc-comparativo --perfil prod --fonte petface --ns 50,200,500
felinet figuras matriz-similaridade --perfil prod --fonte petface --n 50
felinet figuras dist-intra-inter --perfil prod --fonte petface --n 200
felinet figuras roc-openset --perfil prod --fonte petface --n 200
felinet figuras galeria-erros --perfil prod --fonte petface --n 200
```

A figura ``matriz-confusao-fontes`` (Bloco 9) está em estado de esqueleto
nesta release: o comando existe mas a implementação plena depende de
rótulos por imagem.

## Validação final

```bash
make qualidade   # ruff + pytest devem passar 100%
felinet --help   # CLI íntegra
```

O artefato final da monografia agrega os CSVs e PNGs gerados acima
diretamente no manuscrito LaTeX em ``tex/``, que é editado manualmente
fora do escopo deste pipeline.
