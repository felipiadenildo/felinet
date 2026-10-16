"""Reconstrução das imagens de um run a partir das fontes públicas, conferidas pelo SHA-256.

Os runs guardam o manifesto da ingestão (``02_manifesto/manifesto.csv``: caminho relativo e
SHA-256 de cada mídia), mas não as imagens. As duas fontes operacionais da monografia são públicas:

* **Felidae** (LILA BC): o nome do arquivo no run é o mesmo do LILA, então basta localizá-lo nos
  metadados COCO e baixar pelo HTTP público;
* **kaggle_cats** (``samuelayman/cat-dataset``): o caminho relativo do run é o do próprio dataset,
  baixado uma vez (ex.: ``kagglehub.dataset_download``) e indicado como origem.

Cada arquivo é gravado em ``destino/<caminho relativo>`` e só conta como reconstruído se o SHA-256
bater com o do manifesto; assim as figuras com imagens reais usam exatamente os quadros do run.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from felinet.datasets.felidae import URL_BASE_AZURE


@dataclass(frozen=True)
class ItemManifesto:
    caminho_relativo: str
    sha256: str


def ler_manifesto(pasta_run: Path) -> list[ItemManifesto]:
    with open(pasta_run / "02_manifesto" / "manifesto.csv", encoding="utf-8", newline="") as f:
        return [ItemManifesto(r["caminho_relativo"], r["sha256"]) for r in csv.DictReader(f)]


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def indice_lila(json_metadados: Path) -> dict[str, str]:
    """Nome do arquivo -> caminho no blob do LILA (``"<câmera>/<mês>/<nome>.jpg"``)."""
    import json

    imagens = json.loads(Path(json_metadados).read_text(encoding="utf-8"))["images"]
    return {Path(i["file_name"]).name: i["file_name"] for i in imagens}


def _baixar_http(url: str, destino: Path, timeout: float = 60.0) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "felinet/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        destino.write_bytes(resp.read())


def reconstruir(
    itens: Iterable[ItemManifesto],
    destino: Path,
    obter: Callable[[ItemManifesto, Path], None],
) -> dict[str, list[str]]:
    """Obtém cada item com ``obter(item, caminho_destino)`` e confere o SHA-256.

    Itens já presentes e íntegros não são obtidos de novo. Devolve as listas ``ok``,
    ``ja_existia``, ``sha_divergente`` e ``falha`` (caminhos relativos).
    """
    saida: dict[str, list[str]] = {"ok": [], "ja_existia": [], "sha_divergente": [], "falha": []}
    for item in itens:
        alvo = destino / item.caminho_relativo
        if alvo.exists() and sha256_arquivo(alvo) == item.sha256:
            saida["ja_existia"].append(item.caminho_relativo)
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        try:
            obter(item, alvo)
        except (OSError, KeyError) as exc:
            saida["falha"].append(f"{item.caminho_relativo}: {exc}")
            continue
        if sha256_arquivo(alvo) == item.sha256:
            saida["ok"].append(item.caminho_relativo)
        else:
            alvo.unlink()
            saida["sha_divergente"].append(item.caminho_relativo)
    return saida


def obter_do_lila(indice: dict[str, str]) -> Callable[[ItemManifesto, Path], None]:
    def obter(item: ItemManifesto, alvo: Path) -> None:
        _baixar_http(URL_BASE_AZURE + indice[Path(item.caminho_relativo).name], alvo)

    return obter


def obter_de_pasta(origem: Path) -> Callable[[ItemManifesto, Path], None]:
    def obter(item: ItemManifesto, alvo: Path) -> None:
        shutil.copyfile(Path(origem) / item.caminho_relativo, alvo)

    return obter


# ----------------------------------------------------------------------------
# PetFace: só as imagens que um run de re-ID cita, lidas em fluxo do pacote oficial
# ----------------------------------------------------------------------------

PREFIXOS_PETFACE = (
    "/media/felipi/ssd/dados_tcc/PetFace/images/",
    "/home/felipi/Desktop/tcc/tcc_gatos_campus2_v22/data/raw/reid/petface/images/",
)


def arquivos_petface_do_run(embeddings: Path, prefixos=PREFIXOS_PETFACE) -> list[str]:
    """Caminhos relativos (``cat/<id>/<nn>.png``) das imagens citadas em ``embeddings.npz``."""
    import numpy as np

    caminhos = np.load(embeddings, allow_pickle=False)["caminhos"]
    relativos = set()
    for c in map(str, caminhos):
        prefixo = next((p for p in prefixos if c.startswith(p)), None)
        if prefixo is None:
            raise ValueError(f"caminho fora dos prefixos conhecidos do PetFace: {c}")
        relativos.add(c[len(prefixo) :])
    return sorted(relativos)


def extrair_de_tar(fluxo, nomes: set[str], destino: Path, limite_bytes: int = 20_000_000) -> int:
    """Lê um ``.tar.gz`` em fluxo e grava só os membros cujo nome está em ``nomes``.

    Só membros regulares, com nome exatamente igual a um da lista, são gravados (nada de
    caminhos absolutos ou ``..``); para assim que todos aparecem. Devolve quantos gravou.
    """
    import tarfile

    gravados = 0
    with tarfile.open(fileobj=fluxo, mode="r|gz") as tar:
        for membro in tar:
            if not (membro.isfile() and membro.name in nomes and membro.size <= limite_bytes):
                continue
            alvo = Path(destino) / membro.name
            alvo.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(membro) as f:
                alvo.write_bytes(f.read())
            gravados += 1
            if gravados == len(nomes):
                break
    return gravados
