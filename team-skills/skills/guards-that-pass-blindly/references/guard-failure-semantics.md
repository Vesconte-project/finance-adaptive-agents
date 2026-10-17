# Não ver é diferente de concluir

**Decisão:** separa erro de execução, resultado lógico e consequência operacional.
Um input ilegível tanto pode causar um falso `PASS` como uma acusação falsa de
história reescrita ou corrupção. Nenhum deles é evidência sobre o input.

**Evidência:** em 13/10/2026, num host Linux, um objeto Git inacessível à
identidade de recuperação originou um diagnóstico falso de ancestralidade.
A operação passou após separar a fonte do serviço do checkout mutável.
Versão Git não registada; caso único. No mesmo ciclo operacional, falhas de
consulta de política de armazenamento repetiram-se; um contrato revisto e
testado com restic 0.19.1 separou cópia, política e alerta. Não é uma prova de
que qualquer backup pode continuar sob qualquer erro.

## Dá semântica a cada resultado

Antes de interpretar uma comparação ou um exit code como resposta lógica,
prova que o comando executou, leu os inputs obrigatórios e conseguiu analisá-los.
No caso Git, distingue objetos ausentes/ilegíveis, falha de execução e resposta
de ancestralidade segundo a interface instalada. Não traduzas todo resultado
não-zero para “não é antecessor”. Um input opcional ausente também não é uma
resposta negativa sobre um input obrigatório.

Preserva fases e categorias fechadas de erro sem imprimir dados, segredos ou
stderr arbitrário. Um verificador deve permitir distinguir “não encontrei”,
“encontrei” e “não consegui verificar”. Se um serviço depende repetidamente de
ficheiros produzidos por outra identidade, considera uma fonte que ele próprio
mantém e valida, em vez de alargar permissões do checkout por defeito.

## A consequência depende da operação

Para uma função protetora **já autorizada**, num destino e âmbito previamente
aprovados, o operador pode decidir que uma consulta auxiliar indisponível não
impeça a proteção. Um exemplo é continuar uma cópia cifrada e comprovada,
registando separadamente `policy_unverified` e um alarme. Isso não declara a
política segura. Incompatibilidade confirmada continua a recusar; falha da
cópia continua a ser falha da cópia; falha da entrega do alarme tem estado próprio.

Operações destrutivas, irreversíveis ou que estabelecem uma fronteira nova
exigem a verificação necessária antes de avançar: por exemplo inicialização,
prune, retirada de legado ou destino novo. Sem uma decisão explícita de
continuidade e o respetivo modelo de risco, não inventes uma exceção.
**Isto não é uma recomendação geral de fail-open.**

## Verificação e limites

Sinais de falha: todo erro vira “corrupção”; zero inputs vira “limpo”; um sucesso
da cópia apaga o aviso de política; indisponibilidade auxiliar corta todas as
cópias sem que ninguém tenha escolhido esse compromisso.

Em testes descartáveis, cobre input ilegível, resposta negativa válida, consulta
indisponível, incompatibilidade confirmada e falha da própria operação. Confirma
o estado, o código de saída e o alerta de cada ramo. Não provoques essas falhas
em produção sem autorização específica.

**Não aplicar:** uma operação pura com um único resultado e erros já distintos
não precisa de novos estados; uma operação irreversível não herda a exceção
de disponibilidade de uma função protetora.
