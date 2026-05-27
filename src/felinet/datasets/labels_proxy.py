"""Mapeamento de classes (subpastas/categorias) para rótulo binário Felis-vs-resto.

O Bloco 9 (matriz de confusão Felis-vs-resto por fonte) precisa de ground
truth por imagem. Sem rotulação manual exaustiva, recorre-se a dois proxies:

1. **Label de fonte**: para datasets monocategoria (e.g. ``kaggle_cats`` é
   ~100% Felis catus), assume-se a maioria como verdade.
2. **Label por categoria**: para datasets ``layout=por_classe`` (e.g.
   ``felidae``, com subpastas ``bobcat/``, ``puma/``, ``domestic_cat/``),
   o nome da subpasta é o rótulo verdadeiro.

Este módulo centraliza ambos os mapas e a função de despacho.
"""

from __future__ import annotations

from typing import Literal

RotuloBinario = Literal["felis_catus", "outros"]

# ============================================================
# Mapa 1: label proxy POR FONTE (datasets monocategoria)
# ============================================================
# Usar quando o dataset é assumidamente homogêneo. Valor None significa
# "não há proxy de fonte; precisa label por categoria".

LABEL_PROXY_POR_FONTE: dict[str, RotuloBinario | None] = {
    "kaggle_cats": "felis_catus",  # dataset de gatos domésticos
    "lila_ena24": "outros",  # camera-trap norte-americana, fauna selvagem
    "petface": None,  # Re-ID: não entra na matriz de espécie
    "felidae": None,  # multicategoria: usar mapa por classe
    "campus2_2025": None,  # multicategoria potencial
}


# ============================================================
# Mapa 2: nome de subpasta (classe origem) → rótulo binário
# ============================================================
# Cobre os 66 rótulos do Felidae Conservation Fund e categorias comuns de
# outros datasets COCO Camera Traps. Comparação case-insensitive.
# Tudo que NÃO estiver aqui é tratado como "outros" por padrão.

CLASSES_FELIS_CATUS = {
    "domestic_cat",
    "domestic cat",
    "felis_catus",
    "cat",
    "house_cat",
    "feral_cat",
}

# Outras espécies de felídeos selvagens — explicitamente "outros" (NÃO Felis catus).
# Listadas para legibilidade e para evitar que sejam classificadas como Felis
# por engano em algum cruzamento futuro.
CLASSES_OUTROS_FELIDEOS = {
    "bobcat",
    "puma",
    "mountain_lion",
    "cougar",
    "jaguar",
    "leopard",
    "ocelot",
    "lynx",
    "margay",
    "jaguarundi",
    "serval",
    "caracal",
}


def rotulo_por_classe(classe_origem: str) -> RotuloBinario:
    """Mapeia o nome da subpasta de origem para rótulo binário.

    Comparação case-insensitive e tolerante a espaços/underscores.
    """
    if not classe_origem:
        return "outros"
    chave = classe_origem.strip().lower().replace(" ", "_")
    if chave in CLASSES_FELIS_CATUS:
        return "felis_catus"
    return "outros"


def rotulo_por_fonte(fonte: str) -> RotuloBinario | None:
    """Devolve o rótulo proxy de fonte, ou None se não há proxy aplicável."""
    return LABEL_PROXY_POR_FONTE.get(fonte)


def resolver_rotulo_verdadeiro(fonte: str, classe_origem: str | None) -> RotuloBinario | None:
    """Determina o rótulo verdadeiro de uma imagem.

    Prioridade:
    1. Se a fonte tem proxy monocategoria definido, usa ele (mais confiável).
    2. Se há ``classe_origem`` da subpasta de ingestão, mapeia via
       :func:`rotulo_por_classe`.
    3. Caso contrário, devolve ``None`` (sem ground truth — imagem fica fora
       da matriz de confusão).
    """
    proxy = rotulo_por_fonte(fonte)
    if proxy is not None:
        return proxy
    if classe_origem:
        return rotulo_por_classe(classe_origem)
    return None


def fontes_com_ground_truth(fontes: list[str]) -> list[str]:
    """Filtra fontes que têm algum tipo de ground truth disponível.

    Inclui fontes com proxy monocategoria E fontes ``por_classe`` (assume-se
    que estas terão ``classe_origem`` registrada na ingestão).
    """
    out = []
    for f in fontes:
        if rotulo_por_fonte(f) is not None or f in {"felidae", "campus2_2025"}:
            out.append(f)
    return out
