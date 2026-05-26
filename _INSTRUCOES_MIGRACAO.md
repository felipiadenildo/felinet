# Instrucoes de migracao -- v22 -> felinet (src/ layout)

Este ZIP traz a **nova estrutura** do projeto, rebatizada de `tcc_gatos`
para `felinet` e migrada para o padrao `src/` layout da PyPA.

## Caminho recomendado: aplicar por cima do repo existente

A migracao foi pensada para **preservar a historia git**. Por isso o
ZIP contem todos os arquivos novos + um script `reorganizar.sh` que
faz `git mv` das pastas antigas para a nova estrutura.

### Passo a passo

```bash
cd ~/Desktop/tcc/tcc_gatos_campus2_v22

# 1) Backup
git checkout -b refactor/felinet-src-layout
git tag pre-felinet-migration

# 2) Aplique o git mv das pastas antigas (mantem historico)
bash /caminho/para/felinet_v22/reorganizar.sh

# 3) Extraia o ZIP felinet sobre o repo (substitui os arquivos atualizados,
#    mantem os .tex intactos -- decisao explicita do projeto)
cd ~/Desktop/tcc/tcc_gatos_campus2_v22
unzip -o /caminho/para/felinet_v22.zip

# 4) Limpe artefatos pre-existentes do antigo layout que nao foram tocados
#    pelo git mv (ex.: __pycache__, .pytest_cache na raiz)
git clean -fd  src/  tests/   # cuidadoso: dry-run com -n antes

# 5) Reinstale o pacote
uv pip install -e ".[dev]"

# 6) Sanity check
felinet dev validar-ambiente
pytest -q
felinet pipeline executar --perfil dev   # cascata dev em <1 min

# 7) Commit final
git add -A
git commit -m "refactor: src/ layout + rename tcc_gatos -> felinet

- pacote movido para src/felinet/
- CLI unificado (typer): felinet ingestao|deteccao|classificacao|reid|pipeline|...
- env var TCC_PERFIL renomeada para FELINET_PERFIL
- pastas data/ artifacts/ docs/ reorganizadas
- modos operacional (cascata) e metodologico (PetFace) separados
- dataset dev com 5 imagens cobrindo todos os caminhos de rejeicao
- documentacao explicita de escopo nao implementado (P5 humano, P8 blur)
- ver docs/arquitetura/ para detalhes"

git push -u origin refactor/felinet-src-layout
```

## Caminho alternativo: clean install

Se preferir um repo limpo (sem historia das pastas antigas), basta
descompactar o ZIP em um diretorio novo e iniciar um repo git zerado.
Voce perdera o historico de `03_codigo/`, `04_dados/`, etc., mas terao
um repositorio mais simples para auditoria pos-defesa.

## O que NAO foi alterado neste ZIP

- **Arquivos LaTeX (`tex/`).** A reorganizacao **apenas move** o
  diretorio `02_latex/` para `tex/`. O conteudo dos `.tex` permanece
  intacto -- voce decide quando atualizar os caminhos relativos
  (`\input{tabelas/...}`) para apontar para `artifacts/tabelas/`.
- **Resultados experimentais (`data/processed/`).** As avaliacoes
  Re-ID anteriores foram preservadas.

## Diferencas-chave em relacao ao layout antigo

| Item                       | Antes (v22)               | Depois (felinet)                          |
|----------------------------|---------------------------|-------------------------------------------|
| Pacote Python              | `pipeline.fase2_deteccao` | `felinet.pipeline.fase2_deteccao`         |
| Scripts soltos             | `03_codigo/scripts/*.py`  | Subcomandos do CLI `felinet`              |
| Variavel de ambiente perfil| `TCC_PERFIL`              | `FELINET_PERFIL`                          |
| Saidas dev                 | `04_dados/dev/...`        | `data/dev/pipeline/0[1-8]_*`              |
| Tabelas pra LaTeX          | espalhadas                | `artifacts/tabelas/` (`.csv` + `.tex`)    |
| Figuras pra LaTeX          | `05_figuras/`             | `artifacts/figuras/`                      |
| Docs                       | `00_governanca/` etc      | `docs/{arquitetura,escopo,datasets,...}/` |
| LaTeX                      | `02_latex/`               | `tex/`                                    |

## Em caso de duvida

Consulte:
- [`docs/arquitetura/padrao_src_layout.md`](docs/arquitetura/padrao_src_layout.md)
- [`docs/arquitetura/decisao_renomeacao_felinet.md`](docs/arquitetura/decisao_renomeacao_felinet.md)
- [`docs/arquitetura/mapeamento_dfd_pipeline.md`](docs/arquitetura/mapeamento_dfd_pipeline.md)
