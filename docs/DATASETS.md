# Datasets

## Datasets suportados

O felinet trabalha com três famílias de datasets, distinguidas pelo *tipo*
declarado em ``configs/datasets_locais.yaml``. Cada tipo dita as fases do
pipeline aplicáveis e a categoria de symlink criada em ``data/raw/``.

| Nome lógico       | Tipo                              | Layout         | Fases | Categoria física       |
|-------------------|-----------------------------------|----------------|-------|------------------------|
| kaggle_cats       | camera_trap_brutas                | flat           | 1,2,3 | data/raw/camera_trap/  |
| felidae           | camera_trap_brutas                | por_classe     | 1,2,3 | data/raw/camera_trap/  |
| lila_ena24        | camera_trap_brutas                | aninhado_livre | 1,2,3 | data/raw/camera_trap/  |
| campus2_2025      | camera_trap_rotulado_identidade   | cocotraps      | 1-4   | data/raw/camera_trap/  |
| petface           | reid_crops_rotulados              | por_identidade | 4     | data/raw/reid/         |

O dataset Kaggle Cats é a referência ``felis_catus`` pura usada como
smoke-test do classificador binário; o Felidae Conservation Fund (LILA)
fornece imagens de outros felinos para avaliar o filtro Felis-vs-resto;
o LILA-BC ENA24 contribui camera-trap diversificado; o PetFace é o
benchmark canônico de Re-ID. O dataset Campus 2 2025 é a aquisição real
do TCC.

## Como obter

Kaggle Cats é distribuído via ``kagglehub``:

```bash
kagglehub download samuelayman/cat-dataset
```

Felidae Conservation Fund é baixado via comando dedicado, que faz
amostragem estratificada por classe:

```bash
felinet datasets baixar-felidae --destino /media/USUARIO/ssd/Felidae --preset smoke
```

LILA-BC ENA24 e PetFace seguem os procedimentos oficiais documentados nos
respectivos sites (LILA Camera Traps; PetFace dataset paper). O Campus 2
2025 é proprietário e exige autorização do projeto (vide
``anexos/autorizacoes/``).

## Como adicionar um dataset novo

O processo é declarativo e não exige edição de código. A receita básica:

1. Decidir o tipo correto. Imagens cruas de armadilha sem rótulo de
   identidade são ``camera_trap_brutas``; crops já recortados com identidade
   conhecida são ``reid_crops_rotulados``; imagens cruas com rótulo de
   identidade por indivíduo são ``camera_trap_rotulado_identidade``.

2. Decidir o layout. Imagens em pasta única são ``flat``; subpastas por
   espécie são ``por_classe``; subpastas por indivíduo são ``por_identidade``;
   estrutura COCO Camera Traps é ``cocotraps``; estrutura desconhecida é
   ``aninhado_livre`` (varredura recursiva como fallback).

3. Adicionar entrada em ``configs/datasets_locais.yaml``:

```yaml
datasets:
  meu_novo_dataset:
    tipo: camera_trap_brutas
    layout: por_classe
    caminho: /caminho/local/no/disco
    descricao: Descrição livre do dataset
    fases_aplicaveis: [1, 2, 3]
```

4. Registrar a fonte em ``configs/paths.yaml`` (seção ``fontes:``) com o
   mesmo nome lógico apontando para o symlink em ``data/raw/<categoria>/<nome>``.

5. Executar ``felinet datasets linkar --nome meu_novo_dataset`` para criar
   o symlink, e ``felinet datasets listar`` para confirmar.

6. (Opcional) Adicionar smoke-test em ``tests/`` validando a varredura
   com o iterador adequado.

A partir daí, o dataset pode ser passado em ``--fonte`` como qualquer
outra fonte registrada.
