# Retenção: referências executáveis e espaço físico

Lê antes de transformar um inventário em plano de remoção. Aplica-se a releases
locais imutáveis, com política autorizada de retenção; não autoriza remoções,
não define uma quantidade universal e não substitui backups.

## Distinguir auditoria de recuperação

Protege a atual, os predecessores verificados exigidos pela política e qualquer
release ainda necessária a processos, units, timers, pedidos pendentes, pull
steps do orquestrador, observadores e recuperação executável. Inclui DEV: uma
plataforma ainda não migrada pode ter registos e layout anteriores ao engine.
Configuração nova ausente não demonstra que a instalação antiga não existe.

Uma referência histórica a um SHA não obriga por si só a conservar os binários.
Classifica cada documento pela semântica e pelos consumidores do seu formato:

- **Recuperação executável:** um mecanismo ainda pode escolher aquele alvo,
  restaurar a partir dele ou executar código nele. Conserva-o enquanto esse
  compromisso existir, mesmo que o documento seja antigo.
- **Auditoria:** regista uma tentativa ou resultado passado e nenhum consumidor
  operacional depende do conteúdo da release. Preserva o recibo, hashes e
  proveniência segundo a política de auditoria; os binários seguem a retenção.
- **Desconhecido:** falta provar qual dos casos se aplica. Protege provisoriamente
  o âmbito que pode depender dele e pede classificação, sem chamar-lhe auditoria.

Verifica código e configuração de rollback, recovery, forecast e verificadores.
Um histórico que é percorrido para selecionar recuperação tem efeito operacional;
um histórico apenas apresentado num relatório não tem o mesmo efeito. Não
altera nem apaga recibos para conseguir candidatos.

Conta proteções por motivo e também motivos exclusivos: uma release pode estar
em várias categorias. Para cada bloqueio, distingue releases diretamente afetadas
do limite superior de dependências desconhecidas; não somes sobreposições. Resolve
indireções por fontes declaradas, com extrator autorizado de caminhos e saída
sanitizada. Só listar nomes de EnvironmentFiles não prova ausência de referências
nos seus conteúdos. Scripts e gestores de utilizador exigem o mesmo cuidado.

## Medir o que pode efetivamente ser libertado

1. Fixa o conjunto exato de caminhos candidatos e o instante do inventário.
2. Conta blocos alocados uma vez por `(st_dev, st_ino)`, usando a unidade de
   `st_blocks` do sistema. Não uses tamanho lógico nem a soma de `du` independente
   por pasta como ganho do conjunto: hard links podem atravessar releases.
3. Para inodes partilhados, compara links encontrados no conjunto com `st_nlink`.
   Links fora dele conservam o conteúdo. Verifica também descritores abertos e
   mapas de processos: unlink pode não libertar os blocos enquanto estão em uso.
   Falta de acesso a essa inspeção é incerteza, não zero referências.
4. Mede a união e os grupos; não somes grupos com inodes comuns. Limita memória,
   disco e duração do próprio medidor. É possível guardar só os inodes de link
   múltiplo, com contadores agregados para os restantes, se a estabilidade do
   inventário e a correção desse algoritmo forem verificadas.
5. Volta a verificar identidade, links e referências antes de qualquer remoção.
   Mudança durante a medição invalida a estimativa afetada.

Reflinks, compressão, snapshots e contabilidade do filesystem podem alterar o
reclaim real. Chama ao resultado uma estimativa e mede espaço disponível antes e
depois da operação autorizada. Um plano com caminhos e bytes não é autorização.

## Evidência e limites

Em 30/10/2026, num host Linux com releases locais, proteger todo o histórico de
recibos deixava zero candidatos em oito componentes PROD. A classificação inicial
identificou 149 releases PROD protegidas apenas por histórico e seis DEV ainda
sem identidade resolvida. A medição de 155 caminhos contou 2 106 998 inodes e
68 991 909 888 bytes alocados, sem links externos ou retenções por processos
identificados nessa leitura. Os 44 documentos de manutenção/preview continuavam
por classificar: o resultado explicitava `removal_plan_ready=false` e zero
remoções. Logo, espaço medido não era espaço aprovado para apagar.

A primeira versão do medidor excedeu o orçamento da sua base auxiliar; a seguinte
limitou o índice aos inodes partilhados. Este caso justifica medir o custo do
inventário, não assumir que todo medidor precise dessa implementação. Os números
são a amostra de 30/10, não uma política nem uma previsão para outro host.
