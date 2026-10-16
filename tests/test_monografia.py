"""Testes de `felinet monografia` (registro, geração, manifesto e verificação) com runs sintéticos."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from felinet.comandos.monografia import app
from felinet.monografia import dados as d
from felinet.monografia import elementos as el
from felinet.monografia import producao as pr
from felinet.monografia import tabelas as t

runner = CliRunner()


def _json(caminho: Path, conteudo: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")


def _csv(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def _operacional(raiz: Path, fonte: str, sha: str, n: tuple[int, int, int, int]) -> None:
    midias, caixas, imagens, felis = n
    pasta = raiz / "operacional" / fonte / "dev" / "_" / f"{sha}__monografia_n300"
    _json(
        pasta / "manifest.json",
        {
            "metricas_resumo": {
                "n_manifesto": midias,
                "n_deteccoes_animal": caixas,
                "n_imagens_com_animal": imagens,
                "n_classificacoes_felis_catus": felis,
            }
        },
    )
    # Uma caixa por posição, distribuídas entre as imagens com animal; 3 vão para validação.
    caminhos = [f"/origem/{fonte}/classe/img{i:03d}.jpg" for i in range(imagens)]
    por_imagem: dict[str, list] = {c: [] for c in caminhos}
    classificacoes = []
    for k in range(caixas):
        caminho = caminhos[k % imagens]
        indice = len(por_imagem[caminho])
        por_imagem[caminho].append(
            {
                "categoria": "animal",
                "confianca": 0.3 + 0.6 * (k % 7) / 6,
                "bbox": {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5},
            }
        )
        status = (
            "felis_catus" if k < felis else "validacao_humana" if k < felis + 3 else "outra_especie"
        )
        p_gato = 0.9 if status == "felis_catus" else 0.02
        classificacoes.append(
            {
                "media_path": caminho,
                "bbox_indice": indice,
                "status": status,
                "top_k": [{"especie": "domestic cat", "probabilidade": p_gato}],
            }
        )
        if status == "felis_catus":
            from PIL import Image

            recorte = pasta / "05_crops_felis_catus" / f"img{k % imagens:03d}__bbox{indice:02d}.png"
            recorte.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), (40, 40, 40)).save(recorte)
    _json(
        pasta / "03_deteccoes" / "deteccoes.json",
        {
            "resultados": [
                {"media_path": c, "largura": 16, "altura": 16, "deteccoes": dd}
                for c, dd in por_imagem.items()
            ]
        },
    )
    _json(pasta / "04_classificacoes" / "classificacoes.json", {"resultados": classificacoes})


@pytest.fixture
def runs(tmp_path: Path) -> Path:
    raiz = tmp_path / "runs"
    _operacional(raiz, "kaggle_cats", "aaa", (300, 308, 184, 257))
    _operacional(raiz, "felidae", "aaa", (300, 385, 292, 1))
    _csv(
        raiz / "complementar" / "cascatas_multifonte" / "x" / "resultados.csv",
        [
            {"source": s, "n_images": 200, "n_detection_boxes": 150, "n_images_with_animal": a,
             "n_classified_cat": c, "rate_animal": a / 200, "rate_cat": c / max(a, 1),
             "mean_det_score": 0.7, "elapsed_s": 10.0}
            for s, a, c in (("oxford_pet_cats", 182, 182), ("felidae_wild", 6, 0))
        ],
    )  # fmt: skip
    _csv(
        raiz / "complementar" / "sensibilidade_limiar" / "x" / "resultados.csv",
        [
            {
                "source": "oxford_pet_cats",
                "threshold": t,
                "n_boxes": 100,
                "n_images_with_animal": int(100 * r),
                "rate_animal": r,
                "mean_score": m,
            }
            for t, r, m in ((0.1, 0.93, 0.69), (0.2, 0.92, 0.74), (0.5, 0.86, 0.81))
        ],
    )
    rng = np.random.default_rng(0)
    for n in (50, 100, 200):
        base = raiz / "metodologico" / "petface" / "prod"
        cmc = list(np.linspace(0.6, 0.85, 10))
        _json(
            base / f"n{n:04d}" / "aaa" / "metricas.json",
            {
                "n_query": n,
                "n_galeria": 4 * n,
                "relatorio": {
                    "top_k": {str(k + 1): v for k, v in enumerate(cmc)},
                    "cmc": cmc,
                    "mAP_at_k": {"10": 0.6},
                    "mAP": 0.5,
                },
            },
        )
        ids = np.repeat([f"{i:06d}" for i in range(n)], 5)
        splits = np.tile(["query", "gallery", "gallery", "gallery", "gallery"], n)
        vetores = rng.normal(size=(5 * n, 8)).astype(np.float32)
        vetores /= np.linalg.norm(vetores, axis=1, keepdims=True)
        np.savez(
            base / f"n{n:04d}" / "aaa" / "embeddings.npz", vetores=vetores, ids=ids, splits=splits
        )
        curva = np.linspace(0, 1, 11).tolist()
        _json(
            base / f"openset_n{n:04d}" / "aaa" / "metricas.json",
            {
                "auc_media": 0.65,
                "auc_desvio": 0.05,
                "tpr_at_fpr_01_media": 0.2,
                "tpr_at_fpr_05_media": 0.28,
                "por_seed": [
                    {
                        "seed": s,
                        "relatorio": {
                            "fpr_curve": curva,
                            "tpr_curve": curva,
                            "tau_eer": 0.6,
                            "eer": 0.36,
                            "rank1_open_set": 0.2,
                        },
                    }
                    for s in (42, 7, 123)
                ],
            },
        )
    return raiz


# Elementos que só dependem dos runs (os demais exigem imagens, fotos ou o ambiente original).
SO_RUNS = [x for x in el.ELEMENTOS if set(x.requer) <= {"runs"}]


@pytest.fixture
def monografia(tmp_path: Path) -> Path:
    raiz = tmp_path / "mono"
    (raiz / "capitulos").mkdir(parents=True)
    (raiz / "main.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
    return raiz


def _tex_que_usa(monografia: Path, elementos: list[el.Elemento]) -> None:
    linhas = ["\\input{elementos/gerados/apendice/mapa_reproducao}"]
    for x in elementos:
        if x.tipo == "tabela":
            linhas.append(f"\\input{{elementos/gerados/{x.arquivo.removesuffix('.tex')}}}")
        else:
            linhas.append(f"\\gerado[width=\\linewidth]{{{x.arquivo}}}")
    (monografia / "capitulos" / "cap.tex").write_text("\n".join(linhas), encoding="utf-8")


def _gerar(runs: Path, monografia: Path, *extra: str):
    return runner.invoke(
        app, ["gerar", "--runs", str(runs), "--monografia", str(monografia), *extra]
    )


def test_gerar_com_runs_gera_o_que_pode_e_deixa_o_resto_pendente(
    runs: Path, monografia: Path
) -> None:
    r = _gerar(runs, monografia)
    assert r.exit_code == 0, r.output
    pasta = monografia / "elementos" / "gerados"
    for x in SO_RUNS:
        assert (pasta / x.arquivo).is_file(), x.arquivo
    assert "PENDENTE  cap5/exemplos_reid.pdf" in r.output
    assert "PENDENTE  cap3/exemplos_cascata.pdf" in r.output
    manifesto = json.loads((pasta / "MANIFESTO.json").read_text())
    cmc = next(i for i in manifesto["elementos"] if i["arquivo"] == "cap5/reid_cmc.pdf")
    assert cmc["codigo"] == "src/felinet/monografia/graficos.py::curvas_cmc"
    lidos = {a["arquivo"] for a in cmc["entradas"]["arquivos"]}
    assert "runs/metodologico/petface/prod/n0050/aaa/metricas.json" in lidos
    assert (pasta / "LEIAME.md").read_text().count("`fig:cap5-cmc-comparativo`") == 1
    assert "\\ref{fig:cap5-cmc-comparativo}" in (pasta / "apendice/mapa_reproducao.tex").read_text()


def test_gerar_e_reprodutivel(runs: Path, tmp_path: Path) -> None:
    shas = []
    for nome in ("a", "b"):
        mono = tmp_path / nome
        mono.mkdir()
        (mono / "main.tex").write_text("", encoding="utf-8")
        assert _gerar(runs, mono).exit_code == 0
        m = json.loads((mono / "elementos/gerados/MANIFESTO.json").read_text())
        shas.append({i["arquivo"]: i["sha256"] for i in m["elementos"]})
    assert shas[0] == shas[1]


def test_verificar_coerente_e_acusa_problemas(
    runs: Path, monografia: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(el, "ELEMENTOS", SO_RUNS)
    _tex_que_usa(monografia, SO_RUNS)
    assert _gerar(runs, monografia).exit_code == 0
    args = ["verificar", "--runs", str(runs), "--monografia", str(monografia)]
    ok = runner.invoke(app, args)
    assert ok.exit_code == 0, ok.output

    pasta = monografia / "elementos" / "gerados"
    tab = pasta / "cap5" / "tab_reid_closed.tex"
    tab.write_text(tab.read_text().replace("0,500", "0,501"), encoding="utf-8")
    (monografia / "capitulos" / "outro.tex").write_text("\\gerado{cap5/inexistente.pdf}")
    falha = runner.invoke(app, args)
    assert falha.exit_code == 1
    assert "cap5/tab_reid_closed.tex: difere do manifesto" in falha.output
    assert "cap5/inexistente.pdf: citado em capitulos/outro.tex" in falha.output


def test_verificar_acusa_tabela_desatualizada_pelos_runs(
    runs: Path, monografia: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(el, "ELEMENTOS", SO_RUNS)
    _tex_que_usa(monografia, SO_RUNS)
    assert _gerar(runs, monografia).exit_code == 0
    _operacional(runs, "kaggle_cats", "aaa", (300, 308, 185, 257))  # o run mudou
    falha = runner.invoke(app, ["verificar", "--runs", str(runs), "--monografia", str(monografia)])
    assert falha.exit_code == 1
    assert "cap5/tab_comparativo_fontes.tex: a entrada runs/operacional" in falha.output
    assert "cap5/tab_comparativo_fontes.tex: os números não conferem" in falha.output


def test_usos_no_tex_ignora_comentarios_e_completa_extensao(monografia: Path) -> None:
    (monografia / "capitulos" / "c.tex").write_text(
        "\\gerado[width=2cm]{cap5/a.pdf}\n% \\gerado{cap5/comentado.pdf}\n"
        "\\input{elementos/gerados/cap5/tab_x}\n\\input{preambulo/pacotes}\n",
        encoding="utf-8",
    )
    assert set(pr.usos_no_tex(monografia)) == {"cap5/a.pdf", "cap5/tab_x.tex"}


def test_registro_sem_arquivos_repetidos_e_requisitos_conhecidos() -> None:
    arquivos = [x.arquivo for x in el.ELEMENTOS]
    assert len(arquivos) == len(set(arquivos))
    assert all(set(x.requer) <= set(el.REQUISITOS) for x in el.ELEMENTOS)


def test_tabela_comparativo_fontes(runs: Path) -> None:
    tex = t.comparativo_fontes([d.carregar_cascata_operacional(runs, "kaggle_cats")])
    assert r"\texttt{kaggle\_cats} & 300 & 308 & 184 & 61,3\% & 257 & 83,4\% \\" in tex


def test_tabela_dos_exemplos_reproduz_a_execucao_registrada() -> None:
    sel = json.loads((el.EXEMPLOS / "fauna_campus2" / "selecao.json").read_text())
    tex = t.exemplos_cascata(el._resultados_fotos(), sel["especies"])
    assert r"Gato doméstico (\textit{Felis catus}) & 3 & 2 & 0 & 1 \\" in tex
    assert r"Gambá (\textit{Didelphis albiventris}) & 0 & 2 & 1 & 3 \\" in tex


def test_creditos_na_ordem_da_grade_e_escapados() -> None:
    reg = json.loads((el.EXEMPLOS / "fauna_campus2" / "registro.json").read_text())
    sel = json.loads((el.EXEMPLOS / "fauna_campus2" / "selecao.json").read_text())
    tex = t.creditos_fotos(reg, sel["grade"])
    assert tex.splitlines()[1].startswith("Gabi Lopes (CC BY-NC); Yasmin (CC BY-NC)")
    assert "Pedro Henrique Maloso Ramos (CC BY);" in tex
    assert r"marco\_louzada (CC BY-NC)" in tex


def test_runs_divergentes_sao_recusados(runs: Path) -> None:
    _operacional(runs, "kaggle_cats", "bbb", (300, 308, 185, 257))
    with pytest.raises(d.RunsDivergentesError):
        d.carregar_cascata_operacional(runs, "kaggle_cats")


def test_runs_repetidos_identicos_sao_aceitos(runs: Path) -> None:
    _operacional(runs, "kaggle_cats", "bbb", (300, 308, 184, 257))
    c = d.carregar_cascata_operacional(runs, "kaggle_cats")
    assert round(100 * c.taxa_animal, 1) == 61.3
    assert round(100 * c.taxa_felis, 1) == 83.4


def test_caixas_por_status_e_recorte_de_fronteira(runs: Path) -> None:
    caixas = d.carregar_caixas(runs, "felidae")
    assert len(caixas) == 385
    status = [c.status for c in caixas]
    assert status.count("felis_catus") == 1
    assert status.count("validacao_humana") == 3
    aceita = next(c for c in caixas if c.status == "felis_catus")
    assert aceita.recorte is not None and aceita.recorte.exists()
    assert aceita.p_gato == pytest.approx(0.9)


def _imagem(caminho: Path, cor: tuple[int, int, int] = (90, 90, 90)) -> None:
    from PIL import Image

    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), cor).save(caminho)


def test_amostras_com_imagens_remapeadas(runs: Path, tmp_path: Path) -> None:
    origem = tmp_path / "origem"
    for fonte, n in (("kaggle_cats", 184), ("felidae", 292)):
        for i in range(n):
            _imagem(origem / fonte / "classe" / f"img{i:03d}.jpg")
    en = el.Entradas(runs=runs, substituir=(("/origem", str(origem)),))
    assert (
        el.faltando(next(x for x in el.ELEMENTOS if x.arquivo == "cap4/amostras_fontes.pdf"), en)
        == []
    )
    (pastas,) = el._amostras(en)
    fig = el.fx.amostras_datasets(pastas)
    assert len(fig.axes) == 8


def test_exemplos_reid_tem_acerto_e_erro(tmp_path: Path) -> None:
    from felinet.monografia import exemplos as fx

    # 3 indivíduos; consulta 0 casa com a própria galeria, consulta 1 é mais parecida com o indivíduo 2.
    base = np.eye(4, dtype=np.float32)
    vetores = np.stack([base[0], base[0], base[1] * 0.6 + base[2] * 0.8, base[1], base[2], base[3]])
    ids = np.array(["a", "a", "b", "b", "c", "d"])
    splits = np.array(["query", "gallery", "query", "gallery", "gallery", "gallery"])
    caminhos = np.array([str(tmp_path / f"{i}.png") for i in range(6)])
    for c in caminhos:
        _imagem(Path(c))
    fig = fx.exemplos_reid(vetores, ids, splits, caminhos, [], k=3)
    assert len([ax for ax in fig.axes if ax.get_visible()]) == 2 * 4
