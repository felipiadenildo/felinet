# Decisao: renomeacao `tcc_gatos` -> `felinet`

## Contexto

A primeira versao do repositorio usava o nome `tcc_gatos` como pacote
Python e prefixo de variaveis de ambiente (`TCC_PERFIL`). Esse nome
carrega tres problemas:

1. **Acoplamento com a entrega academica.** Apos a defesa, o codigo
   continuara util (potencialmente para outros campi ou para um futuro
   mestrado). O nome `tcc_*` sugere descarte apos a defesa.
2. **Ambiguidade.** "tcc_gatos" eh interno -- ninguem fora do projeto
   reconhece. Para citacoes na monografia (`\texttt{felinet}`), eh
   preferivel um nome curto e mnemonico.
3. **Padroes Python.** Convencao PEP 8: nomes de pacote em minusculas,
   sem prefixos institucionais.

## Decisao

Adotar **`felinet`** como nome canonico do projeto, do pacote e do
binario CLI. Origem do nome: composicao de *felino* + *net* (rede de
camera-trapping).

| Item                | Antes               | Depois               |
|---------------------|---------------------|----------------------|
| Pacote Python       | `tcc_gatos`         | `felinet`            |
| Binario CLI         | (sem entry point)   | `felinet`            |
| Prefixo env vars    | `TCC_*`             | `FELINET_*`          |
| Var perfil          | `TCC_PERFIL`        | `FELINET_PERFIL`     |
| Var config          | (n/a)               | `FELINET_CONFIG`     |
| Repo GitHub         | `tcc-gatos-campus2` | (mantido por enquanto) |

## Impacto

- **Imports**: todos os `from pipeline.X` viraram `from felinet.pipeline.X`.
  O script `reorganizar.sh` (raiz do repo) executa essa migracao com
  `git mv` para preservar historia.
- **Scripts em `03_codigo/scripts/`**: foram refatorados em subcomandos
  do `felinet` CLI. Os scripts antigos sao removidos pelo
  `reorganizar.sh`.
- **Documentacao** (monografia): substituir `\texttt{tcc\_gatos}` por
  `\texttt{felinet}` no Capitulo 5 e nas referencias ao repositorio.

## Compatibilidade

O `paths.yaml` e o `pyproject.toml` foram regenerados para refletir o
novo nome. Nao ha *alias* mantendo o nome antigo -- a quebra eh limpa.

Caso o repositorio seja clonado por um colaborador apos a renomeacao,
basta `uv pip install -e ".[dev]"` para registrar o entry point
`felinet`.
