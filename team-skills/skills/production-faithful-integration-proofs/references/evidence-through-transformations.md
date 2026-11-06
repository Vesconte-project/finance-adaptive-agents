# Seguir a evidência até à decisão do consumidor

Usa dentro do âmbito da Skill principal: uma prova de integração ou de helper operacional
cuja conclusão influencia uma alteração real em produção. O caso relevante é um produtor
observar uma rejeição ou resolver uma identidade, mas um consumidor posterior decidir a partir
de dados transformados, relatórios ou manifestos. O sinal típico é cada componente passar os
seus testes enquanto a decisão composta contradiz a observação original. Aplica-se a
importação, normalização, geração de evidência e previews operacionais; não exige reproduzir
uma infraestrutura inteira para testar lógica pura.

O padrão a procurar é simples: o produtor rejeita uma entrada; uma transformação remove
a entrada problemática; um relatório descreve apenas os sobreviventes como limpos; o
consumidor usa esse relatório para permitir uma ação. Testar a rejeição no produtor e a
aceitação de um relatório limpo no consumidor separadamente não testa essa composição.

## O que faltou às provas anteriores

Num caso sintético fornecido, um adaptador observou uma linha com Close nulo e adjusted Close
válido, registou uma invalidade e descartou a linha durante a normalização. O refresh recusou
a resposta completa, com contagem de invalidade 1. Contudo, um relatório separado recalculou
a qualidade apenas sobre as linhas sobreviventes e declarou 0. O preview de correção consumia
esse relatório e podia chegar a `ready_for_human_review`.

Todas as sessões legítimas estavam presentes. A falha era a perda de uma observação
negativa, não falta de cobertura do calendário. Reintroduzir a data descartada no inventário
teria alterado o significado dos dados sem corrigir a qualidade da evidência.

Os testes anteriores exercitavam o adaptador, a rejeição do refresh, o inventário e o preview
separadamente. As entradas do preview eram construídas diretamente como frames normalizados.
Até um teste de diagnóstico confirmava rejeição e cache intacta, mas nenhum demonstrava que
a rejeição chegava à decisão do preview. Mais testes isolados e PostgreSQL real não cobriam
essa ligação.

## Construir um mapa pequeno e verificável

Antes de acrescentar fixtures, escreve o caminho que determina a decisão:

`observação original → transformação → evidência emitida → consumidor → decisão → primeiro efeito`

Para cada passagem, identifica:

- o valor observado, a população e a tentativa a que pertence;
- o que pode ser descartado, normalizado, omitido ou convertido em valor por defeito;
- o campo efetivamente transportado e o predicado que o consumidor lê;
- a decisão esperada e o primeiro efeito que uma recusa tem de preceder.

No caso acima, a observação de qualidade da tentativa completa precisava de acompanhar o
frame normalizado até ao relatório. O consumidor tinha de verificar a qualidade original e
a validação combinada. A mera presença de um campo novo no relatório não provava esse efeito.

Escolhe uma observação adversarial que possa desaparecer numa transformação e segue-a por
todas as setas. Inspeciona os valores intermédios para localizar a perda, mas afirma também
a decisão final. Uma nova observação explicitamente validada pode mudar a decisão; o simples
descarte de linhas não demonstra que a rejeição original deixou de ser relevante.

Confirma que o caso chega ao predicado que queres provar. Se outro guard bloquear primeiro,
o teste negativo pode passar sem testar a propagação da evidência. Quando isso for relevante,
escolhe um item que pertença também às chaves candidatas da operação e verifica a causa da
recusa. Não retires os restantes guards para forçar o resultado; mantém um controlo válido.

## Transportar significado, não apenas contagens

Mantém separadas a qualidade observada antes do descarte e a forma dos dados sobreviventes.
Preserva o inventário de datas realmente observado após normalização; metadados de rejeição
não são licença para inserir datas ausentes.

Quando o contrato exige prova de zero invalidade, distingue zero conhecido de desconhecido.
No contrato deste caso, apenas inteiros exatos não negativos eram contagens válidas; ausência,
valores negativos, booleanos, strings e floats não provavam zero. Um relatório antigo sem a
secção obrigatória também não provava qualidade. Por outro lado, uma invalidade conhecida
nas linhas sobreviventes continuava conhecida mesmo com qualidade original desconhecida.
Noutro sistema, confirma os tipos e as regras de compatibilidade exigidos pelo consumidor;
não convertas ausência de prova em zero por conveniência.

A regra de combinação depende das populações. Neste adaptador, `max(raw_count,
surviving_count)` evitava contar duas vezes populações sobrepostas e preservava o bloqueio.
Não é uma regra geral de cardinalidade: populações disjuntas, sobreposição parcial ou métricas
diferentes exigem outra demonstração. Documenta essa relação antes de combinar valores.

Liga a evidência completa ao digest do plano quando esse for o contrato. Um hash prova a
ligação aos bytes fornecidos; não demonstra completude nem correção. Evidência regenerada
muda o objeto a rever e selar. Uma aprovação anterior não autoriza automaticamente o plano
alterado, e um digest coincidente não transforma um plano bloqueado em plano aplicável.

## Provar a ligação com o produtor e o consumidor reais

Substitui apenas a fronteira externa necessária por dados sintéticos. Deixa o adaptador,
a normalização, o diagnóstico, a emissão de evidência e o consumidor gerarem e consumirem as
suas estruturas reais. Não repares manualmente o relatório no caso nominal. Alterações
intencionais para testar contradições ou compatibilidade devem ser identificadas como tal.

A evidência fornecida relata a seguinte matriz sintética após a correção:

| Entrada ou alteração adversarial | Resultado relatado |
| --- | --- |
| Close nulo e adjusted Close válido, com descarte | Bloqueado |
| Adjusted Close inválido | Bloqueado |
| Qualidade original desconhecida | Bloqueado |
| Relatório legado sem qualidade anterior ao descarte | Bloqueado |
| Zero normalizado em contradição com rejeição original | Bloqueado |
| Omissão exata limpa, com qualidade conhecida | Pronto apenas para revisão humana |

Para testar a fronteira de efeitos, tenta a aplicação de um plano bloqueado apenas num
ambiente descartável autorizado e verifica que falha antes de criar backups ou apagar linhas.
Compara bytes da cache e linhas canónicas antes/depois. Nos cinco casos negativos fornecidos,
essas verificações foram relatadas como satisfeitas. O controlo positivo distingue um
contrato implementado de um gate que bloqueia tudo; neste caminho, chegar à revisão não
demonstrou aplicação bem-sucedida, e o controlo positivo não foi aplicado.

## Identidade: o mesmo resolver pode receber entradas diferentes

Um segundo caso fornecido encontrou dois componentes a resolver a mesma listagem de modo
diferente: um convertia exchange `NYQ` e MIC vazio em `XNYS`; o outro obtinha `UNKNOWN` e
recusava a mesma exceção aprovada. Uma fixture do consumidor construída independentemente
não revelava a divergência. Ficheiros de módulo idênticos também não provavam equivalência
dos argumentos que os callers passavam.

A correção foi relatada como testada alimentando o consumidor real com a saída real do
produtor, incluindo metadados tabulares NULL, Nasdaq, sufixos estrangeiros e ambiguidade.
Para aplicar o método noutro projeto, acompanha a identidade e os campos de origem através
dos callers; confirma o âmbito exato da decisão, em vez de comparar apenas nomes de funções
ou módulos.

Testa também contradições que afetem esse âmbito: neste caso, entradas aprovadas e revogadas
para o mesmo âmbito não podiam resultar em aprovação por se ler primeiro a entrada aprovada.
Uma reaprovação explicitamente revista era um caso separado. Isto sustenta testar conflitos
no contrato real, não copiar a política inteira desse manifesto para outros projetos.

## Evidência e limites

A evidência sintética fornecida relata uma reprodução anterior à correção com invalidade 1
no refresh e 0 no relatório. Após a correção, os seis casos ligaram download sintético,
adaptador real, diagnóstico, evidência e preview com PostgreSQL descartável e Parquet real;
os cinco casos negativos incluíram tentativa de aplicação recusada. A fronteira externa
foi sintética: isto não foi uma execução contra o fornecedor de produção.

O caso de identidade tem evidência relatada de testes produtor–consumidor. Os detalhes de
reprodução do caso de qualidade não demonstram independentemente todos os resultados do
caso de identidade. Este pacote apresenta o método e os relatos sanitizados; não inclui
código, fixtures ou uma suite independentemente executável, nem relata novas execuções.

Ao reportar uma prova, distingue caminhos completos de componentes testados separadamente.
Havia testes separados de aplicação aprovada, restauro, rollback, falha parcial, retoma e
fences. Não constituíam um único caminho comprovado de fornecedor até aplicação, rebuild,
features e recuperação da página. Respostas reais do fornecedor, permissões, concorrência,
leases operacionais e recuperação de produção continuavam por verificar. Esta referência
não autoriza essas operações nem garante que o método descubra todas as perdas de evidência.
