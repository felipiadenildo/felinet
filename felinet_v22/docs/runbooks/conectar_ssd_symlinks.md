# Runbook: conectar SSD externo via symlinks

O perfil `prod` espera tres datasets em `data/raw/`:

| Caminho esperado          | Conteudo               | Origem tipica                                |
|---------------------------|------------------------|----------------------------------------------|
| `data/raw/lila_bc/`       | ENA24 (e demais LILA)  | https://lila.science/datasets               |
| `data/raw/petface/`       | PetFace cat            | https://github.com/mapooon/PetFace          |
| `data/raw/campus2/`       | Coleta proprietaria    | (privado)                                    |

Como esses datasets ocupam **dezenas de GB**, eles ficam **fora do repo**
em um SSD externo. O acesso eh feito via symlinks.

## Setup (uma vez por maquina)

```bash
# 1) Plugue o SSD; descubra o mount point
lsblk

# 2) Suponha que o SSD esta em /mnt/ssd e contem:
#    /mnt/ssd/datasets/lila_bc/
#    /mnt/ssd/datasets/petface/
#    /mnt/ssd/datasets/campus2/

# 3) Crie os symlinks
cd ~/Desktop/tcc/tcc_gatos_campus2_v22  # raiz do repo
mkdir -p data/raw
ln -s /mnt/ssd/datasets/lila_bc  data/raw/lila_bc
ln -s /mnt/ssd/datasets/petface  data/raw/petface
ln -s /mnt/ssd/datasets/campus2  data/raw/campus2

# 4) Sanity check
ls data/raw/petface/ | head -5
felinet dev validar-ambiente
```

## Verificacao

```bash
felinet pipeline resumir --perfil prod
```

deve mostrar `[OK]` para `manifesto` (gerado a partir de `data/raw/lila_bc/`)
se ja houver uma execucao prevista.

## Alternativa: sem SSD (laptop standalone)

Se nao houver SSD disponivel, **use apenas o perfil `dev`**, que cabe no
proprio repositorio. Todos os experimentos da monografia podem ser
reproduzidos qualitativamente em `dev`, com numeros formais apenas no
PetFace (que cabe em ~3 GB se baixado completo).
