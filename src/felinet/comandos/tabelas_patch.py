"""SNIPPET — substituir _latest_por_fase em src/felinet/comandos/tabelas.py.

Aceita runs do pipeline unificado (comando='pipeline executar') como
satisfazendo qualquer das fases logicas (ingestao/deteccao/classificacao).
Isso e' necessario porque a partir de v23 o pipeline grava um unico run com
subpastas 02_*, 03_*, 04_*, ..., em vez de tres runs separados por fase.
"""

# Mapeia o prefixo logico (usado pelas figuras/tabelas legadas) para os
# comandos reais que podem satisfazer aquela fase.
_COMANDOS_POR_FASE = {
    "ingestao":      ("ingestao", "pipeline executar"),
    "deteccao":      ("deteccao", "pipeline executar"),
    "classificacao": ("classificacao", "pipeline executar"),
}


def _latest_por_fase(
    raiz_runs,
    *,
    fonte: str,
    perfil_nome: str,
    prefixo_comando: str,
):
    """Retorna o ``manifest`` do run mais recente compativel com a fase.

    Aceita:
      - runs antigos (um por fase, ``extras.comando`` = 'ingestao'/'deteccao'/...);
      - runs unificados v23 (``extras.comando`` = 'pipeline executar').

    Em modo operacional os runs compartilham a mesma chave latest, portanto
    ``resolver_latest`` nao discrimina por fase. Aqui usa-se ``listar_runs``
    (ordenado por ``data_inicio`` desc) e filtra-se pelos comandos validos.
    """
    from felinet.runs import listar_runs

    comandos_validos = _COMANDOS_POR_FASE.get(
        prefixo_comando, (prefixo_comando,)
    )
    registros = listar_runs(
        raiz_runs,
        modo="operacional",
        fonte=fonte,
        perfil=perfil_nome,
    )
    for reg in registros:
        comando = (reg.manifest.get("extras") or {}).get("comando", "")
        if reg.manifest.get("sucesso") is not True:
            continue
        if any(comando.startswith(p) for p in comandos_validos):
            return reg.manifest
    return None
