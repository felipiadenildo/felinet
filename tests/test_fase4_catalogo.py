"""Fase IV operacional: catálogo, fusão de partes, atribuição conservadora e auditoria."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from felinet.pipeline.fase4_reid.catalogo import (
    Catalogo,
    ConfigAtribuicao,
    TrilhaAuditoria,
    atribuir,
    fundir,
    reidentificar,
)

E = np.eye(4, dtype=np.float32)


def _catalogo() -> Catalogo:
    cat = Catalogo()
    for ident, base in (("mimi", 0), ("tom", 1), ("zé", 2)):
        cat.adicionar("face", ident, E[base])
        cat.adicionar("flanco", ident, E[base])
    return cat


def test_atribui_quando_top1_claro() -> None:
    d = reidentificar(_catalogo(), {"face": E[0], "flanco": E[0]})
    assert d.status == "atribuido" and d.individuo == "mimi" and d.margem == 1.0


def test_parte_ausente_nao_zera_o_score() -> None:
    d = reidentificar(_catalogo(), {"face": E[1]})  # flanco ocluído
    assert d.status == "atribuido" and d.individuo == "tom"


def test_margem_estreita_vai_para_curadoria() -> None:
    meio = (E[0] + E[1]) / np.sqrt(2)  # igualmente parecido com mimi e tom
    d = reidentificar(_catalogo(), {"face": meio})
    assert (
        d.status == "curadoria"
        and d.individuo is None
        and [i for i, _ in d.ranking[:2]] == ["mimi", "tom"]
    )


def test_abaixo_do_limiar_e_candidato_a_novo() -> None:
    d = reidentificar(_catalogo(), {"face": E[3]})  # ninguém parecido
    assert d.status == "novo_candidato" and d.individuo is None


def test_fusao_ponderada_e_atribuicao_direta() -> None:
    f = fundir({"face": {"a": 0.9, "b": 0.5}, "flanco": {"a": 0.5}}, {"face": 0.6, "flanco": 0.4})
    assert f["a"] == np.float64(0.6 * 0.9 + 0.4 * 0.5) and f["b"] == 0.5
    assert atribuir({"a": 0.9, "b": 0.88}, ConfigAtribuicao(margem=0.05)).status == "curadoria"


def test_catalogo_salva_e_carrega(tmp_path: Path) -> None:
    caminho = tmp_path / "catalogo.npz"
    _catalogo().salvar(caminho)
    d = reidentificar(Catalogo.carregar(caminho), {"face": E[2]})
    assert d.individuo == "zé"


def test_trilha_de_auditoria(tmp_path: Path) -> None:
    trilha = TrilhaAuditoria(tmp_path / "auditoria.sqlite")
    d = reidentificar(_catalogo(), {"face": (E[0] + E[1]) / np.sqrt(2)})
    trilha.registrar("P03/2026-10-15/q12", d)
    trilha.registrar("P03/2026-10-15/q12", atribuir({"mimi": 0.9}), responsavel="voluntario:ana")
    historico = trilha.historico("P03/2026-10-15/q12")
    assert [(s, i, r) for s, i, r, _ in historico] == [
        ("curadoria", None, "automatico"),
        ("atribuido", "mimi", "voluntario:ana"),
    ]
