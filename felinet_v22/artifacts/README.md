# `artifacts/` -- artefatos para a monografia

Conteudo **gerado** que vai diretamente para o LaTeX. Versionado.

- `figuras/` -- PNG/PDF a 300 DPI. Incluidos via `\includegraphics{}`.
- `tabelas/` -- pares `.csv` + `.tex` (booktabs). Incluidos via
  `\input{...}`.

## Regenerar tudo

```bash
make figuras
make tabelas
```

## Convencoes

- Nomes: `<dominio>_<descricao>_n<N:04d>.<ext>` (ex.:
  `reid_cmc_n0200.png`).
- DPI: 300 sempre. `fig.savefig(..., dpi=300, bbox_inches="tight")`.
- Estilo: matplotlib default sem temas customizados (consistencia com o
  template da banca).
- `exemplos/` em `figuras/` armazena recortes ilustrativos (JPGs maiores);
  ver `.gitattributes` para LFS se aplicavel.
