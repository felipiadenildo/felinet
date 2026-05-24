# Decisões de adaptação do template USPSC v3.2

**Data**: 14 de maio de 2026
**Contexto**: Fase 2.5 da revisão pós-Etapa 1/2 do TCC
**Template-base**: Pacote USPSC v3.2 (modelo TCC ICMC) — [tutorial oficial](http://biblioteca.puspsc.usp.br/wp-content/uploads/2023/12/USPSC-Tutorial.pdf)

---

## Princípio mestre

O `main.tex` original (`USPSC-TCC-modelo-ICMCp.tex`) usa `\include{...}` (não `\input`) para os arquivos pré e pós-textuais. Isso significa que **remover arquivos referenciados quebra a compilação**. A estratégia adotada é, portanto:

- **Manter** todos os arquivos `\include`-ados pelo `main.tex`;
- **Esvaziar** os arquivos opcionais que NÃO usaremos (Errata, Índices Remissivos) — ficam com cabeçalho-comentário, sem gerar página no PDF;
- **Descartar** apenas arquivos puramente didáticos/exemplos e arquivos não referenciados pelo main.

---

## Decisões aprovadas pelo usuário (14/05/2026)

| Questão | Decisão |
|---|---|
| Pasta `uspsc-3.2/` completa vs enxuta | **Enxugar para o essencial**, sem descaracterizar template e regras ABNT/ICMC |
| Dedicatória e Epígrafe | **Manter ambos** (Dedicatoria + Epigrafe) |
| Lista de Símbolos e Unidades | **Listas separadas** (padrão USPSC mantido) — Simbolos.tex preservado |
| Próximo passo | **Adaptar template antes** de prosseguir, com **script idempotente** |

---

## Categorização final dos 41 arquivos do zip

### Núcleo intocável (9 arquivos) — copiados como estão

- `USPSC-classe/USPSC.cls`
- `USPSC-classe/USPSC1.cls`
- `USPSC-classe/ABNT6023-10520.sty`
- `USPSC-classe/abntex2-alf-USPSC.bst`
- `USPSC-classe/abntex2-alfeng-USPSC.bst`
- `USPSC-classe/abntex2-num-USPSC.bst`
- `USPSC-classe/abntex2-numeng-USPSC.bst`
- `USPSC-img/CapaICMC.jpg`
- `USPSC-img/USPSC-PaginaEmBranco.jpg`

### Pré-textuais ativos (14 arquivos) — copiados, editáveis

CapaICMC.tex, fichacatalografica (.tex + .pdf), folhadeaprovacao (.tex + .pdf), PaginaEmBranco.pdf, VersoPaginaDeRosto-Relatorio.pdf, Dedicatoria, Agradecimentos, Epigrafe, Resumo, Abstract, AbreviaturasSiglas, Simbolos.

### Pós-textuais ativos (2 arquivos) — copiados, editáveis

Apendices.tex, Anexos.tex.

### Opcionais esvaziados (2 arquivos) — conteúdo comentário-cabeçalho apenas

- `USPSC-TA-PreTextual/USPSC-Errata.tex` (opcional pela ABNT NBR 14724:2011 §4.2.1.2)
- `USPSC-TA-PosTextual/USPSC-IndicesRemissivos.tex` (raramente usado em TCC)

### Renomeados na raiz (2 arquivos)

- `USPSC-TCC-modelo-ICMCp.tex` → **`main.tex`**
- `USPSC-TCC-pre-textual-ICMC.tex` → **`pre-textuais.tex`**

Substituição automática feita no main.tex:
- `\bibliography{USPSC-bib/USPSC-modelo-references}` → `\bibliography{USPSC-bib/references}`

### Descartados (12 arquivos) — NÃO copiados

| Arquivo | Motivo |
|---|---|
| `USPSC-IndicesRemissivos.tex` (raiz) | Duplicado da versão em PosTextual/ |
| `USPSC-unidades.tex` | Didático (lista de unidades de exemplo) |
| `USPSC-bib/USPSC-modelo-references.bib` | Bibliografia de exemplo — substituída por `references.bib` novo |
| `USPSC-img/USPSC-AcentuacaoLaTeX.png` | Imagem didática do tutorial |
| `USPSC-img/USPSC-EstruturaTrabAcad.jpg` | Imagem didática do tutorial |
| `USPSC-img/USPSC-LetrasGregas.png` | Imagem didática do tutorial |
| `USPSC-img/USPSC-SimbolosUteis.png` | Imagem didática do tutorial |
| `USPSC-img/USPSC-modelo-img-grafico.pdf` | Imagem didática do tutorial |
| `USPSC-img/USPSC-modelo-img-marca.pdf` | Imagem didática do tutorial |
| `USPSC-TA-Textual/USPSC-Cap1-Introducao.tex` | Capítulo exemplo — substituído na Fase 5 |
| `USPSC-TA-Textual/USPSC-Cap2-Desenvolvimento.tex` | Capítulo exemplo — substituído na Fase 5 |
| `USPSC-TA-Textual/USPSC-Cap3-Conclusao.tex` | Capítulo exemplo — substituído na Fase 5 |

### Criados (3 arquivos/pastas)

- `USPSC-bib/references.bib` — bibliografia vazia com cabeçalho explicativo
- `USPSC-TA-Textual/.gitkeep` — pasta vazia para capítulos da Fase 5
- `figuras/.gitkeep` — pasta vazia para figuras do projeto
- `README.md` — explica a estrutura adaptada

### Backup completo

- `_ORIGINAL_meutccicmcp/` — cópia intocada do template original (1.7 MB) preservada para referência ABNT/ICMC.

---

## Conformidade com ABNT/ICMC

| Regra do tutorial USPSC | Estado |
|---|---|
| Classe `USPSC.cls` ou `USPSC1.cls` no preâmbulo | mantida |
| Estilo bibliográfico `abntex2-alf-USPSC.bst` | mantido (sistema autor-data, padrão ICMC) |
| Pacote `ABNT6023-10520.sty` (compatibilização NBR 6023:2018 + NBR 10520:2023) | mantido |
| `\siglaunidade{ICMC-TCC}` + `\programa{BCCp}` | mantido (linhas 168-169 do main) |
| Capa ICMC com `BackgroundBranco` | mantida (linhas 246-248) |
| Folha de rosto duplex `\imprimirfolhaderosto*` | mantida (linha 261) |
| Ficha catalográfica em PDF | placeholder PDF do template (substituir pelo definitivo da Biblioteca ICMC antes da defesa) |
| Folha de aprovação em PDF | placeholder PDF do template (substituir após defesa) |
| Errata (opcional NBR 14724) | esvaziada |
| Pré-textuais ICMC obrigatórios: dedicatória, agradecimentos, epígrafe, resumo, abstract, lista figuras/tabelas/quadros, lista siglas, lista símbolos, sumário | TODOS preservados |
| Listas de Figuras/Tabelas/Quadros (`\listoffigures*`, `\listoftables*`, `\listofquadro*`) | inalteradas no main.tex |
| Sumário (`\tableofcontents*`) | inalterado |
| Sistema de citação (autor-data) | inalterado |

---

## Próximas adaptações manuais (não cobertas pelo script)

Estas alterações requerem decisão de conteúdo e ficam para a **Fase 5** (Draft LaTeX):

1. `pre-textuais.tex` — editar:
   - `\titulo{...}` → título do TCC
   - `\autor{Felipi Adenildo Soares Sousa}` + `\autorficha` + `\autorabr`
   - `\orientador{Prof. Dr. Matheus Machado dos Santos}` + `\orientadorcorpoficha` + `\orientadorficha`
   - Datas de defesa (Setembro/2026)
   - Palavras-chave (PT e EN)
2. `USPSC-TA-PreTextual/USPSC-Dedicatoria.tex` — escrever dedicatória pessoal
3. `USPSC-TA-PreTextual/USPSC-Agradecimentos.tex` — escrever agradecimentos
4. `USPSC-TA-PreTextual/USPSC-Epigrafe.tex` — escolher epígrafe
5. `USPSC-TA-PreTextual/USPSC-Resumo.tex` — resumo final (após escrita do TCC)
6. `USPSC-TA-PreTextual/USPSC-Abstract.tex` — abstract final
7. `USPSC-TA-PreTextual/USPSC-AbreviaturasSiglas.tex` — popular com siglas do projeto (já temos lista em `glossario_notas_rodape.md`)
8. `USPSC-TA-PreTextual/USPSC-Simbolos.tex` — popular com símbolos matemáticos usados (mAP, IoU, etc.)
9. `USPSC-TA-PreTextual/USPSC-fichacatalografica.pdf` — solicitar à Biblioteca ICMC antes da defesa
10. `USPSC-TA-PreTextual/USPSC-folhadeaprovacao.pdf` — após defesa (Set/2026)

---

## Como reverter

Para descartar a adaptação e voltar ao zero:

```bash
rm -rf 02_latex/
unzip meutccicmcp.zip -d 02_latex_original/
```

Ou simplesmente use o backup automático em `02_latex/_ORIGINAL_meutccicmcp/`.

## Como reexecutar o script

```bash
cd tcc_gatos_campus2/

# simulação (não altera nada)
python 03_codigo/scripts/adaptar_template_uspsc.py --dry-run

# execução normal (preserva arquivos já editados)
python 03_codigo/scripts/adaptar_template_uspsc.py

# forçar sobrescrita (CUIDADO: apaga suas edições nos pré-textuais)
python 03_codigo/scripts/adaptar_template_uspsc.py --force
```
