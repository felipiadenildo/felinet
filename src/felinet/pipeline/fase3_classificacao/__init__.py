"""Fase III - Classificacao de especie + decisor felis_catus + recorte de crops.

Etapas E2 do pipeline:
1. SpeciesNet sobre cada bbox detectada na Fase II
2. Decisor traduz score do modelo em status (``felis_catus`` / outros)
3. Recorte dos crops aprovados para entrada da Fase IV

NAO IMPLEMENTADO NESTE TCC: anonimizacao (blur) de pessoas detectadas pela
Fase II. A categoria ``person`` apenas e descartada. Blur de pessoa e
trabalho futuro - referencia: docs/escopo/nao_implementado.md, processo P8
do DFD (B4_arquitetura_referencia_parte2.md).
"""
