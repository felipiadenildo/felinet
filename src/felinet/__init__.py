"""felinet - Monitoramento por visao computacional de gatos do Campus 2.

Pacote principal do TCC. Organizacao:

    felinet.config           -- carrega configs/paths.yaml (perfis dev/prod)
    felinet.logging_setup    -- logging estruturado em JSONL
    felinet.datasets         -- adaptadores para PetFace e LILA-BC
    felinet.pipeline.fase1_ingestao    -- Fase I: EXIF, manifesto, Camtrap-DP
    felinet.pipeline.fase2_deteccao    -- Fase II: MegaDetector v6
    felinet.pipeline.fase3_classificacao -- Fase III: SpeciesNet + decisor + crops
    felinet.pipeline.fase4_reid        -- Fase IV: MegaDescriptor + avaliacao
    felinet.monografia       -- tudo o que a monografia recebe: registro, figuras, tabelas, verificacao
    felinet.pipeline.orquestrador      -- encadeia I -> II -> III -> IV
    felinet.comandos         -- subcomandos typer (CLI)
    felinet.utils            -- io, hash
"""

from __future__ import annotations

__version__ = "0.4.0.dev0"
__author__ = "Felipi Adenildo Soares Sousa"
__email__ = "felipiadenildo@gmail.com"

__all__ = ["__version__"]
