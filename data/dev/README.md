# `data/dev/` -- subset versionado

Dois subdiretorios:

- `pipeline/` -- entrada e saidas da cascata operacional (modo I -> IV).
  Contem `01_brutas/` com 5 imagens-placeholder.
- `petface_mini/` -- 5 individuos PetFace (~15 imagens) para validar a
  Fase IV sem acesso ao SSD externo. Gerado por
  `felinet dev preparar-petface-mini --origem /mnt/ssd/petface`.

Ao rodar `felinet pipeline executar --perfil dev`, as pastas
`pipeline/0[2-8]_*` recebem os artefatos da cascata. Para resetar:

```bash
felinet dev limpar-saidas-dev --confirmar
```

`01_brutas/` eh preservada (eh a entrada fixa do dev).
