"""Reconstrução das imagens de um run a partir da fonte, conferida pelo SHA-256 do manifesto."""

from __future__ import annotations

import hashlib
from pathlib import Path

from felinet.datasets import reconstrucao as r


def _run_com_manifesto(tmp_path: Path, conteudos: dict[str, bytes]) -> Path:
    run = tmp_path / "run"
    (run / "02_manifesto").mkdir(parents=True)
    linhas = ["caminho_relativo,sha256,largura,altura"]
    linhas += [f"{k},{hashlib.sha256(v).hexdigest()},1,1" for k, v in conteudos.items()]
    (run / "02_manifesto" / "manifesto.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return run


def test_reconstroi_de_pasta_e_confere_sha(tmp_path: Path) -> None:
    conteudos = {"cat/Images/1.jpg": b"um", "cat/Images/2.jpg": b"dois"}
    run = _run_com_manifesto(tmp_path, conteudos)
    origem = tmp_path / "origem"
    for rel, dados in conteudos.items():
        (origem / rel).parent.mkdir(parents=True, exist_ok=True)
        (origem / rel).write_bytes(dados)
    (origem / "cat/Images/2.jpg").write_bytes(b"alterado")  # versão diferente da do run
    destino = tmp_path / "destino"
    saida = r.reconstruir(r.ler_manifesto(run), destino, r.obter_de_pasta(origem))
    assert saida["ok"] == ["cat/Images/1.jpg"] and saida["sha_divergente"] == ["cat/Images/2.jpg"]
    assert not (destino / "cat/Images/2.jpg").exists()  # divergente não fica no destino
    de_novo = r.reconstruir(r.ler_manifesto(run)[:1], destino, r.obter_de_pasta(origem))
    assert de_novo["ja_existia"] == ["cat/Images/1.jpg"]


def test_lila_usa_o_caminho_do_blob(tmp_path: Path, monkeypatch) -> None:
    run = _run_com_manifesto(tmp_path, {"puma/abc.jpg": b"quadro"})
    urls = []

    def falso(url: str, destino: Path, timeout: float = 60.0) -> None:
        urls.append(url)
        destino.write_bytes(b"quadro")

    monkeypatch.setattr(r, "_baixar_http", falso)
    saida = r.reconstruir(
        r.ler_manifesto(run), tmp_path / "d", r.obter_do_lila({"abc.jpg": "7/2021-05/abc.jpg"})
    )
    assert saida["ok"] == ["puma/abc.jpg"] and urls[0].endswith(
        "felidae-conservation-fund/7/2021-05/abc.jpg"
    )


def test_extrair_petface_do_tar_so_os_citados(tmp_path: Path) -> None:
    import io
    import tarfile

    import numpy as np

    from felinet.datasets import reconstrucao as r

    pacote = io.BytesIO()
    with tarfile.open(fileobj=pacote, mode="w:gz") as tar:
        for nome in ("cat/000001/00.png", "cat/000001/01.png", "cat/000002/00.png", "../fora.png"):
            dado = nome.encode()
            info = tarfile.TarInfo(nome)
            info.size = len(dado)
            tar.addfile(info, io.BytesIO(dado))
    npz = tmp_path / "embeddings.npz"
    np.savez(
        npz,
        caminhos=np.array(
            [
                "/media/felipi/ssd/dados_tcc/PetFace/images/cat/000001/00.png",
                "/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/data/raw/reid/petface/images/cat/000002/00.png",
            ]
        ),
    )
    nomes = set(r.arquivos_petface_do_run(npz))
    assert nomes == {"cat/000001/00.png", "cat/000002/00.png"}
    pacote.seek(0)
    destino = tmp_path / "images"
    assert r.extrair_de_tar(pacote, nomes, destino) == 2
    assert sorted(p.relative_to(destino).as_posix() for p in destino.rglob("*.png")) == sorted(
        nomes
    )
    assert not (tmp_path / "fora.png").exists()
