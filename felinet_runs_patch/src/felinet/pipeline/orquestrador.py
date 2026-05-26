"""Orquestrador da cascata I -> II -> III -> IV.

Encadeia as quatro fases do pipeline operacional em uma execucao unica,
gravando os artefatos intermediarios no diretorio do ``RunDir`` recebido.

Esta cascata e o modo OPERACIONAL do sistema. Para a avaliacao METODOLOGICA
(Fase IV isolada sobre PetFace que gera metricas para a monografia), use os
comandos ``felinet reid avaliar-closed`` / ``avaliar-openset``.

Mapeamento DFD -> arquivo de saida dentro do run:
    P2 (Ingestao+EXIF)        -> 02_manifesto/manifesto.csv
    P3 (Deteccao animal)      -> 03_deteccoes/deteccoes.json
    P4 (SpeciesNet+Decisor)   -> 04_classificacoes/classificacoes.json
    P4.2 (Recorte de crops)   -> 05_crops_felis_catus/
    P5 (Anotacao identidade)  -> 06_anotacao_identidade.json (humano-no-loop)
    P6 (Embedding MegaDescr.) -> 07_embeddings.npz
    P7 (Matching Re-ID)       -> 08_avaliacao_pipeline.json
    P8 (Blur de pessoa)       -> NAO IMPLEMENTADO (escopo futuro)

Ver docs/arquitetura/mapeamento_dfd_pipeline.md e
docs/arquitetura/layout_runs.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from felinet.logging_setup import obter_logger
from felinet.runs import RunDir
from felinet.utils.io import gravar_json, gravar_npz, ler_json

LOG = obter_logger("orquestrador")


@dataclass
class RelatorioCascata:
    """Resumo de uma execucao da cascata."""

    n_brutas: int
    n_manifesto: int
    n_deteccoes_animal: int
    n_classificacoes_felis_catus: int
    n_crops_gerados: int
    n_embeddings: int
    sucesso: bool
    mensagem: str = ""

    def como_dicionario(self) -> dict:
        return {
            "n_brutas": self.n_brutas,
            "n_manifesto": self.n_manifesto,
            "n_deteccoes_animal": self.n_deteccoes_animal,
            "n_classificacoes_felis_catus": self.n_classificacoes_felis_catus,
            "n_crops_gerados": self.n_crops_gerados,
            "n_embeddings": self.n_embeddings,
            "sucesso": self.sucesso,
            "mensagem": self.mensagem,
        }


def executar_cascata(
    *,
    pasta_brutas: Path,
    run: RunDir,
    confianca_min_deteccao: float = 0.20,
    anotacao_identidade_origem: Path | None = None,
) -> RelatorioCascata:
    """Executa I -> II -> III -> IV gravando dentro de ``run.raiz``.

    Args:
        pasta_brutas: Pasta de imagens brutas (geralmente um symlink em
            ``data/raw/...`` resolvido a partir da fonte selecionada).
        run: Diretorio do run criado por ``felinet.runs.criar_run``.
        confianca_min_deteccao: Threshold do MegaDetector.
        anotacao_identidade_origem: Arquivo opcional de rotulos de
            identidade (dev). Quando informado, e copiado para
            ``run.anotacao_path`` e usado pela avaliacao final.

    Returns:
        ``RelatorioCascata`` com contagens por fase.
    """
    if not pasta_brutas.exists():
        # Checagem antes dos imports pesados (torch/MD/SpeciesNet).
        return RelatorioCascata(
            n_brutas=0, n_manifesto=0, n_deteccoes_animal=0,
            n_classificacoes_felis_catus=0, n_crops_gerados=0, n_embeddings=0,
            sucesso=False,
            mensagem=f"Pasta de brutas nao existe: {pasta_brutas}",
        )

    # Lazy import: evita carregar torch/MegaDetector quando o orquestrador
    # so vai ser importado para inspecao (e.g. pelos testes do CLI).
    from felinet.pipeline.fase1_ingestao.manifesto import gerar_manifesto
    from felinet.pipeline.fase2_deteccao.megadetector import DetectorMegaDetectorV6
    from felinet.pipeline.fase2_deteccao.schema import (
        BoundingBox,
        ResultadoDeteccao,
        salvar_resultados_json as salvar_deteccoes_json,
    )
    from felinet.pipeline.fase3_classificacao.crops import persistir_crops_felis_catus
    from felinet.pipeline.fase3_classificacao.schema import (
        STATUS_FELIS_CATUS,
        salvar_resultados_json as salvar_classificacoes_json,
    )
    from felinet.pipeline.fase3_classificacao.decisor import ConfigDecisor
    from felinet.pipeline.fase3_classificacao.speciesnet import (
        ClassificadorSpeciesNet,
        CropEntrada,
    )
    from felinet.pipeline.fase4_reid.megadescriptor import ExtratorMegaDescriptor

    extensoes = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    brutas = sorted(p for p in pasta_brutas.rglob("*") if p.suffix.lower() in extensoes)
    LOG.info(f"Cascata iniciada: {len(brutas)} imagens em {pasta_brutas}")

    # ----- FASE I: Ingestao -----
    run.manifesto_dir.mkdir(parents=True, exist_ok=True)
    arquivo_manifesto = run.manifesto_dir / "manifesto.csv"
    entradas_manifesto = gerar_manifesto(pasta_brutas, arquivo_manifesto)
    LOG.info(f"Fase I OK: {len(entradas_manifesto)} entradas -> {arquivo_manifesto}")

    # ----- FASE II: Deteccao -----
    run.deteccoes_dir.mkdir(parents=True, exist_ok=True)
    detector = DetectorMegaDetectorV6()
    resultados_det: list[ResultadoDeteccao] = []
    deteccoes_por_imagem: dict[str, list[BoundingBox]] = {}
    for entrada in entradas_manifesto:
        caminho = pasta_brutas / entrada.caminho_relativo
        resultado = detector.detectar(caminho, limite_confianca=confianca_min_deteccao)
        resultados_det.append(resultado)
        deteccoes_por_imagem[str(caminho)] = [d.bbox for d in resultado.deteccoes]
    arquivo_det = run.deteccoes_dir / "deteccoes.json"
    salvar_deteccoes_json(resultados_det, arquivo_det)
    n_animal = sum(
        1 for r in resultados_det for d in r.deteccoes if d.categoria == "animal"
    )
    LOG.info(f"Fase II OK: {n_animal} bboxes 'animal' -> {arquivo_det}")

    # ----- FASE III: Classificacao + Crops -----
    run.classificacoes_dir.mkdir(parents=True, exist_ok=True)
    classificador = ClassificadorSpeciesNet(config_decisor=ConfigDecisor())
    classificacoes = []
    for resultado in resultados_det:
        for i, det in enumerate(resultado.deteccoes):
            if det.categoria != "animal":
                continue
            crop_entrada = CropEntrada(
                media_path=Path(resultado.media_path),
                bbox=det.bbox,
                indice=i,
            )
            classificacoes.append(classificador.classificar(crop_entrada))
    arquivo_clf = run.classificacoes_dir / "classificacoes.json"
    salvar_classificacoes_json(classificacoes, arquivo_clf)
    n_felis = sum(1 for c in classificacoes if c.status == STATUS_FELIS_CATUS)
    LOG.info(f"Fase III OK: {n_felis} crops felis_catus -> {arquivo_clf}")

    # ----- Recorte de crops aprovados (ponte para Fase IV) -----
    crops = persistir_crops_felis_catus(
        classificacoes, deteccoes_por_imagem, run.crops_dir,
    )
    LOG.info(f"Crops persistidos: {len(crops)} -> {run.crops_dir}")

    # ----- Copia anotacao de identidade (dev) se fornecida -----
    if anotacao_identidade_origem and anotacao_identidade_origem.exists():
        run.anotacao_path.write_text(
            anotacao_identidade_origem.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    # ----- FASE IV: Embeddings -----
    n_emb = 0
    if crops:
        from PIL import Image

        extrator = ExtratorMegaDescriptor()
        embeddings = []
        for crop in crops:
            img = Image.open(crop.caminho_crop).convert("RGB")
            embedding = extrator.extrair_de_pil(
                media_path=crop.media_path_original,
                bbox_indice=crop.bbox_indice,
                crop_img=img,
            )
            embeddings.append(embedding)
        if embeddings:
            matriz = np.array([e.vetor for e in embeddings], dtype=np.float32)
            ids = np.array([f"{e.media_path}#bbox{e.bbox_indice}" for e in embeddings])
            gravar_npz(run.embeddings_path, vetores=matriz, ids=ids)
            LOG.info(f"Fase IV OK: {len(embeddings)} embeddings -> {run.embeddings_path}")
        n_emb = len(embeddings)
    else:
        LOG.warning("Nenhum crop felis_catus -- Fase IV pulada")

    # ----- Avaliacao Re-ID sobre crops da cascata (se houver anotacao) -----
    if run.anotacao_path.exists() and n_emb > 0:
        try:
            rotulos = ler_json(run.anotacao_path)
            relatorio_reid = _avaliar_reid_cascata(run.embeddings_path, rotulos)
            gravar_json(relatorio_reid, run.avaliacao_path)
            LOG.info(
                f"Avaliacao cascata: top1={relatorio_reid.get('top_1', 'N/A')} "
                f"-> {run.avaliacao_path}"
            )
        except Exception as exc:  # noqa: BLE001
            LOG.warning(f"Avaliacao da cascata falhou: {exc}")

    return RelatorioCascata(
        n_brutas=len(brutas),
        n_manifesto=len(entradas_manifesto),
        n_deteccoes_animal=n_animal,
        n_classificacoes_felis_catus=n_felis,
        n_crops_gerados=len(crops),
        n_embeddings=n_emb,
        sucesso=True,
    )


def _avaliar_reid_cascata(
    arquivo_embeddings: Path,
    rotulos: dict[str, str],
) -> dict:
    """Avalia Top-1 sobre os crops da propria cascata (catalogo = ele mesmo).

    Cada crop e tratado como query; a galeria sao os demais crops do mesmo
    ID. Util como sanidade qualitativa do pipeline integrado.
    """
    from felinet.utils.io import ler_npz

    dados = ler_npz(arquivo_embeddings)
    vetores = dados["vetores"]
    ids_str = dados["ids"]

    rotulos_efetivos = []
    indices_rotulados = []
    for i, ident in enumerate(ids_str):
        chave = str(ident)
        if chave in rotulos:
            rotulos_efetivos.append(rotulos[chave])
            indices_rotulados.append(i)
    if len(set(rotulos_efetivos)) < 2:
        return {
            "observacao": "Insuficiente para avaliacao (menos de 2 IDs distintos).",
            "n_crops_rotulados": len(rotulos_efetivos),
        }

    matriz = vetores[indices_rotulados]
    rotulos_arr = np.array(rotulos_efetivos)
    sim = matriz @ matriz.T
    np.fill_diagonal(sim, -np.inf)
    melhor_match = sim.argmax(axis=1)
    acertos = rotulos_arr[melhor_match] == rotulos_arr
    return {
        "n_crops_rotulados": len(rotulos_efetivos),
        "n_ids_distintos": int(len(set(rotulos_efetivos))),
        "top_1": float(acertos.mean()),
        "observacao": "Avaliacao qualitativa sobre crops da cascata; sem ground-truth externo.",
    }
