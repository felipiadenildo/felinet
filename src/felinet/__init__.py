"""felinet - Monitoramento por visao computacional de gatos do Campus 2.

Pacote principal do TCC. Organizacao:

    felinet.config           -- carrega configs/paths.yaml (perfis dev/prod)
    felinet.logging_setup    -- logging estruturado em JSONL
    felinet.datasets         -- adaptadores para PetFace e LILA-BC
    felinet.pipeline.fase1_ingestao    -- E0: EXIF, manifesto, Camtrap-DP
    felinet.pipeline.fase2_deteccao    -- E1: MegaDetector
    felinet.pipeline.fase3_classificacao -- E2: SpeciesNet + decisor + crops
    felinet.pipeline.fase4_reid        -- E3: MegaDescriptor + avaliacao
    felinet.pipeline.orquestrador      -- encadeia I -> II -> III -> IV
    felinet.comandos         -- subcomandos typer (CLI)
    felinet.utils            -- io, hash, conversores .tex
"""

from __future__ import annotations

__version__ = "0.2.0"
__author__ = "Felipi Adenildo Soares Sousa"
__email__ = "felipiadenildo@gmail.com"

__all__ = ["__version__"]
