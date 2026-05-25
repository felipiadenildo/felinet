"""Testes da política de decisão da Fase III."""
from __future__ import annotations

from pipeline.fase3_classificacao.decisor import (
    ConfigDecisor,
    decidir_status,
)
from pipeline.fase3_classificacao.schema import (
    STATUS_FELIS_CATUS,
    STATUS_OUTRA_ESPECIE,
    STATUS_VALIDACAO_HUMANA,
    PrediccaoEspecie,
)


def _p(especie: str, prob: float) -> PrediccaoEspecie:
    return PrediccaoEspecie(especie=especie, probabilidade=prob)


class TestDecisor:
    def test_felis_catus_com_alta_confianca(self) -> None:
        topk = [_p("Felis catus", 0.92), _p("Lynx rufus", 0.05)]
        assert decidir_status(topk) == STATUS_FELIS_CATUS

    def test_aceita_sinonimos_de_gato(self) -> None:
        topk = [_p("domestic cat", 0.88), _p("dog", 0.10)]
        assert decidir_status(topk) == STATUS_FELIS_CATUS

    def test_outra_especie_com_alta_confianca(self) -> None:
        topk = [_p("Lynx rufus", 0.91), _p("Felis catus", 0.05)]
        assert decidir_status(topk) == STATUS_OUTRA_ESPECIE

    def test_baixa_confianca_vai_para_validacao_humana(self) -> None:
        topk = [_p("Felis catus", 0.30), _p("Lynx rufus", 0.25)]
        assert decidir_status(topk) == STATUS_VALIDACAO_HUMANA

    def test_distribuicao_muito_espalhada_vai_para_validacao(self) -> None:
        # 5 classes com prob ~0.2 cada → entropia alta
        topk = [_p(f"esp_{i}", 0.20) for i in range(5)]
        assert decidir_status(topk) == STATUS_VALIDACAO_HUMANA

    def test_lista_vazia_vai_para_validacao(self) -> None:
        assert decidir_status([]) == STATUS_VALIDACAO_HUMANA

    def test_limiar_customizado(self) -> None:
        topk = [_p("Felis catus", 0.55)]
        cfg_estrito = ConfigDecisor(limiar_confianca=0.80)
        cfg_relaxado = ConfigDecisor(limiar_confianca=0.40)
        assert decidir_status(topk, cfg_estrito) == STATUS_VALIDACAO_HUMANA
        assert decidir_status(topk, cfg_relaxado) == STATUS_FELIS_CATUS
