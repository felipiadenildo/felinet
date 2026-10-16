# Trajetórias de quadros reais (Cap. 5 da monografia)

Cada JSON lista os casos de uma fonte, na ordem das linhas da figura: `fonte`, `arquivo` (nome no run),
`rotulo` e, opcional, `caixa` (índice da caixa a recortar; por padrão, a de decisão mais avançada).
Os casos foram escolhidos para mostrar acertos e os modos de falha observados na execução final:

- `kaggle_cats.json`: gato aceito; gato branco também coberto por caixa de pessoa (desfocado pela anonimização);
  gatos detectados só como pessoa (imagem descartada na Fase II); gato classificado como puma.
- `felidae.json`: puma e lince-pardo rejeitados; coiote confundido com urso-pardo (validação humana); puma visto de
  costas, à noite, aceito como gato doméstico (a única aceitação do Felidae; a outra caixa do quadro, um tronco, saiu
  como "vazio"). O recorte escuro aparece com contraste realçado só na figura.

```bash
felinet monografia gerar --so cap5/trajetorias_kaggle_cats.pdf --so cap5/trajetorias_felidae.pdf
```
Requer as imagens dos runs (no ambiente original, nos caminhos gravados; fora dele, `felinet datasets
reconstruir-run` e `substituir` em `configs/monografia.yaml`; ver `docs/REPRODUCAO_MONOGRAFIA.md`).
