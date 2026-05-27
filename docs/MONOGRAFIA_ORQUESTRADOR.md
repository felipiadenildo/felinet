# Orquestrador da Monografia

Pipeline declarativo que gera **todos** os artefatos da monografia (tabelas, figuras,
runs metodológicos e operacionais), com modo incremental por default, log de erros
isolado e zip versionado a cada execução.

## Visão geral

Dois arquivos principais:

- `scripts/monografia.json` — toda a configuração. Edite para mudar parâmetros (Ns,
  fontes, comandos, paths, top_n_piores, etc).
- `scripts/orquestrar_monografia.py` — runner. Lê o JSON, executa as etapas em ordem,
  gera log + inventário + manifesto + zip versionado.

## Instalação

```bash
# da raiz do repo felinet
cp /caminho/para/monografia.json scripts/monografia.json
cp /caminho/para/orquestrar_monografia.py scripts/orquestrar_monografia.py
chmod +x scripts/orquestrar_monografia.py

# (opcional) cria atalho no Makefile
cat >> Makefile <<'EOF'

monografia:
\tpython scripts/orquestrar_monografia.py

monografia-faltam:
\tpython scripts/orquestrar_monografia.py --so-faltam

monografia-force:
\tpython scripts/orquestrar_monografia.py --force

monografia-tabelas:
\tpython scripts/orquestrar_monografia.py --so-tabelas

monografia-figuras:
\tpython scripts/orquestrar_monografia.py --so-figuras
EOF
```

## Uso

```bash
# modo padrão: incremental (só o que falta)
python scripts/orquestrar_monografia.py

# plano (não executa nada)
python scripts/orquestrar_monografia.py --dry-run

# regera tudo do zero
python scripts/orquestrar_monografia.py --force

# só uma fatia
python scripts/orquestrar_monografia.py --so-tabelas
python scripts/orquestrar_monografia.py --so-figuras

# etapas explícitas (whitelist; repetir flag)
python scripts/orquestrar_monografia.py --etapa reid_closed --etapa figuras_por_n

# pula smoke (não recomendado)
python scripts/orquestrar_monografia.py --skip-smoke

# arquivo de config alternativo
python scripts/orquestrar_monografia.py --config configs/monografia_smoke.json
```

## Saídas

Cada execução gera, com timestamp:

```
logs/monografia/
├── execucao_<ts>.log    log completo (DEBUG)
├── erros_<ts>.log       só linhas WARNING/ERROR — abre primeiro quando algo falha
├── inventario_<ts>.md   tabela expected vs found + falhas detalhadas
└── manifesto_<ts>.json  metadados do run (sha, args, resultados, paths)

entrega/dados_monografia/
└── dados_monografia_<ts>.zip   versionado, mantém histórico
```

O zip contém:

- `artifacts/` completo (tabelas + figuras)
- `runs/metodologico/**/metricas.json` e `manifest.json`
- `runs/operacional/**/manifest.json` + `_estrutura_run.txt` + `dev_visualizacao/resumo.html`
- `runs/operacional/**/manifesto.csv.amostra` (apenas 50 linhas para reduzir tamanho)
- `runs/ambiente/*.json` e `*.md`
- `LOG_experimento.txt` e `RELATORIO_SMOKE.md` se existirem
- `_logs/` com inventário + execucao + erros do run

## Edição do JSON

### Mudar Ns de Re-ID

```json
"reid_closed": {
  "ns": [50, 100, 200, 500],
  ...
}
```

### Adicionar fonte ao pipeline operacional

```json
"pipeline_operacional": {
  "fontes": ["kaggle_cats", "felidae", "lila_ena24"]
}
```

### Mudar perfil ou tag global

```json
"padroes": {
  "perfil_metodologico": "prod",
  "perfil_operacional": "dev"
}
```

### Adicionar tabela nova

Adiciona um item em `etapas.tabelas.items`:

```json
{
  "nome": "minha-tabela",
  "comando": ["tabelas", "minha-tabela", "--perfil", "{perfil_metodologico}"],
  "artefatos": ["artifacts/tabelas/minha_tabela.csv", "artifacts/tabelas/minha_tabela.tex"]
}
```

### Mudar top_n_piores da galeria

```json
"padroes": {
  "top_n_piores": 5
}
```

(já está em 5 por default)

### Desligar uma etapa inteira

```json
"pipeline_operacional": {
  "habilitada": false,
  ...
}
```

## Placeholders suportados

Dentro dos comandos do JSON, qualquer chave de `padroes` ou da própria etapa pode ser
substituída com `{chave}`. Suporta formatação Python via `{n:04d}`:

- `{perfil_metodologico}` → `prod`
- `{n:04d}` → `0050`, `0100`, `0200`
- `{fonte}` → `petface`
- `{git_sha}` → SHA curto do HEAD atual
- `{top_n_piores}` → `5`

## Exit codes

- `0` — todos os artefatos esperados presentes, zero falhas
- `2` — repo inválido (sem pyproject.toml)
- `3` — falha em algum comando não-tolerada
- `4` — comandos OK mas artefato esperado ausente (provavelmente bug silencioso no comando)

## Fluxo típico para fechar a monografia

```bash
# 1. primeira execução completa
python scripts/orquestrar_monografia.py

# 2. olhe o inventário e os erros
cat logs/monografia/inventario_*.md | tail -50
cat logs/monografia/erros_*.log

# 3. se algo falhou ou artefato sumiu, força regenerar só aquela etapa
python scripts/orquestrar_monografia.py --etapa figuras_por_n --force

# 4. confirma 21/21 e empacota zip final
python scripts/orquestrar_monografia.py --so-faltam

# 5. zip mais recente
ls -lht entrega/dados_monografia/*.zip | head -1
```

## Manifesto JSON (automação)

`manifesto_<ts>.json` permite scripts externos consumirem o resultado:

```python
import json
m = json.load(open("logs/monografia/manifesto_20260527T021500.json"))
print(m["esperados_presentes"], "/", m["esperados_total"])
for ausente in m["esperados_ausentes"]:
    print("FALTA:", ausente)
```

## Adicionar ao git

```bash
git add scripts/monografia.json scripts/orquestrar_monografia.py docs/MONOGRAFIA_ORQUESTRADOR.md
git add Makefile
echo "logs/monografia/" >> .gitignore
echo "entrega/dados_monografia/*.zip" >> .gitignore  # opcional: não comitar zips
git commit -m "feat(monografia): orquestrador declarativo (JSON-driven) end-to-end"
```
