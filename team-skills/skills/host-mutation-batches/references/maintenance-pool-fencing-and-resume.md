# Manutenção coordenada: pausa, compensação e retoma

Usa quando uma migração ou mudança de privilégios exige uma janela com produtores
parados e consumidores temporariamente desativados. Depende dos mecanismos reais
de pausa e configuração; não impõe downtime a mudanças que não o exigem.

## Delimitar a pausa

Guarda antes os estados dos pools, limites, schedules, ocorrências e flags que
fazem parte da operação. Se o contrato revisto pede pausa apenas dos work pools,
não a substituas por publicação de deployments, desativação de schedules ou
cancelamento de ocorrências. Pausar um pool impede novas admissões conforme o
orquestrador; não termina runs já lançadas nem impede outro caminho de execução.

Depois da pausa, volta a provar ausência de runs ativas e processos relevantes.
Uma lista vazia observada antes da pausa deixa uma corrida. Confirma também os
outros produtores que não passam por esses pools e a exclusão mútua disponível.

O preflight tem de reservar o tempo de aplicar, verificar, compensar e retomar
antes da próxima carga incompatível. Uma run iminente pode invalidar uma janela
que ainda está formalmente aberta. Não a cancela nem muda a janela por iniciativa
própria; apresenta a alternativa concreta ao operador.

## Consumidores e prontidão

Quando for necessário desligar flags, verifica a configuração efetivamente
consumida pela nova instância, sem valores secretos. Ficheiro escrito não prova
que o processo deixou de usar o estado anterior. Readiness após restart tem uma
espera limitada, incluída no orçamento da janela; não retomes produtores antes
da prova. O detalhe de sondas e estados do serviço pertence à skill
`verify-against-the-host`.

## Reverso explícito de privilégios

Deriva o reverso do snapshot de privilégios anterior: objeto, role beneficiária
do grant original, grantor, grant option e memberships relevantes. O consumidor
que perdeu SELECT efetivo pode herdá-lo de uma capacidade; dar um grant direto
ao login do consumidor cria um estado diferente do anterior.

Testa numa base descartável o delta efetivo para todos os consumidores relevantes,
a restauração exata e a recusa de objeto/grantor/estado inesperados. Executa a
compensação só pelo mecanismo autorizado e com recibo. Um GRANT compensatório
pode restaurar acesso sem desfazer o marcador da migração: não declares que o
schema voltou atrás, nem que repor o ficheiro central desfaz SQL já aplicado.

## Retoma idempotente

- Restaura só os estados alterados por esta manutenção. Um pool que já estava
  pausado continua pausado; não ativa tudo por conveniência.
- Revalida schedules e ocorrências antes de escrever. Drift não explicado exige
  revisão, não sobrescrita com o snapshot nem recriação de runs.
- Liga cada passo ao snapshot e à tentativa. Um erro depois do commit pode deixar
  a alteração aplicada sem recibo final; lê o estado antes de repetir.
- Distingue migração aplicada, compensação aplicada, saúde confirmada e retoma
  concluída. Se a retoma falhar, conserva uma via revista e idempotente de a
  concluir sem reaplicar a migração.

## Evidência e limites

Na manutenção de 30/10/2026 de `finance-infra` #166, a V8 retirava SELECT legado
herdado por um consumidor. A prova sintética em PostgreSQL 16.13 verificou grantor,
ACL, memberships, delta efetivo, grant option e atomicidade do reverso. Os testes
incluíram pausa só de pools, recusa de run ativa, drift de schedules antes da
retoma e impossibilidade de criar runs pela API do lote.

As revisões da janela expuseram uma run iminente e uma sonda HTTP anterior à
prontidão após restart. A revisão final acrescentou polling limitado e o operador
reportou PASS às 12:37 UTC. Isso suporta reservar tempo para prontidão e retoma;
não prova uma duração universal nem autoriza reutilizar aquele snapshot noutra
migração. Fonte pública de âmbito: [finance-infra #166](https://github.com/Vesconte-project/finance-infra/pull/166).
