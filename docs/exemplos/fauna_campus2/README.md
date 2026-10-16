# Exemplos da cascata em fauna do Campus 2 (Cap. 3 da monografia)

Execução ilustrativa, **fora dos experimentos** da monografia: as Fases II e III (MegaDetector v6 `MDV6-yolov10-c`,
SpeciesNet e o decisor, com os mesmos limiares dos experimentos) aplicadas a 36 fotografias de fauna registrada no
Brasil (6 por espécie: gato doméstico, gato-do-mato, gato-mourisco, quati, gambá e teiú).

- `registro.json`: cada foto, com observação do iNaturalist, autor e licença (CC0, CC BY ou CC BY-NC). As fotos não
  são versionadas aqui; o script abaixo as baixa de novo.
- `resultados.json`: saída de `felinet exemplos cascata` (caixas, confiança, top-5 do SpeciesNet e decisão).

Executado em CPU (Python 3.12, torch 2.5.1+cpu, PytorchWildlife 1.3.0, speciesnet 5.0.3), em menos de 2 minutos.

```bash
python scripts/baixar_exemplos_inat.py data/exemplos/fauna_campus2 docs/exemplos/fauna_campus2/registro.json  # as 36 fotos
felinet exemplos cascata --imagens data/exemplos/fauna_campus2 --saida docs/exemplos/fauna_campus2/resultados.json --dispositivo cpu
felinet monografia gerar --so fig:exemplos-cascata --so tab:exemplos-cascata   # grade, créditos e tabela do Cap. 3
```

- `selecao.json`: as espécies da tabela (na ordem das linhas) e as 9 fotos da grade (na ordem da grade). Os créditos
  da figura saem do `registro.json`, na mesma ordem.

Sem o segundo argumento, o script faz uma busca nova (o iNaturalist ordena por votos e o resultado muda com o
tempo); com ele, baixa exatamente as fotos usadas na monografia.

## Com o filtro geográfico do Brasil
`resultados_filtro_bra.json`: a mesma execução com `--pais BRA`, que liga o filtro geográfico oficial do SpeciesNet
e manda à validação humana os rótulos genéricos que incluem o gato doméstico (ex.: "cat family"). Mudanças em relação
à execução sem filtro, por espécie (gato / validação / outra / sem detecção):

| Espécie | Sem filtro | Com BRA |
|---|---|---|
| gato doméstico | 3 / 2 / 0 / 1 | 3 / 1 / 1 / 1 (um gato rotulado "hiena" passa a ser descartado) |
| teiú | 0 / 3 / 2 / 1 | 0 / 1 / 4 / 1 |
| demais | inalteradas | inalteradas |
