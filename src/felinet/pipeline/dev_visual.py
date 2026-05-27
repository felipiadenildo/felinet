"""Galeria visual didática para o modo ``--dev`` do pipeline.

A intenção do modo ``--dev`` é permitir inspeção humana do que cada fase do
pipeline aceitou, descartou e por quê. Esta implementação é deliberadamente
leve: cria a estrutura de subpastas e os CSVs de motivos por fase, e expõe
helpers (``desenhar_bbox``) que as fases podem usar opcionalmente para
salvar miniaturas com bbox sobreposta.

Layout produzido em ``run.raiz/dev_visualizacao/``::

    01_ingestao/motivos.csv
    02_deteccao/deteccoes.csv
    03_classificacao/classificacoes.csv

Cada CSV usa cabeçalho explícito e é seguro de gerar mesmo sem GPU/modelos
pesados (as fases que falharem por falta de modelo simplesmente não
adicionam linhas, mas o arquivo persiste).
"""

from __future__ import annotations

import csv
from pathlib import Path

CABECALHO_INGESTAO = ["nome_arq", "motivo", "detalhe"]
CABECALHO_DETECCAO = ["nome_arq", "n_bbox", "max_score", "decisao"]
CABECALHO_CLASSIFICACAO = ["nome_arq", "idx_crop", "classe", "score"]


def preparar_estrutura(raiz_run: Path) -> Path:
    """Cria ``raiz_run/dev_visualizacao/`` com subpastas e CSVs vazios.

    Retorna o ``Path`` da raiz da galeria.
    """
    base = raiz_run / "dev_visualizacao"
    subpastas = {
        "01_ingestao": CABECALHO_INGESTAO,
        "02_deteccao": CABECALHO_DETECCAO,
        "03_classificacao": CABECALHO_CLASSIFICACAO,
    }
    nomes_csv = {
        "01_ingestao": "motivos.csv",
        "02_deteccao": "deteccoes.csv",
        "03_classificacao": "classificacoes.csv",
    }
    base.mkdir(parents=True, exist_ok=True)
    for sub, header in subpastas.items():
        (base / sub).mkdir(parents=True, exist_ok=True)
        arq = base / sub / nomes_csv[sub]
        if not arq.exists():
            with arq.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)
    return base


def registrar_ingestao(
    base: Path, nome_arq: str, motivo: str, detalhe: str = ""
) -> None:
    """Acrescenta uma linha em ``01_ingestao/motivos.csv``.

    ``motivo`` é um slug curto (``aceita``, ``hash_dup``, ``formato_invalido``,
    ``corrompida``); ``detalhe`` é texto livre opcional.
    """
    arq = base / "01_ingestao" / "motivos.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, motivo, detalhe])


def registrar_deteccao(
    base: Path,
    nome_arq: str,
    n_bbox: int,
    max_score: float,
    decisao: str,
) -> None:
    """Acrescenta uma linha em ``02_deteccao/deteccoes.csv``.

    ``decisao`` ∈ {``com_animal``, ``sem_animal``, ``abaixo_limiar``}.
    """
    arq = base / "02_deteccao" / "deteccoes.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, n_bbox, f"{max_score:.3f}", decisao])


def registrar_classificacao(
    base: Path,
    nome_arq: str,
    idx_crop: int,
    classe: str,
    score: float,
) -> None:
    """Acrescenta uma linha em ``03_classificacao/classificacoes.csv``."""
    arq = base / "03_classificacao" / "classificacoes.csv"
    with arq.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([nome_arq, idx_crop, classe, f"{score:.3f}"])


def desenhar_bbox(
    img_path: Path,
    bboxes: list[tuple[float, float, float, float]],
    scores: list[float],
    limiar: float,
    saida: Path,
    cor_aceita: str = "green",
    cor_recusa: str = "red",
) -> None:
    """Desenha bboxes em uma imagem e grava em ``saida``.

    Bboxes com ``score >= limiar`` saem em verde; abaixo do limiar em
    vermelho. Útil para popular ``02_deteccao/com_animal`` e
    ``02_deteccao/abaixo_limiar``.
    """
    from PIL import Image, ImageDraw

    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for (x1, y1, x2, y2), s in zip(bboxes, scores, strict=False):
        cor = cor_aceita if s >= limiar else cor_recusa
        draw.rectangle([x1, y1, x2, y2], outline=cor, width=3)
        draw.text((x1, max(0, y1 - 12)), f"{s:.2f}", fill=cor)
    saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, quality=85)


# ============================================================
# Geração do resumo HTML navegável
# ============================================================

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>felinet — galeria dev_visualizacao</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 24px;
         background: #f5f5f7; color: #1d1d1f; }}
  h1   {{ font-size: 22px; margin: 0 0 4px; }}
  h2   {{ font-size: 18px; margin: 32px 0 8px; color: #333; }}
  h3   {{ font-size: 14px; margin: 12px 0 6px; color: #555; font-weight: 600; }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 16px; }}
  .stats {{ background: #fff; border-radius: 8px; padding: 12px 16px;
            display: inline-block; margin: 4px 8px 4px 0; font-size: 13px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .stats b {{ color: #007aff; }}
  .grid {{ display: grid;
           grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
           gap: 8px; margin-top: 8px; }}
  .cell {{ background: #fff; border-radius: 6px; overflow: hidden;
           box-shadow: 0 1px 2px rgba(0,0,0,0.06); }}
  .cell img {{ width: 100%; height: 140px; object-fit: cover; display: block; }}
  .cell .legenda {{ padding: 6px 8px; font-size: 11px; color: #444;
                    word-break: break-all; line-height: 1.3; }}
  .vazio {{ color: #888; font-style: italic; padding: 8px 0; }}
  details {{ background: #fff; border-radius: 8px; padding: 8px 16px;
             margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  summary {{ cursor: pointer; font-weight: 600; padding: 4px 0; }}
</style>
</head>
<body>
<h1>felinet — galeria didática (modo --dev)</h1>
<div class="meta">{meta}</div>
{secoes}
</body>
</html>
"""


def _coletar_amostra(pasta: Path, max_n: int = 24) -> list[Path]:
    """Retorna até ``max_n`` arquivos de imagem na pasta, ordenados."""
    if not pasta.is_dir():
        return []
    extensoes = {".jpg", ".jpeg", ".png", ".webp"}
    arquivos = sorted(
        p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in extensoes
    )
    return arquivos[:max_n]


def _renderizar_galeria(
    titulo: str, pasta: Path, base_html: Path, max_n: int = 24
) -> str:
    """Renderiza uma seção HTML com galeria de imagens de uma pasta."""
    arquivos = _coletar_amostra(pasta, max_n=max_n)
    if not arquivos:
        return f'<h3>{titulo} <span class="vazio">(vazio)</span></h3>'
    total = sum(1 for p in pasta.iterdir() if p.is_file()) if pasta.is_dir() else 0
    mais = f" (mostrando {len(arquivos)} de {total})" if total > len(arquivos) else ""
    cells = []
    for arq in arquivos:
        rel = arq.relative_to(base_html.parent).as_posix()
        cells.append(
            f'<div class="cell"><a href="{rel}" target="_blank">'
            f'<img src="{rel}" alt="{arq.name}" loading="lazy"></a>'
            f'<div class="legenda">{arq.name}</div></div>'
        )
    return (
        f"<h3>{titulo}{mais}</h3>"
        f'<div class="grid">{"".join(cells)}</div>'
    )


def _contar_linhas_csv(arq: Path) -> int:
    """Conta linhas de dados em um CSV (excluindo cabeçalho)."""
    if not arq.exists():
        return 0
    with arq.open("r", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)

def _contar_csv_por_coluna(arq: Path, coluna: str) -> dict[str, int]:
    """Conta ocorrências de cada valor único de ``coluna`` em um CSV.

    Retorna dict ``{valor: n}``. Vazio se o arquivo não existir ou a coluna
    não estiver presente.
    """
    if not arq.exists():
        return {}
    contagem: dict[str, int] = {}
    with arq.open("r", encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames is None or coluna not in leitor.fieldnames:
            return {}
        for linha in leitor:
            v = (linha.get(coluna) or "").strip()
            if not v:
                continue
            contagem[v] = contagem.get(v, 0) + 1
    return contagem


def gerar_resumo_html(base: Path, titulo_run: str = "") -> Path:
    """Gera ``base/resumo.html`` consolidando a galeria das 3 fases.

    ``base`` é a raiz da ``dev_visualizacao/`` (não a raiz do run). Lê os
    CSVs para estatísticas, lista as imagens em cada subpasta e produz um
    HTML único navegável.
    """
    if not base.is_dir():
        raise FileNotFoundError(f"pasta dev_visualizacao não existe: {base}")

    arq_html = base / "resumo.html"

    # ----- Fase 1: ingestão -----
    f1 = base / "01_ingestao"
    arq_motivos = f1 / "motivos.csv"
    contagem_ing = _contar_csv_por_coluna(arq_motivos, "motivo")
    n_aceitas = contagem_ing.get("aceita", 0)
    n_rejeitadas = sum(v for k, v in contagem_ing.items() if k != "aceita")
    n_motivos = _contar_linhas_csv(arq_motivos)
    sec_f1 = (
        "<h2>Fase 1 — Ingestão</h2>"
        f'<div class="stats">aceitas: <b>{n_aceitas}</b></div>'
        f'<div class="stats">rejeitadas: <b>{n_rejeitadas}</b></div>'
        f'<div class="stats">registros CSV: <b>{n_motivos}</b></div>'
        '<details><summary>motivos.csv</summary>'
        '<p>Veja <a href="01_ingestao/motivos.csv">01_ingestao/motivos.csv</a> '
        "para detalhes de cada decisão.</p></details>"
        + _renderizar_galeria("Aceitas", f1 / "aceitas", arq_html)
        + _renderizar_galeria("Rejeitadas", f1 / "rejeitadas", arq_html)
    )

    # ----- Fase 2: detecção -----
    f2 = base / "02_deteccao"
    arq_det = f2 / "deteccoes.csv"
    contagem_det = _contar_csv_por_coluna(arq_det, "decisao")
    n_com = contagem_det.get("com_animal", 0)
    n_sem = contagem_det.get("sem_animal", 0)
    n_low = contagem_det.get("abaixo_limiar", 0)
    n_det = _contar_linhas_csv(arq_det)
    sec_f2 = (
        "<h2>Fase 2 — Detecção (MegaDetector)</h2>"
        f'<div class="stats">com animal: <b>{n_com}</b></div>'
        f'<div class="stats">sem animal: <b>{n_sem}</b></div>'
        f'<div class="stats">abaixo do limiar: <b>{n_low}</b></div>'
        f'<div class="stats">registros CSV: <b>{n_det}</b></div>'
        '<details><summary>deteccoes.csv</summary>'
        '<p>Veja <a href="02_deteccao/deteccoes.csv">02_deteccao/deteccoes.csv</a> '
        "para coordenadas e scores de cada bbox.</p></details>"
        + _renderizar_galeria("Com animal (bbox verde)", f2 / "com_animal", arq_html)
        + _renderizar_galeria("Abaixo do limiar (bbox vermelha)", f2 / "abaixo_limiar", arq_html)
        + _renderizar_galeria("Sem animal", f2 / "sem_animal", arq_html)
    )

    # ----- Fase 3: classificação -----
    f3 = base / "03_classificacao"
    arq_cls = f3 / "classificacoes.csv"
    contagem_cls = _contar_csv_por_coluna(arq_cls, "classe")
    n_felis = contagem_cls.get("felis_catus", 0)
    n_outros = sum(v for k, v in contagem_cls.items() if k != "felis_catus")
    n_cls = _contar_linhas_csv(arq_cls)
    sec_f3 = (
        "<h2>Fase 3 — Classificação (SpeciesNet Felis-vs-resto)</h2>"
        f'<div class="stats">felis_catus: <b>{n_felis}</b></div>'
        f'<div class="stats">outros: <b>{n_outros}</b></div>'
        f'<div class="stats">registros CSV: <b>{n_cls}</b></div>'
        '<details><summary>classificacoes.csv</summary>'
        '<p>Veja <a href="03_classificacao/classificacoes.csv">03_classificacao/classificacoes.csv</a> '
        "para a classe e score de cada crop.</p></details>"
        + _renderizar_galeria("Classificados como felis_catus", f3 / "felis_catus", arq_html)
        + _renderizar_galeria("Classificados como outros", f3 / "outros", arq_html)
    )

    meta = titulo_run or f"galeria gerada de {base}"
    html = _HTML_TEMPLATE.format(meta=meta, secoes=sec_f1 + sec_f2 + sec_f3)
    arq_html.write_text(html, encoding="utf-8")
    return arq_html
