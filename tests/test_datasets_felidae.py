"""Testes do loader + sampler estratificado do dataset Felidae."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from felinet.datasets.felidae import (
    COTAS_PADRAO,
    ImagemFelidae,
    amostrar_estratificado,
    baixar_em_paralelo,
    gravar_manifesto_selecao,
)


@pytest.fixture
def coco_sintetico() -> tuple[list[dict], list[dict], dict[int, str]]:
    """COCO sintético com 4 categorias e distribuição desbalanceada."""
    cat_map = {1: "bobcat", 2: "puma", 3: "gray fox", 4: "unknown bird"}

    images = []
    annotations = []
    contagem = {1: 200, 2: 5, 3: 100, 4: 50}
    for cat_id, n in contagem.items():
        for i in range(n):
            img_id = f"loc/2024-01/{cat_id:02d}_{i:04d}.jpg"
            images.append(
                {
                    "id": img_id,
                    "file_name": img_id,
                    "datetime": "2024-01-01T00:00:00+00:00",
                    "location": "loc",
                }
            )
            annotations.append({"id": f"{img_id}_ann", "image_id": img_id, "category_id": cat_id})
    return images, annotations, cat_map


def test_amostrar_respeita_cotas_e_caps_quando_insuficiente(coco_sintetico) -> None:
    images, anns, cat_map = coco_sintetico
    cotas = {"bobcat": 50, "puma": 10, "gray fox": 30}
    selecao = amostrar_estratificado(images, anns, cat_map, cotas=cotas, cota_demais=5, seed=42)

    cont: dict[str, int] = {}
    for item in selecao:
        cont[item.categoria_nome] = cont.get(item.categoria_nome, 0) + 1

    assert cont["bobcat"] == 50
    assert cont["puma"] == 5  # cap natural (só existem 5)
    assert cont["gray fox"] == 30
    assert cont["unknown bird"] == 5


def test_amostrar_determinismo_via_seed(coco_sintetico) -> None:
    images, anns, cat_map = coco_sintetico
    sel1 = amostrar_estratificado(images, anns, cat_map, seed=123, cota_demais=10)
    sel2 = amostrar_estratificado(images, anns, cat_map, seed=123, cota_demais=10)
    sel3 = amostrar_estratificado(images, anns, cat_map, seed=999, cota_demais=10)

    ids1 = sorted(it.id for it in sel1)
    ids2 = sorted(it.id for it in sel2)
    ids3 = sorted(it.id for it in sel3)
    assert ids1 == ids2
    assert ids1 != ids3


def test_amostrar_aplica_cota_demais_a_classes_nao_listadas(coco_sintetico) -> None:
    images, anns, cat_map = coco_sintetico
    selecao = amostrar_estratificado(
        images, anns, cat_map, cotas={"bobcat": 999}, cota_demais=7, seed=0
    )
    cont: dict[str, int] = {}
    for item in selecao:
        cont[item.categoria_nome] = cont.get(item.categoria_nome, 0) + 1
    assert cont["bobcat"] == 200
    assert cont["puma"] == 5
    assert cont["gray fox"] == 7
    assert cont["unknown bird"] == 7


def test_gravar_manifesto_selecao_cria_csv(tmp_path: Path) -> None:
    itens = [
        ImagemFelidae(
            id="1/x.jpg",
            categoria_id=9,
            categoria_nome="bobcat",
            location="1",
            datetime="2024-01-01T00:00:00",
        ),
        ImagemFelidae(
            id="2/y.jpg",
            categoria_id=35,
            categoria_nome="puma",
            location="2",
            datetime="2024-02-02T00:00:00",
        ),
    ]
    saida = tmp_path / "selecao.csv"
    gravar_manifesto_selecao(itens, saida)
    assert saida.exists()
    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 3
    assert linhas[0].startswith("id,categoria_id")
    assert "bobcat" in linhas[1]
    assert "puma" in linhas[2]


def test_baixar_em_paralelo_mock_simula_ok_e_falha(tmp_path: Path) -> None:
    """Mock do urllib para não bater na rede; valida orquestração."""
    itens = [
        ImagemFelidae(
            id=f"loc/2024-01/{i:04d}.jpg",
            categoria_id=1,
            categoria_nome="bobcat",
            location="loc",
            datetime="2024-01-01T00:00:00",
        )
        for i in range(3)
    ]

    def fake_baixar(item, destino_raiz, *, timeout=30.0, tentativas=3):
        if "0001" in item.id:
            return item, False, "falha mock"
        pasta = destino_raiz / item.categoria_nome.replace(" ", "_")
        pasta.mkdir(parents=True, exist_ok=True)
        nome = Path(item.id).name
        (pasta / nome).write_bytes(b"\xff\xd8\xff\xe0")
        return item, True, "ok"

    with patch("felinet.datasets.felidae._baixar_uma", side_effect=fake_baixar):
        contadores = baixar_em_paralelo(itens, tmp_path, n_threads=2)

    assert contadores["ok"] == 2
    assert contadores["falha"] == 1
    assert (tmp_path / "_erros.log").exists()
    erros = (tmp_path / "_erros.log").read_text(encoding="utf-8")
    assert "0001" in erros


def test_cotas_padrao_focam_em_felinos_e_confundiveis() -> None:
    assert "bobcat" in COTAS_PADRAO
    assert "puma" in COTAS_PADRAO
    assert "domestic cat" in COTAS_PADRAO
    assert COTAS_PADRAO["bobcat"] >= 1
    assert COTAS_PADRAO["puma"] >= 1

# ============================================================
# Preset smoke (validacao rapida)
# ============================================================


def test_presets_smoke_existe_e_eh_menor_que_completo() -> None:
    from felinet.datasets.felidae import (
        COTA_DEMAIS_PADRAO,
        COTA_DEMAIS_SMOKE,
        COTAS_PADRAO,
        COTAS_SMOKE,
        PRESETS,
    )

    assert "completo" in PRESETS
    assert "smoke" in PRESETS
    assert PRESETS["completo"] == (COTAS_PADRAO, COTA_DEMAIS_PADRAO)
    assert PRESETS["smoke"] == (COTAS_SMOKE, COTA_DEMAIS_SMOKE)
    assert set(COTAS_SMOKE.keys()) == set(COTAS_PADRAO.keys())

    total_completo = sum(COTAS_PADRAO.values()) + COTA_DEMAIS_PADRAO * 59
    total_smoke = sum(COTAS_SMOKE.values()) + COTA_DEMAIS_SMOKE * 59
    assert total_smoke < total_completo / 20


def test_amostragem_smoke_respeita_cotas_reduzidas(
    coco_sintetico: tuple[list[dict], list[dict], dict[int, str]],
) -> None:
    from felinet.datasets.felidae import COTAS_SMOKE, amostrar_estratificado

    images, anns, cat_map = coco_sintetico
    selecao = amostrar_estratificado(
        images, anns, cat_map, cotas=COTAS_SMOKE, cota_demais=1, seed=42
    )
    from collections import Counter

    cont = Counter(item.categoria_nome for item in selecao)
    assert cont["bobcat"] == 40
    assert cont["puma"] == 5  # so 5 disponiveis no sintetico
    assert cont["gray fox"] == 30
    assert cont["unknown bird"] == 1


def test_cli_baixar_felidae_aceita_preset_smoke(
    tmp_path: Path, coco_sintetico: tuple[list[dict], list[dict], dict[int, str]]
) -> None:
    """Smoke test do CLI: --preset smoke + --apenas-planejar."""
    from typer.testing import CliRunner

    from felinet.comandos.datasets import app as datasets_app

    images, anns, cat_map = coco_sintetico

    json_fake = tmp_path / "meta" / "felidae_conservation_fund_2020_2025.json"
    json_fake.parent.mkdir(parents=True, exist_ok=True)
    json_fake.write_text("{}", encoding="utf-8")

    with (
        patch("felinet.datasets.felidae.baixar_metadados", return_value=json_fake),
        patch(
            "felinet.datasets.felidae.carregar_anotacoes",
            return_value=(images, anns, cat_map),
        ),
    ):
        runner = CliRunner()
        result = runner.invoke(
            datasets_app,
            [
                "baixar-felidae",
                "--destino",
                str(tmp_path / "felidae_out"),
                "--preset",
                "smoke",
                "--apenas-planejar",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "PLANO:" in result.output
    assert (tmp_path / "felidae_out" / "selecao_amostral.csv").exists()


def test_cli_baixar_felidae_rejeita_preset_invalido(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from felinet.comandos.datasets import app as datasets_app

    runner = CliRunner()
    result = runner.invoke(
        datasets_app,
        [
            "baixar-felidae",
            "--destino",
            str(tmp_path / "felidae_out"),
            "--preset",
            "inexistente",
            "--apenas-planejar",
        ],
    )
    assert result.exit_code != 0
