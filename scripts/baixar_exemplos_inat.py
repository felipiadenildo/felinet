"""Baixa as fotografias dos exemplos da cascata (Cap. 3): iNaturalist, Brasil (place_id 6878), nível pesquisa,
licenças CC0, CC BY e CC BY-NC, seis por espécie.

Uso:
  python scripts/baixar_exemplos_inat.py <pasta>                  # nova busca (o resultado muda com o tempo)
  python scripts/baixar_exemplos_inat.py <pasta> <registro.json>  # baixa exatamente as fotos do registro
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DESTINO = Path(sys.argv[1])
# taxon_id do iNaturalist (o nome sozinho às vezes não resolve)
ESPECIES = {
    "gato_domestico": ("Felis catus", 118552),
    "gamba": ("Didelphis albiventris", 42658),
    "quati": ("Nasua nasua", 41670),
    "gato_mourisco": ("Herpailurus yagouaroundi", 197781),
    "gato_do_mato": ("Leopardus guttulus", 544590),
    "teiu": ("Salvator merianae", 318758),
}
LICENCAS = "cc0,cc-by,cc-by-nc"


def get(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "felinet-exemplos/0.1 (monografia USP)"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


if len(sys.argv) > 2:
    DESTINO.mkdir(parents=True, exist_ok=True)
    registro = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    for r in registro:
        (DESTINO / r["arquivo"]).write_bytes(get(r["foto"]))
        time.sleep(1.0)
    (DESTINO / "registro.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"{len(registro)} fotos do registro baixadas")
    sys.exit(0)

registro = []
for chave, (taxon, tid) in ESPECIES.items():
    q = urllib.parse.urlencode(
        {
            "taxon_id": tid,
            "place_id": 6878,
            "quality_grade": "research",
            "photos": "true",
            "photo_license": LICENCAS,
            "per_page": 30,
            "order_by": "votes",
        }
    )
    dados = json.loads(get(f"https://api.inaturalist.org/v1/observations?{q}"))
    n = 0
    for obs in dados["results"]:
        foto = next(
            (f for f in obs.get("photos", []) if f.get("license_code") in LICENCAS.split(",")), None
        )
        if not foto:
            continue
        url = foto["url"].replace("square", "large")
        arq = DESTINO / f"{chave}_{obs['id']}.jpg"
        arq.write_bytes(get(url))
        registro.append(
            {
                "arquivo": arq.name,
                "especie": taxon,
                "observacao": f"https://www.inaturalist.org/observations/{obs['id']}",
                "licenca": foto["license_code"],
                "atribuicao": foto.get("attribution", ""),
                "foto": url,
            }
        )
        n += 1
        time.sleep(1.0)  # respeita o limite da API
        if n >= 6:
            break
    print(chave, n)
(DESTINO / "registro.json").write_text(
    json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8"
)
