# `src/` -- codigo-fonte do pacote

Layout `src/` da PyPA. Contem **apenas** o pacote `felinet/`. Para a
justificativa desta escolha, ver
[`docs/arquitetura/padrao_src_layout.md`](../docs/arquitetura/padrao_src_layout.md).

Apos `uv pip install -e ".[dev]"`, o pacote fica acessivel em qualquer
diretorio via `import felinet` ou via o entry point `felinet` no PATH.
