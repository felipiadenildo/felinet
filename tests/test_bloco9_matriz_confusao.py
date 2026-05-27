"""Testes para Bloco 9: matriz de confusão Felis-vs-resto por fonte."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from felinet.datasets.labels_proxy import (
    fontes_com_ground_truth,
    resolver_rotulo_verdadeiro,
    rotulo_por_classe,
    rotulo_por_fonte,
)
from felinet.metricas.confusao_especie import (
    MatrizConfusao,
    calcular_matriz,
    ler_classe_origem_de_run,
    ler_predicoes_de_run,
)

# ============================================================
# labels_proxy
# ============================================================


def test_rotulo_por_classe_felis() -> None:
    assert rotulo_por_classe("domestic_cat") == "felis_catus"
    assert rotulo_por_classe("Domestic Cat") == "felis_catus"
    assert rotulo_por_classe("felis_catus") == "felis_catus"


def test_rotulo_por_classe_outros_felideos() -> None:
    assert rotulo_por_classe("bobcat") == "outros"
    assert rotulo_por_classe("puma") == "outros"
    assert rotulo_por_classe("lynx") == "outros"


def test_rotulo_por_classe_default_outros() -> None:
    assert rotulo_por_classe("raccoon") == "outros"
    assert rotulo_por_classe("") == "outros"
    assert rotulo_por_classe("desconhecido") == "outros"


def test_rotulo_por_fonte_kaggle() -> None:
    assert rotulo_por_fonte("kaggle_cats") == "felis_catus"


def test_rotulo_por_fonte_felidae_sem_proxy() -> None:
    assert rotulo_por_fonte("felidae") is None


def test_resolver_rotulo_prioriza_proxy_de_fonte() -> None:
    # kaggle_cats tem proxy; classe_origem é ignorada
    assert resolver_rotulo_verdadeiro("kaggle_cats", "bobcat") == "felis_catus"


def test_resolver_rotulo_usa_classe_quando_fonte_sem_proxy() -> None:
    assert resolver_rotulo_verdadeiro("felidae", "puma") == "outros"
    assert resolver_rotulo_verdadeiro("felidae", "domestic_cat") == "felis_catus"


def test_resolver_rotulo_sem_dados_retorna_none() -> None:
    assert resolver_rotulo_verdadeiro("felidae", None) is None
    assert resolver_rotulo_verdadeiro("dataset_nao_listado", None) is None


def test_fontes_com_ground_truth_filtra() -> None:
    todas = ["kaggle_cats", "felidae", "petface", "dataset_x"]
    com_gt = fontes_com_ground_truth(todas)
    assert "kaggle_cats" in com_gt
    assert "felidae" in com_gt
    assert "petface" not in com_gt
    assert "dataset_x" not in com_gt


# ============================================================
# MatrizConfusao
# ============================================================


def test_matriz_metricas_basicas() -> None:
    m = MatrizConfusao(fonte="t", tp=80, fp=5, tn=90, fn=10)
    assert m.total == 185
    assert m.precisao == pytest.approx(80 / 85)
    assert m.revocacao == pytest.approx(80 / 90)
    assert m.acuracia == pytest.approx(170 / 185)
    assert m.f1 > 0.8


def test_matriz_zerada_nao_explode() -> None:
    m = MatrizConfusao(fonte="t", tp=0, fp=0, tn=0, fn=0)
    assert m.total == 0
    assert m.precisao == 0
    assert m.revocacao == 0
    assert m.f1 == 0
    assert m.acuracia == 0


def test_matriz_como_dict_serializavel() -> None:
    m = MatrizConfusao(fonte="kaggle_cats", tp=10, fp=1, tn=5, fn=2)
    d = m.como_dict()
    assert d["fonte"] == "kaggle_cats"
    assert d["tp"] == 10
    assert "precisao" in d and isinstance(d["precisao"], float)


# ============================================================
# calcular_matriz
# ============================================================


def test_calcular_matriz_fonte_monocategoria_felis() -> None:
    # kaggle_cats: tudo é felis_catus por proxy.
    # 8 predições felis (TP), 2 predições outros (FN), nenhum fp/tn.
    preds = [(f"img_{i}.jpg", "felis_catus") for i in range(8)] + [
        (f"img_{i}.jpg", "outros") for i in range(8, 10)
    ]
    m = calcular_matriz("kaggle_cats", preds)
    assert m.tp == 8
    assert m.fn == 2
    assert m.fp == 0
    assert m.tn == 0
    assert m.precisao == 1.0  # 8 / 8
    assert m.revocacao == 0.8  # 8 / 10


def test_calcular_matriz_felidae_com_classe_origem() -> None:
    # felidae sem proxy de fonte: usa classe_origem por imagem.
    preds = [
        ("a.jpg", "felis_catus"),  # classe domestic_cat → TP
        ("b.jpg", "felis_catus"),  # classe bobcat → FP
        ("c.jpg", "outros"),  # classe bobcat → TN
        ("d.jpg", "outros"),  # classe domestic_cat → FN
        ("e.jpg", "felis_catus"),  # sem classe → sem GT
    ]
    classes = {
        "a.jpg": "domestic_cat",
        "b.jpg": "bobcat",
        "c.jpg": "bobcat",
        "d.jpg": "domestic_cat",
        # "e.jpg" deliberadamente ausente
    }
    m = calcular_matriz("felidae", preds, classes)
    assert m.tp == 1
    assert m.fp == 1
    assert m.tn == 1
    assert m.fn == 1
    assert m.sem_ground_truth == 1
    assert m.total == 4


def test_calcular_matriz_lista_vazia() -> None:
    m = calcular_matriz("kaggle_cats", [])
    assert m.total == 0
    assert m.sem_ground_truth == 0


# ============================================================
# ler_predicoes_de_run e ler_classe_origem_de_run
# ============================================================


def test_ler_predicoes_csv(tmp_path: Path) -> None:
    arq = tmp_path / "classificacoes.csv"
    with arq.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nome_arq", "idx_crop", "classe", "score"])
        w.writeheader()
        w.writerow({"nome_arq": "a.jpg", "idx_crop": 0, "classe": "felis_catus", "score": 0.92})
        w.writerow({"nome_arq": "b.jpg", "idx_crop": 0, "classe": "outros", "score": 0.71})
        w.writerow({"nome_arq": "c.jpg", "idx_crop": 0, "classe": "cat", "score": 0.88})

    preds = ler_predicoes_de_run(tmp_path)
    assert len(preds) == 3
    assert preds[0] == ("a.jpg", "felis_catus")
    assert preds[1] == ("b.jpg", "outros")
    assert preds[2] == ("c.jpg", "felis_catus")  # 'cat' mapeia para felis


def test_ler_predicoes_run_sem_dados(tmp_path: Path) -> None:
    preds = ler_predicoes_de_run(tmp_path)
    assert preds == []


def test_ler_classe_origem_csv(tmp_path: Path) -> None:
    arq = tmp_path / "manifesto.csv"
    with arq.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["caminho_relativo", "sha256", "classe_origem"])
        w.writeheader()
        w.writerow(
            {"caminho_relativo": "bobcat/img1.jpg", "sha256": "abc", "classe_origem": "bobcat"}
        )
        w.writerow({"caminho_relativo": "puma/img2.jpg", "sha256": "def", "classe_origem": "puma"})

    mapa = ler_classe_origem_de_run(tmp_path)
    assert mapa["bobcat/img1.jpg"] == "bobcat"
    assert mapa["puma/img2.jpg"] == "puma"


# ============================================================
# Integração com manifesto da ingestão (classe_origem)
# ============================================================


def test_manifesto_grava_classe_origem_em_por_classe(tmp_path: Path) -> None:
    """Quando layout='por_classe', a coluna classe_origem é populada."""
    from PIL import Image

    from felinet.pipeline.fase1_ingestao.manifesto import gerar_manifesto

    raiz = tmp_path / "felidae_fake"
    (raiz / "bobcat").mkdir(parents=True)
    (raiz / "puma").mkdir(parents=True)
    img1 = raiz / "bobcat" / "img1.jpg"
    img2 = raiz / "puma" / "img2.jpg"
    for p in (img1, img2):
        Image.new("RGB", (10, 10), color="red").save(p)

    saida = tmp_path / "manifesto.csv"
    entradas = gerar_manifesto(raiz, saida, layout="por_classe")

    classes = {e.caminho_relativo: e.classe_origem for e in entradas}
    # caminhos relativos vêm com separador do SO; basta conter a classe
    assert any(c == "bobcat" for c in classes.values())
    assert any(c == "puma" for c in classes.values())


def test_manifesto_vazio_em_layout_flat(tmp_path: Path) -> None:
    """Quando layout!='por_classe', classe_origem fica vazio."""
    from PIL import Image

    from felinet.pipeline.fase1_ingestao.manifesto import gerar_manifesto

    raiz = tmp_path / "flat_fake"
    raiz.mkdir()
    Image.new("RGB", (10, 10)).save(raiz / "a.jpg")

    saida = tmp_path / "manifesto.csv"
    entradas = gerar_manifesto(raiz, saida, layout="flat")

    assert all(e.classe_origem == "" for e in entradas)
