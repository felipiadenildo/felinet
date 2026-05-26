# Escopo: o que NAO foi implementado neste TCC

Documento de transparencia academica. Lista as funcionalidades previstas
no DFD da monografia que **nao foram implementadas** nesta entrega,
justificando cada omissao e indicando para trabalhos futuros.

## 1. P8 -- Anonimizacao de pessoas (blur de bbox `person`)

**Status:** nao implementado.

**Onde aparece na monografia:** Capitulo 3 (DFD, processo P8), Capitulo 5
(secao "trabalhos futuros").

**Justificativa da omissao:**
- O LILA-BC, usado para validar Fases II e III, eh disponibilizado
  **ja anonimizado** pelas instituicoes provedoras (sem rostos identificaveis).
- A coleta proprietaria em Campus 2 ainda nao gerou imagens com pessoas
  em segundo plano.
- A implementacao tecnica eh trivial (Gaussian blur sobre cada bbox de
  classe `person` retornada pelo MegaDetector) e nao agrega valor
  metodologico ao TCC.

**Como seria implementado em trabalhos futuros:**
```python
# Em felinet.pipeline.fase3_classificacao.anonimizacao (novo modulo)
def anonimizar_pessoas(imagem, deteccoes):
    for det in deteccoes:
        if det.categoria == "person":
            recortar e aplicar GaussianBlur(radius=50)
    return imagem
```

## 2. P5 -- Interface de anotacao humana de identidade

**Status:** nao implementado; substituido por JSON pre-preenchido em dev.

**Onde aparece na monografia:** Capitulo 3 (DFD, processo P5).

**Justificativa da omissao:**
- Construir uma interface usavel (web ou desktop) com fila de revisao,
  controle de versao de rotulos e UX adequada para o monitor de Campus 2
  excede o escopo de um TCC de engenharia.
- A avaliacao quantitativa do Re-ID nao depende dessa interface: usamos
  o PetFace com ground-truth ja anotado.

**Substituto adotado:** `06_anotacao_identidade.json` (mapa
crop -> ID animal). Em dev eh pre-preenchido; em prod, seria editado
pelo monitor.

## 3. P9 -- Persistencia continua em SGBD

**Status:** esqueleto apenas (`src/felinet/persistencia/`).

**Justificativa da omissao:**
- O esqueleto define as tabelas alinhadas com Camtrap-DP, mas a
  integracao continua entre cascata e banco esta postergada.
- Para a monografia, o armazenamento em JSON/CSV eh suficiente para
  reproduzir todos os experimentos.

## 4. Hardware embarcado em Campus 2

**Status:** especificado mas nao instalado.

**Onde aparece na monografia:** Capitulo 2 (caracterizacao dos pontos
de instalacao, requisitos, decisao arquitetural).

**Justificativa da omissao:**
- A entrega do TCC eh **um sistema computacional validado em datasets
  publicos**. A instalacao fisica permanente em Campus 2 requer
  autorizacao institucional adicional e nao eh requisito de defesa.

## 5. Fine-tuning de modelos

**Status:** nao realizado.

**Justificativa da omissao:**
- O orcamento de GPU disponivel (NVIDIA MX250, 2 GB VRAM) **nao comporta**
  fine-tuning das redes usadas (MegaDetector, SpeciesNet, MegaDescriptor).
- A monografia adota explicitamente a estrategia **zero-shot / out-of-the-box**
  como um requisito do projeto (baixo custo computacional para o operador
  final).
- Os resultados reportados sao das versoes pre-treinadas oficiais.

## 6. Coleta proprietaria em Campus 2

**Status:** parcial.

**Justificativa:**
- Iniciada em 2026 com voluntarios; a base atual eh insuficiente para
  treinar/validar modelos. As metricas reportadas na monografia usam
  apenas LILA-BC (II, III) e PetFace (IV).
