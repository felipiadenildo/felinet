#!/usr/bin/env bash
# Diagnostico v2 — foca nos comandos que falharam no smoke v2.
# Saida: DIAGNOSTICO_SMOKE_v2.txt

set +e
OUT="DIAGNOSTICO_SMOKE_v2.txt"
exec > "$OUT" 2>&1

echo "=========================================="
echo "DIAGNOSTICO_SMOKE_v2 — $(date -Iseconds)"
echo "=========================================="

echo
echo "## 1. felinet reid extrair-embeddings --help"
felinet reid extrair-embeddings --help

echo
echo "## 2. felinet reid avaliar-closed --help"
felinet reid avaliar-closed --help

echo
echo "## 3. felinet reid avaliar-openset --help"
felinet reid avaliar-openset --help

echo
echo "## 4. felinet reid listar --help"
felinet reid listar --help

echo
echo "## 5. felinet reid listar (estado atual)"
felinet reid listar 2>&1 | head -50

echo
echo "## 6. felinet figuras comparativo-fontes --help"
felinet figuras comparativo-fontes --help

echo
echo "## 7. felinet figuras reid-cmc --help"
felinet figuras reid-cmc --help

echo
echo "## 8. felinet figuras matriz-similaridade --help"
felinet figuras matriz-similaridade --help

echo
echo "## 9. felinet figuras cmc-comparativo --help"
felinet figuras cmc-comparativo --help

echo
echo "## 10. felinet figuras dist-intra-inter --help"
felinet figuras dist-intra-inter --help

echo
echo "## 11. felinet figuras roc-openset --help"
felinet figuras roc-openset --help

echo
echo "## 12. felinet figuras galeria-erros --help"
felinet figuras galeria-erros --help

echo
echo "## 13. felinet figuras comparativo-fontes (codigo)"
sed -n '60,160p' src/felinet/comandos/figuras.py

echo
echo "## 14. felinet dev gerar-resumo-html --help"
felinet dev gerar-resumo-html --help

echo
echo "## 15. configs/paths.yaml — fontes:"
sed -n '/^fontes:/,/^[a-z]/p' configs/paths.yaml | head -40

echo
echo "## 16. Estrutura runs/ apos pipeline executar"
find runs/ -maxdepth 6 -type d 2>/dev/null

echo
echo "## 17. Conteudo de um run operacional (qualquer)"
find runs/operacional -maxdepth 5 -type f 2>/dev/null | head -30

echo
echo "## 18. Estado data/processed (avaliacoes existentes)"
ls -la data/processed/ 2>/dev/null

echo
echo "## 19. Embeddings existentes em data/interim"
ls -la data/interim/ 2>/dev/null | grep -E "embed|npz"

echo
echo "## 20. Estrutura artifacts/ apos smoke"
find artifacts/ -type f 2>/dev/null

echo
echo "## 21. Codigo do dev gerar-resumo-html (opcoes)"
grep -n -A 30 "def gerar_resumo_html\|gerar-resumo-html" src/felinet/comandos/dev.py | head -60

echo
echo "=========================================="
echo "FIM v2"
echo "=========================================="