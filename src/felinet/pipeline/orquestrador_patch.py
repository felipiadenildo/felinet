"""SNIPPET — substituir RelatorioCascata.como_dicionario() em
src/felinet/pipeline/orquestrador.py.

Adiciona aliases para que o `metricas_resumo` do run unificado seja
consumivel pelos comandos legados de figuras/tabelas que esperam os
nomes 'n_entradas', 'n_animais_detectados', 'n_felis_catus'.
"""

# Apenas substituir o metodo como_dicionario() da classe RelatorioCascata:


def como_dicionario(self) -> dict:
    return {
        # nomes canonicos
        "n_brutas": self.n_brutas,
        "n_manifesto": self.n_manifesto,
        "n_deteccoes_animal": self.n_deteccoes_animal,
        "n_classificacoes_felis_catus": self.n_classificacoes_felis_catus,
        "n_crops_gerados": self.n_crops_gerados,
        "n_embeddings": self.n_embeddings,
        "sucesso": self.sucesso,
        "mensagem": self.mensagem,
        # aliases legados (consumidos por figuras/comparativo_fontes)
        "n_entradas":             self.n_manifesto,
        "n_animais_detectados":   self.n_deteccoes_animal,
        "n_felis_catus":          self.n_classificacoes_felis_catus,
    }
