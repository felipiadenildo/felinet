# Manual do voluntário (AEX Gatos do C2)

O que o sistema faz pelas pessoas que cuidam da colônia, e o que ainda depende delas.

## O que o sistema faz
1. **Fase I:** recebe os vídeos dos cartões de memória e separa os quadros úteis (descarta escuros, estourados e
   repetidos).
2. **Fase II:** encontra animais nos quadros. Pessoas que aparecem são **desfocadas** antes de qualquer imagem ser
   guardada (LGPD).
3. **Fase III:** separa gatos domésticos da fauna do campus (gambá, quati, teiú, gato-do-mato…). Quando não tem
   certeza, **não decide sozinho**: manda para a fila de validação humana.
4. **Fase IV:** compara cada gato com o catálogo da colônia e sugere quem é.

## Onde entra o voluntário
| Situação | O que o sistema mostra | O que se pede |
|---|---|---|
| Fase III em dúvida | o recorte e as espécies mais prováveis | confirmar se é gato doméstico |
| Fase IV com margem estreita | o recorte e os indivíduos mais parecidos do catálogo | escolher o indivíduo certo |
| Nenhum indivíduo parecido | o recorte marcado como candidato a novo | confirmar se é gato novo e cadastrá-lo |

Cada decisão fica registrada com data e responsável (trilha de auditoria), para que os erros possam ser corrigidos.

## Estado atual
A interface para essas revisões (painel) ainda não existe; hoje as decisões são feitas pela linha de comando ou
pelos arquivos de resultado. O cadastro do catálogo precisa de fotos dos gatos já castrados (CED), de frente (face) e
de lado (flanco).
