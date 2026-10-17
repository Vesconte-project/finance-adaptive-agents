# Zero restantes não diz quem apagou

**Decisão:** o estado final vazio não atribui eliminações a uma execução.
Antes de repetir uma retirada falhada, localiza a primeira ação destrutiva e
reconcilia as tentativas e intervenções separadamente.

**Evidência:** caso único, 14/10/2026, com restic 0.19.1 num host Linux e
armazenamento remoto. Uma retirada recusou nomes inesperados antes da primeira
eliminação. Dois objetos foram removidos nominalmente numa ação separada;
a tentativa seguinte retirou o restante conjunto e os ficheiros locais.
O recibo vazio foi preservado e uma verificação independente confirmou ausência.
Não generalizar esta ordem a outras implementações: inspeciona a versão exata.

## Depois de uma recusa

Determina a fase e o motivo por metadados sanitizados. Um exit não-zero tanto
pode anteceder qualquer escrita como ocorrer depois de uma eliminação parcial.
Cruza a ordem do código instalado com o recibo e os inventários antes/depois.
Não uses uma mensagem final de erro para inferir atomicidade.

**Nunca alargues padrões de nomes para desbloquear uma limpeza.** Um nome
inesperado exige classificação e decisão dentro do âmbito autorizado. Não
concluas pelo nome que o conteúdo é descartável. Se o operador aprovar retirar
objetos exatos separadamente, guarda essa ação e o inventário seguinte; não
a atribuas depois à rotina principal.

Preserva a tentativa falhada antes de criar o recibo seguinte. Não apagues um
recibo vazio para fingir que nada aconteceu, nem o trates como sucesso. Antes
de retomar, revalida a fonte, o alvo, os bloqueios e os pré-requisitos de
recuperação; a aprovação anterior não autoriza um alvo mais amplo.

## Verificação e limites

Sinais de falha: “terminou a zero, logo a tentativa anterior nada apagou”;
recibos sobrescritos; remoções manuais sem registo; padrões progressivamente
mais permissivos após cada recusa.

O relatório final separa estado residual de ações executadas: o que cada
tentativa retirou, o que ficou e o que foi removido fora da rotina. Usa
identidades e inventários adequados ao contrato; só contagens não chegam se
houver escritores concorrentes. Confirma ausência pelo caminho local e remoto
relevante, sem confundir objetos técnicos transitórios com os dados retirados.

**Não aplicar:** verificações apenas de leitura ou operações transacionais
cuja reversão integral foi comprovada. O sucesso de uma reversão também precisa
de evidência; não o assumes pela presença de um trap.
