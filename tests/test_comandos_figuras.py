"""Testes para os comandos de figuras Re-ID (Bloco 2)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from typer.testing import CliRunner

from felinet.comandos.figuras import app as figuras_app

# ============================================================
# Helpers
# ============================================================


def _l2(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x, axis=1, keepdims=True).clip(min=1e-12)


def _criar_imagem(caminho: Path, cor: tuple[int, int, int]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), color=cor).save(caminho, "PNG")


def _construir_run_closed(
    raiz_run: Path,
    *,
    n_ids: int = 3,
    n_galeria_por_id: int = 3,
    com_caminhos: bool = True,
    perfeito: bool = True,
) -> None:
    """Constroi um run closed-set sintético com embeddings.npz e metricas.json.

    Se perfeito=True, embeddings dos mesmos IDs sao quase identicos -> Top-1=1.
    Se perfeito=False, embedding query do ID i fica colado no ID i+1 ->
    forca erros de Top-1 controlados.
    """
    rng = np.random.default_rng(42)
    dim = 16
    vetores: list[np.ndarray] = []
    ids: list[str] = []
    splits: list[str] = []
    caminhos: list[str] = []

    pasta_imgs = raiz_run / "imgs_sint"
    pasta_imgs.mkdir(parents=True, exist_ok=True)

    centros = _l2(rng.standard_normal((n_ids, dim)).astype(np.float32))
    for i in range(n_ids):
        # Query
        if perfeito:
            v_q = centros[i] + 0.01 * rng.standard_normal(dim).astype(np.float32)
        else:
            # Forca confusao: query do id i fica entre centro i e centro i+1
            outro = (i + 1) % n_ids
            v_q = 0.4 * centros[i] + 0.6 * centros[outro]
        v_q = v_q / np.linalg.norm(v_q)
        vetores.append(v_q.astype(np.float32))
        ids.append(f"{i:06d}")
        splits.append("query")
        cam = pasta_imgs / f"q_{i}.png"
        _criar_imagem(cam, (255 * (i % 2), 100, 200))
        caminhos.append(str(cam))

        # Galeria
        for k in range(n_galeria_por_id):
            v_g = centros[i] + 0.05 * rng.standard_normal(dim).astype(np.float32)
            v_g = v_g / np.linalg.norm(v_g)
            vetores.append(v_g.astype(np.float32))
            ids.append(f"{i:06d}")
            splits.append("gallery")
            cam = pasta_imgs / f"g_{i}_{k}.png"
            _criar_imagem(cam, (100, 255 * (k % 2), 50))
            caminhos.append(str(cam))

    matriz = np.stack(vetores).astype(np.float32)
    kwargs: dict[str, np.ndarray] = {
        "vetores": matriz,
        "ids": np.array(ids),
        "splits": np.array(splits),
    }
    if com_caminhos:
        kwargs["caminhos"] = np.array(caminhos)
    np.savez(raiz_run / "embeddings.npz", **kwargs)

    # metricas.json minimo
    cmc = [0.9, 0.95, 1.0, 1.0, 1.0]
    relatorio = {
        "n_queries": n_ids,
        "n_galeria": n_ids * n_galeria_por_id,
        "n_ids": n_ids,
        "top_k": {"1": cmc[0], "5": cmc[4]},
        "cmc": cmc,
        "mAP_at_k": {"1": cmc[0], "5": 0.92},
        "mAP": 0.93,
    }
    payload = {
        "n_query": n_ids,
        "n_galeria": n_ids * n_galeria_por_id,
        "relatorio": relatorio,
    }
    (raiz_run / "metricas.json").write_text(json.dumps(payload), encoding="utf-8")


def _construir_run_openset(raiz_run: Path, n_seeds: int = 3) -> None:
    """Constroi metricas.json open-set com por_seed contendo curvas ROC."""
    rng = np.random.default_rng(0)
    por_seed = []
    aucs = []
    for seed in range(n_seeds):
        fpr = np.linspace(0, 1, 20)
        # tpr = fpr + ruido => ROC um pouco acima da diagonal
        ruido = 0.05 * rng.standard_normal(20)
        tpr = np.clip(fpr + 0.3 * np.sqrt(fpr) + ruido, 0, 1)
        tpr.sort()  # garante monotonia
        auc_val = float(np.trapz(tpr, fpr))
        aucs.append(auc_val)
        por_seed.append(
            {
                "seed": seed,
                "relatorio": {
                    "auc_roc": auc_val,
                    "tpr_at_fpr_01": float(np.interp(0.01, fpr, tpr)),
                    "tpr_at_fpr_05": float(np.interp(0.05, fpr, tpr)),
                    "eer": 0.30 + 0.01 * seed,
                    "tau_eer": 0.50 + 0.02 * seed,
                    "rank1_open_set": 0.6,
                    "fpr_curve": fpr.tolist(),
                    "tpr_curve": tpr.tolist(),
                },
            }
        )
    payload = {
        "seeds": list(range(n_seeds)),
        "auc_media": float(np.mean(aucs)),
        "auc_desvio": float(np.std(aucs)),
        "tpr_at_fpr_01_media": 0.15,
        "tpr_at_fpr_05_media": 0.40,
        "por_seed": por_seed,
    }
    (raiz_run / "metricas.json").write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def projeto_sintetico(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Monta layout runs/ minimo e patcheia carregar_perfil + raiz_projeto.

    Estrutura:
        <tmp>/runs/metodologico/petface/dev/n0200/<sha>/embeddings.npz
                                        n0200/<sha>/metricas.json
                                        openset_n0200/<sha>/metricas.json
        <tmp>/artifacts/figuras/...
    """
    raiz = tmp_path / "proj"
    raiz.mkdir()
    sha = "abc1234"
    base_closed = raiz / "runs" / "metodologico" / "petface" / "dev" / "n0200" / sha
    base_openset = raiz / "runs" / "metodologico" / "petface" / "dev" / "openset_n0200" / sha
    base_closed.mkdir(parents=True)
    base_openset.mkdir(parents=True)

    _construir_run_closed(base_closed, n_ids=4, n_galeria_por_id=3, perfeito=False)
    _construir_run_openset(base_openset, n_seeds=3)

    # Symlinks "latest" -- chave eh modo__fonte__perfil__protocolo
    latest_root = raiz / "runs" / "latest"
    latest_root.mkdir(parents=True, exist_ok=True)
    (latest_root / "metodologico__petface__dev__n0200").symlink_to(base_closed)
    (latest_root / "metodologico__petface__dev__openset_n0200").symlink_to(base_openset)

    # Patch carregar_perfil
    class _CfgFake:
        nome = "dev"
        extras = {"raiz_runs": "runs"}

        def caminho_artifact(self, modo: str, fonte: str) -> Path:
            p = raiz / "artifacts" / "figuras" / modo / fonte
            p.mkdir(parents=True, exist_ok=True)
            return p

    def _fake_carregar(_perfil: str) -> _CfgFake:
        return _CfgFake()

    def _fake_fonte_default(_cfg, _modo: str) -> str:
        return "petface"

    def _fake_raiz_projeto() -> Path:
        return raiz

    monkeypatch.setattr("felinet.comandos.figuras.carregar_perfil", _fake_carregar)
    monkeypatch.setattr("felinet.comandos.figuras.fonte_default", _fake_fonte_default)
    monkeypatch.setattr("felinet.comandos.figuras.raiz_projeto", _fake_raiz_projeto)
    return raiz


# ============================================================
# Testes
# ============================================================


def test_cmc_comparativo_gera_png(projeto_sintetico: Path) -> None:
    """cmc-comparativo deve produzir PNG e processar pelo menos 1 curva."""
    # Replica do N=200 para N=50,500 (mesma estrutura, dirs diferentes)
    sha = "abc1234"
    latest_root = projeto_sintetico / "runs" / "latest"
    for n in (50, 500):
        base = projeto_sintetico / "runs" / "metodologico" / "petface" / "dev" / f"n{n:04d}" / sha
        base.mkdir(parents=True, exist_ok=True)
        _construir_run_closed(base, n_ids=3, n_galeria_por_id=2, perfeito=True)
        link = latest_root / f"metodologico__petface__dev__n{n:04d}"
        if not link.exists():
            link.symlink_to(base)

    runner = CliRunner()
    result = runner.invoke(
        figuras_app,
        ["cmc-comparativo", "--perfil", "dev", "--fonte", "petface", "--ns", "50,200,500"],
    )
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output
    saida = (
        projeto_sintetico
        / "artifacts"
        / "figuras"
        / "metodologico"
        / "petface"
        / "reid_cmc_comparativo.png"
    )
    assert saida.exists()
    assert saida.stat().st_size > 1000  # PNG razoavel


def test_dist_intra_inter_gera_png(projeto_sintetico: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        figuras_app,
        ["dist-intra-inter", "--perfil", "dev", "--fonte", "petface", "--n", "200"],
    )
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output
    saida = (
        projeto_sintetico
        / "artifacts"
        / "figuras"
        / "metodologico"
        / "petface"
        / "n0200"
        / "reid_dist_intra_inter.png"
    )
    assert saida.exists()


def test_roc_openset_gera_png_com_banda(projeto_sintetico: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        figuras_app,
        ["roc-openset", "--perfil", "dev", "--fonte", "petface", "--n", "200"],
    )
    assert result.exit_code == 0, result.output
    saida = (
        projeto_sintetico
        / "artifacts"
        / "figuras"
        / "metodologico"
        / "petface"
        / "openset_n0200"
        / "reid_roc_openset.png"
    )
    assert saida.exists()
    assert saida.stat().st_size > 1000


def test_galeria_erros_gera_png_quando_ha_erros(projeto_sintetico: Path) -> None:
    """Run sintetico tem perfeito=False -> queries com Top-1 errado existem."""
    runner = CliRunner()
    result = runner.invoke(
        figuras_app,
        [
            "galeria-erros",
            "--perfil",
            "dev",
            "--fonte",
            "petface",
            "--n",
            "200",
            "--piores",
            "2",
            "--top-k",
            "2",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output
    saida = (
        projeto_sintetico
        / "artifacts"
        / "figuras"
        / "metodologico"
        / "petface"
        / "n0200"
        / "reid_galeria_erros.png"
    )
    assert saida.exists()


def test_galeria_erros_falha_sem_caminhos_no_npz(
    projeto_sintetico: Path,
) -> None:
    """Se embeddings.npz nao tem 'caminhos', o comando avisa e sai com codigo 2."""
    sha = "abc1234"
    base = projeto_sintetico / "runs" / "metodologico" / "petface" / "dev" / "n0200" / sha
    # Reconstroi sem caminhos
    _construir_run_closed(base, n_ids=4, n_galeria_por_id=3, perfeito=False, com_caminhos=False)

    runner = CliRunner()
    result = runner.invoke(
        figuras_app,
        ["galeria-erros", "--perfil", "dev", "--fonte", "petface", "--n", "200"],
    )
    assert result.exit_code == 2
    # Mensagem amigavel deve ter sido logada
