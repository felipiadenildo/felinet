# B5 — Plano de validação e implementação (Parte 3)

**Parte 3 cobre:** B5.11 (piloto offline com 5 vídeos representativos), B5.12 (pipeline fim-a-fim E0→E4 + dashboard Streamlit), B5.13 (confronto A2.0 × resultados), B5.14 (reprodutibilidade total: Docker + DVC remote + checksums), B5.15 (limitações e trabalho futuro), B5.16 (checklist final de B5)
**Continuidade:** Parte 1 (setup + repo + datasets + protocolo) e Parte 2 (wrappers + scripts + métricas + figuras) estão entregues. Parte 3 fecha B5. Próximo: **B6 — Consolidação final da Etapa 2**.

---

## B5.11 — Piloto offline em laboratório

### B5.11.1 — Por que piloto offline (e não em campo)

Conforme PDF Sec. 3.2 do projeto base e diretrizes consolidadas, **o TCC não envolve instalação física de câmeras no Campus 2**. A validação prática se dá através de:

1. **Datasets públicos** (B5.6-B5.8): respondem "os modelos funcionam em dados de referência?"
2. **Piloto offline** (esta seção): responde "a pipeline completa funciona fim-a-fim no PC do Felipi, com dados que se parecem com o que esperamos do campus?"

A combinação dos dois cobre o que a banca esperaria de um "experimento prático" sem expor o projeto aos riscos de campo (mau tempo, vandalismo, autorizações pendentes — listados em PDF Sec. 9).

### B5.11.2 — Os 5 vídeos representativos

Construímos 5 vídeos que **simulam** o que cada um dos 5 perfis de aquisição (Categoria I/PIR e II/VMD definidos em B3) entregaria para a pipeline. A composição é feita com **dados públicos + simulação controlada**.

| ID | Perfil | Origem dos clips | Duração | FPS | Resolução | Simula |
|---|---|---|---|---|---|---|
| **V1** | **A** — trail wildlife | YouTube cat videos + clips Crawford recortados | 5 min | 15 | 1920×1080 | trail cam noturna IR no P4 |
| **V2** | **B** — IP cam + Pi (Frigate) | HelloStreetCat + CatFLW concatenados | 8 min | 25 | 1920×1080 | IP cam ONVIF contínua no P1 |
| **V3** | **D** — Tapo/Reolink consumer + PIR | Cat Individual Images em sequência | 4 min | 15 | 2560×1440 | Tapo C400 com PIR no P2 |
| **V4** | **E1** — OEM Anyka + SD swap | Mix HelloStreetCat + Crawford com timestamps controlados | 6 min | 10 | 1280×720 | câmera genérica AC+SD no P3 |
| **V5** | **E2** — OEM RTSP pull | RTSP estimulado por ffmpeg de loop em arquivo | 10 min | 12 | 1920×1080 | câmera genérica via RTSP no P7 |

**Construção:** os vídeos não são produzidos do zero — são **montagens com ffmpeg** a partir dos datasets já baixados. Esta abordagem é cientificamente honesta porque (a) preservamos rastreabilidade total dos clips originais e (b) controlamos completamente a verdade-de-base (sabemos quais gatos, quantos, em que momento).

### B5.11.3 — Script de construção dos vídeos

`scripts/build_pilot_videos.py`:

```python
"""
Monta 5 vídeos representativos a partir dos datasets já baixados.

Cada vídeo:
  - usa ffmpeg para concatenar imagens/clips em sequência
  - injeta timestamps EXIF coerentes com o perfil simulado
  - aplica degradação visual quando relevante (IR cinza, ruído noturno)
  - exporta para data/pilot_videos/V{1..5}_{perfil}.mp4
  - salva data/pilot_videos/V{1..5}_groundtruth.csv com (frame_idx, individual_id, n_cats)
"""
import argparse, subprocess, json
from pathlib import Path
import cv2, numpy as np, pandas as pd

PILOT_DIR = Path("data/pilot_videos")
PILOT_DIR.mkdir(parents=True, exist_ok=True)


def make_ground_truth(video_id: str, frames_metadata: list[dict]):
    """Salva CSV com (frame_idx, individual_id, n_cats, perfil_simulado)"""
    df = pd.DataFrame(frames_metadata)
    df.to_csv(PILOT_DIR / f"{video_id}_groundtruth.csv", index=False)


def build_V1_trail_wildlife():
    """V1 - Trail cam noturna IR. Frames esparsos, IR (cinza), ruído.
    Source: amostra do Crawford com conversão para cinza + ruído gaussiano."""
    images = sorted(Path("data/raw/cat_dataset_crawford").rglob("*.jpg"))[:75]
    frames_meta = []
    tmp_dir = PILOT_DIR / "_tmp_V1"
    tmp_dir.mkdir(exist_ok=True)

    for i, img_path in enumerate(images):
        img = cv2.imread(str(img_path))
        if img is None: continue
        # Conversão para escala de cinza estilo IR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        # Ruído gaussiano (simula ISO alto noturno)
        noise = np.random.normal(0, 8, gray.shape).astype(np.uint8)
        gray = cv2.add(gray, noise)
        # Overlay timestamp + temperatura
        cv2.putText(gray, f"2026-03-15 22:{30+i//4:02d}:{(i*7)%60:02d}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(gray, "TEMP 18C IR-ON", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        out_path = tmp_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(out_path), gray)
        frames_meta.append({"frame_idx": i, "individual_id": f"trail_cat_{i%4}",
                            "n_cats": 1, "perfil": "A"})

    subprocess.run([
        "ffmpeg", "-y", "-framerate", "15", "-i", str(tmp_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-metadata", "comment=Pilot V1 - Trail cam IR (sintetizado)",
        str(PILOT_DIR / "V1_trail_wildlife.mp4")
    ], check=True)
    make_ground_truth("V1_trail_wildlife", frames_meta)
    print("[OK] V1 gerado")


def build_V2_ipcam_pi_frigate():
    """V2 - IP cam contínua. Frames densos, qualidade alta, sem ruído."""
    images = sorted(Path("data/raw/hellostreetcat").rglob("*.jpg"))[:200]
    frames_meta = []
    tmp_dir = PILOT_DIR / "_tmp_V2"; tmp_dir.mkdir(exist_ok=True)
    for i, p in enumerate(images):
        img = cv2.imread(str(p))
        if img is None: continue
        cv2.putText(img, f"ONVIF P1 2026-03-15 14:{i//60:02d}:{i%60:02d}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imwrite(str(tmp_dir / f"frame_{i:04d}.png"), img)
        frames_meta.append({"frame_idx": i, "individual_id": f"hs_cat_{(i//10)%12}",
                            "n_cats": 1, "perfil": "B"})

    subprocess.run([
        "ffmpeg", "-y", "-framerate", "25", "-i", str(tmp_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(PILOT_DIR / "V2_ipcam_pi_frigate.mp4")
    ], check=True)
    make_ground_truth("V2_ipcam_pi_frigate", frames_meta)
    print("[OK] V2 gerado")


def build_V3_consumer_pir():
    """V3 - Tapo/Reolink. Clips curtos disparados por PIR (cada 'evento' = 8 segundos)."""
    # implementação análoga: 12 eventos de 8s, 15 fps, 2560x1440
    pass

def build_V4_oem_sd_swap():
    """V4 - OEM Anyka. Resolução 720p, FPS 10, timestamps grudados na imagem."""
    pass

def build_V5_oem_rtsp():
    """V5 - OEM RTSP. Vídeo contínuo simulando stream H.264, 12 fps."""
    pass


VIDEOS = {
    "V1": build_V1_trail_wildlife,
    "V2": build_V2_ipcam_pi_frigate,
    "V3": build_V3_consumer_pir,
    "V4": build_V4_oem_sd_swap,
    "V5": build_V5_oem_rtsp,
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", choices=list(VIDEOS.keys()) + ["all"], default="all")
    args = ap.parse_args()
    if args.video == "all":
        for fn in VIDEOS.values(): fn()
    else:
        VIDEOS[args.video]()
```

O Felipi rodaria:

```bash
uv run python scripts/build_pilot_videos.py --video all
ls -lh data/pilot_videos/
```

### B5.11.4 — Tabela de simulação por perfil

Para cada vídeo, o piloto **mede explicitamente** o que diferencia os perfis de B3:

| Item medido | V1 (A) | V2 (B) | V3 (D) | V4 (E1) | V5 (E2) |
|---|---|---|---|---|---|
| **Latência E0→E1** | dias (SD swap manual) | minutos (Frigate snapshot) | minutos (cloud sync) | dias (SD swap manual) | minutos (RTSP) |
| **Volume bruto/min vídeo** | ~5 MB | ~120 MB | ~30 MB (eventos) | ~30 MB | ~80 MB |
| **% mídia útil pós-E0** | 90% (PIR já filtra) | 5% (VMD precisa filtrar) | 80% (PIR + cloud filtra) | 30% (VMD básico no PC) | 5% (VMD precisa filtrar) |
| **Robustez a chuva** | alta (selado IP65) | média (depende do mount) | alta | baixa-média | média |
| **Custo/ponto (B3.5)** | R$ 800-1200 | R$ 1500-2400 | R$ 300-600 | R$ 80-150 | R$ 80-150 |
| **Custo de operação** | troca SD quinzenal | só energia AC | troca bateria mensal | troca SD mensal | só energia AC |

Esta tabela alimenta diretamente a **Discussão** da monografia: trade-offs reais por perfil.

---

## B5.12 — Pipeline fim-a-fim E0→E4

### B5.12.1 — Orquestrador `run_pilot.py`

`scripts/run_pilot.py`:

```python
"""
Roda a pipeline completa E0→E4 sobre os vídeos do piloto.
Popula SQLite seguindo schema B4.4 (Camtrap-DP + extensões).

Saídas:
  results/pilot/pilot.sqlite          (banco populado, vai para DVC)
  results/pilot/pipeline_log.json     (timing por estágio)
  results/pilot/figures/*.png         (estatísticas finais)
"""
import argparse, json, time, uuid
from pathlib import Path
from datetime import datetime, timezone
import cv2, pandas as pd, numpy as np
from tqdm import tqdm

from tcc_gatosdoc2.pipeline.e0_ingestion import IngestionStage
from tcc_gatosdoc2.pipeline.e1_detection import DetectionStage
from tcc_gatosdoc2.pipeline.e2_species import SpeciesStage
from tcc_gatosdoc2.pipeline.e3_reid import ReIDStage
from tcc_gatosdoc2.pipeline.e4_indicators import IndicatorsStage
from tcc_gatosdoc2.db.session import init_db, get_session
from tcc_gatosdoc2.utils.runtime_log import snapshot_runtime


def main(videos_dir: str, output_dir: str):
    videos = sorted(Path(videos_dir).glob("V*.mp4"))
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    snapshot_runtime(out)

    db_path = out / "pilot.sqlite"
    init_db(db_path)
    session = get_session(db_path)

    timings = {}

    # Instancia estágios uma vez (modelos carregados em memória)
    e0 = IngestionStage()
    e1 = DetectionStage(model_name="yolo11n")
    e2 = SpeciesStage(model_name="speciesnet")
    e3 = ReIDStage(model_name="miewid_msv3")
    e4 = IndicatorsStage()

    for video in videos:
        print(f"\n=== Processando {video.name} ===")
        video_timings = {}

        # === E0 — Ingestão ===
        t0 = time.perf_counter()
        media_records = e0.ingest_video(video, session=session)
        video_timings["E0_ingestion_s"] = time.perf_counter() - t0
        print(f"  E0: {len(media_records)} mídias ingeridas em {video_timings['E0_ingestion_s']:.1f}s")

        # === E1 — Detecção ===
        t0 = time.perf_counter()
        observations = e1.run(media_records, session=session)
        video_timings["E1_detection_s"] = time.perf_counter() - t0
        print(f"  E1: {len(observations)} detecções em {video_timings['E1_detection_s']:.1f}s")

        # === E2 — Espécie ===
        t0 = time.perf_counter()
        species_results = e2.run(observations, session=session)
        cat_count = sum(1 for o in species_results if o.scientific_name == "Felis catus")
        video_timings["E2_species_s"] = time.perf_counter() - t0
        print(f"  E2: {cat_count}/{len(species_results)} confirmadas como Felis catus")

        # === E3 — Re-ID ===
        t0 = time.perf_counter()
        reid_results = e3.run(species_results, session=session)
        unique_ids = len({r.individual_id for r in reid_results if r.individual_id})
        video_timings["E3_reid_s"] = time.perf_counter() - t0
        print(f"  E3: {unique_ids} indivíduos distintos")

        # === E4 — Indicadores ===
        t0 = time.perf_counter()
        indicators = e4.compute_for_deployment(
            deployment_id=str(video.stem), session=session,
        )
        video_timings["E4_indicators_s"] = time.perf_counter() - t0
        timings[video.name] = video_timings

    (out / "pipeline_log.json").write_text(json.dumps(timings, indent=2))
    print(f"\n[OK] Pipeline completa. Banco em {db_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", default="data/pilot_videos")
    ap.add_argument("--output", default="results/pilot")
    args = ap.parse_args()
    main(args.videos, args.output)
```

### B5.12.2 — Dashboard Streamlit

`src/tcc_gatosdoc2/viz/dashboard.py`:

```python
"""
Dashboard Streamlit consumindo results/pilot/pilot.sqlite.
Exibido no defesa do TCC como prova de conceito viva.

Roda com:  uv run streamlit run src/tcc_gatosdoc2/viz/dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import sqlite3
from pathlib import Path

DB = Path("results/pilot/pilot.sqlite")

st.set_page_config(page_title="Gatosdoc2 — Monitoramento", layout="wide")
st.title("🐈 Sistema de Monitoramento — Colônia Gatosdoc2 (USP São Carlos)")
st.caption("Demonstração do piloto offline — TCC Felipi & Bárbara")

if not DB.exists():
    st.error("Banco do piloto não encontrado. Rode `make pilot` antes.")
    st.stop()

conn = sqlite3.connect(DB)

# KPIs principais
col1, col2, col3, col4 = st.columns(4)
n_individuals = conn.execute("SELECT COUNT(*) FROM individuals").fetchone()[0]
n_obs = conn.execute("SELECT COUNT(*) FROM observations WHERE observationType='animal'").fetchone()[0]
n_ear_tipped = conn.execute("SELECT COUNT(*) FROM individuals WHERE earTipped=1").fetchone()[0]
n_deployments = conn.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
col1.metric("Indivíduos detectados", n_individuals)
col2.metric("Observações totais", n_obs)
col3.metric("Castrados (ear-tip)", f"{n_ear_tipped} ({100*n_ear_tipped/max(n_individuals,1):.0f}%)")
col4.metric("Pontos monitorados", n_deployments)

# Mapa dos pontos
st.subheader("📍 Pontos monitorados")
deployments = pd.read_sql("SELECT * FROM deployments", conn)
if not deployments.empty:
    m = folium.Map(
        location=[deployments.latitude.mean(), deployments.longitude.mean()],
        zoom_start=17,
    )
    for _, r in deployments.iterrows():
        folium.Marker(
            [r.latitude, r.longitude],
            popup=f"{r.locationName}<br>Câmera: {r.cameraModel}",
            tooltip=r.locationID,
        ).add_to(m)
    st_folium(m, height=400)

# Visitação por ponto/hora
st.subheader("⏱️ Visitação por ponto e hora")
visits = pd.read_sql("""
    SELECT d.locationID AS ponto,
           CAST(strftime('%H', m.timestamp) AS INTEGER) AS hora,
           COUNT(*) AS visitas
    FROM observations o
    JOIN media m ON m.mediaID = o.mediaID
    JOIN deployments d ON d.deploymentID = o.deploymentID
    WHERE o.observationType = 'animal' AND o.scientificName = 'Felis catus'
    GROUP BY ponto, hora
""", conn)
if not visits.empty:
    fig = px.density_heatmap(visits, x="hora", y="ponto", z="visitas",
                              color_continuous_scale="Viridis")
    st.plotly_chart(fig, use_container_width=True)

# Indivíduos
st.subheader("👤 Indivíduos identificados")
indv = pd.read_sql("""
    SELECT individualID, nickname, sex, lifeStage, earTipped, status,
           firstSeen, lastSeen
    FROM individuals ORDER BY lastSeen DESC
""", conn)
st.dataframe(indv, use_container_width=True)

# Re-ID confiabilidade
st.subheader("🔬 Confiabilidade da reidentificação")
matches = pd.read_sql("""
    SELECT model, decision, COUNT(*) AS n, AVG(similarity) AS sim_media
    FROM match_history GROUP BY model, decision
""", conn)
if not matches.empty:
    fig2 = px.bar(matches, x="model", y="n", color="decision", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)
```

Execução:

```bash
uv run streamlit run src/tcc_gatosdoc2/viz/dashboard.py
# Abre em http://localhost:8501
```

### B5.12.3 — Saída esperada do piloto (formato de "captura de tela" para a monografia)

A monografia inclui screenshots do dashboard rodando. Para o capítulo de Resultados, gere as capturas com:

```bash
# Use o helper screenshot_dashboard.py
uv run python scripts/screenshot_dashboard.py --port 8501 --output results/figures/
```

Que gera:
- `fig_dashboard_overview.png` — KPIs + mapa
- `fig_dashboard_visitation.png` — heatmap de visitação
- `fig_dashboard_individuals.png` — tabela de indivíduos
- `fig_dashboard_reid.png` — gráfico de confiabilidade

---

## B5.13 — Confronto requisitos A2.0 × resultados medidos

Esta é **a tabela mais importante da monografia para a banca**. Materializa em uma única visão se o sistema "passou" ou "não passou".

### B5.13.1 — Estrutura da tabela

`scripts/generate_requirements_table.py` lê:
- `revisao_tcc/etapa2/A2.0_requisitos_sistema.md` (NFRs e métricas-alvo)
- `results/e1/*/metrics.json`, `results/e2/*/metrics.json`, `results/e3/*/metrics.json`
- `results/pilot/pipeline_log.json`

E produz `results/figures/table_requirements_vs_results.tex`:

| ID Req. | Requisito (de A2.0) | Métrica | Valor-alvo | Valor medido | Status |
|---|---|---|---|---|---|
| **NFR-001** | Detecção de gato em imagem com IoU ≥ 0.5 | mAP@0.5 | ≥ 0.80 | (preencher após bench) | ✓ / ✗ |
| **NFR-002** | Classificação de espécie `Felis catus` | Recall | ≥ 0.95 | — | — |
| **NFR-003** | Reidentificação individual | Rank-1 | ≥ 0.85 | — | — |
| **NFR-004** | Reidentificação individual | mAP | ≥ 0.75 | — | — |
| **NFR-005** | Reidentificação — equilíbrio known/unknown | BAKS, BAUS | ≥ 0.80 | — | — |
| **NFR-006** | Janela batch noturna | Tempo total | ≤ 8 h | — | — |
| **NFR-007** | Storage mensal pós-filtragem | Volume | ≤ 200 GB | — | — |
| **NFR-008** | Funcionamento offline | Operação sem internet | binário | sim/não | — |
| **NFR-009** | Conformidade Camtrap-DP | Validação `frictionless validate` | passa | — | — |
| **NFR-010** | Anonimização LGPD | Sem rostos humanos no DB | binário | sim/não | — |

### B5.13.2 — Geração automática da tabela

```python
# scripts/generate_requirements_table.py (esqueleto)
import json
import re
from pathlib import Path

NFRS = {
    "NFR-001": {
        "desc": "Detecção de gato (IoU >= 0.5)",
        "metric": "mAP@0.5",
        "target": 0.80,
        "source": "results/e1/yolo11n/*/metrics.json",
        "extract": lambda j: max(d["mAP@0.5"] for d in j["per_dataset"].values()),
    },
    "NFR-002": {
        "desc": "Recall Felis catus",
        "metric": "felis_catus_recall",
        "target": 0.95,
        "source": "results/e2/speciesnet/*/metrics.json",
        "extract": lambda j: j["felis_catus_recall"],
    },
    "NFR-003": {
        "desc": "Re-ID Rank-1",
        "metric": "rank_1",
        "target": 0.85,
        "source": "results/e3/miewid_msv3/*/metrics.json",
        "extract": lambda j: np.mean([d["rank_1"] for d in j["per_dataset"].values()]),
    },
    # ...continua para NFR-004 a NFR-010
}

def latest(glob_pattern: str):
    files = sorted(Path(".").glob(glob_pattern))
    return json.loads(files[-1].read_text()) if files else None

rows = []
for rid, spec in NFRS.items():
    j = latest(spec["source"])
    measured = spec["extract"](j) if j else None
    status = "✓" if (measured is not None and measured >= spec["target"]) else "✗"
    rows.append({
        "id": rid, "desc": spec["desc"], "metric": spec["metric"],
        "target": spec["target"], "measured": measured, "status": status,
    })
# Gera markdown + LaTeX
...
```

### B5.13.3 — Como ler o resultado na monografia

A monografia (capítulo Resultados → Discussão) discutirá **cada NFR individualmente**:
- Se ✓: explicar por que e em que regime
- Se ✗: explicar por que falhou e proposta de mitigação (volta para B6 → Trabalho Futuro)

Esta postura honesta é exatamente o que a banca espera (e o que o PDF Sec. 9 antecipou como mitigação do risco "teórico demais").

---

## B5.14 — Reprodutibilidade total

### B5.14.1 — Princípios de FAIR + executável

O projeto adota os 4 princípios FAIR (Findable, Accessible, Interoperable, Reusable) **executáveis**: a banca pode clonar o repositório, rodar `make reproduce-all` e reproduzir todos os números do TCC.

### B5.14.2 — Dockerfile

`docker/Dockerfile`:

```dockerfile
FROM python:3.11-slim-bookworm

# Sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs ffmpeg curl ca-certificates \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

# Variáveis ajustáveis em runtime
ENV PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

# Comando padrão exibe ajuda
CMD ["bash", "-lc", "make help"]
```

`docker-compose.yml`:

```yaml
version: "3.9"
services:
  tcc:
    build: { context: ., dockerfile: docker/Dockerfile }
    image: tcc-gatosdoc2:latest
    volumes:
      - ./data:/workspace/data
      - ./models:/workspace/models
      - ./results:/workspace/results
      - ~/.kaggle:/root/.kaggle:ro
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: bash
  dashboard:
    image: tcc-gatosdoc2:latest
    command: uv run streamlit run src/tcc_gatosdoc2/viz/dashboard.py --server.address 0.0.0.0
    ports: ["8501:8501"]
    volumes:
      - ./results:/workspace/results
    depends_on: [tcc]
```

Uso:

```bash
docker compose build
docker compose run --rm tcc make reproduce-all
docker compose up dashboard
# http://localhost:8501
```

### B5.14.3 — DVC remote (compartilhar com orientador)

```bash
# Configurar Google Drive como remote (precisa OAuth)
uv run dvc remote add -d gdrive_remote gdrive://<PASTA_ID_DRIVE>
uv run dvc remote modify gdrive_remote gdrive_use_service_account false

# Enviar todos os artefatos (datasets, modelos, resultados, banco do piloto)
uv run dvc push

# Orientador roda:
git clone <repo>
cd tcc_gatosdoc2
uv sync
uv run dvc pull   # baixa todos os dados/modelos do Drive
make reproduce-all
```

### B5.14.4 — Checksums dos artefatos

`scripts/compute_checksums.py`:

```python
"""Calcula SHA256 de todos os artefatos versionados e gera CHECKSUMS.txt."""
import hashlib
from pathlib import Path

PATHS = [
    "data/raw", "models", "results/e1", "results/e2",
    "results/e3", "results/pilot/pilot.sqlite",
]

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

lines = []
for path_str in PATHS:
    p = Path(path_str)
    if p.is_file():
        lines.append(f"{sha256(p)}  {p}")
    elif p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file() and not any(part.startswith(".") for part in f.parts):
                lines.append(f"{sha256(f)}  {f}")

Path("CHECKSUMS.txt").write_text("\n".join(lines))
print(f"Wrote {len(lines)} checksums")
```

Comando final no Makefile:

```makefile
checksums:
	uv run python scripts/compute_checksums.py
	git add CHECKSUMS.txt
	git commit -m "Update CHECKSUMS.txt for reproducibility audit"

reproduce-all: install download-datasets download-models benchmark-e1 benchmark-e2 benchmark-e3 pilot figures checksums
	@echo "Reprodução completa. Veja results/figures/ e CHECKSUMS.txt"
```

### B5.14.5 — Badge de reprodutibilidade no README

`README.md` do repositório (trecho):

```markdown
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Reproducible](https://img.shields.io/badge/reproducible-yes-brightgreen)
![DVC](https://img.shields.io/badge/data-DVC-13ADC7)
![License](https://img.shields.io/badge/license-MIT-green)

## Reprodução em 4 comandos

```bash
git clone https://github.com/<user>/tcc_gatosdoc2
cd tcc_gatosdoc2
uv sync && uv run dvc pull
make reproduce-all
```
```

### B5.14.6 — Lista de "artefatos obrigatórios" para anexar à monografia

| Artefato | Caminho | Citado em | Apêndice |
|---|---|---|---|
| Código fonte completo | GitHub repo | Cap. Implementação | A |
| Inventário de datasets | `docs/datasets_inventory.md` | Cap. Metodologia | B |
| Inventário de modelos | `docs/models_inventory.md` | Cap. Metodologia | B |
| Snapshot de ambiente | `results/*/runtime.json` | Cap. Reprodutibilidade | C |
| Métricas brutas (JSON) | `results/*/metrics.json` | Cap. Resultados | D |
| Banco do piloto (SQLite) | `results/pilot/pilot.sqlite` | Cap. Resultados | E |
| Figuras geradas | `results/figures/*.png` | Cap. Resultados | inline |
| Tabelas LaTeX | `results/figures/*.tex` | Cap. Resultados | inline |
| CHECKSUMS | `CHECKSUMS.txt` | Cap. Reprodutibilidade | F |

---

## B5.15 — Limitações e trabalho futuro

Esta seção é **acadêmica e honesta** — preenche o requisito do projeto base (PDF Sec. 9: "discutir realisticamente limitações") e funciona como ponte para o item 12 do todo (B6).

### B5.15.1 — Limitações conhecidas de B5

| # | Limitação | Origem | Mitigação aplicada | Trabalho futuro |
|---|---|---|---|---|
| **L1** | Vídeos do piloto são **sintéticos** (datasets concatenados), não capturas reais do Campus 2 | Decisão de não instalar câmeras no TCC | Vídeos preservam metadados rastreáveis e cobrem 5 perfis | Coleta real no Campus 2 em projeto pós-TCC (com autorização CET/USP) |
| **L2** | PetFace requer aprovação por Google Form que pode atrasar | Política dos autores | Solicitação enviada imediatamente; substituição parcial por HelloStreetCat | Documentar no relatório se for negada |
| **L3** | PPGNet-Cat (Akbar 2025) não tem pesos oficiais publicados | Estado da arte muito recente | Stub com plano de reimplementação; se inviável, registrado em L | Reprodução completa em fase 2 do projeto |
| **L4** | Avaliação só em **CPU** (i7 do Felipi); GPU dedicada não garantida | Hardware disponível | Reportar latências CPU honestamente; estimar GPU via fator conhecido | Re-rodar em GPU laboratório ICMC se conseguir acesso |
| **L5** | BAKS/BAUS exigem split known/unknown que **não vem nativamente** em todos os datasets | Limitação dos datasets | Simular holdout 20% dos IDs | Coletar dados próprios na colônia AEX com partição explícita |
| **L6** | SQLite tem limite prático de ~1 TB | Tecnologia escolhida | Suficiente para o projeto previsto | Migração planejada para PostgreSQL+PostGIS (B4.4.5) |
| **L7** | Detecção noturna sob IR é mais difícil que diurna | Domínio do problema | YOLO11+MegaDetector ambos treinados em IR via CCT2020 e Wildlife datasets | Treino fine-tune específico com vídeo noturno do Campus quando disponível |
| **L8** | Outras espécies (capivaras, gambás) não foram **explicitamente avaliadas** em E2 | Foco do TCC em gatos | SpeciesNet cobre 2.498 categorias incluindo essas espécies | Validação com dataset local pós-TCC |

### B5.15.2 — Trabalho futuro estruturado

Organizado em 3 horizontes:

**Curto prazo (≤ 3 meses pós-defesa):**
- Instalação física de **1 ponto piloto** (P1 — comedouro principal AEX) com câmera real para validar pipeline em campo
- Reprodução completa de PPGNet-Cat com pesos próprios
- Migração SQLite → PostgreSQL+PostGIS

**Médio prazo (3–12 meses):**
- Expansão para os 10 pontos com mix de perfis A/B/D/E1/E2
- Aplicativo móvel para AEX/ONG ASA registrar capturas/castrações via QR code
- Publicação dos dados em GBIF via Camtrap-DP
- Treino com dados locais (fine-tune de MiewID com gatos da colônia)

**Longo prazo (≥ 1 ano):**
- Modelos cat-specific treinados especificamente em colônias urbanas brasileiras
- Federação com outras universidades brasileiras com gatos (UNESP, UFSCar, UFMG)
- Integração com alimentadores inteligentes físicos (PDF Sec. 2.2.2(c)) — bloco B4.7 já preparou interface
- Avaliação de bem-estar baseada em comportamento (Action Units do CatFLW)

---

## B5.16 — Checklist final de B5

Antes de finalizar B5 e seguir para B6, o Felipi deve confirmar que **todos estes itens estão ✓**:

### Setup
- [ ] PC inventariado, ambiente Python 3.11 com uv instalado
- [ ] Hugging Face e Kaggle configurados com tokens
- [ ] FFmpeg, git-lfs, dvc instalados
- [ ] Repositório GitHub criado e estrutura canônica adotada

### Datasets
- [ ] Oxford-IIIT Pet baixado
- [ ] CatFLW baixado (Kaggle ou GitHub)
- [ ] Cat Individual Images baixado
- [ ] Cat Dataset (Crawford) baixado
- [ ] HelloStreetCat baixado (Hugging Face)
- [ ] **PetFace solicitado via Google Form** (aguardando aprovação)
- [ ] `docs/datasets_inventory.md` gerado
- [ ] Splits canônicos (seed=42) gerados onde aplicável

### Modelos
- [ ] YOLO11n pesos baixados
- [ ] MegaDetector v6 pesos baixados
- [ ] SpeciesNet instalado (pacote ou clone)
- [ ] MiewID-msv3 baixado do HF Hub
- [ ] MegaDescriptor-L-384 baixado do HF Hub
- [ ] OSNet via torchreid funcionando
- [ ] PPGNet-Cat: decisão tomada (reproduzir ou registrar como trabalho futuro)

### Benchmarks
- [ ] `make benchmark-e1` rodou — `results/e1/*/metrics.json` existe para YOLO11n e MegaDetector
- [ ] `make benchmark-e2` rodou — `results/e2/speciesnet/*/metrics.json` existe
- [ ] `make benchmark-e3` rodou — `results/e3/*/metrics.json` existe para MiewID, MegaDesc, OSNet (PPGNet opcional)
- [ ] MLflow tracking ativo (`mlruns/` populada)

### Piloto e Pipeline
- [ ] 5 vídeos representativos gerados em `data/pilot_videos/`
- [ ] `make pilot` executou com sucesso, `results/pilot/pilot.sqlite` existe
- [ ] Dashboard Streamlit abre e mostra dados do piloto
- [ ] `results/pilot/pipeline_log.json` mostra timing por estágio

### Tabelas e Figuras
- [ ] `make figures` rodou
- [ ] 11 figuras PNG geradas em `results/figures/`
- [ ] 7 tabelas LaTeX geradas
- [ ] Tabela `requirements_vs_results.tex` com NFR-001 a NFR-010 preenchida

### Reprodutibilidade
- [ ] `Dockerfile` testado (build + run completam)
- [ ] DVC remote configurado e `dvc push` executado
- [ ] `CHECKSUMS.txt` gerado e commitado
- [ ] README.md com badge "reproducible" e instruções `make reproduce-all`

### Documentação
- [ ] `docs/hardware_setup.md` preenchido
- [ ] `docs/datasets_inventory.md` atualizado
- [ ] `docs/models_inventory.md` preenchido
- [ ] `docs/reproducibility.md` escrito
- [ ] Apêndices A-F do TCC mapeados para arquivos do repo

Quando tudo ✓, o Felipi tem **evidência completa** de que cada decisão de B1-B4 foi validada — pronto para B6.

---

## Resumo executivo da Parte 3

| Bloco | Entregável | Itens |
|---|---|---|
| **B5.11** | Piloto offline + 5 vídeos representativos com ground-truth controlada | Script `build_pilot_videos.py` (5 funções) + tabela comparativa por perfil |
| **B5.12** | Pipeline fim-a-fim E0→E4 + dashboard Streamlit | `run_pilot.py` + `dashboard.py` |
| **B5.13** | Confronto Requisitos A2.0 × Resultados (tabela NFR-001 a NFR-010) | `generate_requirements_table.py` |
| **B5.14** | Reprodutibilidade total (Docker + DVC remote + CHECKSUMS + badge) | `Dockerfile` + `docker-compose.yml` + `compute_checksums.py` |
| **B5.15** | Limitações (L1-L8) + trabalho futuro estruturado em 3 horizontes | Documentação para Sec. Limitações da monografia |
| **B5.16** | Checklist final de 30+ itens para "B5 concluído" | Pronto para auditoria do orientador |

---

## B5 — Visão consolidada das 3 partes

| Parte | Foco | Linhas de código | KB do markdown |
|---|---|---|---|
| **Parte 1** | Setup + Repo + Datasets + Protocolo | ~250 | ~30 |
| **Parte 2** | Wrappers + Scripts + Métricas + Figuras | ~1.160 | ~46 |
| **Parte 3** | Piloto + Pipeline + Reprodutibilidade | ~600 | ~36 |
| **Total B5** | Manual operacional completo | **~2.000 linhas de código** | **~112 KB** |

**Próximo: B6 — Consolidação final da Etapa 2.** Vai cobrir:
- Mapeamento "Etapas do PDF base ↔ Blocos B1-B6"
- Hardware avaliado e excluído (ESP32-CAM, Jetson, LoRaWAN, 4G, solar)
- "Quem valida o quê" (Dra. Léa, ONG ASA, AEX, orientador)
- Cronograma atualizado
- Síntese das decisões consolidadas (Categorias I/II, 5 perfis, E0-E4, MiewID primário, SQLite + Camtrap-DP)
- Pré-leitura para Etapa 3 (LaTeX final)

---

## Fontes citadas nesta parte

- [Streamlit — framework para dashboards Python](https://docs.streamlit.io/)
- [folium — mapas Leaflet em Python](https://python-visualization.github.io/folium/)
- [streamlit-folium — integração](https://github.com/randyzwitch/streamlit-folium)
- [Plotly Express](https://plotly.com/python/plotly-express/)
- [Docker — Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [DVC remote — Google Drive](https://dvc.org/doc/user-guide/data-management/remote-storage/google-drive)
- [Frictionless Framework — validação de Data Packages](https://framework.frictionlessdata.io/)
- [FAIR Principles — Wilkinson et al., 2016](https://www.nature.com/articles/sdata201618)
- Akbar et al., 2025 (BAKS/BAUS) — carryover B4/B5
- Projeto base do TCC — `projeto_tcc.pdf` (Sec. 3.2, 7.5, 9)
