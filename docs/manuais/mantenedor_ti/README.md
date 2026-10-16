# Manual do mantenedor de TI

## Ambientes
- **Servidor sem GPU:** núcleo + dev bastam para CI, tabelas, figuras e testes (`make instalar`, cerca de 250 MB).
  A inferência em CPU é viável para lotes pequenos: 36 imagens nas Fases II e III em menos de 2 minutos.
- **Ambiente da monografia** (GPU MX250, CUDA 12.1): `requirements/ambiente-original.txt`.
- Python 3.11 ou 3.12; `numpy<2` (o cálculo de AUC usa `np.trapz`); OpenCV `<5`, pela mesma razão.

## Qualidade
- CI no GitHub Actions (`.github/workflows/ci.yml`): `ruff check` + `pytest` em CPU, sem baixar pesos.
- Testes marcados `smoke` precisam de GPU e pesos; ficam fora do CI (`pytest -m smoke` para rodá-los).

## Dados e resultados
- `runs/` é a saída rastreável de cada execução (`docs/arquitetura/layout_runs.md`); não versionar.
- Os runs da execução da monografia ficam no Drive (`academic__felinet__runs.tar`).
- Pesos de modelos são baixados para o cache do usuário na primeira execução (Zenodo, Kaggle, Hugging Face).

## Licenças
`docs/MODELOS.md`. Atenção ao MegaDescriptor (CC BY-NC 4.0) e aos componentes AGPL antes de qualquer uso fora do
projeto acadêmico.
