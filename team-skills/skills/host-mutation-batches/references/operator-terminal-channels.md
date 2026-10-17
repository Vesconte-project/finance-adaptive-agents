# Um bloco silencioso pode estar em três estados diferentes

**Decisão:** antes de repetir uma possível mutação, distingue espera prevista,
prompt privado e processo suspenso. O silêncio não prova que o comando não começou.

**Evidência:** dois episódios em 14 e 16/10/2026 num host Linux. Um comando
interativo de credenciais ficou parado antes da substituição; noutro, um
paginador e o comando que o lançou estavam em estado `T+`. Uma espera explícita
de observação foi depois confundida com bloqueio. No segundo episódio:
systemd 259.5; versões de sudo e do paginador não registadas. Não atribuir o
primeiro bloqueio a um sinal específico que não foi recolhido.

## Escolhe o canal antes de entregar o bloco

Um heredoc fornece stdin ao interpretador; não prova que um programa interativo
tenha acesso ao terminal ou esteja no grupo de processos em primeiro plano.
Há programas que leem um terminal separado. Confirma o mecanismo antes de
embutir um prompt numa sequência. Quando necessário, separa o comando interativo
do bloco não interativo, conservando os guardas, o alvo e a ordem aprovados.

Desativa paginadores nos comandos destinados a blocos não interativos, usando
opções suportadas pela ferramenta. Não basta fazê-lo só nos comandos do gestor
de serviços: um comando auxiliar pode abrir outro paginador. Para uma espera
deliberada, imprime a duração e o próximo resultado esperado antes de esperar.
Nunca peças que o operador cole um segredo até o prompt privado estar confirmado.

## Diagnostica sem expor ou repetir

Sinais: nenhum prompt apesar de ser esperado; retorno que não chega; estado
parado (`T` em Linux) em vez de espera normal; paginador filho de um comando do
bloco. Recolhe primeiro apenas PID, PPID, estado, tempo e nome do executável.
Evita argv e ambiente, que podem conter segredos. Um processo `sleep` isolado
não prova a que bloco pertence.

Antes de retomar, confirma se a mutação começou, consultando o recibo ou estado
específico da operação. Não uses um PID antigo sem reconfirmar a identidade.
Terminar ou continuar processos exige autorização e âmbito exatos; não mates
um grupo inteiro para desbloquear um terminal. Depois, exige o resultado final
do bloco, não apenas o desaparecimento do processo.

**Não aplicar:** jobs sem terminal nem interação; uma espera conhecida e ainda
dentro do prazo não justifica interromper ou repetir o trabalho.
