# `configs/` — Configuração centralizada

Tudo que **não é código** mas controla o comportamento do pipeline vive aqui.

## Arquivos

| Arquivo | Função |
|---|---|
| `paths.yaml` | Mapeamento de caminhos por perfil (`dev` / `prod`). Carregado por `felinet.config.carregar_perfil()`. |
| `modelos.yaml` | Versões fixadas dos modelos pré-treinados (MegaDetector, SpeciesNet, MegaDescriptor) com URLs oficiais e cache local. |
| `pipeline.yaml` | Parâmetros operacionais: thresholds de confiança, batch size, seeds, métricas obrigatórias. |

## Como o código consome

```python
from felinet.config import carregar_perfil

cfg = carregar_perfil("dev")
caminho_brutas = cfg.raw_camera_trap   # data/dev/pipeline/01_brutas
caminho_petface = cfg.raw_petface      # data/dev/petface_mini
```

A escolha do perfil vem, em ordem de precedência:

1. Argumento `--perfil` do comando CLI (`felinet reid avaliar-closed --perfil prod`)
2. Variável de ambiente `FELINET_PERFIL`
3. Default `dev`

## Sobrescritas pontuais

Para uma execução única apontar um path diferente sem editar o YAML:

```bash
FELINET_DATA_RAW=/outro/path felinet pipeline executar
```

A variável `FELINET_DATA_RAW` sobrescreve `raw_camera_trap` do perfil ativo. Útil para experimentos pontuais.
