# 08 — Modelos

Pesos baixados de modelos pré-treinados e exports para deploy.

| Pasta | Conteúdo |
|---|---|
| `pesos/` | Checkpoints originais (`.pt`, `.pth`) — **não versionar no Git, usar DVC** |
| `exports/` | Versões otimizadas para deploy (`.onnx`, TorchScript) |

## Pesos esperados

- `megadetector_v6c.pt` — MegaDetector v6-compact (MIT, [release](https://github.com/microsoft/CameraTraps/releases))
- `miew_id_multispecies.pt` — MiewID multispecies ([Wild Me](https://wildbook.docs.wildme.org/))
- `megadescriptor_b224.pt` — MegaDescriptor-B-224 ([Hugging Face](https://huggingface.co/BVRA/MegaDescriptor-B-224))
- `yolo11n.pt` — YOLO11n (Ultralytics)
- (Opcional) `ppgnet_cat.pt` — PPGNet-Cat (Akbar 2025) se disponibilizado pelos autores

## Política

- Cada peso tem `<nome>.LICENSE.md` documentando licença e citação obrigatória.
- Pesos NÃO entram em `09_artefatos_entrega/`.
